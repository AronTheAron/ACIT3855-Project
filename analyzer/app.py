import connexion
from connexion import NoContent
import json
import logging
import logging.config
import yaml
import os
from pykafka import KafkaClient
from pykafka.common import OffsetType
from flask import jsonify, request


SERVICE_NAME = "analyzer"

# Load logging configuration from YAML
with open("config/log_conf.yml", "r") as log_file:
    log_config = yaml.safe_load(log_file)
    log_config['handlers']['file']['filename'] = f'logs/{SERVICE_NAME}.log'
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

# Load configuration from YAML
with open("config/analyzer_conf.yml", "r") as f:
    CONFIG = yaml.safe_load(f)

# Kafka Configuration
KAFKA_HOST = f"{CONFIG['events']['kafka']['hostname']}:{CONFIG['events']['kafka']['port']}"
KAFKA_TOPIC = CONFIG["events"]["kafka"]["topic"]

################################################################

def get_event_by_index(index, event_type):
    """Retrieve an event from Kafka based on its index in the queue."""
    try:
        client = KafkaClient(hosts=KAFKA_HOST)
        topic = client.topics[KAFKA_TOPIC.encode()]
        consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
        
        current_index = -1  # Initialize current index to -1 to put it at the beginning

        for msg in consumer:
            if msg is None:
                break  # No more messages in queue

            message = msg.value.decode("utf-8")
            data = json.loads(message)

            # Check for event type
            if (event_type == "player" and  data["type"] == "player_event") or \
               (event_type == "server" and  data["type"] == "server_event"):
                current_index += 1  # Increment index for the specific event type

                if current_index == index:
                    logger.info(f"Found {event_type} message at index {index}: {data}")
                    return data, 200
                
        logger.warning(f"No {event_type} message found at index {index}")
        return {"message": f"No {event_type} message at index {index}!"}, 404

    except Exception as e:
        logger.error(f"Error retrieving message: {e}")
        return {"message": "Internal server error"}, 500
    
################################################################

def get_player_event():
    """API Endpoint: Fetch a player event from Kafka by index."""
    index = request.args.get("index", type=int)
    if index is None:
        return jsonify({"message": "Index parameter is required"}), 400

    return jsonify(get_event_by_index(index, event_type="player"))

def get_server_event():
    """API Endpoint: Fetch a server event from Kafka by index."""
    index = request.args.get("index", type=int)
    if index is None:
        return jsonify({"message": "Index parameter is required"}), 400

    return jsonify(get_event_by_index(index, event_type="server"))

################################################################

def get_event_statistics():
    """API Endpoint: Retrieve statistics about events in Kafka."""
    try:
        client = KafkaClient(hosts=KAFKA_HOST)
        topic = client.topics[KAFKA_TOPIC.encode()]
        consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

        num_player_events = 0
        num_server_events = 0

        for msg in consumer:
            if msg is None:
                break  # No more messages

            message = msg.value.decode("utf-8")
            data = json.loads(message)


            if "payload" in data:
                payload = data["payload"]
                if "player_id" in payload:
                    num_player_events += 1
                elif "server_id" in payload:
                    num_server_events += 1

        stats = {
            "num_player_events": num_player_events,
            "num_server_events": num_server_events
        }

        logger.info(f"Kafka events tracked in the queue: {stats}")
        return jsonify(stats), 200

    except Exception as e:
        logger.error(f"Error retrieving Kafka statistics: {e}")
        return jsonify({"message": "Internal server error"}), 500

# Create the connexion app
app = connexion.FlaskApp(__name__, specification_dir='')

# Add the API specification (make sure your openapi.yml file is in place)
app.add_api("ACIT3855-ProjectAnalyzer.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")
