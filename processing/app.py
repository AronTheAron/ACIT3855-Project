import connexion
from connexion import NoContent
import logging
import logging.config
import yaml
import requests
import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


SERVICE_NAME = "processing"

# Load logging configuration from YAML
with open("config/log_conf.yml", "r") as log_file:
    log_config = yaml.safe_load(log_file)
    log_config['handlers']['file']['filename'] = f'logs/{SERVICE_NAME}.log'
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Load the configuration file
with open('config/processing_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# JSON file path for storing stats - Fetch from the configuration
STATS_FILE = app_config['datastore']['filename']  # Updated to use the config value

# Default statistics
default_stats = {
    "total_player_events": 0,
    "total_server_events": 0,
    "max_player_score": 0,
    "avg_cpu_usage": 0.0,
    "last_updated": "1970-01-01T00:00:00"
}

# Function to get statistics
def get_statistics():
    """Returns the latest statistics from the JSON file."""
    logger.info("Received request for statistics.")

    if not os.path.exists(STATS_FILE):
        logger.error("Statistics file not found.")
        return {"message": "Statistics do not exist"}, 404  # Return 404 if file doesn't exist

    # If file exists, read the stats
    try:
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
        logger.debug(f"Current statistics: {stats}")
        logger.info("Request completed successfully.")
        return stats, 200  # Return stats with 200 status code
    except Exception as e:
        logger.error(f"Error reading statistics file: {e}")
        return {"message": "Internal server error"}, 500  # Return 500 if there's an error reading the file


# Function to update statistics periodically
def populate_stats():
    """Fetches new events from storage and updates statistics."""
    logger.info("Starting periodic processing of statistics...")

    # Read current statistics from JSON file
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
    else:
        stats = default_stats.copy()

    last_updated = stats.get("last_updated", "1970-01-01T00:00:00")
    start_timestamp = last_updated
    end_timestamp = datetime.utcnow().isoformat()

    # Query storage service for new events
    player_events_url = f"{app_config['eventstore']['url']}/player?start_timestamp={start_timestamp}&end_timestamp={end_timestamp}"
    server_events_url = f"{app_config['eventstore']['url']}/server?start_timestamp={start_timestamp}&end_timestamp={end_timestamp}"

    try:
        player_resp = requests.get(player_events_url)
        server_resp = requests.get(server_events_url)

        # Check if the responses were successful
        if player_resp.status_code != 200:
            logger.error(f"Failed to fetch player events, status code: {player_resp.status_code}")
            return
        if server_resp.status_code != 200:
            logger.error(f"Failed to fetch server events, status code: {server_resp.status_code}")
            return

        player_events = player_resp.json()
        server_events = server_resp.json()

        logger.info(f"Received {len(player_events)} new player events.")
        logger.info(f"Received {len(server_events)} new server events.")

        # Calculate updated statistics
        if player_events:
            stats["total_player_events"] += len(player_events)
            stats["max_player_score"] = max(
                stats["max_player_score"], 
                max(event["score"] for event in player_events)
            )

        if server_events:
            stats["total_server_events"] += len(server_events)
            stats["avg_cpu_usage"] = sum(event["cpu_usage"] for event in server_events) / len(server_events)

        # Update the last_updated timestamp
        stats["last_updated"] = end_timestamp

        # Write updated stats to JSON file
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=4)

        logger.debug(f"Updated stats: {stats}")
    except Exception as e:
        logger.error(f"Error occurred while fetching or processing events: {e}")

    logger.info("Finished periodic processing of statistics.")

# Function to initialize the scheduler
def init_scheduler():
    """Sets up a periodic task to update statistics."""
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['interval'])
    sched.start()
    logger.info("Scheduler initialized and running")

# Create the connexion app
app = connexion.FlaskApp(__name__, specification_dir='')

# Add the API specification
app.add_api("ACIT3855-ProjectProcessing.yaml", strict_validation=True, validate_responses=True)

# Run the app
if __name__ == "__main__":
    init_scheduler()  # Start periodic statistics update
    logger.info("Starting Processing Service on port 8100")
    app.run(port=8100, host="0.0.0.0")

