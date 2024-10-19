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


class DbApi:
    def __init__(self):
        self.url = "http://localhost:8080"
        self.conn = SqliteCRUD("filesystem.db")
        self.current_pid = 1

    # def getId(self, name, pid=1):
    #     """Retrieve the directory ID (pid) based on the directory name."""
    #     conn = self._connect()
    #     cursor = conn.cursor()
    #     cursor.execute("SELECT id FROM directories WHERE name = ? AND pid = ?", (name, pid))
    #     result = cursor.fetchone()
    #     conn.close()
    #     if result:
    #         return {'id': result[0]}
    #     else:
    #         print(f"Error: Directory '{name}' not found.")
    #         return None  # Return None if the directory is not found
    
    def getId(self, name, pid=1):
        """Retrieve the directory ID (pid) based on the directory name using sqliteCRUD."""
        return self.conn.get_directory_id(name, pid)

    
    # def run_ls(self, cmd): 
    #     """Execute the ls command with optional flags and directory name."""
    #     params = cmd["params"]
    #     pid = 1  # Default to root directory if no directory is specified
        
    #     # If a directory name is passed, get its pid
    #     if params:
    #         dir_name = params[0]  # First param should be the directory name
    #         result = self.getId(dir_name)  # Fetch the pid of the directory
            
    #         if result is None:
    #             # Directory was not found, stop further execution
    #             print(f"Error: Directory '{dir_name}' not found.")
    #             return
            
    #         pid = result.get("id", 1)  # Set the pid to the found directory's id
        
    #     # Build the query parameters based on flags
    #     flags = cmd["flags"]
    #     query_params = {
    #         'l': '-l' in flags,
    #         'a': '-a' in flags,
    #         'h': '-h' in flags,
    #     }

    #     # Send a request to the API to list the directory contents
    #     response = requests.get(f"{self.url}/ls/{pid}", params=query_params)
    #     if response.status_code == 200:
    #         contents = response.json().get('contents', [])
    #         print(contents)  # Debugging print

    #         # Process and print directory contents
    #         self._print_ls_output(contents, flags)
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    def run_ls(self, cmd): 
        """Execute the ls command with optional flags and use the current directory pid."""
        params = cmd["params"]
        
        # By default, use the current directory (current_pid)
        pid = self.current_pid  
        
        # If a directory name is passed, get its pid
        if params:
            dir_name = params[0]
            result = self.getId(dir_name)
            if result is None:
                print(f"Error: Directory '{dir_name}' not found.")
                return
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
            print(contents)  # Debugging print

            # Process and print directory contents
            self._print_ls_output(contents, flags)
        else:
          print(f"Error: {response.json().get('detail', 'Unknown error')}")



    def _print_ls_output(self, contents, flags):
        """Helper method to handle printing the output based on flags."""
        for item in contents:
            name = item.get('name', 'Unknown')
            file_type = item.get('type', 'Unknown')
            size = item.get('size', None)  # Assuming 'size' is returned in the response

            if '-h' in flags and size is not None:
                # Apply human-readable size conversion
                size_str = self.human_readable_size(size)
            else:
                size_str = f"{size} bytes" if size is not None else "N/A"

            if '-l' in flags:
                # Print long listing with size and file type
                print(f"{name} ({file_type}) - Size: {size_str}")
            else:
                # Regular listing
                print(f"{name} ({file_type})")

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

    # def run_cd(self, cmd):
    #     """Execute the cd command with support for ~, .., and directory names."""
    #     params = cmd["params"]

    #     if not params or params[0] == "~":
    #         # Change to home directory (e.g., '/home/user')
    #         target_dir = self.get_home_directory()
    #     elif params[0] == "..":
    #         # Change to parent directory
    #         target_dir = self.get_parent_directory()
    #     else:
    #         # Change to the specified directory
    #         target_dir = params[0]
        
    #     # Send the request to the API to change the directory
    #     response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
        
    #     if response.status_code == 200:
    #         new_pid = response.json().get("new_pid")
    #         self.current_pid = new_pid  # Update the shell's current directory
    #         print(f"Changed directory to: {target_dir}")
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    # def run_cd(self, cmd):
    #     """Execute the cd command with support for ~, .., and directory names."""
    #     params = cmd["params"]

    #     if not params or params[0] == "~":
    #         # Change to home directory (e.g., '/home')
    #         target_dir = self.get_home_directory_pid()
    #     elif params[0] == "..":
    #         # Change to parent directory
    #         target_dir = self.get_parent_directory()
    #     else:
    #         # Change to the specified directory
    #         target_dir = params[0]
        
    #     # Send the request to the API to change the directory
    #     response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
        
    #     if response.status_code == 200:
    #         new_pid = response.json().get("new_pid")
    #         self.current_pid = new_pid  # Update the shell's current directory (IMPORTANT)
    #         print(f"Changed directory to: {target_dir}")
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    # def run_cd(self, cmd):
    #     """Execute the cd command with support for ~, .., and directory names."""
    #     params = cmd["params"]

    #     if not params or params[0] == "~":
    #         # Change to home directory (id = 1)
    #         target_dir = self.get_home_directory_pid()
    #     elif params[0] == "..":
    #         # Change to parent directory
    #         target_dir = self.get_parent_directory()
    #     else:
    #         # Change to the specified directory
    #         target_dir = params[0]
        
    #     # Send the request to the API to change the directory
    #     response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
        
    #     if response.status_code == 200:
    #         new_pid = response.json().get("new_pid")
    #         self.current_pid = new_pid  # Update the shell's current directory (IMPORTANT)
    #         print(f"Changed directory to: {target_dir}")
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    # def run_cd(self, cmd):
    #     """Execute the cd command with support for ~, .., and directory names."""
    #     params = cmd["params"]

    #     if not params or params[0] == "~":
    #         # Change to home directory (id = 1)
    #         target_dir = self.get_home_directory_pid()
    #         print(f"Home directory id fetched: {target_dir}")  # Debugging
    #     elif params[0] == "..":
    #         # Change to parent directory
    #         target_dir = self.get_parent_directory()
    #     else:
    #         # Change to the specified directory
    #         target_dir = params[0]
    #         print(f"Changing to specified directory: {target_dir}")  # Debugging
        
    #     # Send the request to the API to change the directory
    #     response = requests.get(f"{self.url}/cd/?dir={target_dir}&current_pid={self.current_pid}")
    #     print(f"API Request sent to: /cd/?dir={target_dir}&current_pid={self.current_pid}")  # Debugging
    #     print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")  # Debugging
        
    #     if response.status_code == 200:
    #         new_pid = response.json().get("new_pid")
    #         self.current_pid = new_pid  # Update the shell's current directory (IMPORTANT)
    #         print(f"Changed directory to: {target_dir}, New PID: {self.current_pid}")
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")

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


    def run_cp(self, cmd):
        # already know what dir we are in
        #       cp dog pet (copy dog to pet in local directory)
        #       cp dog /other/dir/pet (copy dog to pet in other directory)
        #       cp dog /other/dir/pet/  (copy dog to directory pet keeping its own name dog)
        # get all the dog info from the db
        # insert that info into the pets folder
        pass

    # def run_cat(self, cmd):
    #     """Execute the cat command to concatenate and display the content of a file."""
    #     params = cmd["params"]
        
    #     if not params:
    #         print("Error: No file specified.")
    #         return

    #     # The first parameter should be the file name
    #     file_name = params[0]
    #     print(f"Fetching contents of file: {file_name}") # Debugging
        
    #     # Send the request to the API to fetch file contents
    #     response = requests.get(f"{self.url}/cat/?ffile_name={file_name}&pid={self.current_pid}")

    #     # Print debugging info
    #     print(f"API Request sent to: /cat/?file_name={file_name}&pid={self.current_pid}")
    #     print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")        

    #     if response.status_code == 200:
    #         file_contents = response.json().get("contents")
    #         print(file_contents)  # Display the file contents
    #     else:
    #         print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
    def run_cat(self, cmd):
        """Execute the cat command to concatenate and display the content of a file."""
        params = cmd["params"]

        if not params:
            print("Error: No file specified.")
            return
        
        # The first parameter should be the file name
        file_name = params[0]
        print(f"Fetching contents of file: {file_name} in directory with pid: {self.current_pid}")  # Debugging

        # Send the request to the API to fetch file contents, passing the current pid
        response = requests.get(f"{self.url}/cat/?file_name={file_name}&pid={self.current_pid}")
        
        # Print debugging info
        print(f"API Request sent to: /cat/?file_name={file_name}&pid={self.current_pid}")
        print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")

        if response.status_code == 200:
            file_contents = response.json().get("contents")
            print(file_contents)  # Display the file contents
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
            
    
    def run_sort(self, cmd):
        """Execute the sort command to sort and display the contents of a file."""
        params = cmd["params"]

        if not params:
            print("Error: No file specified.")
            return
        
        # The first parameter should be the file name
        file_name = params[0]
        print(f"Sorting contents of file: {file_name} in directory with pid: {self.current_pid}")  # Debugging

        # Send the request to the API to fetch and sort file contents
        response = requests.get(f"{self.url}/sort/?file_name={file_name}&pid={self.current_pid}")
        
        # Print debugging info
        print(f"API Request sent to: /sort/?file_name={file_name}&pid={self.current_pid}")
        print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")

        if response.status_code == 200:
            sorted_contents = response.json().get("sorted_contents")
            print("\n".join(sorted_contents))  # Display the sorted contents
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")
    
            
    
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
            
    def run_wc_w(self, cmd):
        """Handle wc -w command."""
        params = cmd["params"]

        if not params:
            print("Error: No file specified for wc -w command.")
            return

        file_name = params[0]

        # Send request to the API to count words in the file
        response = requests.get(f"{self.url}/wc_w/?file_name={file_name}&pid={self.current_pid}")
        print(f"API Request sent to: /wc_w/?file_name={file_name}&pid={self.current_pid}")  # Debugging
        print(f"API Response Status Code: {response.status_code}, Response: {response.json()}")  # Debugging

        if response.status_code == 200:
            word_count = response.json().get('word_count')
            print(f"{word_count} {file_name}")
        else:
            print(f"Error: {response.json().get('detail', 'Unknown error')}")




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


def parse(cmd):
    """This function takes a command and parses it into a list of tokens
    1. Explode on redeirects
    2. Explode on pipes

    """
    redirect = None

    if ">" in cmd:
        cmd, redirect = cmd.split(">")
    if "|" in cmd:
        sub_cmds = cmd.split("|")
    else:
        sub_cmds = [cmd]

    for i in range(len(sub_cmds)):
        cmd = sub_cmds[i].strip()
        cmd = cmd.split(" ")

        cmdDict = {
            "cmd": cmd[0],
            "flags": get_flags(cmd),
            "params": get_params(cmd[1:]),
        }

    return cmdDict


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
            raise SystemExit("Bye.")

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

            if parsed_cmd["cmd"] == "ls":
                print("Running ls command")
                DbApi.run_ls(parsed_cmd)
            elif parsed_cmd["cmd"] == "cd":
                DbApi.run_cd(parsed_cmd)
            elif parsed_cmd["cmd"] == "cat":
                DbApi.run_cat(parsed_cmd)
            elif parsed_cmd["cmd"] == "sort":
                DbApi.run_sort(parsed_cmd)
            elif parsed_cmd["cmd"] == "wc" and "-w" in parsed_cmd["flags"]:
                print("Running wc -w command")
                DbApi.run_wc_w(parsed_cmd)
            elif parsed_cmd["cmd"] == "wc":
                print("Running wc command")
                DbApi.run_wc(parsed_cmd)
            elif parsed_cmd["cmd"] == "pwd":
                DbApi.run_pwd(parsed_cmd)

            ## YOUR CODE HERE
            ## API CALLS TO OUR DB FILESYTEM OR LOCAL METHODS TO HANDLE COMMANDS
            ## Parse the command
            ## Figure out what your executing like finding pipes and redirects

            cmd = ""  # reset command to nothing (since we just executed it)

            print_cmd(cmd)  # now print empty cmd prompt
        else:
            cmd += char  # add typed character to our "cmd"
            print_cmd(cmd)  # print the cmd out