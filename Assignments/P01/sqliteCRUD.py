# # sqliteCRUD.py

# import sqlite3
# from datetime import datetime

# class SqliteCRUD:
#     def __init__(self, db_path='filesystem.db'):
#         """Store the database path."""
#         self.db_path = db_path
#         self.conn = None  # Initialize the connection as None

#     def _connect(self):
#         """Create and return a new database connection."""
#         if self.conn is None:  # Only create connection if it doesn't exist
#             self.conn = sqlite3.connect(self.db_path)
#         return self.conn

#     def create_directory(self, name, pid, oid):
#         """Create a new directory."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO directories (name, pid, oid)
#             VALUES (?, ?, ?);
#         """, (name, pid, oid))
#         conn.commit()
#         last_row_id = cursor.lastrowid
#         conn.close()
#         return last_row_id

#     def list_directory(self, pid):
#         """List files and directories in the current directory."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT name, 'dir' as type FROM directories WHERE pid = ?
#             UNION
#             SELECT name, 'file' as type FROM files WHERE pid = ?;
#         """, (pid, pid))
#         results = cursor.fetchall()
#         conn.close()
#         return results

#     def change_directory(self, dir_name, current_pid):
#         """Change to a different directory by name and current pid."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT id FROM directories WHERE name = ? AND pid = ?;
#         """, (dir_name, current_pid))
#         result = cursor.fetchone()
#         conn.close()
#         if result:
#             return result[0]
#         else:
#             raise Exception("Directory not found")


#     def create_file(self, name, contents, pid, oid, size=0):
#         """Create a new file in the specified directory (pid)."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO files (name, contents, pid, oid, size)
#             VALUES (?, ?, ?, ?, ?);
#         """, (name, contents, pid, oid, size))
#         self.conn.commit()
#         return self.cursor.lastrowid

#     def move_file(self, file_name, src_pid, dest_pid):
#         """Move a file from one directory to another."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE files SET pid = ? WHERE name = ? AND pid = ?;
#         """, (dest_pid, file_name, src_pid))
#         conn.commit()
#         if cursor.rowcount == 0:
#             raise Exception(f"File {file_name} not found in the source directory.")
#         conn.close()


#     def copy_file(self, file_name, src_pid, dest_pid):
#         """Copy a file from one directory to another."""
#         self.cursor.execute("""
#             SELECT name, contents, oid, size FROM files WHERE name = ? AND pid = ?;
#         """, (file_name, src_pid))
#         file_data = self.cursor.fetchone()
#         if file_data:
#             name, contents, oid, size = file_data
#             self.create_file(name, contents, dest_pid, oid, size)
#         else:
#             raise Exception(f"File {file_name} not found in the source directory.")

#     def delete_file(self, file_name, pid):
#         """Delete a file from a directory."""
#         self.cursor.execute("""
#             DELETE FROM files WHERE name = ? AND pid = ?;
#         """, (file_name, pid))
#         self.conn.commit()
#         if self.cursor.rowcount == 0:
#             raise Exception(f"File {file_name} not found in the directory.")

#     def delete_directory(self, dir_name, pid):
#         """Delete a directory and its contents recursively."""
#         self.cursor.execute("""
#             SELECT id FROM directories WHERE name = ? AND pid = ?;
#         """, (dir_name, pid))
#         dir_data = self.cursor.fetchone()
#         if dir_data:
#             dir_id = dir_data[0]
#             self.cursor.execute("DELETE FROM directories WHERE id = ?", (dir_id,))
#             self.cursor.execute("DELETE FROM files WHERE pid = ?", (dir_id,))
#             self.conn.commit()
#         else:
#             raise Exception(f"Directory {dir_name} not found in the current directory.")

#     def read_file(self, file_name, pid):
#         """Read the contents of a file."""
#         self.cursor.execute("""
#             SELECT contents FROM files WHERE name = ? AND pid = ?;
#         """, (file_name, pid))
#         result = self.cursor.fetchone()
#         if result:
#             return result[0]
#         else:
#             raise Exception(f"File {file_name} not found in the directory.")

#     def chmod(self, file_name, pid, permissions):
#         """Change file permissions."""
#         conn = self._connect()
#         cursor = conn.cursor()
#         cursor.execute("""
#             UPDATE files
#             SET read_permission = ?, write_permission = ?, execute_permission = ?
#             WHERE name = ? AND pid = ?;
#         """, (permissions['read'], permissions['write'], permissions['execute'], file_name, pid))
#         conn.commit()
#         if cursor.rowcount == 0:
#             raise Exception(f"File {file_name} not found in the directory.")
#         conn.close()


#     def close(self):
#         """Close the database connection if it exists."""
#         if self.conn:  # Check if the connection is not None
#             self.conn.close()
#             self.conn = None  # Set it to None to avoid multiple close attempts


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
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO directories (name, pid, oid)
            VALUES (?, ?, ?);
        """, (name, pid, oid))
        conn.commit()
        last_row_id = cursor.lastrowid
        conn.close()
        return last_row_id

    # def list_directory(self, pid):
    #     """List files and directories in the current directory."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT name, 'dir' as type FROM directories WHERE pid = ?
    #         UNION
    #         SELECT name, 'file' as type FROM files WHERE pid = ?;
    #     """, (pid, pid))
    #     results = cursor.fetchall()
    #     conn.close()
    #     return results
    
    # def list_directory(self, pid):
    #     """List files and directories in the current directory with details for long listing."""
    #     conn = self._connect()
    #     cursor = conn.cursor()

    #     # Select size and modified for files, but return NULL for directories
    #     cursor.execute("""
    #         SELECT name, 'dir' as type, NULL as size, NULL as modified FROM directories WHERE pid = ?
    #         UNION ALL
    #         SELECT name, 'file' as type, size, modified_date FROM files WHERE pid = ?;
    #     """, (pid, pid))

    #     results = cursor.fetchall()
    #     conn.close()
    #     return results

    # def list_directory(self, pid, name=None):
    #     """List files and directories in the current directory, optionally filtering by name."""
    #     conn = self._connect()
    #     cursor = conn.cursor()

    #     # If a specific name is provided, filter by that name
    #     if name:
    #         cursor.execute("""
    #             SELECT name, 'dir' as type, NULL as size FROM directories WHERE pid = ? AND name = ?
    #             UNION ALL
    #             SELECT name, 'file' as type, size FROM files WHERE pid = ? AND name = ?;
    #         """, (pid, name, pid, name))
    #     else:
    #         cursor.execute("""
    #             SELECT name, 'dir' as type, NULL as size FROM directories WHERE pid = ?
    #             UNION ALL
    #             SELECT name, 'file' as type, size FROM files WHERE pid = ?;
    #         """, (pid, pid))

    #     results = cursor.fetchall()
    #     conn.close()
    #     return results
  
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
                SELECT name, 'dir' as type, NULL as size FROM directories WHERE pid = ? AND name = ?
                UNION ALL
                SELECT name, 'file' as type, size FROM files WHERE pid = ? AND name = ?;
            """, (pid, name, pid, name))
        else:
            cursor.execute(""" 
                SELECT name, 'dir' as type, NULL as size FROM directories WHERE pid = ?
                UNION ALL
                SELECT name, 'file' as type, size FROM files WHERE pid = ?;
            """, (pid, pid))

        results = cursor.fetchall()
        conn.close()
        return results

    ### cd

    # def change_directory(self, dir_name, current_pid):
    #     """Change to a different directory by name and current pid."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT id FROM directories WHERE name = ? AND pid = ?;
    #     """, (dir_name, current_pid))
    #     result = cursor.fetchone()
    #     conn.close()
    #     if result:
    #         return result[0]
    #     else:
    #         raise Exception("Directory not found")
    
    # def get_home_directory_pid(self):
    #     """Fetch the pid of the home directory from the database."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT id FROM directories WHERE name = 'home'")
    #     result = cursor.fetchone()
    #     conn.close()
    #     print(f"Fetched home directory result: {result}")  # Debugging
    #     return result[0] if result else 0  # Return pid, default to 0 if not found
    
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

    def move_file(self, file_name, src_pid, dest_pid):
        """Move a file from one directory to another."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE files SET pid = ? WHERE name = ? AND pid = ?;
        """, (dest_pid, file_name, src_pid))
        conn.commit()
        if cursor.rowcount == 0:
            raise Exception(f"File {file_name} not found in the source directory.")
        conn.close()

    def copy_file(self, file_name, src_pid, dest_pid):
        """Copy a file from one directory to another."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, contents, oid, size FROM files WHERE name = ? AND pid = ?;
        """, (file_name, src_pid))
        file_data = cursor.fetchone()
        if file_data:
            name, contents, oid, size = file_data
            self.create_file(name, contents, dest_pid, oid, size)
        else:
            raise Exception(f"File {file_name} not found in the source directory.")
        conn.close()

    def delete_file(self, file_name, pid):
        """Delete a file from a directory."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM files WHERE name = ? AND pid = ?;
        """, (file_name, pid))
        conn.commit()
        if cursor.rowcount == 0:
            raise Exception(f"File {file_name} not found in the directory.")
        conn.close()

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

    # def read_file(self, file_name, pid):
    #     """Read the contents of a file."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("""
    #         SELECT contents FROM files WHERE name = ? AND pid = ?;
    #     """, (file_name, pid))
    #     result = cursor.fetchone()
    #     conn.close()
    #     if result:
    #         return result[0]
    #     else:
    #         raise Exception(f"File {file_name} not found in the directory.")

    def chmod(self, file_name, pid, permissions):
        """Change file permissions."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE files
            SET read_permission = ?, write_permission = ?, execute_permission = ?
            WHERE name = ? AND pid = ?;
        """, (permissions['read'], permissions['write'], permissions['execute'], file_name, pid))
        conn.commit()
        if cursor.rowcount == 0:
            raise Exception(f"File {file_name} not found in the directory.")
        conn.close()

    def close(self):
        """Close the database connection (not used since each method handles its own connection)."""
        pass
