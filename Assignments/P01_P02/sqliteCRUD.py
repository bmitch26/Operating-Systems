# sqliteCRUD.py

"""
This file provides the core functionality for creating, reading, updating, and
deleting entries in the SQLite database, managing file and directory metadata, 
permissions, and user information. It acts as the database interface, enabling 
the API to execute the necessary queries and operations based on the shell's requests.
"""

import sqlite3

class SqliteCRUD:
    def __init__(self, db_path='filesystem.db'):
        """Store the database path."""
        self.db_path = db_path

    def _connect(self):
        """Create and return a new database connection."""
        return sqlite3.connect(self.db_path)

    def create_directory(self, name, pid, oid):
        """Create a new directory."""
        print(f"vars: {name}, {pid}, {oid}")
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO 'directories' ('name', 'pid', 'oid') VALUES ('{name}', '{int(pid)}', '{int(oid)}');")
        conn.commit()
        last_row_id = cursor.lastrowid
        conn.close()
        return last_row_id
  
    # def get_directory_id(self, name, parent_pid=1):
    #     """Retrieve the directory ID (pid) based on the directory name and its parent directory."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT id FROM directories WHERE name = ? AND pid = ?;
    #     """, (name, parent_pid))
    #     result = cursor.fetchone()
    #     conn.close()
    #     if result:
    #         return {'id': result[0]}  # Return the directory ID
    #     else:
    #         return None  # Return None if directory not found  
    
    def get_directory_id(self, name, parent_pid=1):
        """Retrieve the directory ID (pid) based on the directory name and its parent directory."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM directories WHERE name = ? AND pid = ?;
        """, (name, parent_pid))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {'id': result[0]}  # Return the directory ID
        else:
            return None  # Return None if directory not found

    
    
    def list_directory(self, pid, name=None):
        """List files and directories in the current directory, optionally filtering by name."""
        conn = self._connect()
        cursor = conn.cursor()

        # If a specific name is provided, filter by that name
        if name:
            cursor.execute("""
                SELECT name, 'dir' as type, modified_at, oid, read_permission, write_permission, execute_permission, world_read, world_write, world_execute, NULL as size
                FROM directories 
                WHERE pid = ? AND name = ?
                UNION ALL
                SELECT name, 'file' as type, modified_date, oid, read_permission, write_permission, execute_permission, world_read, world_write, world_execute, size 
                FROM files 
                WHERE pid = ? AND name = ?;
            """, (pid, name, pid, name))
        else:
            cursor.execute(""" 
                SELECT name, 'dir' as type, modified_at, oid, read_permission, write_permission, execute_permission, world_read, world_write, world_execute, NULL as size
                FROM directories 
                WHERE pid = ?
                UNION ALL
                SELECT name, 'file' as type, modified_date, oid, read_permission, write_permission, execute_permission, world_read, world_write, world_execute, size 
                FROM files 
                WHERE pid = ?;
            """, (pid, pid))

        results = cursor.fetchall()
        conn.close()
        return results



    ### cd
    
    def get_home_directory_pid(self):
        """Fetch the id of the home directory from the database."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM directories WHERE name = 'home'")
        result = cursor.fetchone()
        conn.close()
        print(f"Database result for home directory: {result}")  # Debugging
        return result[0] if result else 1  # Return id (1), or default to 1 if not found

    def get_parent_directory_pid(self, current_pid):
        """Return the pid of the parent directory of the current directory."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT pid FROM directories WHERE id = ?", (current_pid,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_directory_pid_by_name(self, name, current_pid):
        """Return the pid of a directory by its name and current pid."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM directories WHERE name = ? AND pid = ?", (name, current_pid))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_directory_info(self, pid):
        """Retrieve directory name and parent ID based on the pid."""
        conn = self._connect()
        cursor = conn.cursor()  # Get a cursor from the connection

        query = "SELECT name, pid FROM directories WHERE id = ?"
        cursor.execute(query, (pid,))
        result = cursor.fetchone()
        conn.close()  # Ensure the connection is closed after use

        if result:
            return {'name': result[0], 'pid': result[1]}  # name and parent id
        return None  # Return None if directory not found

    ### cat, sort
    def read_file(self, file_name: str, pid: int):
        """Read the contents of a file from the database."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Query to get the file contents where name matches and pid is the current directory
        cursor.execute("""
            SELECT contents FROM files WHERE name = ? AND pid = ?
        """, (file_name, pid))
        
        result = cursor.fetchone()
        conn.close()

        if result:
            return result[0]  # Return file contents
        else:
            return None  # File not found

    #### wc -w
    def count_words(self, file_name, pid):
        """Count the number of words in the specified file."""
        conn = self._connect()
        cursor = conn.cursor()

        try:
            # Fetch the file contents
            cursor.execute("SELECT contents FROM files WHERE name = ? AND pid = ?", (file_name, pid))
            result = cursor.fetchone()

            if result:
                file_contents = result[0].decode('utf-8')  # Decode the BLOB contents
                words = file_contents.split()  # Split by whitespace to count words
                word_count = len(words)
                return word_count
            else:
                return None  # File not found

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

        finally:
            conn.close()
            
    def count_lines_words_chars(self, file_name, pid):
        """Count lines, words, and characters in the specified file."""
        conn = self._connect()
        cursor = conn.cursor()

        try:
            # Fetch the file contents
            cursor.execute("SELECT contents FROM files WHERE name = ? AND pid = ?", (file_name, pid))
            result = cursor.fetchone()

            if result:
                file_contents = result[0].decode('utf-8')  # Decode the BLOB contents
                lines = file_contents.splitlines()
                line_count = len(lines)
                word_count = sum(len(line.split()) for line in lines)
                char_count = len(file_contents)
                return line_count, word_count, char_count
            else:
                return None, None, None  # File not found

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None, None, None

        finally:
            conn.close()



    def create_file(self, name, contents, pid, oid, size=0):
        """Create a new file in the specified directory (pid)."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO files (name, contents, pid, oid, size)
            VALUES (?, ?, ?, ?, ?);
        """, (name, contents, pid, oid, size))
        conn.commit()
        last_row_id = cursor.lastrowid
        conn.close()
        return last_row_id

    # def move_file(self, file_name, src_pid, dest_pid):
    #     """Move a file from one directory to another."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         UPDATE files SET pid = ? WHERE name = ? AND pid = ?;
    #     """, (dest_pid, file_name, src_pid))
    #     conn.commit()
    #     if cursor.rowcount == 0:
    #         raise Exception(f"File {file_name} not found in the source directory.")
    #     conn.close()
    
    
    def move_file(self, file_name, src_pid, dest_pid, dest_name):
        """Move or rename a file."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Update the file's directory (pid) and optionally its name
        cursor.execute("""
            UPDATE files 
            SET pid = ?, name = ? 
            WHERE name = ? AND pid = ?;
        """, (dest_pid, dest_name, file_name, src_pid))
        
        conn.commit()

        if cursor.rowcount == 0:
            raise Exception(f"File {file_name} not found in the source directory.")
        
        conn.close()


    # def copy_file(self, file_name, src_pid, dest_pid):
    #     """Copy a file from one directory to another."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT name, contents, oid, size FROM files WHERE name = ? AND pid = ?;
    #     """, (file_name, src_pid))
    #     file_data = cursor.fetchone()
    #     if file_data:
    #         name, contents, oid, size = file_data
    #         self.create_file(name, contents, dest_pid, oid, size)
    #     else:
    #         raise Exception(f"File {file_name} not found in the source directory.")
    #     conn.close()
    
    def copy_file(self, file_name, src_pid, dest_pid, dest_name):
        """Copy a file from one directory to another, potentially renaming it."""
        conn = self._connect()
        cursor = conn.cursor()

        # Fetch the file details from the source directory
        cursor.execute("""
            SELECT name, contents, oid, size FROM files WHERE name = ? AND pid = ?;
        """, (file_name, src_pid))
        file_data = cursor.fetchone()

        if file_data:
            # Use the dest_name for the copied file (which could be the same as file_name)
            _, contents, oid, size = file_data
            self.create_file(dest_name, contents, dest_pid, oid, size)
        else:
            raise Exception(f"File {file_name} not found in the source directory.")

        conn.commit()
        conn.close()

    #### DO NOT USE DELETE_FILE
    # def delete_file(self, file_name, pid):
    #     """Delete a file from a directory."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         DELETE FROM files WHERE name = ? AND pid = ?;
    #     """, (file_name, pid))
    #     conn.commit()
    #     if cursor.rowcount == 0:
    #         raise Exception(f"File {file_name} not found in the directory.")
    #     conn.close()
    
    # def grep_file(self, pattern: str, file_name: str, l: bool = False):
    #     """Search for a pattern in the file's contents."""
    #     try:
    #         conn = self._connect()
    #         cursor = conn.cursor()

    #         # Fetch the file contents
    #         cursor.execute("SELECT contents FROM files WHERE name = ?", (file_name,))
    #         result = cursor.fetchone()
            
    #         if result:
    #             # Debug: Print the file contents
    #             contents = result[0].decode('utf-8')
    #             print(f"File contents for {file_name}: {contents}")
                
    #             # Grep for the pattern
    #             lines = contents.splitlines()
    #             matched_lines = [line for line in lines if pattern in line]
                
    #             # Debug: Show lines that match the pattern
    #             print(f"Matched lines for pattern '{pattern}': {matched_lines}")
                
    #             if l:
    #                 # Return just the file name if -l flag is set
    #                 return [file_name] if matched_lines else []
    #             else:
    #                 return matched_lines
    #         else:
    #             print(f"Error: File {file_name} not found")
    #             return []
    #     except Exception as e:
    #         print(f"Error in grep_file: {e}")
    #         raise e
    #     finally:
    #         conn.close()
    
    
    def grep_file(self, pattern: str, file_name: str, l: bool = False):
        """Search for a pattern in the file's contents."""
        try:
            conn = self._connect()
            cursor = conn.cursor()

            # Fetch the file contents
            cursor.execute("SELECT contents FROM files WHERE name = ?", (file_name,))
            result = cursor.fetchone()
            
            if result:
                contents = result[0]
                
                # Check if the contents are in bytes (BLOB), then decode; otherwise, assume it's a string
                if isinstance(contents, bytes):
                    contents = contents.decode('utf-8')
                    print(f"Decoded BLOB content for {file_name}")
                else:
                    print(f"File content for {file_name} is a string")

                # Split the contents into lines and search for the pattern
                lines = contents.splitlines()
                matched_lines = [line for line in lines if pattern in line]
                
                # Debug: Show lines that match the pattern
                print(f"Matched lines for pattern '{pattern}': {matched_lines}")
                
                if l:
                    # Return just the file name if -l flag is set
                    return [file_name] if matched_lines else []
                else:
                    return matched_lines
            else:
                print(f"Error: File {file_name} not found")
                return []
        except Exception as e:
            print(f"Error in grep_file: {e}")
            raise e
        finally:
            conn.close()



        # Helper function to remove a file
    def remove_file(self, target):
        """Remove the specified file."""
        conn = self._connect()
        cursor = conn.cursor()

        # SQL query to delete the file from the database
        cursor.execute("DELETE FROM files WHERE name = ?", (target,))
        conn.commit()
        conn.close()
        print(f"File {target} has been removed from the database.")  # Debugging

    # Helper function to remove a directory
    def remove_directory(self, target, recursive=False):
        """Remove the specified directory (and its contents if recursive)."""
        conn = self._connect()
        cursor = conn.cursor()

        if recursive:
            # SQL query to remove directory and its contents recursively
            cursor.execute("DELETE FROM directories WHERE name = ?", (target,))
            cursor.execute("DELETE FROM files WHERE pid IN (SELECT id FROM directories WHERE name = ?)", (target,))
            print(f"Directory {target} and its contents have been removed.")  # Debugging
        else:
            # SQL query to remove just the directory
            cursor.execute("DELETE FROM directories WHERE name = ?", (target,))
            print(f"Directory {target} has been removed.")  # Debugging

        conn.commit()
        conn.close()

    # Helper function to get target info (file or directory)
    def get_target_info(self, target):
        """Retrieve file or directory information."""
        conn = self._connect()
        cursor = conn.cursor()

        # Check if it's a file or directory
        cursor.execute("SELECT name, 'file' as type FROM files WHERE name = ? UNION SELECT name, 'dir' as type FROM directories WHERE name = ?", (target, target))
        result = cursor.fetchone()
        conn.close()

        return {"name": result[0], "type": result[1]} if result else None



    def delete_directory(self, dir_name, pid):
        """Delete a directory and its contents recursively."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM directories WHERE name = ? AND pid = ?;
        """, (dir_name, pid))
        dir_data = cursor.fetchone()
        if dir_data:
            dir_id = dir_data[0]
            cursor.execute("DELETE FROM directories WHERE id = ?", (dir_id,))
            cursor.execute("DELETE FROM files WHERE pid = ?", (dir_id,))
            conn.commit()
        else:
            raise Exception(f"Directory {dir_name} not found in the current directory.")
        conn.close()

    
    # def chmod(self, file_name, pid, permissions):
    #     """Change directory permissions."""
    #     conn = self._connect()
    #     cursor = conn.cursor()

    #     # Update the permissions for the directory
    #     cursor.execute("""
    #         UPDATE directories
    #         SET read_permission = ?, write_permission = ?, execute_permission = ?,
    #             world_read = ?, world_write = ?, world_execute = ?
    #         WHERE name = ? AND pid = ?;
    #     """, (permissions['read_permission'], permissions['write_permission'], permissions['execute_permission'],
    #         permissions['world_read'], permissions['world_write'], permissions['world_execute'], file_name, pid))

    #     conn.commit()

    #     if cursor.rowcount == 0:
    #         raise Exception(f"Directory {file_name} not found.")
        
    #     conn.close()
    

    
    def chmod_file(self, file_name, pid, permissions):
        """Change file permissions."""
        conn = self._connect()
        cursor = conn.cursor()

        # Update the permissions for the file
        cursor.execute("""
            UPDATE files
            SET read_permission = ?, write_permission = ?, execute_permission = ?,
                world_read = ?, world_write = ?, world_execute = ?
            WHERE name = ? AND pid = ?;
        """, (permissions['read_permission'], permissions['write_permission'], permissions['execute_permission'],
            permissions['world_read'], permissions['world_write'], permissions['world_execute'], file_name, pid))

        conn.commit()

        if cursor.rowcount == 0:
            raise Exception(f"File {file_name} not found.")
        
        conn.close()
        
    def chmod_directory(self, file_name, pid, permissions):
        """Change directory permissions."""
        conn = self._connect()
        cursor = conn.cursor()

        # Update the permissions for the directory
        cursor.execute("""
            UPDATE directories
            SET read_permission = ?, write_permission = ?, execute_permission = ?,
                world_read = ?, world_write = ?, world_execute = ?
            WHERE name = ? AND pid = ?;
        """, (permissions['read_permission'], permissions['write_permission'], permissions['execute_permission'],
            permissions['world_read'], permissions['world_write'], permissions['world_execute'], file_name, pid))

        conn.commit()

        if cursor.rowcount == 0:
            raise Exception(f"Directory {file_name} not found.")
        
        conn.close()

    
    def check_if_dir_or_file(self, file_name, pid):
        """Check whether the target is a file or directory."""
        conn = self._connect()
        cursor = conn.cursor()

        # First check if it's a directory
        cursor.execute("""
            SELECT name FROM directories WHERE name = ? AND pid = ?;
        """, (file_name, pid))
        result = cursor.fetchone()

        if result:
            return "directory"

        # If not a directory, check if it's a file
        cursor.execute("""
            SELECT name FROM files WHERE name = ? AND pid = ?;
        """, (file_name, pid))
        result = cursor.fetchone()

        if result:
            return "file"

        raise Exception(f"{file_name} not found in the directory.")

        conn.close()


    def close(self):
        """Close the database connection (not used since each method handles its own connection)."""
        pass
