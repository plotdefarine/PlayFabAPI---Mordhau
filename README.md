# 📘 README – PlayFab Info Collector (PlayFabAPI)

This project retrieves player information using the PlayFab GetPlayerCombinedInfo API and stores the data into a MariaDB database.  
It is designed for asynchronous batch processing of player statistics, especially suited for Mordhau server owners and community managers.

---

# 🛠️ Project Status

This is an **open-source** and **incomplete** project.  
Originally planned to include interaction with the **Steam Web API** to gather additional metadata (e.g., player profile, ban status, hours played, etc.).  
Although the implementation was not completed, several lines of code are **already commented and prepared** for easy future integration of the Steam API.

Feel free to contribute or fork the project!

---

## 📂 Configuration – config.ini

The `config.ini` file centralizes all essential configuration. It is divided into three sections:

```ini
[database]
host = x.x.x.x             ; MariaDB server IP or hostname
port = xxxx                     ; Database port (default: 3306)
user = xxxxx                ; MariaDB username
password = xxxxxx         ; MariaDB password
database = xxxxx       ; Target database name
table = playfab_player_info    ; Destination table name


[sql_query]
get_playfab_ids = SELECT PlayFabId FROM playerlist
; EXAMPLE : SQL query to retrieve PlayFabIds to fetch 

[playfab]
title_id = 12D56               ; PlayFab Game Title ID
custom_id = xxxxx         ; CustomID used for login (it's just a name, you can put whatever you want)
session_ticket = ...           ; SessionTicket (auto-refreshed via LoginWithCustomID)
```

💡 Tip: Use `getSessionTicket.py` to regenerate a fresh session_ticket using your custom_id.

---

## 🗄️ Database Table – playfab_player_info

In MariaDB :
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
| id            | Player's Steam ID (if available)                 |
| platform      | Player’s platform (e.g., Steam, Epic)            |
| username      | Username as defined in PlayFab                   |
| entity_id     | Player's EntityID (used internally by PlayFab)   |
| created_at    | Account creation date on PlayFab                 |
| stats_json    | Player statistics as a raw JSON blob             |
| last_updated  | Auto-updated on insert or update                 |

---

## ⏱️ API Rate Limiting – How to manage it

PlayFab enforces a **maximum of 10-20 requests per second**.

To stay under this threshold, this project uses an `asyncio.Semaphore` to limit concurrent API calls:

```python
# Located in GetPlayFabAPI.py
semaphore = asyncio.Semaphore(12)
```

Feel free to adjust the value depending on your expected load.  
A value of `12` provides a good balance between speed and safety, avoiding `RateLimitExceeded` errors.

---

## 🔐 Security Best Practices

1. **Table name safety**  
   Table name is fetched from `config.ini`. Make sure it's a valid SQL identifier (`^[a-zA-Z_][a-zA-Z0-9_]*$`).

2. **Secure database credentials**  
   Avoid plain text storage in production. Use `.env` files or environment variables instead.

3. **Protect your session_ticket**  
   Session tickets are short-lived and should be refreshed regularly via `LoginWithCustomID`.

---

## 🧪 Recommended Testing

- Run with 100+ PlayFab IDs to verify concurrency.
- Make sure your session_ticket is still valid during processing.
- Clean up `playerlist` to avoid dead or invalid PlayFab IDs.

---

## 📦 Dependencies

Install the required Python libraries with:

```bash
pip install aiomysql aiohttp
```

---

# ✍️ Author

A small project by **Plotdefarine (known in the mordhau community as Needyy)**, created to asynchronously collect and store player information from PlayFab into MariaDB.

Gmail : plotdefarine@gmail.com
Website : 🔗 https://needys-community.com
