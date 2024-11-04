# shell.py
"""
This file is about using getch to capture input and handle certain keys 
when the are pushed. The 'command_DbApi.py' was about parsing and calling functions.
This file is about capturing the user input so that you can mimic shell behavior.

"""


import os
import sys
from time import sleep
from fastapi import FastAPI, HTTPException
from sqliteCRUD import SqliteCRUD # REVISIT THIS
import sqlite3
import shutil
import random
import logging

from getch import Getch
import requests

app = FastAPI()
db = SqliteCRUD()

# Core global functions #

def parse(cmd):
    """This function takes a command and parses it into a list of tokens
    1. Explode on redirects
    2. Explode on pipes
    """
    redirect = None
    append = False
    sub_cmds = []

    # Check for output redirection
    if ">>" in cmd:
        cmd, redirect = cmd.split(">>")
        append = True  # We are appending to the file
    elif ">" in cmd:
        cmd, redirect = cmd.split(">")

    # Check for piping
    if "|" in cmd:
        sub_cmds = cmd.split("|")
    else:
        sub_cmds = [cmd]

    # Parsing each sub-command
    parsed_cmds = []
    for i in range(len(sub_cmds)):
        sub_cmd = sub_cmds[i].strip().split(" ")
        cmdDict = {
            "cmd": sub_cmd[0],
            "flags": get_flags(sub_cmd),
            "params": get_params(sub_cmd[1:]),
            "output": None  # This field will store the output of a command for piping
        }
        parsed_cmds.append(cmdDict)

    return {
        "sub_cmds": parsed_cmds,
        "redirect": redirect.strip() if redirect else None,
        "append": append
    }

def human_readable_size(size_in_bytes):
    """Convert bytes to a human-readable format (e.g., KB, MB, GB)."""
    if size_in_bytes is None:
        return "N/A"
    
    # Ensure size_in_bytes is a float for comparison
    try:
        size_in_bytes = float(size_in_bytes)
    except ValueError:
        return "N/A"  # Return "N/A" if size_in_bytes is not a valid number
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"



class DbApi:
    def __init__(self):
        self.url = "http://localhost:8080"
        self.conn = SqliteCRUD("filesystem.db")
        self.current_pid = 1
        self.history_file = "command_history.txt"  # Path to history file
        self.history = self.load_history()
        self.history_index = len(self.history)  # Start at the end of the history

    def save_to_history(self, cmd):
        """Save the command to history and append it to the history file."""
        self.history.append(cmd)
        with open(self.history_file, "a") as f:
            f.write(f"{cmd}\n")  # Append the command to the history file
        print(f"Command added to history: {cmd}")

    def show_history(self):
        """Display the command history."""
        for index, command in enumerate(self.history, start=1):
            print(f"{index}: {command}")

    def load_history(self):
        """Load history from file if it exists."""
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                return f.read().splitlines()
        return []

    def clear_history(self):
        """Clear history from memory and the file."""
        self.history = []
        if os.path.exists(self.history_file):
            os.remove(self.history_file)            

    
    # def getId(self, name, pid=1):
    #     """Retrieve the directory ID (pid) based on the directory name using sqliteCRUD."""
    #     return self.conn.get_directory_id(name, pid)
    
    def getId(self, path, start_pid=1):
        """
        Retrieve the directory ID (pid) based on the full path.
        The start_pid is the root directory or current directory to start searching from.
        """
        parts = path.strip('/').split('/')  # Split the path into parts (e.g., ['raj', 'cp_standalone.txt'])
        
        pid = start_pid  # Start with the root or current directory
        for part in parts:
            # Get the next directory's ID based on the current pid
            result = self.conn.get_directory_id(part, pid)
            if result is None:
                return None  # Directory not found at this level
            pid = result['id']  # Update the pid to the next level

        return {'id': pid}  # Return the final directory ID

    
    # ls command #

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



    def run_ls(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the ls command with optional flags and handle piping and redirection.
                
                Manual:
                LS(1)                                                      User Commands                                                      LS(1)

        NAME
            ls - list directory contents

        SYNOPSIS
            ls [OPTION]... [FILE]...

        DESCRIPTION
            List  information  about the FILEs (the current directory by default).  Sort entries alphabetically if none of -cftuvSUX nor
            --sort is specified.

            Mandatory arguments to long options are mandatory for short options too.

            -a, --all
                    do not ignore entries starting with .

            -h, --human-readable
                    with -l and -s, print sizes like 1K 234M 2G etc.

            -l     use a long listing format

            The  SIZE argument is an integer and optional unit (example: 10K is 10*1024).  Units are K,M,G,T,P,E,Z,Y (powers of 1024) or    
            KB,MB,... (powers of 1000).  Binary prefixes can be used, too: KiB=K, MiB=M, and so on.

            The TIME_STYLE argument can be full-iso, long-iso, iso, locale, or +FORMAT.  FORMAT is interpreted like in date(1).  If FOR‐    
            MAT  is  FORMAT1<newline>FORMAT2, then FORMAT1 applies to non-recent files and FORMAT2 to recent files.  TIME_STYLE prefixed    
            with 'posix-' takes effect only outside the POSIX locale.  Also the TIME_STYLE environment variable sets the  default  style    
            to use.

            Using color to distinguish file types is disabled both by default and with --color=never.  With --color=auto, ls emits color    
            codes only when standard output is connected to a terminal.  The LS_COLORS environment variable  can  change  the  settings.    
            Use the dircolors command to set it.

        Exit status:
            0      if OK,

            1      if minor problems (e.g., cannot access subdirectory),

            2      if serious trouble (e.g., cannot access command-line argument).

        AUTHOR
            Written by Richard M. Stallman and David MacKenzie.

        REPORTING BUGS
            GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
            Report any translation bugs to <https://translationproject.org/team/>

        COPYRIGHT
            Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
            censes/gpl.html>.
            This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

        SEE ALSO
            Full documentation <https://www.gnu.org/software/coreutils/ls>
            or available locally via: info '(coreutils) ls invocation'

        GNU coreutils 8.32                                         February 2024                                                      LS(1)
        """
        params = cmd["params"]
        
        # Handle piped input if it exists (though 'ls' typically doesn't process piped input)
        if previous_output:
            print("Processing piped input for ls")  # Debugging
            contents = previous_output
        else:
            # By default, use the current directory (current_pid)
            pid = self.current_pid  

            # If a directory name is passed, get its pid
            if params:
                dir_name = params[0]
                result = self.getId(dir_name)
                if result is None:
                    print(f"Error: Directory '{dir_name}' not found.")
                    return []
                pid = result.get("id", self.current_pid)  # Update to new directory's pid if specified

            # Build the query parameters based on flags
            flags = cmd["flags"]
            query_params = {
                'l': '-l' in flags,
                'a': '-a' in flags,
                'h': '-h' in flags,
            }

            # Send a request to the API to list the directory contents
            response = requests.get(f"{self.url}/ls/{pid}", params=query_params)
            if response.status_code == 200:
                contents = response.json().get('contents', [])
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        # Extract only the file/directory names if contents are dictionaries
        contents_str = []
        for item in contents:
            if isinstance(item, dict):
                contents_str.append(item.get('name', 'Unknown'))
            else:
                contents_str.append(str(item))

        # Handle redirection if applicable
        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write("\n".join(contents_str) + "\n")
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []  # No output to console when redirecting
        else:
            # If no redirection, print the directory contents or piped input to the console
            self._print_ls_output(contents, flags)
            return contents_str  # Return contents for further piping if needed

    # def human_readable_size(self, size_in_bytes):
    #     """Convert a file size in bytes to a human-readable format."""
    #     if size_in_bytes is None:
    #         return "N/A"
    #     for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
    #         if size_in_bytes < 1024.0:
    #             return f"{size_in_bytes:.1f} {unit}"
    #         size_in_bytes /= 1024.0
    #     return f"{size_in_bytes:.1f} PB"
    


    
    def _print_ls_output(self, contents, flags):
        """Print the output of the ls command, taking into account flags.
                
                        
                Manual:
                LS(1)                                                      User Commands                                                      LS(1)

        NAME
            ls - list directory contents

        SYNOPSIS
            ls [OPTION]... [FILE]...

        DESCRIPTION
            List  information  about the FILEs (the current directory by default).  Sort entries alphabetically if none of -cftuvSUX nor
            --sort is specified.

            Mandatory arguments to long options are mandatory for short options too.

            -l     use a long listing format

            The  SIZE argument is an integer and optional unit (example: 10K is 10*1024).  Units are K,M,G,T,P,E,Z,Y (powers of 1024) or    
            KB,MB,... (powers of 1000).  Binary prefixes can be used, too: KiB=K, MiB=M, and so on.

            The TIME_STYLE argument can be full-iso, long-iso, iso, locale, or +FORMAT.  FORMAT is interpreted like in date(1).  If FOR‐    
            MAT  is  FORMAT1<newline>FORMAT2, then FORMAT1 applies to non-recent files and FORMAT2 to recent files.  TIME_STYLE prefixed    
            with 'posix-' takes effect only outside the POSIX locale.  Also the TIME_STYLE environment variable sets the  default  style    
            to use.

            Using color to distinguish file types is disabled both by default and with --color=never.  With --color=auto, ls emits color    
            codes only when standard output is connected to a terminal.  The LS_COLORS environment variable  can  change  the  settings.    
            Use the dircolors command to set it.

        Exit status:
            0      if OK,

            1      if minor problems (e.g., cannot access subdirectory),

            2      if serious trouble (e.g., cannot access command-line argument).

        AUTHOR
            Written by Richard M. Stallman and David MacKenzie.

        REPORTING BUGS
            GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
            Report any translation bugs to <https://translationproject.org/team/>

        COPYRIGHT
            Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
            censes/gpl.html>.
            This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

        SEE ALSO
            Full documentation <https://www.gnu.org/software/coreutils/ls>
            or available locally via: info '(coreutils) ls invocation'

        GNU coreutils 8.32                                         February 2024                                                      LS(1)"""
        # ANSI color codes for blue directories
        BLUE = '\033[94m'  # Blue color for directories
        RESET = '\033[0m'  # Reset to default color
        
        # Check if long format '-l' and '-h' is passed
        long_format = '-l' in flags
        human_readable = '-h' in flags  # Check if human-readable format is needed

        for item in contents:
            if isinstance(item, dict):
                if long_format:
                    file_type = 'd' if item['type'] == 'dir' else '-'
                    permissions = item['permissions']  # Already formatted as 'r-x' etc.
                    owner = item['owner']
                    modified_time = item.get('modified_at', item.get('modified_date', "N/A"))
                    
                    # Apply human-readable formatting if '-h' is set
                    size = human_readable_size(item['size']) if human_readable else item['size']
                    name = item['name']

                    # Apply blue color to directory names
                    name = f"{BLUE}{item['name']}{RESET}" if item['type'] == 'dir' else item['name']

                    # Format and print the output in long format
                    print(f"{file_type}{permissions} {owner} {size} {modified_time} {name}")
                else:
                    # Short format: just print the names
                    name = f"{BLUE}{item['name']}{RESET}" if item['type'] == 'dir' else item['name']
                    # print(item['name'])
                    print(name)
            else:
                # Handle the case where the item is a string or other type (for example, from piped input)
                print(item)



    #### cd
    def get_home_directory_pid(self):
        """Return the pid of the home directory using sqliteCRUD."""
        # Use the SqliteCRUD connection (self.conn)
        return self.conn.get_home_directory_pid()


    def get_parent_directory(self):
        """Return the parent directory based on the current pid."""
        return ".."
    
    def get_current_path(self):
        """Reconstruct the current directory path based on current_pid."""
        path_parts = []
        pid = self.current_pid

        while pid != 1:  # Continue until we reach the root directory
            directory_info = self.conn.get_directory_info(pid)  # This should return the name and parent ID
            if directory_info is None:
                break  # Handle case where directory isn't found (e.g., deleted or invalid pid)
            
            path_parts.insert(0, directory_info['name'])  # Add directory name to the path
            pid = directory_info['pid']  # Move up to the parent directory

        # Join all parts to form the full path
        return "/" + "/".join(path_parts) if path_parts else "/"

    def run_cd(self, cmd):
        """Execute the cd command with support for ~, .., and directory names.
        
        Manual:
        NAME
    cd - Change the shell working directory.

SYNOPSIS
    cd [-L|[-P [-e]] [-@]] [dir]

DESCRIPTION
    Change the shell working directory.
    
    Change the current directory to DIR.  The default DIR is the value of the
    HOME shell variable.
    
    The variable CDPATH defines the search path for the directory containing
    DIR.  Alternative directory names in CDPATH are separated by a colon (:).
    A null directory name is the same as the current directory.  If DIR begins
    with a slash (/), then CDPATH is not used.
    
    If the directory is not found, and the shell option `cdable_vars' is set,
    the word is assumed to be  a variable name.  If that variable has a value,
    its value is used for DIR.
    
    The default is to follow symbolic links, as if `-L' were specified.
    `..' is processed by removing the immediately previous pathname component
    back to a slash or the beginning of DIR.
    
    Exit Status:
    Returns 0 if the directory is changed, and if $PWD is set successfully when
    -P is used; non-zero otherwise.

SEE ALSO
    bash(1)

IMPLEMENTATION
    GNU bash, version 5.0.17(1)-release (x86_64-redhat-linux-gnu)
    Copyright (C) 2019 Free Software Foundation, Inc.
    License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>"""
        # params = cmd["params"]

        # if not params or params[0] == "~":
        #     # Change to home directory, reset current_pid to 1 (home's id)
        #     target_dir = "home"  # Always use 'home' for ~
        #     print(f"Changing to home directory: {target_dir}")  # Debugging
        #     self.current_pid = 1  # Reset current_pid to home directory's id (id = 1)
        # elif params[0] == "..":
        #     # Change to parent directory
        #     target_dir = self.get_parent_directory()
        #     print(f"Changing to parent directory: {target_dir}")  # Debugging
        # else:
        #     # Change to the specified directory
        #     target_dir = params[0]
        #     print(f"Changing to specified directory: {target_dir}")  # Debugging
        
        # # Send the request to the API to change the directory
        # response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
        # print(f"API Request sent to: /cd/?dir={target_dir}&current_pid={self.current_pid}")  # Debugging
        # print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")  # Debugging
        
        # if response.status_code == 200:
        #     new_pid = response.json().get("new_pid")
        #     self.current_pid = new_pid  # Update the shell's current directory (IMPORTANT)
        #     print(f"Changed directory to: {target_dir}, New PID: {self.current_pid}")
        # else:
        #     print(f"Error: {response.json().get('detail', 'Unknown error')}")
        
        params = cmd["params"]

        if not params or params[0] == "~":
            self.current_pid = 1  # Home directory
        elif params[0] == "..":
            # Set to parent if not at root
            parent_directory = self.conn.get_parent_directory(self.current_pid)
            self.current_pid = parent_directory['pid'] if parent_directory else self.current_pid
        else:
            # Change to specified directory
            target_dir = params[0]
            response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
            if response.status_code == 200:
                self.current_pid = response.json().get("new_pid")

        # Update the prompt with the new path
        update_prompt(self.get_current_path())
    
    # cat command (meow) #

    # def run_cat(self, cmd, previous_output=None, redirect=None, append=False):
    #     """Execute the cat command to concatenate and display the content of a file."""
    #     params = cmd["params"]

    #     if previous_output:
    #         file_contents = "\n".join(previous_output)
    #         print(f"Processing piped input in 'cat': {file_contents}")
    #     else:
    #         if not params:
    #             print("Error: No file specified.")
    #             return []

    #         file_name = params[0]
    #         print(f"Fetching contents of file: {file_name} in directory with pid: {self.current_pid}")

    #         response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
    #         if response.status_code == 200:
    #             file_contents = response.json().get("contents", "")
    #         else:
    #             print(f"Error: {response.json().get('detail', 'Unknown error')}")
    #             return []

    #     if redirect:
    #         mode = 'a' if append else 'w'
    #         try:
    #             with open(redirect, mode) as f:
    #                 f.write(file_contents)
    #             print(f"Output successfully written to {redirect}")
    #         except IOError as e:
    #             print(f"Error writing to file {redirect}: {e}")
    #         return []
    #     else:
    #         print(file_contents)
    #         return file_contents.splitlines()
    
    
    def run_cat(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the cat command to concatenate and display the content of a file.
        
        Manual:
        
        CAT(1)                                                     User Commands                                                     CAT(1)

NAME
       cat - concatenate files and print on the standard output

SYNOPSIS
       cat [OPTION]... [FILE]...

DESCRIPTION
       Concatenate FILE(s) to standard output.

       With no FILE, or when FILE is -, read standard input.

EXAMPLES

       cat    Copy standard input to standard output.

AUTHOR
       Written by Torbjorn Granlund and Richard M. Stallman.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       tac(1)

       Full documentation <https://www.gnu.org/software/coreutils/cat>
       or available locally via: info '(coreutils) cat invocation'

GNU coreutils 8.32                                         February 2024                                                     CAT(1)"""
        params = cmd["params"]

        if previous_output:
            file_contents = "\n".join(previous_output)
            print(f"Processing piped input in 'cat': {file_contents}")
        else:
            if not params:
                print("Error: No file specified.")
                return []

            all_contents = []

            # Loop through each file in params
            for file_name in params:
                print(f"Fetching contents of file: {file_name} in directory with pid: {self.current_pid}")

                response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
                if response.status_code == 200:
                    file_contents = response.json().get("contents", "")
                    all_contents.append(file_contents)
                else:
                    print(f"Error: {response.json().get('detail', 'Unknown error')}")
                    return []

            # Join contents of all files with a newline between each
            combined_contents = "\n".join(all_contents)

        # Handle redirection if applicable
        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write(combined_contents)
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []
        else:
            # Print the concatenated file contents
            print(combined_contents)
            return combined_contents.splitlines()


    # sort command #        
    
    def run_sort(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the sort command to sort and display the contents of a file or piped input.
        
        Manual: 
        SORT(1)                                                    User Commands                                                    SORT(1)

NAME
       sort - sort lines of text files

SYNOPSIS
       sort [OPTION]... [FILE]...
       sort [OPTION]... --files0-from=F

DESCRIPTION
       Write sorted concatenation of all FILE(s) to standard output.

       With no FILE, or when FILE is -, read standard input.

       Mandatory arguments to long options are mandatory for short options too.  Ordering options:

       KEYDEF is F[.C][OPTS][,F[.C][OPTS]] for start and stop position, where F is a field number and C a character position in the    
       field; both are origin 1, and the stop position defaults to the line's end.  If neither -t nor -b is in  effect,  characters    
       in  a  field are counted from the beginning of the preceding whitespace.  OPTS is one or more single-letter ordering options    
       [bdfgiMhnRrV], which override global ordering options for that key.  If no key is given, use the entire  line  as  the  key.    
       Use --debug to diagnose incorrect key usage.

       SIZE may be followed by the following multiplicative suffixes: % 1% of memory, b 1, K 1024 (default), and so on for M, G, T,    
       P, E, Z, Y.

       *** WARNING *** The locale specified by the environment affects sort order.  Set LC_ALL=C to get the traditional sort  order    
       that uses native byte values.

AUTHOR
       Written by Mike Haertel and Paul Eggert.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       shuf(1), uniq(1)

       Full documentation <https://www.gnu.org/software/coreutils/sort>
       or available locally via: info '(coreutils) sort invocation'

GNU coreutils 8.32                                         February 2024                                                    SORT(1) """
        params = cmd["params"]

        # Check if we are sorting piped input
        if previous_output:
            print("Sorting piped input")  # Debugging
            # Sort the piped input
            sorted_contents = sorted(previous_output)
        else:
            # If no piped input, sort the contents of a file as usual
            if not params:
                print("Error: No file specified.")
                return []
            
            # The first parameter should be the file name
            file_name = params[0]
            print(f"Sorting contents of file: {file_name} in directory with pid: {self.current_pid}")  # Debugging

            # Send the request to the API to fetch and sort file contents
            response = requests.get(f"{self.url}/sort/?file_name={file_name}&pid={self.current_pid}")
            
            # Print debugging info
            print(f"API Request sent to: /sort/?file_name={file_name}&pid={self.current_pid}")
            print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")

            if response.status_code == 200:
                sorted_contents = response.json().get("sorted_contents", [])
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        # Handle redirection if applicable
        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write("\n".join(sorted_contents) + "\n")
                print(f"Sorted output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []  # No output to console when redirecting
        else:
            # If no redirection, print the sorted contents or piped input to the console
            print("\n".join(sorted_contents))
            return sorted_contents  # Return the sorted contents for further piping
    
    # wc with w flag command #        
            
    def run_wc_w(self, cmd, previous_output=None):
        """Execute the wc -w command to count words.
        
        Manual:
        
        WC(1)                                                      User Commands                                                      WC(1)

NAME
       wc - print newline, word, and byte counts for each file

SYNOPSIS
       wc [OPTION]... [FILE]...
       wc [OPTION]... --files0-from=F

DESCRIPTION
       Print  newline,  word,  and  byte  counts  for  each FILE, and a total line if more than one FILE is specified.  A word is a    
       non-zero-length sequence of characters delimited by white space.

       With no FILE, or when FILE is -, read standard input.

       The options below may be used to select which counts are printed, always in the following order: newline,  word,  character,    
       byte, maximum line length.

       -w, --words
              print the word counts

AUTHOR
       Written by Paul Rubin and David MacKenzie.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       Full documentation <https://www.gnu.org/software/coreutils/wc>
       or available locally via: info '(coreutils) wc invocation'

GNU coreutils 8.32                                         February 2024                                                      WC(1)"""
        if previous_output:
            # Count the words in the piped input
            word_count = sum(len(line.split()) for line in previous_output)
            print(f"Word count from piped input: {word_count}")
            return [str(word_count)]  # Return the result as a list for further piping
        else:
            # Handle the case when there's no previous output (file input)
            params = cmd["params"]
            if len(params) < 1:
                print("Error: wc requires a file or input")
                return []
            
            file_name = params[0]
            try:
                with open(file_name, 'r') as f:
                    content = f.read()
                    word_count = len(content.split())
            except IOError as e:
                print(f"Error reading file {file_name}: {e}")
                return []

            print(f"Word count from file: {word_count}")
            return [str(word_count)]


    #### wc

    # def run_wc(self, cmd, previous_output=None):
    #     if previous_output:
    #         # Process piped input
    #         line_count = len(previous_output)
    #         word_count = sum(len(line.split()) for line in previous_output)
    #         char_count = sum(len(line) for line in previous_output)
            
    #         print(f"Line count: {line_count}, Word count: {word_count}, Character count: {char_count}")
    #         return [str(line_count), str(word_count), str(char_count)]  # Return as a list for further piping
    #     else:
    #         # Handle the case when there's no previous output (file input)
    #         params = cmd["params"]
    #         if len(params) < 1:
    #             print("Error: wc requires a file or input")
    #             return []
            
    #         file_name = params[0]
    #         try:
    #             with open(file_name, 'r') as f:
    #                 content = f.readlines()
    #                 line_count = len(content)
    #                 word_count = sum(len(line.split()) for line in content)
    #                 char_count = sum(len(line) for line in content)
    #         except IOError as e:
    #             print(f"Error reading file {file_name}: {e}")
    #             return []

    #         print(f"Line count: {line_count}, Word count: {word_count}, Character count: {char_count}")
    #         return [str(line_count), str(word_count), str(char_count)]


    def run_wc(self, cmd, previous_output=None, redirect=None, append=False):
        # Perform word, line, and character count
        if previous_output:
            # Process piped input
            line_count = len(previous_output)
            word_count = sum(len(line.split()) for line in previous_output)
            char_count = sum(len(line) for line in previous_output)
        else:
            # Handle file input
            params = cmd["params"]
            if len(params) < 1:
                print("Error: wc requires a file or input")
                return []
            
            file_name = params[0]
            try:
                with open(file_name, 'r') as f:
                    content = f.readlines()
                    line_count = len(content)
                    word_count = sum(len(line.split()) for line in content)
                    char_count = sum(len(line) for line in content)
            except IOError as e:
                print(f"Error reading file {file_name}: {e}")
                return []

        # Prepare output as a single string
        output = f"Line count: {line_count}, Word count: {word_count}, Character count: {char_count}\n"

        # Handle redirection if specified
        if redirect:
            mode = 'a' if append else 'w'
            with open(redirect, mode) as f:
                f.write(output)
            return []  # Return an empty list since output was redirected
        else:
            # No redirection, so print to terminal and return for piping
            print(output.strip())
            return [output.strip()]



    # grep command #    
    
    def run_grep(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the grep command with optional flags and handle piping/redirection.
        
        Manual:
        GREP(1)                                                    User Commands                                                    GREP(1)

NAME
       grep, egrep, fgrep, rgrep - print lines that match patterns

SYNOPSIS
       grep [OPTION...] PATTERNS [FILE...]
       grep [OPTION...] -e PATTERNS ... [FILE...]
       grep [OPTION...] -f PATTERN_FILE ... [FILE...]

DESCRIPTION
       grep  searches for PATTERNS in each FILE.  PATTERNS is one or more patterns separated by newline characters, and grep prints    
       each line that matches a pattern.  Typically PATTERNS should be quoted when grep is used in a shell command.

       A FILE of “-” stands for standard input.  If no FILE is  given,  recursive  searches  examine  the  working  directory,  and    
       nonrecursive searches read standard input.

       In addition, the variant programs egrep, fgrep and rgrep are the same as grep -E, grep -F, and grep -r, respectively.  These    
       variants are deprecated, but are provided for backward compatibility.

OPTIONS
   Generic Program Information

       -l, --files-with-matches
              Suppress normal output; instead print the name of each input file from which output would normally have been printed.    
              Scanning each input file stops upon first match.

REGULAR EXPRESSIONS
       A regular expression is a pattern that describes a set of strings.   Regular  expressions  are  constructed  analogously  to    
       arithmetic expressions, by using various operators to combine smaller expressions.

       grep  understands  three different versions of regular expression syntax: “basic” (BRE), “extended” (ERE) and “perl” (PCRE).    
       In  GNU  grep  there  is  no  difference  in  available  functionality  between  basic  and  extended  syntaxes.   In  other    
       implementations,  basic  regular  expressions  are  less  powerful.   The  following description applies to extended regular    
       expressions; differences for basic regular expressions are summarized afterwards.  Perl-compatible regular expressions  give    
       additional  functionality,  and  are  documented in B<pcresyntax>(3) and B<pcrepattern>(3), but work only if PCRE support is    
       enabled.

       The fundamental building blocks are the regular expressions that match a single character.  Most characters,  including  all    
       letters and digits, are regular expressions that match themselves.  Any meta-character with special meaning may be quoted by    
       preceding it with a backslash.

       The period . matches any single character.  It is unspecified whether it matches an encoding error.

   Character Classes and Bracket Expressions
       A bracket expression is a list of characters enclosed by [ and ].  It matches any single character in  that  list.   If  the    
       first  character  of  the  list  is  the caret ^ then it matches any character not in the list; it is unspecified whether it    
       matches an encoding error.  For example, the regular expression [0123456789] matches any single digit.

       Within a bracket expression, a range expression consists of two characters separated by a hyphen.   It  matches  any  single    
       character  that  sorts  between the two characters, inclusive, using the locale's collating sequence and character set.  For    
       example, in the default C locale, [a-d] is equivalent to [abcd].  Many locales sort characters in dictionary order,  and  in    
       these  locales [a-d] is typically not equivalent to [abcd]; it might be equivalent to [aBbCcDd], for example.  To obtain the    
       traditional interpretation of bracket expressions, you can use the C locale by setting the LC_ALL  environment  variable  to    
       the value C.

       Finally,  certain  named  classes of characters are predefined within bracket expressions, as follows.  Their names are self    
       explanatory, and they are [:alnum:], [:alpha:], [:blank:], [:cntrl:], [:digit:], [:graph:], [:lower:], [:print:], [:punct:],    
       [:space:],  [:upper:],  and  [:xdigit:].   For  example, [[:alnum:]] means the character class of numbers and letters in the    
       current locale.  In the C locale and ASCII character set encoding, this is the same as [0-9A-Za-z].  (Note that the brackets    
       in these class names are part of the symbolic names, and must be included in addition to the brackets delimiting the bracket    
       expression.)  Most meta-characters lose their special meaning inside bracket expressions.  To include a literal ]  place  it    
       first in the list.  Similarly, to include a literal ^ place it anywhere but first.  Finally, to include a literal - place it    
       last.

   Anchoring
       The caret ^ and the dollar sign $ are meta-characters that respectively match the empty string at the beginning and end of a    
       line.

   The Backslash Character and Special Expressions
       The  symbols  \<  and  \> respectively match the empty string at the beginning and end of a word.  The symbol \b matches the    
       empty string at the edge of a word, and \B matches the empty string provided it's not at the edge of a word.  The symbol  \w    
       is a synonym for [_[:alnum:]] and \W is a synonym for [^_[:alnum:]].

   Repetition
       A regular expression may be followed by one of several repetition operators:
       ?      The preceding item is optional and matched at most once.
       *      The preceding item will be matched zero or more times.
       +      The preceding item will be matched one or more times.
       {n}    The preceding item is matched exactly n times.
       {n,}   The preceding item is matched n or more times.
       {,m}   The preceding item is matched at most m times.  This is a GNU extension.
       {n,m}  The preceding item is matched at least n times, but not more than m times.

   Concatenation
       Two regular expressions may be concatenated; the resulting regular expression matches any string formed by concatenating two    
       substrings that respectively match the concatenated expressions.

   Alternation
       Two regular expressions may be joined by the infix operator |; the resulting regular expression matches any string  matching    
       either alternate expression.

   Precedence
       Repetition  takes precedence over concatenation, which in turn takes precedence over alternation.  A whole expression may be    
       enclosed in parentheses to override these precedence rules and form a subexpression.

   Back-references and Subexpressions
       The back-reference \n, where n is a single digit,  matches  the  substring  previously  matched  by  the  nth  parenthesized    
       subexpression of the regular expression.

   Basic vs Extended Regular Expressions
       In  basic  regular  expressions  the  meta-characters  ?,  +,  {,  |,  (,  and ) lose their special meaning; instead use the    
       backslashed versions \?, \+, \{, \|, \(, and \).

EXIT STATUS
       Normally the exit status is 0 if a line is selected, 1 if no lines were selected, and 2 if an error occurred.   However,  if    
       the -q or --quiet or --silent is used and a line is selected, the exit status is 0 even if an error occurred.

ENVIRONMENT
       The behavior of grep is affected by the following environment variables.

       The  locale  for  category  LC_foo  is  specified by examining the three environment variables LC_ALL, LC_foo, LANG, in that    
       order.  The first of these variables that is set specifies the locale.  For example, if LC_ALL is not set,  but  LC_MESSAGES    
       is set to pt_BR, then the Brazilian Portuguese locale is used for the LC_MESSAGES category.  The C locale is used if none of    
       these environment variables are set, if the locale catalog is not installed, or if  grep  was  not  compiled  with  national    
       language support (NLS).  The shell command locale -a lists locales that are currently available.

       GREP_COLOR
              This  variable  specifies  the  color  used  to  highlight  matched  (non-empty)  text.  It is deprecated in favor of    
              GREP_COLORS, but still supported.  The mt, ms, and mc capabilities of GREP_COLORS have priority over it.  It can only    
              specify  the  color  used  to highlight the matching non-empty text in any matching line (a selected line when the -v    
              command-line option is omitted, or a context line when -v is specified).  The default is 01;31, which  means  a  bold    
              red foreground text on the terminal's default background.

       GREP_COLORS
              Specifies  the  colors  and  other  attributes  used to highlight various parts of the output.  Its value is a colon-    
              separated list of capabilities that defaults to ms=01;31:mc=01;31:sl=:cx=:fn=35:ln=32:bn=32:se=36 with the rv and  ne    
              boolean capabilities omitted (i.e., false).  Supported capabilities are as follows.

              sl=    SGR  substring  for  whole selected lines (i.e., matching lines when the -v command-line option is omitted, or    
                     non-matching lines when -v is specified).  If however the boolean rv capability and the -v command-line option    
                     are  both specified, it applies to context matching lines instead.  The default is empty (i.e., the terminal's    
                     default color pair).

              cx=    SGR substring for whole context lines (i.e., non-matching lines when the -v command-line option is omitted, or    
                     matching lines when -v is specified).  If however the boolean rv capability and the -v command-line option are    
                     both specified, it applies to selected non-matching lines instead.  The default is empty (i.e., the terminal's    
                     default color pair).

              rv     Boolean  value  that  reverses  (swaps)  the meanings of the sl= and cx= capabilities when the -v command-line    
                     option is specified.  The default is false (i.e., the capability is omitted).

              mt=01;31
                     SGR substring for matching non-empty text in any matching line (i.e., a selected line when the -v command-line    
                     option  is  omitted,  or a context line when -v is specified).  Setting this is equivalent to setting both ms=    
                     and mc= at once to the same value.  The  default  is  a  bold  red  text  foreground  over  the  current  line    
                     background.

              ms=01;31
                     SGR  substring  for  matching  non-empty text in a selected line.  (This is only used when the -v command-line    
                     option is omitted.)  The effect of the sl= (or cx= if rv) capability remains active when this kicks  in.   The    
                     default is a bold red text foreground over the current line background.

              mc=01;31
                     SGR  substring  for  matching  non-empty  text in a context line.  (This is only used when the -v command-line    
                     option is specified.)  The effect of the cx= (or sl= if rv) capability remains active when this kicks in.  The    
                     default is a bold red text foreground over the current line background.

              fn=35  SGR  substring  for  file names prefixing any content line.  The default is a magenta text foreground over the    
                     terminal's default background.

              ln=32  SGR substring for line numbers prefixing any content line.  The default is a green text  foreground  over  the    
                     terminal's default background.

              bn=32  SGR  substring  for  byte offsets prefixing any content line.  The default is a green text foreground over the    
                     terminal's default background.

              se=36  SGR substring for separators that are inserted between selected line fields (:), between context line  fields,    
                     (-),  and between groups of adjacent lines when nonzero context is specified (--).  The default is a cyan text    
                     foreground over the terminal's default background.

              ne     Boolean value that prevents clearing to the end of line using Erase in Line (EL) to Right (\33[K) each time  a    
                     colorized  item  ends.   This  is needed on terminals on which EL is not supported.  It is otherwise useful on    
                     terminals for which the back_color_erase (bce) boolean terminfo capability does not  apply,  when  the  chosen    
                     highlight colors do not affect the background, or when EL is too slow or causes too much flicker.  The default    
                     is false (i.e., the capability is omitted).

              Note that boolean capabilities have no =... part.  They are omitted (i.e., false) by default  and  become  true  when    
              specified.

              See  the  Select Graphic Rendition (SGR) section in the documentation of the text terminal that is used for permitted    
              values and their meaning as character attributes.  These substring values are integers in decimal representation  and    
              can  be  concatenated  with  semicolons.   grep  takes  care  of  assembling  the result into a complete SGR sequence    
              (\33[...m).  Common values to concatenate include 1 for bold, 4 for underline, 5 for blink, 7  for  inverse,  39  for    
              default  foreground  color,  30  to 37 for foreground colors, 90 to 97 for 16-color mode foreground colors, 38;5;0 to    
              38;5;255 for 88-color and 256-color modes foreground colors, 49 for default background color, 40 to 47 for background    
              colors,  100  to  107  for  16-color  mode background colors, and 48;5;0 to 48;5;255 for 88-color and 256-color modes    
              background colors.

       LC_ALL, LC_COLLATE, LANG
              These variables specify the locale for the LC_COLLATE category, which  determines  the  collating  sequence  used  to    
              interpret range expressions like [a-z].

       LC_ALL, LC_CTYPE, LANG
              These  variables  specify  the locale for the LC_CTYPE category, which determines the type of characters, e.g., which    
              characters are whitespace.  This category also determines the character encoding, that is, whether text is encoded in    
              UTF-8,  ASCII,  or  some  other  encoding.  In the C or POSIX locale, all characters are encoded as a single byte and    
              every byte is a valid character.

       LC_ALL, LC_MESSAGES, LANG
              These variables specify the locale for the LC_MESSAGES category, which determines the language  that  grep  uses  for    
              messages.  The default C locale uses American English messages.

       POSIXLY_CORRECT
              If  set,  grep  behaves as POSIX requires; otherwise, grep behaves more like other GNU programs.  POSIX requires that    
              options that follow file names must be treated as file names; by default, such options are permuted to the  front  of    
              the  operand  list  and  are  treated  as  options.   Also,  POSIX requires that unrecognized options be diagnosed as    
              “illegal”, but since  they  are  not  really  against  the  law  the  default  is  to  diagnose  them  as  “invalid”.    
              POSIXLY_CORRECT also disables _N_GNU_nonoption_argv_flags_, described below.

       _N_GNU_nonoption_argv_flags_
              (Here  N  is  grep's  numeric  process  ID.)   If the ith character of this environment variable's value is 1, do not    
              consider the ith operand of grep to be an option, even if it appears to be one.  A shell can put this variable in the    
              environment  for  each command it runs, specifying which operands are the results of file name wildcard expansion and    
              therefore should not be treated as options.  This behavior is available only with the GNU C library,  and  only  when    
              POSIXLY_CORRECT is not set.

NOTES
       This man page is maintained only fitfully; the full documentation is often more up-to-date.

COPYRIGHT
       Copyright 1998-2000, 2002, 2005-2021 Free Software Foundation, Inc.

       This is free software; see the source for copying conditions.  There is NO warranty; not even for MERCHANTABILITY or FITNESS    
       FOR A PARTICULAR PURPOSE.

BUGS
   Reporting Bugs
       Email     bug     reports     to     the     bug-reporting     address     ⟨bug-grep@gnu.org⟩.      An     email     archive    
       ⟨https://lists.gnu.org/mailman/listinfo/bug-grep⟩ and a bug tracker ⟨https://debbugs.gnu.org/cgi/pkgreport.cgi?package=grep⟩    
       are available.

   Known Bugs
       Large repetition counts in the {n,m} construct may cause grep to use lots of memory.  In  addition,  certain  other  obscure    
       regular expressions require exponential time and space, and may cause grep to run out of memory.

       Back-references are very slow, and may require exponential time.

EXAMPLE
       The  following  example outputs the location and contents of any line containing “f” and ending in “.c”, within all files in    
       the current directory whose names contain “g” and end in “.h”.  The -n option outputs line numbers, the --  argument  treats    
       expansions of “*g*.h” starting with “-” as file names not options, and the empty file /dev/null causes file names to be out‐    
       put even if only one file name happens to be of the form “*g*.h”.

         $ grep -n -- 'f.*\.c$' *g*.h /dev/null
         argmatch.h:1:/* definitions and prototypes for argmatch.c

       The only line that matches is line 1 of argmatch.h.  Note that the regular expression syntax used  in  the  pattern  differs    
       from the globbing syntax that the shell uses to match file names.

SEE ALSO
   Regular Manual Pages
       awk(1),  cmp(1), diff(1), find(1), perl(1), sed(1), sort(1), xargs(1), read(2), pcre(3), pcresyntax(3), pcrepattern(3), ter‐    
       minfo(5), glob(7), regex(7)

   Full Documentation
       A complete manual ⟨https://www.gnu.org/software/grep/manual/⟩ is available.  If the info and grep programs are properly  in‐    
       stalled at your site, the command

              info grep

       should give you access to the complete manual.

GNU grep 3.7                                                 2019-12-29                                                     GREP(1)
        """
        params = cmd["params"]

        # Debugging: Print the parsed command
        print(f"Running grep command with params: {params}")
        
        if len(params) < 1:
            print("Error: grep requires at least a pattern")
            return []
        
        pattern = params[0]
        
        if previous_output:
            # If previous_output is provided (piped input), search in that data
            print(f"Searching for pattern: {pattern} in piped input")
            matched_lines = [line for line in previous_output if pattern in line]

            if redirect:
                # Handle redirection if present
                mode = 'a' if append else 'w'
                try:
                    with open(redirect, mode) as f:
                        for line in matched_lines:
                            f.write(line + "\n")
                    print(f"Output successfully written to {redirect}")
                except IOError as e:
                    print(f"Error writing to file {redirect}: {e}")
            else:
                # No redirection, print the matched lines to the console
                for line in matched_lines:
                    print(line)

            return matched_lines  # Return the matched lines for further piping

        else:
            # If no previous_output (piping), assume input comes from a file
            if len(params) < 2:
                print("Error: grep requires a pattern and a file")
                return []
            
            file_name = params[1]
            print(f"Searching for pattern: {pattern} in file: {file_name}")
            
            # Build the query parameters based on flags
            flags = cmd["flags"]
            query_params = {
                'l': '-l' in flags,
            }

            # Send a request to the API to grep the file
            response = requests.get(f"{self.url}/grep/?pattern={pattern}&file_name={file_name}", params=query_params)
            
            if response.status_code == 200:
                matched_lines = response.json().get('matched_lines', [])
                
                if redirect:
                    mode = 'a' if append else 'w'
                    try:
                        with open(redirect, mode) as f:
                            for line in matched_lines:
                                f.write(line + "\n")
                        print(f"Output successfully written to {redirect}")
                    except IOError as e:
                        print(f"Error writing to file {redirect}: {e}")
                else:
                    for line in matched_lines:
                        print(line)
                
                return matched_lines  # Return matched lines for further piping
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

    # rm command #

    def run_rm(self, cmd):
        """Execute the rm command with optional flags -r (recursive) and -f (force).
        
        Manual:
        RM(1)                                                      User Commands                                                      RM(1)

NAME
       rm - remove files or directories

SYNOPSIS
       rm [OPTION]... [FILE]...

DESCRIPTION
       This  manual page documents the GNU version of rm.  rm removes each specified file.  By default, it does not remove directo‐    
       ries.

       If the -I or --interactive=once option is given, and there are more than three files or  the  -r,  -R,  or  --recursive  are    
       given,  then  rm prompts the user for whether to proceed with the entire operation.  If the response is not affirmative, the    
       entire command is aborted.

       Otherwise, if a file is unwritable, standard input is a terminal, and the -f or --force option is not given, or  the  -i  or    
       --interactive=always  option  is given, rm prompts the user for whether to remove the file.  If the response is not affirma‐    
       tive, the file is skipped.

OPTIONS
       Remove (unlink) the FILE(s).

       -f, --force
              ignore nonexistent files and arguments, never prompt
       -r
              remove directories and their contents recursively

       Note  that  if you use rm to remove a file, it might be possible to recover some of its contents, given sufficient expertise    
       and/or time.  For greater assurance that the contents are truly unrecoverable, consider using shred.

AUTHOR
       Written by Paul Rubin, David MacKenzie, Richard M. Stallman, and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright © 2020 Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3  or  later  <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       unlink(1), unlink(2), chattr(1), shred(1)

       Full documentation <https://www.gnu.org/software/coreutils/rm>
       or available locally via: info '(coreutils) rm invocation'

GNU coreutils 8.32                                         February 2024                                                      RM(1) 
        """
        params = cmd["params"]
        flags = cmd["flags"]

        if not params:
            print("Error: No file or directory specified for removal.")
            return

        target = params[0]
        recursive = "-r" in flags
        force = "-f" in flags

        # Build the API request parameters
        query_params = {
            'recursive': recursive,
            'force': force,
            'target': target
        }

        # Send the request to the API
        response = requests.delete(f"{self.url}/rm/", params=query_params)
        print(f"API Request sent to: /rm/?target={target}&recursive={recursive}&force={force}")  # Debugging
        print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")  # Debugging

        # Handle the response from the API
        if response.status_code == 200:
            print(f"Successfully removed {target}.")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")    


    # mkdir command #

    def run_mkdir(self, cmd):
        """Execute the mkdir command to create a directory.
        
        Manual:
        MKDIR(1)                                                   User Commands                                                   MKDIR(1)

NAME
       mkdir - make directories

SYNOPSIS
       mkdir [OPTION]... DIRECTORY...

DESCRIPTION
       Create the DIRECTORY(ies), if they do not already exist.

       Mandatory arguments to long options are mandatory for short options too.

       -p, --parents
              no error if existing, make parent directories as needed

AUTHOR
       Written by David MacKenzie.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       mkdir(2)

       Full documentation <https://www.gnu.org/software/coreutils/mkdir>
       or available locally via: info '(coreutils) mkdir invocation'

GNU coreutils 8.32                                         February 2024                                                   MKDIR(1) 
        """
        params = cmd["params"]
        flags = cmd["flags"]

        if not params:
            print("Error: No directory name specified.")
            return

        dir_name = params[0]
        parent_pid = self.current_pid

        if '-p' in flags:
            parts = dir_name.split('/')
            for part in parts:
                if part:
                    response = requests.post(f"{self.url}/mkdir/?name={part}&pid={parent_pid}&oid=1")
                    if response.status_code == 200:
                        parent_pid = response.json().get("directory_id")
                    else:
                        print(f"Error: {response.json().get('detail', 'Unknown error')}")
                        return
            print(f"Created directory {dir_name} with parent directories.")
        else:
            # print(f"{self.url}/mkdir/", {"name": dir_name, "pid": parent_pid, "oid": 1})
            obj ={"name": dir_name, "pid": parent_pid, "oid": 1}
            print(obj)
            response = requests.post(f"{self.url}/mkdir/?name={dir_name}&pid={parent_pid}&oid=1")
            if response.status_code == 200:
                print(f"Created directory {dir_name}")
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")

    # pwd command #

    def run_pwd(self, cmd):
        """Execute the pwd command to display the current path.
        
        Manual:
        PWD(1)                                                     User Commands                                                     PWD(1)

NAME
       pwd - print name of current/working directory

SYNOPSIS
       pwd [OPTION]...

DESCRIPTION
       Print the full filename of the current working directory.

AUTHOR
       Written by Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright © 2020 Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3  or  later  <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       getcwd(3)

       Full documentation <https://www.gnu.org/software/coreutils/pwd>
       or available locally via: info '(coreutils) pwd invocation'

GNU coreutils 8.32                                         February 2024                                                     PWD(1)"""
        # no need for params, only need command itself
        print(f"Current directory PID: {self.current_pid}")
    
    # # mv command #
    
    def run_mv(self, cmd):
        """Execute the mv command to either move a file or rename it.
        
        Manual:
        
        MV(1)                                                      User Commands                                                      MV(1)

NAME
       mv - move (rename) files

SYNOPSIS
       mv [OPTION]... [-T] SOURCE DEST
       mv [OPTION]... SOURCE... DIRECTORY
       mv [OPTION]... -t DIRECTORY SOURCE...

DESCRIPTION
       Rename SOURCE to DEST, or move SOURCE(s) to DIRECTORY.

       Mandatory arguments to long options are mandatory for short options too.

AUTHOR
       Written by Mike Parker, David MacKenzie, and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright © 2020 Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3  or  later  <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       rename(2)

       Full documentation <https://www.gnu.org/software/coreutils/mv>
       or available locally via: info '(coreutils) mv invocation'

GNU coreutils 8.32                                         February 2024                                                      MV(1) """
        params = cmd["params"]

        if len(params) < 2:
            print("Error: Source and destination must be specified.")
            return

        src_file = params[0]
        dest_path = params[1]

        # Handle if the destination is a directory or a file
        if dest_path.endswith('/'):
            # Destination is a directory, get the directory's ID
            dest_dir_name = dest_path.rstrip('/')
            dest_info = self.getId(dest_dir_name)  # Get directory info from the database
            if not dest_info:
                print(f"Error: Destination directory {dest_dir_name} not found.")
                return
            dest_pid = dest_info.get("id")
            dest_name = src_file  # Keep the original file name when moving to a directory
        else:
            # Split the destination path into directory and file name
            dest_parts = dest_path.rsplit('/', 1)
            if len(dest_parts) == 2:
                # Move and rename
                dest_dir_name, dest_name = dest_parts
                dest_info = self.getId(dest_dir_name)  # Get the directory info
                if not dest_info:
                    print(f"Error: Destination directory {dest_dir_name} not found.")
                    return
                dest_pid = dest_info.get("id")
            else:
                # Just rename the file in the current directory
                dest_pid = self.current_pid
                dest_name = dest_path

        # Send a request to the API to move or rename the file
        response = requests.post(f"{self.url}/mv/?file_name={src_file}&src_pid={self.current_pid}&dest_pid={dest_pid}&dest_name={dest_name}")
        if response.status_code == 200:
            print(f"Moved {src_file} to {dest_path}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")

    
    # Less command #

    def run_less(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the less command to display the contents of a file starting from the bottom.
        
        Manual:
        LESS(1)                  General Commands Manual                 LESS(1)
NAME         top
       less - opposite of more
SYNOPSIS         top
       less -?
       less --help
       less -V
       less --version
       less [-[+]aABcCdeEfFgGiIJKLmMnNqQrRsSuUVwWX~]
            [-b space] [-h lines] [-j line] [-k keyfile]
            [-{oO} logfile] [-p pattern] [-P prompt] [-t tag]
            [-T tagsfile] [-x tab,...] [-y lines] [-[z] lines]
            [-# shift] [+[+]cmd] [--] [filename]...
       (See the OPTIONS section for alternate option syntax with long
       option names.)
DESCRIPTION         top
       Less is a program similar to more(1), but which allows backward
       movement in the file as well as forward movement.  Also, less
       does not have to read the entire input file before starting, so
       with large input files it starts up faster than text editors like
       vi(1).  Less uses termcap (or terminfo on some systems), so it
       can run on a variety of terminals.  There is even limited support
       for hardcopy terminals.  (On a hardcopy terminal, lines which
       should be printed at the top of the screen are prefixed with a
       caret.)

       Commands are based on both more and vi.  Commands may be preceded
       by a decimal number, called N in the descriptions below.  The
       number is used by some commands, as indicated.
COMMANDS         top
       In the following descriptions, ^X means control-X.  ESC stands
       for the ESCAPE key; for example ESC-v means the two character
       sequence "ESCAPE", then "v".

       Enter
              Scroll forward N lines, default one window (see option -z
              below).  If N is more than the screen size, only the final
              screenful is displayed.  Warning: some systems use ^V as a
              special literalization character.
              
SEE ALSO         top
       lesskey(1), lessecho(1)
COPYRIGHT         top
       Copyright (C) 1984-2023  Mark Nudelman

       less is part of the GNU project and is free software.  You can
       redistribute it and/or modify it under the terms of either (1)
       the GNU General Public License as published by the Free Software
       Foundation; or (2) the Less License.  See the file README in the
       less distribution for more details regarding redistribution.  You
       should have received a copy of the GNU General Public License
       along with the source for less; see the file COPYING.  If not,
       write to the Free Software Foundation, 59 Temple Place, Suite
       330, Boston, MA  02111-1307, USA.  You should also have received
       a copy of the Less License; see the file LICENSE.

       less is distributed in the hope that it will be useful, but WITH‐
       OUT ANY WARRANTY; without even the implied warranty of MER‐
       CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
       General Public License for more details.
AUTHOR         top
       Mark Nudelman
       Report bugs at https://github.com/gwsw/less/issues.
       For more information, see the less homepage at
       https://greenwoodsoftware.com/less
COLOPHON         top
       This page is part of the less (A file pager) project.  Informa‐
       tion about the project can be found at 
       ⟨http://www.greenwoodsoftware.com/less/⟩.  If you have a bug
       report for this manual page, see
       ⟨http://www.greenwoodsoftware.com/less/faq.html#bugs⟩.  This page
       was obtained from the tarball less-643.tar.gz fetched from
       ⟨http://www.greenwoodsoftware.com/less/download.html⟩ on
       2024-06-14.  If you discover any rendering problems in this HTML
       version of the page, or you believe there is a better or more up-
       to-date source for the page, or you have corrections or
       improvements to the information in this COLOPHON (which is not
       part of the original manual page), send a mail to
       man-pages@man7.org

                        Version 643: 20 Jul 2023                 LESS(1)
"""
        params = cmd["params"]

        if previous_output:
            lines = previous_output[::-1]
        else:
            if not params:
                print("Error: No file specified.")
                return []

            file_name = params[0]
            response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
            if response.status_code == 200:
                lines = response.json().get("contents").splitlines()[::-1]
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        terminal_size = shutil.get_terminal_size((80, 20))
        page_size = terminal_size.lines - 1

        for i in range(0, len(lines), page_size):
            output = "\n".join(lines[i:i + page_size])
            if redirect:
                mode = 'a' if append else 'w'
                try:
                    with open(redirect, mode) as f:
                        f.write(output)
                    print(f"Output successfully written to {redirect}")
                except IOError as e:
                    print(f"Error writing to file {redirect}: {e}")
                return []
            else:
                print(output)
                if i + page_size < len(lines):
                    input("Press Enter to continue...")
        return lines[::-1]
        
    # more command #

    def run_more(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the more command to display the contents of a file starting from the top.
        
        Manual:
        
        MORE(1)                       User Commands                      MORE(1)
NAME         top
       more - display the contents of a file in a terminal
SYNOPSIS         top
       more [options] file ...
DESCRIPTION         top
       more is a filter for paging through text one screenful at a time.
       This version is especially primitive. Users should realize that
       less(1) provides more(1) emulation plus extensive enhancements.
       
       COMMANDS         top
       Interactive commands for more are based on vi(1). Some commands
       may be preceded by a decimal number, called k in the descriptions
       below. In the following descriptions, ^X means control-X.

       ENTER
           Display next k lines of text. Defaults to current screen
           size.
    
        HISTORY         top
       The more command appeared in 3.0BSD. This man page documents more
       version 5.19 (Berkeley 6/29/88), which is currently in use in the
       Linux community. Documentation was produced using several other
       versions of the man page, and extensive inspection of the source
       code.
AUTHORS         top
       Eric Shienbrood, UC Berkeley.

       Modified by Geoff Peck, UCB to add underlining, single spacing.

       Modified by John Foderaro, UCB to add -c and MORE environment
       variable.
SEE ALSO         top
       less(1), vi(1)
REPORTING BUGS         top
       For bug reports, use the issue tracker at
       https://github.com/util-linux/util-linux/issues.
AVAILABILITY         top
       The more command is part of the util-linux package which can be
       downloaded from Linux Kernel Archive
       <https://www.kernel.org/pub/linux/utils/util-linux/>. This page
       is part of the util-linux (a random collection of Linux
       utilities) project. Information about the project can be found at
       ⟨https://www.kernel.org/pub/linux/utils/util-linux/⟩. If you have
       a bug report for this manual page, send it to
       util-linux@vger.kernel.org. This page was obtained from the
       project's upstream Git repository
       ⟨git://git.kernel.org/pub/scm/utils/util-linux/util-linux.git⟩ on
       2024-06-14. (At that time, the date of the most recent commit
       that was found in the repository was 2024-06-10.) If you discover
       any rendering problems in this HTML version of the page, or you
       believe there is a better or more up-to-date source for the page,
       or you have corrections or improvements to the information in
       this COLOPHON (which is not part of the original manual page),
       send a mail to man-pages@man7.org

util-linux 2.39.594-1e0ad      2023-07-19                        MORE(1)
"""
        params = cmd["params"]

        if previous_output:
            lines = previous_output
        else:
            if not params:
                print("Error: No file specified.")
                return []

            file_name = params[0]
            response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
            if response.status_code == 200:
                lines = response.json().get("contents").splitlines()
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        terminal_size = shutil.get_terminal_size((80, 20))
        page_size = terminal_size.lines - 1

        for i in range(0, len(lines), page_size):
            output = "\n".join(lines[i:i + page_size])
            if redirect:
                mode = 'a' if append else 'w'
                try:
                    with open(redirect, mode) as f:
                        f.write(output)
                    print(f"Output successfully written to {redirect}")
                except IOError as e:
                    print(f"Error writing to file {redirect}: {e}")
                return []
            else:
                print(output)
                if i + page_size < len(lines):
                    input("Press Enter to continue...")
        return lines
        
    # head command #

    def run_head(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the head command to display the first few lines of a file.
        
        Manual:
        
        HEAD(1)                                                    User Commands                                                    HEAD(1)

NAME
       head - output the first part of files

SYNOPSIS
       head [OPTION]... [FILE]...

DESCRIPTION
       Print  the  first  10 lines of each FILE to standard output.  With more than one FILE, precede each with a header giving the    
       file name.

       With no FILE, or when FILE is -, read standard input.

       Mandatory arguments to long options are mandatory for short options too.

AUTHOR
       Written by David MacKenzie and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright © 2020 Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3  or  later  <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       tail(1)

       Full documentation <https://www.gnu.org/software/coreutils/head>
       or available locally via: info '(coreutils) head invocation'

GNU coreutils 8.32                                         February 2024                                                    HEAD(1)  """
        params = cmd["params"]
        flags = cmd["flags"]

        if previous_output:
            lines = previous_output
        else:
            if not params:
                print("Error: No file specified.")
                return []

            file_name = params[0]
            response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
            if response.status_code == 200:
                lines = response.json().get("contents").splitlines()
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        num_lines = 10  # Default number of lines
        if '-n' in flags:
            try:
                num_lines = int(params[1])
            except (IndexError, ValueError):
                print("Error: Invalid number of lines specified.")
                return []

        output = "\n".join(lines[:num_lines])

        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write(output)
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []
        else:
            print(output)
            return output.splitlines()
        
    # tail command #

    def run_tail(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the tail command to display the bottom parts of a file's content as specified.
        
        Manual:
        
        TAIL(1)                                                    User Commands                                                    TAIL(1)

NAME
       tail - output the last part of files

SYNOPSIS
       tail [OPTION]... [FILE]...

DESCRIPTION
       Print  the  last  10  lines of each FILE to standard output.  With more than one FILE, precede each with a header giving the    
       file name.

       With no FILE, or when FILE is -, read standard input.

       Mandatory arguments to long options are mandatory for short options too.

AUTHOR
       Written by Paul Rubin, David MacKenzie, Ian Lance Taylor, and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright © 2020 Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3  or  later  <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       head(1)

       Full documentation <https://www.gnu.org/software/coreutils/tail>
       or available locally via: info '(coreutils) tail invocation'

GNU coreutils 8.32                                         February 2024                                                    TAIL(1)"""
        params = cmd["params"]
        flags = cmd["flags"]

        if previous_output:
            lines = previous_output
        else:
            if not params:
                print("Error: No file specified.")
                return []

            file_name = params[0]
            response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
            if response.status_code == 200:
                lines = response.json().get("contents").splitlines()
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        num_lines = 10  # Default number of lines
        if '-n' in flags:
            try:
                num_lines = int(params[1])
            except (IndexError, ValueError):
                print("Error: Invalid number of lines specified.")
                return []

        output = "\n".join(lines[-num_lines:])

        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write(output)
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []
        else:
            print(output)
            return output.splitlines()

    # chmod command #     
    
    def run_chmod(self, cmd):
        """Execute the chmod command to change the permissions of the designated file or directory.
        
        Manual:
        
        CHMOD(1)                                                   User Commands                                                   CHMOD(1)

NAME
       chmod - change file mode bits

SYNOPSIS
       chmod [OPTION]... MODE[,MODE]... FILE...
       chmod [OPTION]... OCTAL-MODE FILE...
       chmod [OPTION]... --reference=RFILE FILE...

DESCRIPTION
       This manual page documents the GNU version of chmod.  chmod changes the file mode bits of each given file according to mode,    
       which can be either a symbolic representation of changes to make, or an octal number representing the bit  pattern  for  the    
       new mode bits.

       The  format  of  a  symbolic  mode is [ugoa...][[-+=][perms...]...], where perms is either zero or more letters from the set    
       rwxXst, or a single letter from the set ugo.  Multiple symbolic modes can be given, separated by commas.

       A combination of the letters ugoa controls which users' access to the file will be changed: the user who owns it (u),  other    
       users  in  the file's group (g), other users not in the file's group (o), or all users (a).  If none of these are given, the    
       effect is as if (a) were given, but bits that are set in the umask are not affected.

       The operator + causes the selected file mode bits to be added to the existing file mode bits of each file; - causes them  to    
       be  removed;  and  = causes them to be added and causes unmentioned bits to be removed except that a directory's unmentioned    
       set user and group ID bits are not affected.

       The letters rwxXst select file mode bits for the affected users: read (r), write (w), execute (or  search  for  directories)    
       (x),  execute/search  only if the file is a directory or already has execute permission for some user (X), set user or group    
       ID on execution (s), restricted deletion flag or sticky bit (t).  Instead of one or more of these letters, you  can  specify    
       exactly  one of the letters ugo: the permissions granted to the user who owns the file (u), the permissions granted to other    
       users who are members of the file's group (g), and the permissions granted to users that are in neither of the two preceding    
       categories (o).

       A  numeric mode is from one to four octal digits (0-7), derived by adding up the bits with values 4, 2, and 1.  Omitted dig‐    
       its are assumed to be leading zeros.  The first digit selects the set user ID (4) and set group ID (2) and restricted  dele‐    
       tion  or  sticky  (1) attributes.  The second digit selects permissions for the user who owns the file: read (4), write (2),    
       and execute (1); the third selects permissions for other users in the file's group, with the same values; and the fourth for    
       other users not in the file's group, with the same values.

       chmod never changes the permissions of symbolic links; the chmod system call cannot change their permissions.  This is not a    
       problem since the permissions of symbolic links are never used.  However, for each symbolic link listed on the command line,    
       chmod  changes  the permissions of the pointed-to file.  In contrast, chmod ignores symbolic links encountered during recur‐    
       sive directory traversals.

SETUID AND SETGID BITS
       chmod clears the set-group-ID bit of a regular file if the file's group ID does not match the user's effective group  ID  or    
       one  of  the  user's supplementary group IDs, unless the user has appropriate privileges.  Additional restrictions may cause    
       the set-user-ID and set-group-ID bits of MODE or RFILE to be ignored.  This behavior depends on the policy and functionality    
       of the underlying chmod system call.  When in doubt, check the underlying system behavior.

       For  directories  chmod preserves set-user-ID and set-group-ID bits unless you explicitly specify otherwise.  You can set or    
       clear the bits with symbolic modes like u+s and g-s.  To clear these bits for directories with a numeric  mode  requires  an    
       additional leading zero, or leading = like 00755 , or =755

RESTRICTED DELETION FLAG OR STICKY BIT
       The restricted deletion flag or sticky bit is a single bit, whose interpretation depends on the file type.  For directories,    
       it prevents unprivileged users from removing or renaming a file in the directory unless they own the file or the  directory;    
       this  is  called  the  restricted  deletion flag for the directory, and is commonly found on world-writable directories like    
       /tmp.  For regular files on some older systems, the bit saves the program's text image on the swap device so  it  will  load    
       more quickly when run; this is called the sticky bit.

AUTHOR
       Written by David MacKenzie and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       chmod(2)

       Full documentation <https://www.gnu.org/software/coreutils/chmod>
       or available locally via: info '(coreutils) chmod invocation'

GNU coreutils 8.32                                         February 2024                                                   CHMOD(1)"""
        params = cmd["params"]

        if len(params) < 2:
            print("Error: File/directory and permissions must be specified.")
            return

        file_name = params[1]
        permissions = params[0]

        # Convert permissions to a dictionary
        if permissions.isdigit() and len(permissions) == 2:
            owner_perm = int(permissions[0])
            world_perm = int(permissions[1])

            perm_dict = {
                'read_permission': owner_perm & 4 != 0,
                'write_permission': owner_perm & 2 != 0,
                'execute_permission': owner_perm & 1 != 0,
                'world_read': world_perm & 4 != 0,
                'world_write': world_perm & 2 != 0,
                'world_execute': world_perm & 1 != 0
            }
        else:
            print("Error: Invalid permissions specified.")
            return

        # Determine if the target is a file or directory by calling a helper API endpoint or checking the database
        response = requests.get(f"{self.url}/is_dir_or_file/?file_name={file_name}&pid={self.current_pid}")
        if response.status_code == 200:
            target_type = response.json().get("type")

            if target_type == "file":
                # Apply chmod to a file
                response = requests.post(f"{self.url}/chmod/?file_name={file_name}&pid={self.current_pid}&target=file", json=perm_dict)
            elif target_type == "directory":
                # Apply chmod to a directory
                response = requests.post(f"{self.url}/chmod/?file_name={file_name}&pid={self.current_pid}&target=directory", json=perm_dict)

            if response.status_code == 200:
                print(f"Permissions updated for {file_name}")
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")



    # cp command #
    
    def run_cp(self, cmd):
        """Execute the cp command to copy a file or directory.
        
        Manual:
        
        CP(1)                                                      User Commands                                                      CP(1)

NAME
       cp - copy files and directories

SYNOPSIS
       cp [OPTION]... [-T] SOURCE DEST
       cp [OPTION]... SOURCE... DIRECTORY
       cp [OPTION]... -t DIRECTORY SOURCE...

DESCRIPTION
       Copy SOURCE to DEST, or multiple SOURCE(s) to DIRECTORY.

       Mandatory arguments to long options are mandatory for short options too.

       By  default,  sparse  SOURCE files are detected by a crude heuristic and the corresponding DEST file is made sparse as well.    
       That is the behavior selected by --sparse=auto.  Specify --sparse=always to create a sparse DEST file  whenever  the  SOURCE    
       file contains a long enough sequence of zero bytes.  Use --sparse=never to inhibit creation of sparse files.

       When  --reflink[=always]  is specified, perform a lightweight copy, where the data blocks are copied only when modified.  If    
       this is not possible the copy fails, or if --reflink=auto is specified, fall back to a standard copy.   Use  --reflink=never    
       to ensure a standard copy is performed.

       The  backup suffix is '~', unless set with --suffix or SIMPLE_BACKUP_SUFFIX.  The version control method may be selected via    
       the --backup option or through the VERSION_CONTROL environment variable.  Here are the values:

       none, off
              never make backups (even if --backup is given)

       numbered, t
              make numbered backups

       existing, nil
              numbered if numbered backups exist, simple otherwise

       simple, never
              always make simple backups

       As a special case, cp makes a backup of SOURCE when the force and backup options are given and SOURCE and DEST are the  same    
       name for an existing, regular file.

AUTHOR
       Written by Torbjorn Granlund, David MacKenzie, and Jim Meyering.

REPORTING BUGS
       GNU coreutils online help: <https://www.gnu.org/software/coreutils/>
       Report any translation bugs to <https://translationproject.org/team/>

COPYRIGHT
       Copyright  ©  2020  Free  Software  Foundation,  Inc.   License  GPLv3+:  GNU  GPL  version  3 or later <https://gnu.org/li‐    
       censes/gpl.html>.
       This is free software: you are free to change and redistribute it.  There is NO WARRANTY, to the extent permitted by law.       

SEE ALSO
       Full documentation <https://www.gnu.org/software/coreutils/cp>
       or available locally via: info '(coreutils) cp invocation'

GNU coreutils 8.32                                         February 2024                                                      CP(1) """
        params = cmd["params"]

        if len(params) < 2:
            print("Error: Source and destination must be specified.")
            return

        src_name = params[0]
        dest_path = params[1]

        # Check if the destination is a directory path or a file path
        if dest_path.endswith('/'):
            # Destination is a directory, get the destination directory's ID
            dest_info = self.getId(dest_path.rstrip('/'))  # Get directory info from the database
            if not dest_info:
                print(f"Error: Destination directory {dest_path} not found.")
                return
            dest_pid = dest_info.get("id")
            dest_name = src_name  # Keep the original file name when copying to a directory
        else:
            # Split the destination into directory and file name
            dest_parts = dest_path.rsplit('/', 1)
            if len(dest_parts) == 2:
                # A directory path and file name are specified
                dest_dir_name, dest_name = dest_parts
                dest_info = self.getId(dest_dir_name)  # Get directory info from the database
                if not dest_info:
                    print(f"Error: Destination directory {dest_dir_name} not found.")
                    return
                dest_pid = dest_info.get("id")
            else:
                # No directory path specified, use current directory
                dest_pid = self.current_pid
                dest_name = dest_path

        # Send a request to the API to copy the file
        response = requests.post(f"{self.url}/cp/?file_name={src_name}&src_pid={self.current_pid}&dest_pid={dest_pid}&dest_name={dest_name}")
        if response.status_code == 200:
            print(f"Copied {src_name} to {dest_path}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")




    # !x command #
    def x_history(self, index):
        """Retrieve a command from history based on its index BUT DO NOT EXECUTE."""
        if 0 <= index < len(self.history):
            return self.history[index]
        else:
            print(f"No command found at index {index}")
            return None

    # fortune command #
    def run_fortune(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the fortune command to display a random line from fortunes.txt."""
        try:
            with open("fortunes.txt", "r") as file:
                lines = file.readlines()
                if not lines:
                    print("No fortunes found.")
                    return []

                random_index = random.randint(0, len(lines) - 1)
                output = lines[random_index].strip()

                if redirect:
                    mode = 'a' if append else 'w'
                    try:
                        with open(redirect, mode) as f:
                            f.write(output)
                        print(f"Output successfully written to {redirect}")
                    except IOError as e:
                        print(f"Error writing to file {redirect}: {e}")
                    return []
                else:
                    print(output)
                    return [output]
        except FileNotFoundError:
            print("fortunes.txt file not found.")
            return []

    # touch command #
    def run_touch(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the touch command to create empty files."""
        if previous_output:
            # Split the previous output into individual words
            words = " ".join(previous_output).split()
        else:
            params = cmd["params"]
            if not params:
                print("Error: No file names specified.")
                return []
            words = params

        outputs = []
        for word in words:
            response = requests.post(f"{self.url}/create_file/?name={word}&contents=''&pid={self.current_pid}&oid=1&size=0")
            if response.status_code == 200:
                output = f"Created file {word}"
                outputs.append(output)
                if redirect:
                    mode = 'a' if append else 'w'
                    try:
                        with open(redirect, mode) as f:
                            f.write(output + "\n")
                        print(f"Output successfully written to {redirect}")
                    except IOError as e:
                        print(f"Error writing to file {redirect}: {e}")
                    return []
                else:
                    print(output)
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        return outputs

    # cowspeak command #
    def run_cowspeak(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the cowspeak command to display a message with a cow.

        Manual:
        meow
        meow
        meow
        woof"""
        print(f"Previous output: {previous_output}")
        print(f"Command params: {cmd['params']}")
        print(f"Redirect: {redirect}, Append: {append}")

        if previous_output:
            message = " ".join(previous_output)
        else:
            params = cmd["params"]
            if not params:
                print("Error: No message specified.")
                return []
            message = " ".join(params)

        cow = f"""
        {message}
        \\
          \\
            \\
            ^__^
            (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
        """

        if redirect:
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write(cow)
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []
        else:
            print(cow)
            return [cow]
    
    # man command #

    def run_man(self, cmd):
        """ General manual command to display the manual of any defined function. """
        params = cmd["params"]

        if not params:
            print("Error: No command specified.")
            return

        function_name = params[0]
        function = getattr(self, f"run_{function_name}", None)

        if function and callable(function):
            docstring = function.__doc__
            if docstring:
                manual_start = docstring.find("Manual:")
                if manual_start != -1:
                    print(docstring[manual_start:])
                else:
                    print("No manual found in the docstring.")
            else:
                print("No docstring available for this function.")
        else:
            print(f"No such command: {function_name}")

"""
- the shell allows users to enter commands
- we then parse the command and make function calls accordingly
    - simple commands would be implemented right here in this file (still possibly talking to the db)
    - more complex commands would be implemented and service using the api and the db
"""


##################################################################################
##################################################################################


getch = Getch()  # create instance of our getch class

# DbApi = DbApi()

# ANSI color codes for blue path
BLUE = '\033[94m'
RESET = '\033[0m'

# prompt = "$"  # set default prompt
prompt = f"{BLUE}~{RESET}$ "

def update_prompt(path):
    """Update the global prompt with the current path in blue."""
    global prompt
    prompt = f"{BLUE}{path}{RESET}$ "

def get_flags(cmd):
    flags = []
    for c in cmd:
        if c.startswith("-") or c.startswith("--"):
            flags.append(c)
    return flags


def get_params(cmd):
    params = []
    for c in cmd:
        if "-" in c or "--" in c:
            continue
        params.append(c)

    for i, p in enumerate(params[:-1]):
        if (
            params[i].startswith("'")
            and params[i + 1].endswith("'")
            or params[i].startswith('"')
            and params[i + 1].endswith('"')
        ):
            params[i] = params[i] + " " + params[i + 1]

    return params


def print_cmd(cmd, cursor_pos):
    """This function "cleans" off the command line, then prints
    whatever cmd that is passed to it to the bottom of the terminal.
    """
    padding = " " * 80
    sys.stdout.write("\r" + padding)  # clear the line
    sys.stdout.write("\r" + prompt + cmd)  # print the prompt and the command
    sys.stdout.write("\r" + prompt + cmd[:cursor_pos])  # move cursor to the correct position
    sys.stdout.flush()  # flush the buffer

if __name__ == "__main__":

    db_api = DbApi()
    cmd = ""  # empty cmd variable
    cursor_pos = 0 # cursor position in the terminal

    print_cmd(cmd, cursor_pos)  # print to terminal

    while True:  # loop forever

        char = getch()  # read a character (but don't print)

        if char == "\x03" or cmd == "exit":  # ctrl-c
            raise SystemExit("\nFine, be that way.")

        elif char == "\x7f":  # back space pressed
            cmd = cmd[:-1]
            print_cmd(cmd, cursor_pos)

        elif char in "\x1b":  # arrow key pressed
            null = getch()  # waste a character (this will be the '[' character)
            direction = getch()  # grab the direction character (A, B, C, or D)

            if direction in "A":  # up arrow pressed
                db_api.history_index = (db_api.history_index - 1) % (len(db_api.history) + 1)
                if db_api.history_index == len(db_api.history):
                    cmd = ""
                else:
                    cmd = db_api.history[db_api.history_index]
                cursor_pos = len(cmd)
                print_cmd(cmd, cursor_pos)

            if direction in "B":  # down arrow pressed
                db_api.history_index = (db_api.history_index + 1) % (len(db_api.history) + 1)
                if db_api.history_index == len(db_api.history):
                    cmd = ""
                else:
                    cmd = db_api.history[db_api.history_index]
                cursor_pos = len(cmd)
                print_cmd(cmd, cursor_pos)

            if direction in "C":  # right arrow pressed
                if cursor_pos < len(cmd):
                    cursor_pos += 1
                    sys.stdout.write("\033[C")
                    sys.stdout.flush()

            if direction in "D":  # left arrow pressed
                if cursor_pos > 0:
                    cursor_pos -= 1
                    sys.stdout.write("\033[D")
                    sys.stdout.flush()

            print_cmd(cmd, cursor_pos)  # print the command (again)

        elif char in "\r":  # return pressed
            print_cmd("", cursor_pos)
            if cmd.startswith("!"):
                try:
                    index = int(cmd[1:]) - 1  # Convert to zero-based index
                    history_cmd = db_api.x_history(index)
                    if history_cmd:
                        cmd = history_cmd
                        print_cmd(cmd, cursor_pos)  # Print the command from history
                        continue
                except ValueError:
                    print("Error: Invalid history index.")
            # This 'elif' simulates something "happening" after pressing return
            else:
                parsed_cmd = parse(cmd)
                print(parsed_cmd)
                sleep(1)

                # Save the command to history
                parsed_cmd = parse(cmd)
                db_api.save_to_history(cmd)


                # Iterate through each sub-command parsed
                previous_output = None
                for sub_cmd in parsed_cmd["sub_cmds"]:
                    if sub_cmd["cmd"] == "ls":
                        print("Running ls command")
                        # previous_output = db_api.run_ls(sub_cmd)
                        previous_output = db_api.run_ls(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "cd":
                        previous_output = db_api.run_cd(sub_cmd)
                    elif sub_cmd["cmd"] == "cat":
                        # Pass the redirection and append values to run_cat
                        previous_output = db_api.run_cat(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "sort":
                        # previous_output = db_api.run_sort(sub_cmd)
                        previous_output = db_api.run_sort(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "wc" and "-w" in sub_cmd["flags"]:
                        print("Running wc -w command")
                        previous_output = db_api.run_wc_w(sub_cmd, previous_output)
                    elif sub_cmd["cmd"] == "wc":
                        print("Running wc command")
                        # previous_output = db_api.run_wc(sub_cmd)
                        previous_output = db_api.run_wc(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "grep":
                        # Pass the previous output if there's piping
                        previous_output = db_api.run_grep(sub_cmd, previous_output)
                    elif sub_cmd["cmd"] == "history":
                        previous_output = db_api.show_history()
                    elif sub_cmd["cmd"] == "rm":
                        previous_output = db_api.run_rm(sub_cmd)
                    elif sub_cmd["cmd"] == "pwd":
                        previous_output = db_api.run_pwd(sub_cmd)
                    elif sub_cmd["cmd"] == "mv":
                        previous_output = db_api.run_mv(sub_cmd)
                    elif sub_cmd["cmd"] == "mkdir":
                        previous_output = db_api.run_mkdir(sub_cmd)
                    elif sub_cmd["cmd"] == "chmod":
                        previous_output = db_api.run_chmod(sub_cmd)
                    elif sub_cmd["cmd"] == "cp":
                        previous_output = db_api.run_cp(sub_cmd)
                    elif sub_cmd["cmd"] == "more":
                        previous_output = db_api.run_more(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "less":
                        previous_output = db_api.run_less(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "head":
                        previous_output = db_api.run_head(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "tail":
                        previous_output = db_api.run_tail(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "fortune":
                        previous_output = db_api.run_fortune(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "touch":
                        previous_output = db_api.run_touch(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "cowspeak":
                        previous_output = db_api.run_cowspeak(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                    elif sub_cmd["cmd"] == "man":
                        db_api.run_man(sub_cmd)

                    else:
                        print(f"Unknown command: {sub_cmd['cmd']}")

            cmd = ""  # reset command to nothing (since we just executed it)
            cursor_pos = 0  # reset cursor position
            db_api.history_index = len(db_api.history)  # reset history index
            print_cmd(cmd, cursor_pos)  # now print empty cmd prompt
        else:
            cmd += char  # add typed character to our "cmd"
            cursor_pos += 1  # move cursor position forward
            print_cmd(cmd, cursor_pos)  # print the cmd out