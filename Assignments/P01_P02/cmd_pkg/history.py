# cmd_pkg/history.py

from pathlib import Path

# Global list to store command history
command_history = []
history_file = Path.home() / ".shell_history"  # The history file path in the home directory

def load_history():
    """
    Load the command history from the .shell_history file.
    """
    global command_history
    if history_file.exists():
        with open(history_file, 'r') as f:
            command_history = [line.strip() for line in f.readlines()]

def append_to_history(command):
    """
    Add a command to the history list and append it to the history file.
    """
    global command_history
    command_history.append(command)

    # Append the new command to the .shell_history file
    with open(history_file, 'a') as f:
        f.write(f"{command}\n")

def history():
    """
    Display the command history.
    """
    # Print each command with its index (like typical shell history)
    return '\n'.join([f"{i+1} {cmd}" for i, cmd in enumerate(command_history)])
