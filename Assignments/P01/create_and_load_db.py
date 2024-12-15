# create_and_load_db.py

import sqlite3
from datetime import datetime

# Connect to (or create) the database
conn = sqlite3.connect('filesystem.db')
cursor = conn.cursor()

# Create tables
tables = [
    """
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pid INTEGER,
        oid INTEGER,
        name TEXT,
        size INTEGER DEFAULT 0,
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        contents BLOB,
        read_permission INTEGER DEFAULT 1,
        write_permission INTEGER DEFAULT 0,
        execute_permission INTEGER DEFAULT 1,
        world_read INTEGER DEFAULT 1,
        world_write INTEGER DEFAULT 0,
        world_execute INTEGER DEFAULT 1
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS directories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- parent directory
        pid INTEGER,                            -- parent directory
        oid INTEGER,                            -- owner
        name TEXT NOT NULL,                     -- directory name
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        read_permission INTEGER DEFAULT 1,
        write_permission INTEGER DEFAULT 0,
        execute_permission INTEGER DEFAULT 1,
        world_read INTEGER DEFAULT 1,
        world_write INTEGER DEFAULT 0,
        world_execute INTEGER DEFAULT 1
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]

# Execute table creation
for table in tables:
    cursor.execute(table)

# Insert initial users
cursor.execute("""
INSERT INTO users (username, password) VALUES
    ('root', 'password0'),
    ('bob', 'password1'),
    ('mia', 'password2'),
    ('raj', 'password3');
""")

# Insert directories
cursor.execute("""
INSERT INTO directories (pid, oid, name) VALUES
    (NULL, 1, 'home'),      -- Root directory 'home'
    (1, 2, 'bob'),          -- Bob's home directory
    (1, 3, 'mia'),          -- Mia's home directory
    (1, 4, 'raj'),          -- Raj's home directory
    (2, 2, 'bananas'),      -- Directory created by Bob
    (3, 3, 'docs');         -- Directory created by Mia
""")

# Insert files
cursor.execute("""
INSERT INTO files (pid, oid, name, size, contents, read_permission, write_permission, execute_permission) VALUES
    (2, 2, 'somefile.txt', 1024, 'This is Bob''s file.', 1, 1, 0), -- File in Bob's directory
    (6, 3, 'report.txt', 2048, 'Mia''s report data.', 1, 1, 0);    -- File in Mia's docs directory
""")

# Commit changes and close connection
conn.commit()
conn.close()
