import connexion
from connexion import NoContent
from models import PlayerEvent, ServerEvent, make_session
from models import Base, engine
from dateutil import parser
import yaml
import json
from sqlalchemy import create_engine
import sqlalchemy
import logging
import logging.config
from datetime import datetime
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


SERVICE_NAME = "storage"

# Load logging configuration from YAML
with open("config/log_conf.yml", "r") as log_file:
    log_config = yaml.safe_load(log_file)
    log_config['handlers']['file']['filename'] = f'logs/{SERVICE_NAME}.log'
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Load the configuration file
with open('config/storage_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Extract database settings from the configuration file
db_config = app_config['datastore']
db_url = f"mysql://{db_config['user']}:{db_config['password']}@{db_config['hostname']}:{db_config['port']}/{db_config['db']}?charset=utf8mb4"

# Create engine using the loaded config
engine = create_engine(db_url)

# Ensure that all tables are created before starting the application
Base.metadata.create_all(engine)

# Extract Kafka connection details
kafka_config = app_config['events']['kafka']
KAFKA_HOST = f"{kafka_config['hostname']}:{kafka_config['port']}"
TOPIC_NAME = kafka_config['topic']

def process_messages():
    """Consume Kafka messages and store them in the database"""
    client = KafkaClient(hosts=KAFKA_HOST)
    topic = client.topics[str.encode(TOPIC_NAME)]
    
    consumer = topic.get_simple_consumer(
        consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST
    )

    logger.info("Kafka Consumer started... Listening for messages.")

    for msg in consumer:
        if msg is not None:
            msg_str = msg.value.decode('utf-8')
            msg_json = json.loads(msg_str)

            logger.info(f"Received message: {msg_json}")
            payload = msg_json["payload"]

            session = make_session()

            try:
                if msg_json["type"] == "player_event":
                    event = PlayerEvent(
                        player_id=payload['player_id'],
                        server_id=payload['server_id'],
                        action=payload['action'],
                        score=payload['score'],
                        timestamp=parser.isoparse(payload['timestamp']),
                        trace_id=payload['trace_id']
                    )
                    session.add(event)
                    logger.info(f"Stored Player event: {payload}")

                elif msg_json["type"] == "server_event":
                    event = ServerEvent(
                        server_id=payload['server_id'],
                        uptime=payload['uptime'],
                        cpu_usage=payload['cpu_usage'],
                        memory_usage=payload['memory_usage'],
                        timestamp=parser.isoparse(payload['timestamp']),
                        trace_id=payload['trace_id']
                    )
                    session.add(event)
                    logger.info(f"Stored Server event: {payload}")

                session.commit()
                consumer.commit_offsets()  # Ensure offset is committed only after successful processing
                
            except sqlalchemy.exc.IntegrityError as e:
                logger.error(f"Duplicate entry detected: {e}")
                session.rollback()  # Rollback the transaction if a duplicate is detected

            finally:
                session.close()


def setup_kafka_thread():
    consumer_thread = Thread(target=process_messages)
    consumer_thread.daemon = True
    consumer_thread.start()

# Define a function to fetch player events within a date range
def get_player_events(start_timestamp, end_timestamp):
    session = make_session()
    start_time = parser.isoparse(start_timestamp)
    end_time = parser.isoparse(end_timestamp)

    # Query the PlayerEvent table
    events = session.query(PlayerEvent).filter(
        PlayerEvent.date_created >= start_time,
        PlayerEvent.date_created < end_time
    ).all()

    # Convert the events to dictionaries
    event_list = [event.__dict__ for event in events]
    for event in event_list:
        event.pop('_sa_instance_state', None)  # Remove SQLAlchemy internal state

    session.close()
    return event_list

# Define a function to fetch server events within a date range
def get_server_events(start_timestamp, end_timestamp):
    session = make_session()
    start_time = parser.isoparse(start_timestamp)
    end_time = parser.isoparse(end_timestamp)

    # Query the ServerEvent table
    events = session.query(ServerEvent).filter(
        ServerEvent.date_created >= start_time,
        ServerEvent.date_created < end_time
    ).all()

    # Convert the events to dictionaries
    event_list = [event.__dict__ for event in events]
    for event in event_list:
        event.pop('_sa_instance_state', None)  # Remove SQLAlchemy internal state

    session.close()
    return event_list

# Create the connexion app
app = connexion.FlaskApp(__name__, specification_dir='')

# Add the API specification
app.add_api("ACIT3855-ProjectStorage.yaml", strict_validation=True, validate_responses=True)

# Run the app
if __name__ == "__main__":
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")

