#!/home/sly/anaconda3/bin/python3
"""
This file is about using getch to capture input and handle certain keys 
when the are pushed. The 'command_DbApi.py' was about parsing and calling functions.
This file is about capturing the user input so that you can mimic shell behavior.

"""
import cmd_pkg.ls as ls_cmd
import cmd_pkg.cd as cd_cmd


import os
import sys
from time import sleep
from sqliteCRUD import SqliteCRUD # REVISIT THIS
import sqlite3

from getch import Getch
import requests




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


class DbApi:
    def __init__(self):
        self.url = "http://localhost:8080"
        self.conn = SqliteCRUD("filesystem.db")
        self.current_pid = 1
        self.history_file = "command_history.txt"  # Path to history file
        self.history = self.load_history()    

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

    
    def getId(self, name, pid=1):
        """Retrieve the directory ID (pid) based on the directory name using sqliteCRUD."""
        return self.conn.get_directory_id(name, pid)


    def run_ls(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the ls command with optional flags and handle piping and redirection."""
        params = cmd["params"]
        
        # Handle piped input if it exists (though 'ls' typically doesn't process piped input)
        if previous_output:
            print("Listing piped input (not typical for ls)")  # Debugging
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
                # Assuming the dictionary has a 'name' field for the file/directory name
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
            self._print_ls_output(contents_str, flags)
            return contents_str  # Return contents for further piping if needed

    
    def _print_ls_output(self, contents, flags):
        """Print the output of the ls command, taking into account flags."""
        # Check if long format '-l' is passed
        long_format = '-l' in flags

        for item in contents:
            if isinstance(item, dict):
                # Handle the case where the item is a dictionary (detailed listing)
                if long_format:
                    file_type = 'd' if item['type'] == 'dir' else '-'
                    permissions = item['permissions']  # Already formatted as 'r-x' etc.
                    owner = item['owner']
                    size = item['size']
                    modified_date = item['modified_date']
                    name = item['name']

                    # Format and print the output in long format
                    print(f"{file_type}{permissions} {owner} {size} {modified_date} {name}")
                else:
                    # Short format: just print the names
                    print(item['name'])
            else:
                # Handle the case where the item is a string or other type (for example, from piped input)
                print(item)


    def human_readable_size(self, size_in_bytes):
        """Convert a file size in bytes to a human-readable format."""
        if size_in_bytes is None:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} PB"



    #### cd
    def get_home_directory_pid(self):
        """Return the pid of the home directory using sqliteCRUD."""
        # Use the SqliteCRUD connection (self.conn)
        return self.conn.get_home_directory_pid()


    def get_parent_directory(self):
        """Return the parent directory based on the current pid."""
        return ".."


    def run_cd(self, cmd):
        """Execute the cd command with support for ~, .., and directory names."""
        params = cmd["params"]

        if not params or params[0] == "~":
            # Change to home directory, reset current_pid to 1 (home's id)
            target_dir = "home"  # Always use 'home' for ~
            print(f"Changing to home directory: {target_dir}")  # Debugging
            self.current_pid = 1  # Reset current_pid to home directory's id (id = 1)
        elif params[0] == "..":
            # Change to parent directory
            target_dir = self.get_parent_directory()
            print(f"Changing to parent directory: {target_dir}")  # Debugging
        else:
            # Change to the specified directory
            target_dir = params[0]
            print(f"Changing to specified directory: {target_dir}")  # Debugging
        
        # Send the request to the API to change the directory
        response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
        print(f"API Request sent to: /cd/?dir={target_dir}&current_pid={self.current_pid}")  # Debugging
        print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")  # Debugging
        
        if response.status_code == 200:
            new_pid = response.json().get("new_pid")
            self.current_pid = new_pid  # Update the shell's current directory (IMPORTANT)
            print(f"Changed directory to: {target_dir}, New PID: {self.current_pid}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            
    
    def run_cat(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the cat command to concatenate and display the content of a file."""
        params = cmd["params"]

        # Handle piped input (if there is any)
        if previous_output:
            file_contents = "\n".join(previous_output)
            print(f"Processing piped input in 'cat': {file_contents}")
        else:
            # If no piped input, read the file as usual
            if not params:
                print("Error: No file specified.")
                return []
            
            # The first parameter should be the file name
            file_name = params[0]
            print(f"Fetching contents of file: {file_name} in directory with pid: {self.current_pid}")  # Debugging

            # Send the request to the API to fetch file contents
            response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
            
            # Check if the file exists and has contents
            if response.status_code == 200:
                file_contents = response.json().get("contents", "")
            else:
                print(f"Error: {response.json().get('detail', 'Unknown error')}")
                return []

        # Handle redirection after fetching the file
        if redirect:
            # Write to the redirected file
            mode = 'a' if append else 'w'
            try:
                with open(redirect, mode) as f:
                    f.write(file_contents)
                print(f"Output successfully written to {redirect}")
            except IOError as e:
                print(f"Error writing to file {redirect}: {e}")
            return []  # No output to console when redirecting
        else:
            # If no redirection, print the file contents or piped input to the console
            print(file_contents)
            return file_contents.splitlines()  # Return the file contents as a list of lines for further piping


    def run_sort(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the sort command to sort and display the contents of a file or piped input."""
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

    
    # def run_wc(self, cmd):
    #     """Implement the general wc command to count lines, words, and characters."""
        
    #     def count_words_lines_characters(text):
    #         """Return a tuple containing line count, word count, and character count."""
    #         lines = text.splitlines()  # Splitting based on new lines
    #         words = text.split()  # Splitting based on spaces and new lines
    #         characters = len(text)  # Length of the text gives the character count
    #         return len(lines), len(words), characters
        
    #     params = cmd["params"]

    #     if not params:
    #         print("Error: No file specified for wc command.")
    #         return

    #     file_name = params[0]

    #     # Fetch the file contents from the database
    #     conn = sqlite3.connect(db_path)
    #     cursor = conn.cursor()
        
    #     cursor.execute("SELECT contents FROM files WHERE name = ? AND pid = ?", (file_name, pid))
    #     result = cursor.fetchone()

    #     if result:
    #         # Decode the BLOB contents
    #         file_contents = result[0].decode('utf-8')

    #         # Count lines, words, and characters
    #         lines, words, characters = count_words_lines_characters(file_contents)
    #         print(f"{lines} {words} {characters} {file_name}")
    #     else:
    #         print(f"Error: File '{file_name}' not found in the current directory.")
        
    #     conn.close()
     

    
    def run_wc_w(self, cmd, previous_output=None):
        """Execute the wc -w command to count words."""
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


    def run_grep(self, cmd, previous_output=None, redirect=None, append=False):
        """Execute the grep command with optional flags and handle piping/redirection."""
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



    def run_rm(self, cmd):
        """Execute the rm command with optional flags -r (recursive) and -f (force)."""
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


    ### fortune


"""
- the shell allows users to enter commands
- we then parse the command and make function calls accordingly
    - simple commands would be implemented right here in this file (still possibly talking to the db)
    - more complex commands would be implemented and service using the api and the db
"""


##################################################################################
##################################################################################


getch = Getch()  # create instance of our getch class

DbApi = DbApi()

prompt = "$"  # set default prompt


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


def print_cmd(cmd):
    """This function "cleans" off the command line, then prints
    whatever cmd that is passed to it to the bottom of the terminal.
    """
    padding = " " * 80
    sys.stdout.write("\r" + padding)  # clear the line
    sys.stdout.write("\r" + prompt + cmd)  # print the prompt and the command
    sys.stdout.flush()  # flush the buffer


if __name__ == "__main__":

    # cmd = "ls /home/user/griffin /www/html -l -a | grep 'student gpa' 'test.txt' '23,43,12' | wc -l > output.txt"  # empty cmd variable
    # print(cmd)
    # cmd = parse(cmd)

    # sys.exit(0)

    cmd = ""  # empty cmd variable

    print_cmd(cmd)  # print to terminal

    while True:  # loop forever

        char = getch()  # read a character (but don't print)

        if char == "\x03" or cmd == "exit":  # ctrl-c
            raise SystemExit("\nBye.")

        elif char == "\x7f":  # back space pressed
            cmd = cmd[:-1]
            print_cmd(cmd)

        elif char in "\x1b":  # arrow key pressed
            null = getch()  # waste a character
            direction = getch()  # grab the direction

            if direction in "A":  # up arrow pressed
                # get the PREVIOUS command from your history (if there is one)
                # prints out 'up' then erases it (just to show something)
                cmd += "\u2191"
                print_cmd(cmd)
                sleep(0.3)
                # cmd = cmd[:-1]

            if direction in "B":  # down arrow pressed
                # get the NEXT command from history (if there is one)
                # prints out 'down' then erases it (just to show something)
                cmd += "\u2193"
                print_cmd(cmd)
                sleep(0.3)
                # cmd = cmd[:-1]

            if direction in "C":  # right arrow pressed
                # move the cursor to the right on your command prompt line
                # prints out 'right' then erases it (just to show something)
                cmd += "\u2192"
                print_cmd(cmd)
                sleep(0.3)
                # cmd = cmd[:-1]

            if direction in "D":  # left arrow pressed
                # moves the cursor to the left on your command prompt line
                # prints out 'left' then erases it (just to show something)
                cmd += "\u2190"
                print_cmd(cmd)
                sleep(0.3)
                # cmd = cmd[:-1]

            print_cmd(cmd)  # print the command (again)

        elif char in "\r":  # return pressed
            print_cmd("")
            # This 'elif' simulates something "happening" after pressing return
            parsed_cmd = parse(cmd)
            print(parsed_cmd)
            sleep(1)
            
            # Save the command to history
            parsed_cmd = parse(cmd)
            DbApi.save_to_history(cmd)
            

            # Iterate through each sub-command parsed
            previous_output = None
            for sub_cmd in parsed_cmd["sub_cmds"]:
                if sub_cmd["cmd"] == "ls":
                    print("Running ls command")
                    # previous_output = DbApi.run_ls(sub_cmd)
                    previous_output = DbApi.run_ls(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                elif sub_cmd["cmd"] == "cd":
                    previous_output = DbApi.run_cd(sub_cmd)
                elif sub_cmd["cmd"] == "cat":
                    # Pass the redirection and append values to run_cat
                    previous_output = DbApi.run_cat(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                elif sub_cmd["cmd"] == "sort":
                    # previous_output = DbApi.run_sort(sub_cmd)
                    previous_output = DbApi.run_sort(sub_cmd, previous_output, redirect=parsed_cmd["redirect"], append=parsed_cmd["append"])
                elif sub_cmd["cmd"] == "wc" and "-w" in sub_cmd["flags"]:
                    print("Running wc -w command")
                    previous_output = DbApi.run_wc_w(sub_cmd, previous_output)
                elif sub_cmd["cmd"] == "wc":
                    print("Running wc command")
                    previous_output = DbApi.run_wc(sub_cmd)
                elif sub_cmd["cmd"] == "grep":
                    # Pass the previous output if there's piping
                    previous_output = DbApi.run_grep(sub_cmd, previous_output)
                elif sub_cmd["cmd"] == "history":
                    previous_output = DbApi.show_history()
                elif sub_cmd["cmd"] == "rm":
                    previous_output = DbApi.run_rm(sub_cmd)
                elif sub_cmd["cmd"] == "pwd":
                    previous_output = DbApi.run_pwd(sub_cmd)
                else:
                    print(f"Unknown command: {sub_cmd['cmd']}")


            cmd = ""  # reset command to nothing (since we just executed it)

            print_cmd(cmd)  # now print empty cmd prompt
        else:
            cmd += char  # add typed character to our "cmd"
            print_cmd(cmd)  # print the cmd out