# shell.py

import importlib # Dynamically imports Python modules (in this case, shell commands)
import pkgutil # Helps iterate through the modules in the cmd_pkg package
import cmd_pkg # this is the package where the shell commands reside
from cmd_pkg import append_to_history, load_history

# Dictionary of commands to store available commands - keys are command names (e.g. ls, pwd) and values are the actual function references.
cmds = {}

def load_commands():
    """This function scans the cmd_pkg directory, dynamically importing all modules and loading the callable functions (commands) into the cmds dictionary."""
    global cmds
    # Shell loop for user input. It searches for the command in the cmds dictionary and executes the corresponding function.
    # If command exists, it executes it using the parameters provided by the user. If does not exist, returns "Command not found" message.
    
    # Loop through all moduels in the cmd_pkg package
    for _, module_name, _ in pkgutil.iter_modules(cmd_pkg.__path__):
        module = importlib.import_module(f"cmd_pkg.{module_name}")
        
        # Loop through the attributes in each module
        for name in dir(module):
            obj = getattr(module, name)
            # Check if it's a callable function and does not start with '__'
            if callable(obj) and not name.startswith("__"):
                cmds[name] = obj
                
# Function to execute the shell loop
def shell_loop():
    while True:
        # Prompt for user input
        user_input = input("$ ").strip()
        
        # Exit the shell if the user types 'exit' or 'quit'
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting shell.")
            break
        
        # Append command to history
        append_to_history(user_input)

        # Split the input into command and parameters
        if user_input:
            input_parts = user_input.split()
            cmd = input_parts[0]  # The command (e.g., 'ls', 'pwd', etc.)
            params = input_parts[1:]  # Any parameters for the command
            
            # Execute the command if it's found
            if cmd in cmds:
                try:
                    result = cmds[cmd](*params)  # Call the command with params
                    if result:
                        print(result)
                except TypeError as e:
                    print(f"Error: {e}")
            else:
                print(f"Command '{cmd}' not found.")


    
if __name__ == '__main__':
    # Load command history
    load_history()
    
    # Load commands dynamically from cmd_pkg
    load_commands()
    
    # Run the shell loop to accept user commands
    shell_loop()