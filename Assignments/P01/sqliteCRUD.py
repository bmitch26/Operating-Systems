# sqliteCRUD.py

import sqlite3

# Class to represent all errors related to database interactions
class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

# Connect to database
def connect():
    """Connect to the SQLite database"""
    try:
        return sqlite3.connect('filesystem2.db')
    except sqlite3.Error as e:
        raise DatabaseError(f"Error connecting to database: {e}")


# File Operations (CRUD for Files table)

# Create
# Insert a new file
def insert_file(name, is_directory, parent_id=None):
    """Insert a new file or directory into the Files table"""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO Files (name, parent_id, is_directory)
            VALUES (?, ?, ?)
        ''', (name, parent_id, is_directory))
        
        conn.commit()
        file_id = cursor.lastrowid  # Get the ID of the newly inserted file
        conn.close()
        
        return file_id
    except sqlite3.Error as e:
        raise DatabaseError(f"Error inserting file into database: {e}")
    finally:
        conn.close()

# Read
# Retrieve all files
def get_all_files():
    """Retrieve all files from the Files table"""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM Files')
        files = cursor.fetchall()
        
        conn.close()
        return files
    except sqlite3.Error as e:
        raise DatabaseError(f"Error fetching files from database: {e}")


# Update
# Update file data
def update_file_metadata(file_id, name=None, size=None):
    """Update file metadata (e.g., name or size)"""
    try:
        conn = connect()
        cursor = conn.cursor()

        if name:
            cursor.execute('UPDATE Files SET name = ? WHERE file_id = ?', (name, file_id))
        if size is not None:
            cursor.execute('UPDATE Files SET size = ? WHERE file_id = ?', (size, file_id))
        
        conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Error updating file metadata: {e}")
    finally:
        conn.close()


# Delete
# Delete file
def delete_file(file_id):
    """Delete a file from the Files table"""
    try:
        conn = connect()
        cursor = conn.cursor()

        # Then delete the file itself
        cursor.execute('DELETE FROM Files WHERE file_id = ?', (file_id,))
        
        conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Error deleting file from database: {e}")
    finally:
        conn.close()
    
    
# Example usage
if __name__ == '__main__':
    
    # Get all files
    files = get_all_files()
    print(f'Files in database: {files}')