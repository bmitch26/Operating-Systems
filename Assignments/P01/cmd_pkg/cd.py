# cmd_pkg/cd.py

from pathlib import Path
import os  # We need to import os to change the current working directory

def cd(directory=None):
    """
    Change the current working directory.
    
    Inputs:
    - 'cd' or 'cd ~': Changes to the user's home directory.
    - 'cd ..': Moves to the parent directory.
    - 'cd directory': Changes to the specified directory.
    """
    try:
        # If no directory is specified or 'cd ~', change to the home directory
        if directory is None or directory == '~':
            home_dir = Path.home()
            os.chdir(home_dir)  # Use os.chdir to change the directory
            return f"Changed directory to {home_dir}"
        
        # If 'cd ..', move to the parent directory
        elif directory == '..':
            parent_dir = Path.cwd().parent
            os.chdir(parent_dir)  # Change to the parent directory
            return f"Moved to parent directory {parent_dir}"

        # Otherwise, change to the specified directory
        else:
            target_dir = Path(directory).resolve()  # Get the absolute path
            if target_dir.is_dir():  # Ensure the directory exists
                os.chdir(target_dir)  # Change to the target directory
                return f"Changed directory to {target_dir}"
            else:
                return f"cd: {directory}: No such directory"
    
    except Exception as e:
        return f"Error: {e}"
