import os
import json
import logging
import logging.config
import yaml
from datetime import datetime
from flask import Flask, request, jsonify
from kafka import KafkaConsumer

# Load logging configuration
with open("ano_log_conf.yml", "r") as log_file:
    log_config = yaml.safe_load(log_file)
logging.config.dictConfig(log_config)
logger = logging.getLogger("anomalyLogger")

# Load service configuration
with open("anomaly_conf.yml", "r") as conf_file:
    app_config = yaml.safe_load(conf_file)

# Environment variables for thresholds
CPU_MAX = int(os.getenv("CPU_MAX", 90))
SCORE_MAX = int(os.getenv("SCORE_MAX", 1000000))

# Log thresholds on startup
logger.info(f"CPU_MAX threshold: {CPU_MAX}")
logger.info(f"SCORE_MAX threshold: {SCORE_MAX}")

# Flask app setup
app = Flask(__name__)

# JSON datastore path
DATASTORE_PATH = app_config["datastore"]["filepath"]

# Kafka configuration
KAFKA_HOST = app_config["kafka"]["hostname"]
KAFKA_PORT = app_config["kafka"]["port"]
KAFKA_TOPIC = "events"

# Helper function to detect anomalies
def detect_anomalies(events):
    anomalies = []
    for event in events:
        if event["event_type"] == "PlayerActivityEvent" and event["score"] > SCORE_MAX:
            anomalies.append({
                "id": event["id"],
                "trace_id": event["trace_id"],
                "event_type": event["event_type"],
                "description": f"Score detected: {event['score']}; threshold: {SCORE_MAX}"
            })
            logger.debug(f"Anomaly detected: {anomalies[-1]}")
        elif event["event_type"] == "ServerPerformanceEvent" and event["cpu_usage"] > CPU_MAX:
            anomalies.append({
                "id": event["id"],
                "trace_id": event["trace_id"],
                "event_type": event["event_type"],
                "description": f"CPU usage detected: {event['cpu_usage']}%; threshold: {CPU_MAX}%"
            })
            logger.debug(f"Anomaly detected: {anomalies[-1]}")
    return anomalies

# PUT /update endpoint
@app.route("/update", methods=["PUT"])
def update_anomalies():
    logger.debug("Accessing /update endpoint")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    events = [message.value for message in consumer]
    logger.info(f"Retrieved {len(events)} events from Kafka")

    anomalies = detect_anomalies(events)

    # Write anomalies to JSON datastore
    with open(DATASTORE_PATH, "w") as f:
        json.dump(anomalies, f, indent=4)

    logger.info(f"Anomaly detection completed. {len(anomalies)} anomalies detected.")
    return jsonify({"anomalies_count": len(anomalies)}), 201

# GET /anomalies endpoint
@app.route("/anomalies", methods=["GET"])
def get_anomalies():
    logger.debug("Accessing /anomalies endpoint")
    event_type = request.args.get("event_type", None)

    if not os.path.exists(DATASTORE_PATH):
        logger.error("Anomalies datastore not found.")
        return jsonify({"message": "Anomalies datastore not found"}), 404

    with open(DATASTORE_PATH, "r") as f:
        anomalies = json.load(f)

    if event_type:
        if event_type not in ["PlayerActivityEvent", "ServerPerformanceEvent"]:
            logger.error(f"Invalid event type: {event_type}")
            return jsonify({"message": "Invalid event type. Must be PlayerActivityEvent or ServerPerformanceEvent."}), 400
        anomalies = [a for a in anomalies if a["event_type"] == event_type]

    if not anomalies:
        logger.info("No anomalies found for the given event type.")
        return "", 204

    logger.debug(f"Returning {len(anomalies)} anomalies.")
    return jsonify(anomalies), 200

# Run the app
if __name__ == "__main__":
    logger.info("Starting Anomaly Detection Service on port 8200")
    app.run(port=8200, host="0.0.0.0")

