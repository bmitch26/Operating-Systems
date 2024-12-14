# CPU Scheduler Simulation
## Overview
The purpose of this project is to simulate the way a CPU processes jobs under a variety of test conditions and algorithms. By varying the algorithms and test conditions, we can see how it effects the simulation metrics and make observations about the algorithms.

## Group Members:
- Brett Mitchell and Sly Rahimi

## Algorithms implemented:
- First Come First Serve (fcfs.py)
- Priority Based (pb.py)
- Round Robin (rr.py)
- Multi-Level Feedback Queue (mlfq.py)

## Files
|   #   | File            | Description                                        |
| :---: | --------------- | -------------------------------------------------- |
|   1   | cpu_jobs.py  | Contains job configuration and CPU parameters logic.         |
|   2   | fcfs.py  | Contains FCFS simulation logic.         |
|   3   | mlfq.py | Contains MLFQ simulation logic. |
|   4   | pb.py | Contains PB simulation logic. |
|   5   | rr.py | Contains RR simulation logic. |
|   6   | sim.py         | Main driver of project that acts as entry point for simulations.      |
|   7   | visualization.py | Contains visualization for RR and PB. |
|   8   | visualization_fcfs.py | Contains visualization for FCFS. |
|   9   | visualization_mlfq.py | Contains visualization for MLFQ. |

## Instructions:
- Receive jobs, burst types, and burst durations from 'cpu_jobs.py'.
- Choose First Come First Serve (FCFS), Round Robin (RR), Priority-Based (PB), or Multi-Level Feedback Queue (MLFQ) algorithm to run
- Run the simulation using 'sim.py' in the terminal, the entry point for simulations.

# Sample command run
python sim.py --sched=MLFQ --cpus=2 --ios=2 --queues=3 --quantums=5,10,15 --aging=10
