### Entry point for running simulations

import sys
from fcfs import run_fcfs_simulation
from pb import run_pb_simulation
from rr import run_rr_simulation
from cpu_jobs import getConfig, init
import os
from mlfq import run_mlfq_simulation

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
    if "sched" not in kargs:
        print("Error: --sched must be specified.")
        sys.exit()
    
    if "aging" in kargs:
        try:
            kargs["aging"] = int(kargs["aging"])
            if kargs["aging"] <= 0:
                raise ValueError
        except ValueError:
            print("Error: --aging must be a positive integer.")
            sys.exit()
    else:
        kargs["aging"] = 10  # Default value for aging threshold


    # Validate and convert CPUs and IO devices
    try:
        kargs["cpus"] = int(kargs.get("cpus", 2))  # Default to 2 CPUs
        kargs["ios"] = int(kargs.get("ios", 2))  # Default to 2 IO devices
        kargs["seed"] = kargs.get("seed", None)
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
    config["aging"] = kargs["aging"] # Add aging threshold to the configuration
    config["queues"] = kargs["queues"] # Add number of priority queues to the configuration
    
    # Check if there is a response provided for time quantum
    response = init(config, kargs["seed"])
    if response:
        time_quantum = response['time_slice']
    
    # Check if the user has provided the --queues argument
    if "queues" in kargs:
        try:
            kargs["queues"] = int(kargs["queues"])
            if not (1 <= kargs["queues"] <= 5):
                raise ValueError
            # Override the priority levels in the configuration
            config["priority_levels"] = [kargs["queues"]]
        except ValueError:
            print("Error: --queues must be an integer between 1 and 5.")
            sys.exit()
        else:
            print(f"Using default priority levels from API: {config['priority_levels']}")
            
    
    # Check if the user has provided the --quantums argument
    if "quantums" in kargs:
        try:
            # Split the quantums by commas and convert to integers
            kargs["quantums"] = list(map(int, kargs["quantums"].split(",")))
            if len(kargs["quantums"]) != config["priority_levels"][0]:
                raise ValueError(f"--quantums must have exactly {config['priority_levels'][0]} values to match the number of priority queues.")
            if any(q <= 0 for q in kargs["quantums"]):
                raise ValueError("All values in --quantums must be positive integers.")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit()
        # Override the time quantums in the configuration
        config["time_quantums"] = kargs["quantums"]
    else:
        # Default time quantums: 5 ticks per queue
        config["time_quantums"] = [5] * config["priority_levels"][0]

    # Run selected scheduling algorithm
    if kargs["sched"] == "FCFS":
        print(f"Running FCFS with {kargs['cpus']} CPUs and {kargs['ios']} IO devices...")
        run_fcfs_simulation(config, client_id, num_cores=config["cpus"])
    if kargs["sched"] == "MLFQ":
        print(f"Running MLFQ with {kargs['cpus']} CPUs, {kargs['ios']} IO devices, {config['priority_levels'][0]} priority queues, aging threshold {kargs['aging']}, and time quantums {config['time_quantums']}...")
        run_mlfq_simulation(config, client_id, num_cores=config["cpus"])
    elif kargs["sched"] == "PB":
        print(f"Running PB with {kargs['cpus']} CPUs and {kargs['ios']} IO devices...")
        run_pb_simulation(config, client_id, num_cores=config["cpus"])
    elif kargs["sched"] == "RR":
        print(f"Running RR with {kargs['cpus']} CPUs and {kargs['ios']} IO devices...")
        run_rr_simulation(config, client_id, num_cores=config["cpus"], time_quantum=time_quantum)
