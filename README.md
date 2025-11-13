# README – PlayFab Info Collector (PlayFabAPI)

This project retrieves player information using the PlayFab GetPlayerCombinedInfo API and stores the data into a MariaDB database.  
It is designed for asynchronous batch processing of player statistics, especially suited for Mordhau server owners and community managers.

---

# Project Status

This is an **open-source** and **incomplete** project.  
Originally planned to include interaction with the **Steam Web API** to gather additional metadata (e.g., player profile, ban status, hours played, etc.).  
Although the implementation was not completed, several lines of code are **already commented and prepared** for easy future integration of the Steam API.

Feel free to contribute or fork the project!

---

## Configuration – `config.ini`

The `config.ini` file centralizes all essential configuration. It is divided into six sections:

```ini
[database]
host = x.x.x.x                          ; MariaDB server IP or hostname
port = 3306                             ; Database port (default: 3306)
user = username                         ; MariaDB username
password = your_password                ; MariaDB password
database = your_database                ; Target database name
table = playfab_player_info             ; Destination table name

[sql_query]
get_playfab_ids = SELECT PlayFabId FROM playerlist
; SQL query to retrieve PlayFab IDs from your database

[playfab]
title_id = 12D56                        ; Mordhau PlayFab Title ID
custom_id = custom_name                 ; CustomID used for login (any string)
session_ticket = ...                    ; SessionTicket (auto-refreshed)
semaphore_limit = 10                    ; Controls the max concurrent API calls

[input]
source = manual_file                    ; Either 'database' or 'manual_file'
manual_file = configurations/manual_playfabids.txt  ; Path to manual ID file

[output]
destination = txt_file                  ; Either 'database' or 'txt_file'
txt_file = configurations/saved_playfabids.txt     ; Path to local save file
```

Tip: Use `getSessionTicket.py` to regenerate a fresh `session_ticket` using your `custom_id`.

---

## Input & Output Modes

This project now supports **flexible data flow**:

### Input Sources

#### 1. **Database Mode** (`source = database`)
Fetch PlayFab IDs from your MariaDB database using the SQL query defined in `config.ini`:

```ini
[input]
source = database
```

The application will execute the `get_playfab_ids` query to retrieve all PlayFab IDs from your database.

#### 2. **Manual File Mode** (`source = manual_file`)
Fetch PlayFab IDs from a local text file instead of a database:

```ini
[input]
source = manual_file
manual_file = configurations/manual_playfabids.txt
```

Write your PlayFabIDs into `manual_playfabids.txt`, one ID per line:

```
ABC1234567890
XYZ9876543210
QWE1122334455
```

This mode is especially useful for testing, quick lookups, or when you don't have a database configured.

---

### Output Destinations

#### 1. **Database Mode** (`destination = database`)
Save all collected player data directly into your MariaDB database:

```ini
[output]
destination = database
```

Data is inserted into the `playfab_player_info` table with all player stats and metadata.

#### 2. **Text File Mode** (`destination = txt_file`)
Save all collected player data as JSON lines into a local text file:

```ini
[output]
destination = txt_file
txt_file = configurations/saved_playfabids.txt
```

Each line of `saved_playfabids.txt` contains a complete JSON object with player information:

```json
{"playfab_id":"ABC1234567890","id":"STEAM_0:1:123456","platform":"Steam","username":"PlayerName","entity_id":"...","created_at":"2024-01-15 10:30:00","stats":{"DuelRank":1500,...}}
{"playfab_id":"XYZ9876543210","id":"STEAM_0:0:654321","platform":"Steam","username":"OtherPlayer","entity_id":"...","created_at":"2024-02-20 14:45:00","stats":{"DuelRank":1200,...}}
```

This mode is perfect for:
- Local development and testing
- Avoiding database dependencies
- Archiving player data as structured JSON
- Post-processing data with other tools

---

## Manual Input Support

You can now bypass the database and directly fetch PlayFab data by writing raw PlayFabIDs manually into a text file.

- Set the input source in `config.ini`:
  ```ini
  source = manual_file
  ```
- Then write your PlayFabIDs into `manual_playfabids.txt`, one ID per line, like this:

  ```
  ABC1234567890
  XYZ9876543210
  QWE1122334455
  ```

This mode is especially useful for testing or quick lookups without configuring a full database.

## Database Table – `playfab_player_info`

In MariaDB:

```sql
CREATE TABLE playfab_player_info (
    playfab_id   VARCHAR(50)   NOT NULL PRIMARY KEY,
    id           VARCHAR(50),
    platform     VARCHAR(20),
    username     VARCHAR(100),
    entity_id    VARCHAR(100),
    created_at   DATETIME,
    stats_json   LONGTEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**Field descriptions**:

| Field         | Description                                      |
|---------------|--------------------------------------------------|
| playfab_id    | Unique PlayFab player ID (primary key)           |
| id            | Player's Epic Games ID / Steam ID (if available) |
| platform      | Player’s platform (e.g., Steam, Epic)            |
| username      | Username as defined in PlayFab                   |
| entity_id     | Player's EntityID (used internally by PlayFab)   |
| created_at    | Account creation date on PlayFab                 |
| stats_json    | Player statistics as a raw JSON blob             |
| last_updated  | Auto-updated on insert or update                 |

---

## API Rate Limiting – How to manage it

PlayFab enforces a maximum of 10–20 requests per second.

To stay under this threshold, this project uses an `asyncio.Semaphore` to limit concurrent API calls. The limit can be set in `config.ini`:

```ini
[playfab]
semaphore_limit = 12
```

You can increase or decrease this value depending on your use case.


## Logging

This project writes runtime logs to `logs/app.log` (rotating file handler) and also prints to the console. You can control how verbose the logs are using the new `[logging]` section in `config.ini`.

Add or edit the section like this:

```ini
[logging]
# standard -> INFO to console + INFO to file (default)
# medium   -> DEBUG to console + INFO to file
# maximum  -> DEBUG to console + DEBUG to file
log_level = standard
```

Meaning of levels:
- `standard` (default) — console: INFO, file: INFO
- `medium` — console: DEBUG, file: INFO
- `maximum` — console: DEBUG, file: DEBUG

Use `maximum` only for troubleshooting as it logs request/response bodies (truncated) and more details.

Log file location and rotation:
- File: `logs/app.log`
- Rotation: 5 MB per file, up to 5 backups

## Security Best Practices

1. **Table name safety**  
   Ensure the table name in `config.ini` is a valid SQL identifier.

2. **Secure database credentials**  
   Avoid hardcoding credentials in production. Use environment variables or `.env` files.

3. **Protect your session_ticket**  
   Session tickets are temporary. Refresh them regularly using the provided helper script.

---

## Recommended Testing

- Run with 100+ PlayFab IDs to verify concurrency handling.
- Make sure your session ticket is valid and active during long runs.
- Use manual input for quick experiments or debugging.

---

## Dependencies

Install the required Python libraries with:

```bash
pip install aiomysql aiohttp
```

---

# Author

A small project by **Plotdefarine (also known in the Mordhau community as Needyy)**, created to asynchronously collect and store player information from PlayFab into MariaDB.

- Gmail: plotdefarine@gmail.com  
- Website: https://needys-community.com
