import connexion
from connexion import NoContent
from connexion import Flaskapp
import httpx
import uuid
import yaml
import logging
import logging.config
import datetime
import json
from pykafka import KafkaClient


SERVICE_NAME = "receiver"

# Load logging configuration from YAML
with open("config/log_conf.yml", "r") as log_file:
    log_config = yaml.safe_load(log_file)
    log_config['handlers']['file']['filename'] = f'logs/{SERVICE_NAME}.log'
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Load the app configuration from the YAML file
with open('config/receiver_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Extract Kafka details from the config
KAFKA_HOST = f"{app_config['events']['kafka']['hostname']}:{app_config['events']['kafka']['port']}"
TOPIC_NAME = app_config["events"]["kafka"]["topic"]

# Initialize Kafka client
client = KafkaClient(hosts=KAFKA_HOST)
topic = client.topics[str.encode(TOPIC_NAME)]
producer = topic.get_sync_producer()

def send_event_to_kafka(event_type, event_data):
    """Publishes an event to Kafka"""
    msg = {
        "type": event_type,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": event_data
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode("utf-8"))
    logger.info(f"Produced event to Kafka: {msg}")

# Extract the event URLs from the config
PLAYER_EVENT_URL = app_config['events']['player']['url']
SERVER_EVENT_URL = app_config['events']['server']['url']

# Function for receiving player events and sending them to the storage service
def receive_player_event(body):
    # Generate a unique trace_id using uuid
    trace_id = str(uuid.uuid4())
    # Prepare event data for storage
    event_data = {
        "player_id": body["player_id"],
        "server_id": body["server_id"],
        "action": body["action"],
        "score": body["score"],
        "timestamp": body["timestamp"],
        "trace_id": trace_id
    }
    
    # Log that an event was received with the trace ID
    logger.info(f"Received Player event; Trace Id:{trace_id}")    
    send_event_to_kafka("player_event", event_data)

    # Return the appropriate response based on the result from the storage service
    return NoContent, 201

# Function for receiving server events and sending them to the storage service
def receive_server_event(body):
    # Generate a unique trace_id using uuid
    trace_id = str(uuid.uuid4())
    # Prepare event data for storage
    event_data = {
        "server_id": body["server_id"],
        "uptime": body["uptime"],
        "cpu_usage": body["cpu_usage"],
        "memory_usage": body["memory_usage"],
        "timestamp": body["timestamp"],
        "trace_id": trace_id 
    }

    # Log that an event was received with the trace ID
    logger.info(f"Received Storage event; Trace Id:{trace_id}")
    send_event_to_kafka("server_event", event_data)
    
    # Return the appropriate response based on the result from the storage service
    return NoContent, 201

# Create the connexion app
app = connexion.FlaskApp(__name__, specification_dir='')

# Add the API specification (make sure your openapi.yml file is in place)
app.add_api("ACIT3855-ProjectReceiver.yaml", strict_validation=True, validate_responses=True)

# Run the app
if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")

