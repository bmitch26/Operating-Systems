### 11/26/2024 Update
### Need to:
## - pass in number of priority queues as a karg
## - pass in time quantums for priority queues as a karg
## - aging as a karg
##- when remaining burst time is 0, process is finished. Not at -1.


### Contains the MLFQ algorithm logic

from collections import deque
from rich.console import Console
from cpu_jobs import init, getJob, getBurst, getJobsLeft
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from visualization_mlfq import render_queues, render_metrics
import time
from getch import getch


console = Console()

aging_threshold=20

def render_clock(clock):
    """Renders the clock dynamically using the rich live display."""
    text = Text(f"CPU Simulation - Clock: {clock}", style="bold green")
    return text

def run_mlfq_simulation(config, client_id, num_cores):    
    # Initialize the simulation
    response = init(config)
    if response is None:
        console.print("[red]Initialization failed. Exiting simulation.[/red]")
        return
    if 'session_id' not in response or 'start_clock' not in response:
        console.print("[red]Invalid response from init. Missing 'session_id' or 'start_clock'. Exiting simulation.[/red]")
        return

    time_quantums = [5, 10, 15]  # Example time quantum for each priority level
    job_execution_time = {}  # Track execution time for jobs
    session_id = response['session_id']
    start_clock = response['start_clock']
    clock = start_clock

    # Queues
    new_queue = deque()
    priority_queues = [deque() for _ in range(config["priority_levels"][0])]
    running_queue = []  # Maximum size of 4 jobs
    waiting_queue = deque()
    io_queue = deque()
    exit_queue = []
    
    exit_job_ids = set()  # Track job IDs in the exit queue to prevent duplicates
    
    # Initialize metrics
    completed_jobs = 0
    total_wait_time = 0
    job_wait_times = {}
    turnaround_times = []
    cpu_active_time = 0
    cpu_time_per_job = {}
    
    done_jobs = []  # Tracks jobs that are fully completed for visualization

    with Live(console=console, refresh_per_second=1) as live:
        layout = Layout()
        # Adjust the layout proportions
        layout.split(
            Layout(name="clock", size=3),  # Clock at the top with a fixed height
            Layout(name="body", ratio=1)  # Main body containing queues and metrics
        )
        
        layout["body"].split_row(
            Layout(name="queues", ratio=3),  # Queue visualization takes 3 parts
            Layout(name="metrics", ratio=2)  # Metrics visualization takes 2 parts
        )

        while True:
            # Calculate Metrics
            elapsed_time = clock - start_clock
            if clock > 0:
                throughput = len(done_jobs) / elapsed_time if elapsed_time > 0 else 0
                avg_wait_time = sum(job_wait_times.values()) / len(job_wait_times) if job_wait_times else 0
                avg_turnaround_time = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
                cpu_utilization = ((cpu_active_time / num_cores) / elapsed_time) * 100 if elapsed_time > 0 else 0
                fairness = sum(cpu_time_per_job.values()) / len(cpu_time_per_job) if cpu_time_per_job else 0
            else:
                throughput = avg_wait_time = avg_turnaround_time = cpu_utilization = fairness = 0

            
            # Update the clock and queues in the layout
            layout["clock"].update(render_clock(clock))
            layout["queues"].update(
                render_queues(new_queue, priority_queues, running_queue, waiting_queue, io_queue, exit_queue)
            )
            layout["metrics"].update(
                render_metrics(clock, start_clock, throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness)
            )

            # Update the live view with the layout
            live.update(layout)  
        
            # Check if all queues are empty and all jobs are in the exit queue
            if not getJobsLeft(client_id, session_id) and \
                not new_queue and \
                all(len(queue) == 0 for queue in priority_queues) and \
                not running_queue and \
                not waiting_queue and \
                not io_queue:
                    console.print("[bold green]Simulation Complete[/bold green]")
                    break

            # Fetch new jobs arriving at the current clock time
            new_jobs = getJob(client_id, session_id, clock)
            if new_jobs and new_jobs['success']:
                for job_data in new_jobs['data']:
                    job_id = job_data['job_id']
                    console.print(f"At t:{clock}, job {job_id} entered the new queue.")

                    # Fetch and initialize burst data
                    burst_data = getBurst(client_id, session_id, job_id)
                    if burst_data and burst_data['success']:
                        if isinstance(burst_data['data'], dict):  # Single burst as a dictionary
                            if 'burst_type' not in burst_data['data'] or 'duration' not in burst_data['data']:
                                console.print(f"[red]Error: Missing 'burst_type' or 'duration' for job {job_id}.[/red]")
                                console.print(f"[red]Full burst data: {burst_data['data']}[/red]")
                                continue  # Skip this job
                            job_data['bursts'] = [burst_data['data']]
                            console.print(f"Job {job_id} bursts initialized: {job_data['bursts']}")
                        elif isinstance(burst_data['data'], list):  # Multiple bursts as a list
                            for burst in burst_data['data']:
                                if 'burst_type' not in burst or 'duration' not in burst:
                                    console.print(f"[red]Error: Invalid burst data for job {job_id}: {burst}[/red]")
                                    continue  # Skip this burst
                            job_data['bursts'] = burst_data['data']
                            console.print(f"Job {job_id} bursts initialized: {job_data['bursts']}")
                        else:
                            console.print(f"[red]Error: Unexpected burst data format for job {job_id}: {burst_data['data']}[/red]")
                            continue  # Skip job if burst data is in an unexpected format
                    else:
                        console.print(f"[red]Error: Could not fetch bursts for job {job_id}. Skipping job.[/red]")
                        continue  # Skip jobs with no valid burst data

                    # Add job to the new queue
                    new_queue.append({'job_id': job_id, 'data': job_data, 'arrival_time': clock})
                    job_wait_times[job_id] = 0
                    cpu_time_per_job[job_id] = 0                
            

            # Move jobs from new to priority queue
            for job in list(new_queue):  # Use list to avoid modifying deque during iteration
                if clock - job['arrival_time'] >= 1:  # Ensure job has spent at least 1 tick in the new queue
                    new_queue.remove(job)
                    console.print(f"At t:{clock}, job {job['job_id']} entered the priority queue 0.")
                    job['ready_time'] = clock  # Add ready_time when job enters the priority queue
                    job['queue_entry_time'] = clock  # Track when the job enters the priority queue
                    priority_queues[0].append(job)  # Insert into the highest-priority queue


            # Increment wait time for all jobs in the priority queues and check for aging
            for priority_level, queue in enumerate(priority_queues):
                for job in list(queue):  # Use list to avoid modifying deque during iteration
                    job_id = job['job_id']
                    
                    # Increment job's wait time for aging
                    if 'wait_time' not in job:
                        job['wait_time'] = 1
                    else:
                        job['wait_time'] += 1
                        
                    # Increment overall wait time
                    if job_id in job_wait_times:
                        job_wait_times[job_id] += 1
                    else:
                        job_wait_times[job_id] = 1
                        
                    # Check if the job has exceeded the aging threshold
                    if job['wait_time'] >= aging_threshold and priority_level > 0:
                        queue.remove(job)
                        new_priority_level = priority_level - 1
                        job['priority'] = new_priority_level
                        job['wait_time'] = 0  # Reset wait time after promotion
                        job['queue_entry_time'] = clock  # Track when the job enters the new priority queue
                        priority_queues[new_priority_level].append(job)
                        console.print(f"At t:{clock}, job {job['job_id']} was promoted to priority queue {new_priority_level} due to aging.")


            # Assign CPUs to jobs from priority queues to running queue
            for priority_level, queue in enumerate(priority_queues):
                for job in list(queue):  # Use list to avoid modifying deque during iteration
                    # Ensure the job has stayed in the queue for at least one tick
                    if clock - job.get('queue_entry_time', clock) >= 1:
                        if len(running_queue) < config["cpus"]:  # Check CPU availability
                            queue.remove(job)
                            job['wait_time'] = 0  # Reset wait time when job enters the running queue
                            console.print(f"At t:{clock}, job {job['job_id']} from priority queue {priority_level} obtained a CPU.")
                            job['cpu_start_time'] = clock
                            running_queue.append(job)
                        else:
                            break  # Stop assigning jobs if CPUs are full


            # Process running jobs
            for job in list(running_queue):
                current_burst = job['data']['bursts'][0]  # Access the current burst dictionary
                job_id = job['job_id']
                
                if job_id not in job_execution_time:
                    job_execution_time[job_id] = 0  # Initialize execution time tracker
                
                if 'duration' in current_burst:
                    # Execute the job and increment CPU active time
                    current_burst['duration'] -= 1
                    job_execution_time[job_id] += 1
                    console.print(f"At t:{clock}, job {job_id} is using the CPU. Remaining burst time: {current_burst['duration']}")
                    cpu_active_time += 1
                    cpu_time_per_job[job_id] += 1

                    # Check if the job's quantum is exceeded
                    priority_level = job.get('priority', 0)  # Get current priority level
                    if job_execution_time[job_id] >= time_quantums[priority_level]:
                        # Preempt the job and demote if possible
                        running_queue.remove(job)
                        next_priority = min(len(priority_queues) - 1, job.get('priority', 0) + 1)  # Demote to lower priority
                        job['priority'] = next_priority
                        job['wait_time'] = 1  # Reset wait time to 1 when re-entering priority queues
                        job['queue_entry_time'] = clock  # Track when the job enters the new priority queue
                        priority_queues[next_priority].append(job)
                        job_execution_time[job_id] = 0  # Reset execution time tracker
                        console.print(f"At t:{clock}, job {job_id} was preempted and demoted to priority queue {next_priority}.")
                        continue

                # Check if the burst is complete
                if current_burst['duration'] <= 0:
                    job['data']['bursts'].pop(0)  # Remove completed burst
                    running_queue.remove(job)
                    job_execution_time.pop(job_id, None)  # Clear execution time for completed jobs
                    if not job['data']['bursts']:
                        completion_time = clock
                        arrival_time = job['arrival_time']
                        turnaround_times.append(completion_time - arrival_time)
                    else:
                        priority_queues[0].append(job)

                    # Fetch next burst
                    next_burst_response = getBurst(client_id, session_id, job['job_id'])
                    if next_burst_response and next_burst_response['success']:
                        next_burst_data = next_burst_response['data']
                        if isinstance(next_burst_data, dict):
                            job['data']['bursts'] = [next_burst_data]
                            console.print(f"Job {job_id} bursts initialized: {job_data['bursts']}")
                        elif isinstance(next_burst_data, list):
                            for burst in next_burst_data:
                                if 'burst_type' not in burst or 'duration' not in burst:
                                    console.print(f"[red]Error: Invalid burst data for job {job['job_id']}.[/red]")
                                    exit_queue.append(job)
                                    break
                                else:
                                    job['data']['bursts'] = next_burst_data

                        # Determine the next action based on burst type
                        if job['data']['bursts']:
                            next_burst = job['data']['bursts'][0]
                            if next_burst['burst_type'] == 'CPU':  # Next burst is CPU-bound
                                console.print(f"At t:{clock}, job {job['job_id']} moved back to the ready queue for CPU processing.")
                                next_priority = 0  # Return to highest priority
                                job['priority'] = next_priority
                                job['wait_time'] = 1  # Reset wait time
                                job['queue_entry_time'] = clock
                                if job not in priority_queues[next_priority]:
                                    priority_queues[next_priority].append(job)
                            elif next_burst['burst_type'] == 'IO':  # Next burst is IO-bound
                                console.print(f"At t:{clock}, job {job['job_id']} moved to the waiting queue for IO.")
                                waiting_queue.append(job)                                
                            elif next_burst['burst_type'] == 'EXIT':  # Job is complete
                                if job['job_id'] not in exit_job_ids:
                                    exit_queue.append(job)
                                    exit_job_ids.add(job['job_id'])
                                    done_jobs.append(job)
                                    completed_jobs += 1
                                    console.print(f"At t:{clock}, job {job['job_id']} has completed all bursts and terminated.")
                    

            # Process jobs in the waiting queue and increment wait time for all jobs in the waiting queue
            for job in list(waiting_queue):  # Iterate over a copy of the waiting queue to avoid modification issues
                # Track when the job entered the waiting queue
                if 'waiting_time' not in job:
                    job['waiting_time'] = clock  # Record current clock time

                # Ensure the job stays in the waiting queue for at least one tick
                if clock - job['waiting_time'] >= 1:
                    waiting_queue.remove(job)  # Remove job from waiting queue
                    io_queue.append(job)  # Add job to IO queue
                    console.print(f"At t:{clock}, job {job['job_id']} obtained an IO device.")


            # Process IO jobs
            for job in list(io_queue):  # Iterate over jobs in the IO queue
                if 'bursts' in job['data'] and job['data']['bursts']:
                    current_burst = job['data']['bursts'][0]  # Access the current IO burst
                    if 'duration' in current_burst:
                        current_burst['duration'] -= 1  # Decrement the IO burst duration
                        console.print(f"At t:{clock}, job {job['job_id']} is processing IO. Remaining burst time: {current_burst['duration']}")

                    # Check if the IO burst is complete
                    if current_burst['duration'] <= 0:
                        job['data']['bursts'].pop(0)  # Remove the completed IO burst
                        io_queue.remove(job)
                        job['wait_time'] = 1
                        console.print(f"At t:{clock}, job {job['job_id']} completed its IO burst.")

                        # Fetch the next burst for the job
                        next_burst_response = getBurst(client_id, session_id, job['job_id'])
                        if next_burst_response and next_burst_response['success']:
                            next_burst_data = next_burst_response['data']
                            if isinstance(next_burst_data, dict):
                                if 'burst_type' not in next_burst_data or 'duration' not in next_burst_data:
                                    console.print(f"[red]Error: Missing 'burst_type' or 'duration' for job {job['job_id']}.[/red]")
                                    console.print(f"[red]Full burst data: {next_burst_data}[/red]")
                                    # exit_queue.append(job)
                                    continue
                                job['data']['bursts'].append(next_burst_data)
                            elif isinstance(next_burst_data, list):
                                for burst in next_burst_data:
                                    if 'burst_type' not in burst or 'duration' not in burst:
                                        console.print(f"[red]Error: Invalid burst data for job {job['job_id']}.[/red]")
                                        # exit_queue.append(job)
                                        break
                                else:
                                    job['data']['bursts'].extend(next_burst_data)
                            else:
                                console.print(f"[red]Error: Unexpected next burst data format for job {job['job_id']}.[/red]")
                                # exit_queue.append(job)
                                continue

                            # Determine the next action for the job
                            if job['data']['bursts']:
                                next_burst = job['data']['bursts'][0]
                                if next_burst['burst_type'] == 'CPU':  # Move to ready queue for CPU
                                    console.print(f"At t:{clock}, job {job['job_id']} moved back to the ready queue for CPU processing.")
                                    priority_queues[0].append(job)
                                elif next_burst['burst_type'] == 'IO':  # Move back to waiting queue
                                    if job not in waiting_queue:
                                        waiting_queue.append(job)
                                    console.print(f"At t:{clock}, job {job['job_id']} moved back to the waiting queue.")
                                elif next_burst['burst_type'] == 'EXIT':  # Job is complete
                                    if job['job_id'] not in exit_job_ids:  # Check using the set
                                        console.print(f"At t:{clock}, job {job['job_id']} has completed all bursts and terminated.")
                                        exit_queue.append(job)
                                        exit_job_ids.add(job['job_id'])  # Add job ID to the set
                                        done_jobs.append(job)
                                        completed_jobs += 1
                                    else:
                                        console.print(f"[yellow]Warning: Job {job['job_id']} is already in the exit queue. Skipping duplicate addition.[/yellow]")
    
            
            # Wait for a keypress to continue
            print("Press any key to continue...")
            getch()

            # Increment clock
            clock += 1
            live.update(render_clock(clock))
