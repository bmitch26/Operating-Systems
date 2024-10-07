# schema.py

import sqlite3

def create_schema():
    conn = sqlite3.connect('filesystem2.db')
    c = conn.cursor()
    
    # Create Files Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS Files (
        file_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        is_directory BOOLEAN NOT NULL,
        size INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES directories(dir_id)
    );
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_schema()