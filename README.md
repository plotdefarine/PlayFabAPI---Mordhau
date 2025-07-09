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

The `config.ini` file centralizes all essential configuration. It is divided into four sections:

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
source = database                       ; Either 'database' or 'manual_file'
manual_file = configurations/manual_playfabids.txt  ; Path to manual ID file
```

Tip: Use `getSessionTicket.py` to regenerate a fresh `session_ticket` using your `custom_id`.

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

---

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

---

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
