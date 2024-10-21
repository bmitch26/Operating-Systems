# api.py

from fastapi import FastAPI, HTTPException
from sqliteCRUD import SqliteCRUD
import uvicorn
import logging

app = FastAPI()
db = SqliteCRUD()

### 1. List Directory

# @app.get("/ls/{pid}")
# def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
#     """List the contents of a directory with optional flags."""
#     try:
#         logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
#         contents = db.list_directory(pid)
        
#         # Build the response data based on flags
#         response_data = []
#         for item in contents:
#             name, file_type = item[0], item[1]
#             size = item[2] if len(item) > 2 else None  # Ensure size exists
#             modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
            
#             if l:
#                 # Format long listing details
#                 size_str = f"{size} bytes" if size else "N/A"
#                 modified_time_str = modified_time if modified_time else "N/A"
#                 response_data.append({
#                     'name': name,
#                     'type': file_type,
#                     'size': size_str,
#                     'modified_date': modified_time_str
#                 })
#             else:
#                 # Handle hidden files if '-a' flag is set
#                 if not a and name.startswith('.'):
#                     continue
#                 response_data.append({'name': name, 'type': file_type})
                
#         logging.debug(f"Returning directory contents: {response_data}")
#         return {"contents": response_data}
    
#     except Exception as e:
#         logging.error(f"Error occurred: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))


def human_readable_size(size_in_bytes):
    """Convert a file size in bytes to a human-readable format."""
    if size_in_bytes is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"


# @app.get("/ls/{pid}")
# def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
#     """List the contents of a directory with optional flags."""
#     try:
#         logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
#         contents = db.list_directory(pid)
        
#         # Build the response data based on flags
#         response_data = []
#         for item in contents:
#             name, file_type = item[0], item[1]
#             size = item[2] if len(item) > 2 else None  # Ensure size exists
#             modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
            
#             if l:
#                 # Handle human-readable size if '-h' flag is passed
#                 if h and size:
#                     size_str = human_readable_size(size)
#                 else:
#                     size_str = f"{size} bytes" if size else "N/A"
                
#                 modified_time_str = modified_time if modified_time else "N/A"
#                 response_data.append({
#                     'name': name,
#                     'type': file_type,
#                     'size': size_str,
#                     'modified_date': modified_time_str
#                 })
#             else:
#                 # Handle hidden files if '-a' flag is set
#                 if not a and name.startswith('.'):
#                     continue
#                 response_data.append({'name': name, 'type': file_type})
        
#         logging.debug(f"Returning directory contents: {response_data}")
#         return {"contents": response_data}
    
#     except Exception as e:
#         logging.error(f"Error occurred: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))


# @app.get("/ls/{pid}")
# def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
#     """List the contents of a directory with optional flags."""
#     try:
#         logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
#         contents = db.list_directory(pid)
        
#         # Build the response data based on flags
#         response_data = []
#         for item in contents:
#             name, file_type = item[0], item[1]
#             size = item[2] if len(item) > 2 else None  # Ensure size exists
#             modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
            
#             if l:
#                 # Handle human-readable size if '-h' flag is passed
#                 if h and file_type == 'file' and size:  # Only apply to files, not directories
#                     size_str = human_readable_size(size)
#                 else:
#                     size_str = f"{size} bytes" if size else "N/A"
                
#                 modified_time_str = modified_time if modified_time else "N/A"
#                 response_data.append({
#                     'name': name,
#                     'type': file_type,
#                     'size': size_str,
#                     'modified_date': modified_time_str
#                 })
#             else:
#                 # Handle hidden files if '-a' flag is set
#                 if not a and name.startswith('.'):
#                     continue
#                 response_data.append({'name': name, 'type': file_type})
        
#         logging.debug(f"Returning directory contents: {response_data}")
#         return {"contents": response_data}
    
#     except Exception as e:
#         logging.error(f"Error occurred: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))


def format_permissions(read_perm, write_perm, execute_perm):
    """Format the permissions for display."""
    read = 'r' if read_perm else '-'
    write = 'w' if write_perm else '-'
    execute = 'x' if execute_perm else '-'
    
    # Combine to create permission string
    permissions = f"{read}{write}{execute}"
    return permissions

def human_readable_size(size_in_bytes):
    """Convert a file size in bytes to a human-readable format."""
    if size_in_bytes is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"


# @app.get("/ls/{pid}")
# def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
#     """List the contents of a directory with optional flags."""
#     try:
#         logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
#         contents = db.list_directory(pid, name)
        
#         # Build the response data based on flags
#         response_data = []
#         for item in contents:
#             name, file_type = item[0], item[1]
#             size = item[2] if len(item) > 2 else None  # Ensure size exists
#             modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
#             owner = item[4] if len(item) > 4 else "N/A"  # Owner ID
#             read_perm = item[5] if len(item) > 5 else 0
#             write_perm = item[6] if len(item) > 6 else 0
#             execute_perm = item[7] if len(item) > 7 else 0
            
#             # Handle the '-l' flag for long format output
#             if l:
#                 # Handle human-readable size if '-h' flag is passed
#                 if h and file_type == 'file' and size:  # Only apply to files, not directories
#                     size_str = human_readable_size(size)
#                 else:
#                     size_str = f"{size} bytes" if size else "N/A"
                
#                 modified_time_str = modified_time if modified_time else "N/A"
#                 permissions = format_permissions(read_perm, write_perm, execute_perm)  # Call permission formatter
#                 response_data.append({
#                     'name': name,
#                     'type': file_type,
#                     'size': size_str,
#                     'modified_date': modified_time_str,
#                     'owner': owner,
#                     'permissions': permissions
#                 })
#             else:
#                 # Handle hidden files if '-a' flag is set
#                 if not a and name.startswith('.'):
#                     continue
#                 response_data.append({'name': name, 'type': file_type})
        
#         logging.debug(f"Returning directory contents: {response_data}")
#         return {"contents": response_data}
    
#     except Exception as e:
#         logging.error(f"Error occurred: {str(e)}")
#         raise HTTPException(status_code=400, detail=str(e))


def _format_permissions(item):
    """Format the permissions for the long listing (owner and world permissions only)."""
    # Owner permissions
    owner_read = 'r' if item.get('read_permission', 0) else '-'
    owner_write = 'w' if item.get('write_permission', 0) else '-'
    owner_execute = 'x' if item.get('execute_permission', 0) else '-'

    # World permissions
    world_read = 'r' if item.get('world_read', 0) else '-'
    world_write = 'w' if item.get('world_write', 0) else '-'
    world_execute = 'x' if item.get('world_execute', 0) else '-'

    # Combine permissions: owner and world
    permissions = f"{owner_read}{owner_write}{owner_execute}{world_read}{world_write}{world_execute}"

    # Return the combined permission string (e.g., 'rwxr-x')
    return permissions

@app.get("/ls/{pid}")
def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
    """List the contents of a directory with optional flags."""
    try:
        logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
        contents = db.list_directory(pid, name)
        
        # Build the response data based on flags
        response_data = []
        for item in contents:
            name, file_type = item[0], item[1]
            size = item[2] if len(item) > 2 else None  # Ensure size exists
            modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
            owner = item[4] if len(item) > 4 else "N/A"  # Owner ID
            read_perm = item[5] if len(item) > 5 else 0
            write_perm = item[6] if len(item) > 6 else 0
            execute_perm = item[7] if len(item) > 7 else 0
            world_read = item[8] if len(item) > 8 else 0
            world_write = item[9] if len(item) > 9 else 0
            world_execute = item[10] if len(item) > 10 else 0

            # Handle the '-l' flag for long format output
            if l:
                # Handle human-readable size if '-h' flag is passed
                if h and file_type == 'file' and size:  # Only apply to files, not directories
                    size_str = human_readable_size(size)
                else:
                    size_str = f"{size} bytes" if size else "N/A"
                
                modified_time_str = modified_time if modified_time else "N/A"
                permissions = _format_permissions({
                    'read_permission': read_perm, 
                    'write_permission': write_perm, 
                    'execute_permission': execute_perm,
                    'world_read': world_read,
                    'world_write': world_write,
                    'world_execute': world_execute
                })
                
                response_data.append({
                    'name': name,
                    'type': file_type,
                    'size': size_str,
                    'modified_date': modified_time_str,
                    'owner': owner,
                    'permissions': permissions
                })
            else:
                # Handle hidden files if '-a' flag is set
                if not a and name.startswith('.'):
                    continue
                response_data.append({'name': name, 'type': file_type})
        
        logging.debug(f"Returning directory contents: {response_data}")
        return {"contents": response_data}
    
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))






### 2. Make Directory

@app.post("/mkdir/")
def create_directory(name: str, pid: int, oid: int):
    """Create a new directory."""
    try:
        dir_id = db.create_directory(name, pid, oid)
        return {"directory_id": dir_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

### 3. Change Directory

# @app.get("/cd/")
# def change_directory(dir: str, current_pid: int):
#     """Change directory and return the new pid."""
#     try:
#         if dir == "~":
#             # Go to home directory
#             new_pid = db.get_home_directory_pid()
#         elif dir == "..":
#             # Go to parent directory
#             new_pid = db.get_parent_directory_pid(current_pid)
#         else:
#             # Go to the specified directory
#             new_pid = db.get_directory_pid_by_name(dir, current_pid)
        
#         if new_pid:
#             return {"new_pid": new_pid}
#         else:
#             raise HTTPException(status_code=404, detail="Directory not found")
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

@app.get("/cd/")
def change_directory(dir: str, current_pid: int):
    """Change directory and return the new pid."""
    try:
        print(f"Received request to change directory to: {dir}, current_pid: {current_pid}")  # Debugging
        
        if dir == "~" or dir == "home":
            # Go to home directory
            new_pid = db.get_home_directory_pid()
            print(f"Home directory id fetched: {new_pid}")  # Debugging
        elif dir == "..":
            # Go to parent directory
            new_pid = db.get_parent_directory_pid(current_pid)
            print(f"Parent directory id fetched: {new_pid}")  # Debugging
        else:
            # Go to the specified directory
            new_pid = db.get_directory_pid_by_name(dir, current_pid)
            print(f"Directory id fetched for {dir}: {new_pid}")  # Debugging
        
        if new_pid:
            print(f"Changing to directory with pid: {new_pid}")  # Debugging
            return {"new_pid": new_pid}
        else:
            raise HTTPException(status_code=404, detail="Directory not found")
    except Exception as e:
        print(f"Error in change_directory: {e}")  # Debugging
        raise HTTPException(status_code=400, detail=str(e))

### Real 4. Cat
@app.get("/cat/")
def read_file(file_name: str, pid: int):
    """Read the contents of a file in the specified directory."""
    try:
        print(f"Received request to read file: {file_name}, in directory pid: {pid}")  # Debugging
        
        file_contents = db.read_file(file_name, pid)  # Fetch file contents from the database
        
        if file_contents is not None:
            return {"contents": file_contents}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    
    except Exception as e:
        print(f"Error in read_file: {e}")  # Debugging
        raise HTTPException(status_code=400, detail=str(e))


#### Real 5. sort
@app.get("/sort/")
def sort_file(file_name: str, pid: int):
    """Sort the contents of a file in the specified directory."""
    try:
        print(f"Received request to sort file: {file_name}, in directory pid: {pid}")  # Debugging
        
        file_contents = db.read_file(file_name, pid)  # Fetch file contents from the database
        
        if file_contents is not None:
            # Split the file contents into lines, sort them, and return sorted output
            sorted_lines = sorted(file_contents.splitlines())
            return {"sorted_contents": sorted_lines}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    
    except Exception as e:
        print(f"Error in sort_file: {e}")  # Debugging
        raise HTTPException(status_code=400, detail=str(e))


#### Real 6. wc -w
@app.get("/wc_w/")
def wc_w(file_name: str, pid: int):
    """API endpoint to count words in a file."""
    try:
        # Fetch the file contents and count words using sqliteCRUD
        word_count = db.count_words(file_name, pid)
        if word_count is not None:
            return {"word_count": word_count}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#### Real 7. grep and grep -l
@app.get("/grep/")
def grep_file(pattern: str, file_name: str, l: bool = False):
    """Search for the pattern in the given file."""
    try:
        # Debug: Print input parameters
        print(f"Received grep request. Pattern: {pattern}, File: {file_name}, Flag -l: {l}")
        
        # Call the database layer to grep the file content
        matched_lines = db.grep_file(pattern, file_name, l)
        
        # Debug: Show matched lines
        print(f"Matched lines: {matched_lines}")
        
        return {"matched_lines": matched_lines}
    except Exception as e:
        print(f"Error occurred in grep_file: {e}")
        raise HTTPException(status_code=400, detail=str(e))



#### Real 8. rm
@app.delete("/rm/")
def remove_item(target: str, recursive: bool = False, force: bool = False):
    """Remove the specified file or directory, with optional recursive and force flags."""
    try:
        print(f"Received request to remove: {target}, recursive: {recursive}, force: {force}")  # Debugging

        # Determine the type (file or directory)
        target_info = db.get_target_info(target)
        if not target_info:
            if force:
                print(f"Warning: {target} does not exist, but continuing because of -f flag.")
                return {"detail": f"{target} does not exist, but continuing because of -f flag."}
            else:
                raise HTTPException(status_code=404, detail=f"{target} does not exist.")

        is_directory = target_info["type"] == "dir"

        # Handle file removal
        if not is_directory:
            db.remove_file(target)
            return {"detail": f"File {target} has been removed."}

        # Handle directory removal with -r flag
        if is_directory:
            if recursive:
                db.remove_directory(target, recursive=True)
                return {"detail": f"Directory {target} and its contents have been removed."}
            else:
                raise HTTPException(status_code=400, detail=f"{target} is a directory. Use the -r flag to remove it.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


### 4. Create new file

@app.post("/create_file/")
def create_file(name: str, contents: str, pid: int, oid: int, size: int):
    """Create a new file."""
    try:
        file_id = db.create_file(name, contents, pid, oid, size)
        return {"file_id": file_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

### 5. Move File

@app.post("/mv/")
def move_file(file_name: str, src_pid: int, dest_pid: int):
    """Move a file."""
    try:
        db.move_file(file_name, src_pid, dest_pid)
        return {"detail": f"Moved {file_name} to new directory"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

### 6. Delete a file

@app.post("/rm/")
def delete_file(file_name: str, pid: int):
    """Delete a file."""
    try:
        db.delete_file(file_name, pid)
        return {"detail": f"Deleted {file_name}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


### 8. Change file permissions

@app.post("/chmod/")
def chmod(file_name: str, pid: int, permissions: dict):
    """Change the permissions of a file."""
    try:
        db.chmod(file_name, pid, permissions)
        return {"detail": f"Permissions updated for {file_name}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

### Close database connections

@app.on_event("shutdown")
def shutdown():
    """Close the database connection on API shutdown."""
    db.close()

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8080, reload=True)