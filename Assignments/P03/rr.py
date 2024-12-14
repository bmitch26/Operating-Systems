### Contains the Round Robin algorithm logic

from collections import deque
from rich.console import Console
from cpu_jobs import init, getJob, getBurst, getJobsLeft
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from visualization import render_queues, render_metrics
import time
from getch import getch

console = Console()

def render_clock(clock):
    """Renders the clock dynamically using the rich live display."""
    text = Text(f"CPU Simulation - Clock: {clock}", style="bold green")
    return text

def run_rr_simulation(config, client_id, num_cores, time_quantum):    
    # Initialize the simulation
    response = init(config)
    if response is None:
        console.print("[red]Initialization failed. Exiting simulation.[/red]")
        return
    if 'session_id' not in response or 'start_clock' not in response:
        console.print("[red]Invalid response from init. Missing 'session_id' or 'start_clock'. Exiting simulation.[/red]")
        return

    session_id = response['session_id']
    start_clock = response['start_clock']
    clock = start_clock

    # Queues
    new_queue = deque()
    ready_queue = deque()  # Unlimited size
    running_queue = []  # Maximum size of 4 jobs
    waiting_queue = deque()
    io_queue = deque()
    exit_queue = []
    
    # Initialize metrics
    completed_jobs = 0
    total_wait_time = 0
    job_wait_times = {}
    turnaround_times = []
    cpu_active_time = 0
    cpu_time_per_job = {}
    
    done_jobs = []  # Tracks jobs that are fully completed for visualization

    job_quantum = {}

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
                render_queues(new_queue, ready_queue, running_queue, waiting_queue, io_queue, exit_queue)
            )
            layout["metrics"].update(
                render_metrics(clock, start_clock, throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness)
            )

            # Update the live view with the layout
            live.update(layout)  
        
            # Check if all queues are empty and all jobs are in the exit queue
            if not getJobsLeft(client_id, session_id) and \
                not new_queue and \
                not ready_queue and \
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
            
            # Move jobs from new to ready queue
            for job in list(new_queue):  # Use list to avoid modifying deque during iteration
                if clock - job['arrival_time'] >= 1:  # Ensure job has spent at least 1 tick in the new queue
                    new_queue.remove(job)
                    console.print(f"At t:{clock}, job {job['job_id']} entered the ready queue.")
                    job['ready_time'] = clock  # Add ready_time when job enters the ready queue
                    ready_queue.append(job)

            # Increment wait time for all jobs in the ready queue
            for job in ready_queue:
                job_id = job['job_id']
                if job_id in job_wait_times:
                    job_wait_times[job_id] += 1
                else:
                    job_wait_times[job_id] = 1  # Initialize if not already present  

            # # Increment burst times for jobs in the ready queue
            # for job in ready_queue:
            #     if 'bursts' in job['data'] and job['data']['bursts']:
            #         current_burst = job['data']['bursts'][0]
            #         if 'duration' in current_burst:
            #             current_burst['duration'] += 1  # Increment the burst duration
            #             console.print(f"At t:{clock}, job {job['job_id']} in ready queue incremented burst time to {current_burst['duration']}")

            # # Increment burst times for jobs in the waiting queue
            # for job in waiting_queue:
            #     if 'bursts' in job['data'] and job['data']['bursts']:
            #         current_burst = job['data']['bursts'][0]
            #         if 'duration' in current_burst:
            #             current_burst['duration'] += 1  # Increment the burst duration
            #             console.print(f"At t:{clock}, job {job['job_id']} in waiting queue incremented burst time to {current_burst['duration']}")
            
            # Increment wait time for all jobs in the waiting queue
            for job in waiting_queue:
                job_id = job['job_id']
                if job_id in job_wait_times:
                    job_wait_times[job_id] += 1
            
            # Assign CPUs to jobs from ready queue to running queue
            for job in list(ready_queue):  # Use list to avoid modifying deque during iteration
                if clock - job['ready_time'] >= 1:  # Ensure job has spent at least 1 tick in the ready queue
                    if len(running_queue) < config["cpus"]:  # Use dynamic CPU limit
                        ready_queue.remove(job)
                        console.print(f"At t:{clock}, job {job['job_id']} obtained a CPU.")
                        job['cpu_start_time'] = clock
                        job_quantum[job['job_id']] = time_quantum  # Initialize remaining quantum when job gets CPU
                        running_queue.append(job)

            # Process running jobs
            for job in list(running_queue):
                # Decrement the current burst duration
                current_burst = job['data']['bursts'][0]  # Access the current burst dictionary
                if 'duration' in current_burst:
                    current_burst['duration'] -= 1  # Decrement the duration
                    job_quantum[job['job_id']] -= 1 # Decrement remaining job quantum
                    console.print(f"At t:{clock}, job {job['job_id']} is using the CPU. Remaining burst time: {current_burst['duration']}, Remaining quantum: {job_quantum[job['job_id']]}")
                    cpu_active_time += 1
                    cpu_time_per_job[job['job_id']] += 1

                # Check if there is any remaining job quantum
                if job_quantum[job['job_id']] <= 0:
                        running_queue.remove(job)
                        ready_queue.append(job)
                        job_quantum[job['job_id']] = time_quantum
                        console.print(f"At t:{clock}, job {job['job_id']}'s quantum expired. Moved back to ready queue.")
                        continue

                # Check if the burst is complete
                if current_burst['duration'] <= 0:
                    job['data']['bursts'].pop(0)  # Remove completed burst
                    running_queue.remove(job)  # Remove job from running queue
                    if not job['data']['bursts']:
                        completion_time = clock
                        arrival_time = job['arrival_time']
                        turnaround_times.append(completion_time - arrival_time)
                    else:
                        ready_queue.append(job)

                    # Fetch next burst
                    next_burst_response = getBurst(client_id, session_id, job['job_id'])
                    if next_burst_response and next_burst_response['success']:
                        next_burst_data = next_burst_response['data']
                        if isinstance(next_burst_data, dict):
                            job['data']['bursts'] = [next_burst_data]
                        elif isinstance(next_burst_data, list):
                            for burst in next_burst_data:
                                if 'burst_type' not in burst or 'duration' not in burst:
                                    console.print(f"[red]Error: Invalid burst data for job {job['job_id']}.[/red]")
                                    exit_queue.append(job)
                                    break
                            else:
                                job['data']['bursts'] = next_burst_data
                        else:
                            console.print(f"[red]Error: Unexpected next burst data format for job {job['job_id']}.[/red]")
                            exit_queue.append(job)
                            continue

                        # Determine the next action based on burst type
                        if job['data']['bursts']:
                            next_burst = job['data']['bursts'][0]
                            if next_burst['burst_type'] == 'CPU':  # Next burst is CPU-bound
                                console.print(f"At t:{clock}, job {job['job_id']} moved back to the ready queue for CPU processing.")
                                ready_queue.append(job)
                            elif next_burst['burst_type'] == 'IO':  # Next burst is IO-bound
                                console.print(f"At t:{clock}, job {job['job_id']} moved to the waiting queue for IO.")
                                waiting_queue.append(job)
                            elif next_burst['burst_type'] == 'EXIT':  # Job is complete
                                console.print(f"At t:{clock}, job {job['job_id']} has completed all bursts and terminated.")
                                exit_queue.append(job)
                                done_jobs.append(job)
                                completed_jobs += 1
                            else:  # Unknown burst type
                                console.print(f"[red]Error: Unknown burst type '{next_burst['burst_type']}' for job {job['job_id']}.[/red]")
                                console.print(f"[red]Full burst data: {next_burst}[/red]")
                                exit_queue.append(job)
                        else:
                            console.print(f"[red]Error: No bursts left after API call for job {job['job_id']}.[/red]")
                            exit_queue.append(job)
                    else:
                        console.print(f"[red]Error: Could not fetch the next burst for job {job['job_id']}. Moving to exit queue.[/red]")
                        exit_queue.append(job)
                    

            # Move jobs from waiting queue to IO queue if IO devices are available
            while waiting_queue and len(io_queue) < config["ios"]:  # Use dynamic IO limit
                job = waiting_queue.popleft()
                console.print(f"At t:{clock}, job {job['job_id']} obtained an IO device.")
                io_queue.append(job)


            # Process IO jobs
            for job in list(io_queue):  # Iterate over jobs in the IO queue
                if 'bursts' in job['data'] and job['data']['bursts']:
                    current_burst = job['data']['bursts'][0]  # Access the current IO burst
                    if 'duration' in current_burst:
                        current_burst['duration'] -= 1  # Decrement the IO burst duration
                        console.print(f"At t:{clock}, job {job['job_id']} is processing IO. Remaining burst time: {current_burst['duration']}")
                    else:
                        console.print(f"[red]Error: Missing 'duration' in IO burst for job {job['job_id']}. Moving to exit queue.[/red]")
                        io_queue.remove(job)
                        exit_queue.append(job)
                        continue

                    # Check if the IO burst is complete
                    if current_burst['duration'] <= 0:
                        job['data']['bursts'].pop(0)  # Remove the completed IO burst
                        io_queue.remove(job)
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
                                    ready_queue.append(job)
                                elif next_burst['burst_type'] == 'IO':  # Move back to IO queue
                                    console.print(f"At t:{clock}, job {job['job_id']} moved back to the IO queue.")
                                    io_queue.append(job)
                                elif next_burst['burst_type'] == 'EXIT':  # Job is complete
                                    console.print(f"At t:{clock}, job {job['job_id']} has completed all bursts and terminated.")
                                    exit_queue.append(job)
                                    done_jobs.append(job)
                                    completed_jobs += 1
                                else:  # Unknown burst type
                                    console.print(f"[red]Error: Unknown burst type '{next_burst['burst_type']}' for job {job['job_id']}.[/red]")
                                    console.print(f"[red]Full burst data: {next_burst}[/red]")
                                    exit_queue.append(job)
                            else:
                                console.print(f"[red]Error: No bursts left after IO for job {job['job_id']}.[/red]")
                                exit_queue.append(job)
                        else:
                            console.print(f"[red]Error: Could not fetch the next burst for job {job['job_id']}. Moving to exit queue.[/red]")
                            exit_queue.append(job)
                else:
                    console.print(f"[red]Error: Job {job['job_id']} has no bursts to process in IO queue. Moving to exit queue.[/red]")
                    io_queue.remove(job)
                    exit_queue.append(job)

            # Wait for a keypress to continue
            print("Press any key to continue...")
            getch()

            # Increment clock
            clock += 1
            live.update(render_clock(clock))
