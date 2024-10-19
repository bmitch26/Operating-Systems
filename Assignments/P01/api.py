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


@app.get("/ls/{pid}")
def list_directory(pid: int, l: bool = False, a: bool = False, h: bool = False, name: str = None):
    """List the contents of a directory with optional flags."""
    try:
        logging.debug(f"Received request to list directory with pid={pid}, name={name}, flags l={l}, a={a}, h={h}")
        
        contents = db.list_directory(pid)
        
        # Build the response data based on flags
        response_data = []
        for item in contents:
            name, file_type = item[0], item[1]
            size = item[2] if len(item) > 2 else None  # Ensure size exists
            modified_time = item[3] if len(item) > 3 else None  # Ensure modified time exists
            
            if l:
                # Handle human-readable size if '-h' flag is passed
                if h and file_type == 'file' and size:  # Only apply to files, not directories
                    size_str = human_readable_size(size)
                else:
                    size_str = f"{size} bytes" if size else "N/A"
                
                modified_time_str = modified_time if modified_time else "N/A"
                response_data.append({
                    'name': name,
                    'type': file_type,
                    'size': size_str,
                    'modified_date': modified_time_str
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