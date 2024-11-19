### Entry point for running simulations

import sys
from fcfs import run_fcfs_simulation
from cpu_jobs import getConfig
import os

def MyKwargs(argv):
    """
    Processes argv list into plain args and kwargs.
    """
    args = []
    kargs = {}

    for arg in argv[1:]:  # Skip the script name
        if "=" in arg:
            key, val = arg.split("=", 1)
            kargs[key.strip("-")] = val
        else:
            args.append(arg.strip("-"))
    return args, kargs

if __name__ == "__main__":
    # Parse command-line arguments into args and kargs
    args, kargs = MyKwargs(sys.argv)

    # Validate mandatory arguments
    if "sched" not in kargs or kargs["sched"] != "FCFS":
        print("Error: --sched must be specified and set to FCFS.")
        sys.exit()

    # Validate and convert CPUs and IO devices
    try:
        kargs["cpus"] = int(kargs.get("cpus", 2))  # Default to 2 CPUs
        kargs["ios"] = int(kargs.get("ios", 2))  # Default to 2 IO devices
    except ValueError:
        print("Error: --cpus and --ios must be integers.")
        sys.exit()

    if not (1 <= kargs["cpus"] <= 4):
        print("Error: --cpus must be between 1 and 4.")
        sys.exit()
    if not (1 <= kargs["ios"] <= 4):
        print("Error: --ios must be between 1 and 4.")
        sys.exit()

    # Validate input file
    input_file = kargs.get("input")
    if input_file:
        if not os.path.isfile(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            sys.exit()
        print(f"Using input file: {input_file}")

    # Configuration for the simulation
    client_id = kargs.get("client_id", "brett")  # Default client_id
    config = getConfig(client_id)
    config["cpus"] = kargs["cpus"]  # Add the number of CPUs to the configuration
    config["ios"] = kargs["ios"]  # Add the number of IO devices to the configuration

    # Run selected scheduling algorithm
    if kargs["sched"] == "FCFS":
        print(f"Running FCFS with {kargs['cpus']} CPUs and {kargs['ios']} IO devices...")
        run_fcfs_simulation(config, client_id, num_cores=config["cpus"])