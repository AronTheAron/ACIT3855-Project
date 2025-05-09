﻿Project Description

Project Purpose:
The software is a server/player statistics tracking system for private game servers. It collects event data including player activities and server performance metrics, to provide real-time analytics and insights for server administrators. The system will receive "events" from these servers (e.g., player stats, server stats) through a RESTful API and process them for tracking and analysis.

Events Received, Stored, and Processed:
1. Player Activity Event:
   * Properties:
      * player_id: The unique identifier of the player (numeric or string).
      * server_id: The unique identifier of the server the player was playing on (UUID or string).
      * action: The action taken by the player (e.g., "killed_monster", "looted_item", etc.).
      * score: The points gained or game-specific statistics.
      * timestamp: The date and time the action was performed.
2. Server Performance Event:
   * Properties:
      * server_id: The unique identifier of the server (UUID or string).
      * uptime: The amount of time the server has spent online (numeric).
      * cpu_usage: The CPU usage percentage at the time of the event (numeric).
      * memory_usage: The memory usage at the time of the event (numeric).
      * timestamp: The date and time the data was captured.

Peak Number of Concurrent Events:
The system is expected to handle up to 1000 concurrent events during peak hours, such as when many players log in or when the server undergoes special events.

Users of the System:
1. Game Server Hosts: These are the individuals or teams hosting private servers. They are responsible for sending server and player statistics to the system.
2. Players: These are the users playing on the private servers. While they don't directly interact with the API, their actions generate events that are sent to the system.
3. Administrators: These are the system users who manage the server and player data. They might monitor system performance, perform data analysis, or manage event processing.
