# rms.py

from collections import deque
from rich.console import Console
from cpu_jobs import init, getJob, getBurst, getJobsLeft
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from visualization_rms import render_queues, render_metrics
from getch import getch
import math

console = Console()

def render_clock(clock):
    text = Text(f"Rate Monotonic Scheduler - Clock: {clock}", style="bold green")
    return text

def run_rms_simulation(config, client_id, num_cores):
    response = init(config)
    if response is None or 'session_id' not in response or 'start_clock' not in response:
        console.print("[red]Initialization failed. Exiting.[/red]")
        return

    session_id = response['session_id']
    clock = response['start_clock']

    ready_queue = deque()
    running_jobs = []
    waiting_queue = deque()
    io_queue = deque()
    exit_queue = []
    job_periods = {}
    job_execution_time = {}

    cpu_active_time = 0
    job_wait_times = {}
    turnaround_times = []
    completed_jobs = 0
    cpu_time_per_job = {}
    done_jobs = []

    with Live(console=console, refresh_per_second=1) as live:
        layout = Layout()
        layout.split(Layout(name="clock", size=3), Layout(name="body", ratio=1))
        layout["body"].split_row(Layout(name="queues", ratio=3), Layout(name="metrics", ratio=2))

        while True:
            if not getJobsLeft(client_id, session_id) and not ready_queue and not waiting_queue and not running_jobs and not io_queue:
                console.print("[bold green]Simulation Complete[/bold green]")
                break

            # Fetch new jobs
            new_jobs = getJob(client_id, session_id, clock)
            if new_jobs and new_jobs['success']:
                for job_data in new_jobs['data']:
                    job_id = job_data['job_id']
                    burst_data = getBurst(client_id, session_id, job_id)
                    if burst_data and burst_data['success']:
                        job_data['bursts'] = burst_data['data'] if isinstance(burst_data['data'], list) else [burst_data['data']]
                        job_data['job_id'] = job_id
                        job_data['arrival_time'] = clock
                        job_data['period'] = job_data.get('period', job_data['job_id'] + 1)  # Fallback
                        job_periods[job_id] = job_data['period']
                        ready_queue.append(job_data)
                        job_wait_times[job_id] = 0
                        cpu_time_per_job[job_id] = 0
                        console.print(f"At t:{clock}, job {job_id} released with period {job_periods[job_id]}.")
            
            # Sort ready queue by period (RMS priority)
            ready_queue = deque(sorted(ready_queue, key=lambda j: job_periods[j['job_id']]))

            # Run up to `num_cores` jobs with highest priority
            while len(running_jobs) < num_cores and ready_queue:
                job = ready_queue.popleft()
                job['start_time'] = clock
                running_jobs.append(job)
                console.print(f"At t:{clock}, job {job['job_id']} started execution.")

            for job in list(running_jobs):
                burst = job['bursts'][0]
                burst['duration'] -= 1
                cpu_active_time += 1
                cpu_time_per_job[job['job_id']] += 1

                console.print(f"At t:{clock}, job {job['job_id']} is executing. Remaining burst: {burst['duration']}")

                if burst['duration'] <= 0:
                    job['bursts'].pop(0)
                    running_jobs.remove(job)
                    if not job['bursts']:
                        turnaround_times.append(clock - job['arrival_time'])
                        exit_queue.append(job)
                        done_jobs.append(job)
                        completed_jobs += 1
                        console.print(f"At t:{clock}, job {job['job_id']} completed.")
                    else:
                        next_burst_resp = getBurst(client_id, session_id, job['job_id'])
                        if next_burst_resp and next_burst_resp['success']:
                            job['bursts'] = [next_burst_resp['data']] if isinstance(next_burst_resp['data'], dict) else next_burst_resp['data']
                            if job['bursts'][0]['burst_type'] == 'IO':
                                waiting_queue.append(job)
                            else:
                                ready_queue.append(job)

            # Process waiting -> IO
            for job in list(waiting_queue):
                waiting_queue.remove(job)
                io_queue.append(job)
                console.print(f"At t:{clock}, job {job['job_id']} moved to IO.")

            # Process IO
            for job in list(io_queue):
                burst = job['bursts'][0]
                burst['duration'] -= 1
                if burst['duration'] <= 0:
                    io_queue.remove(job)
                    job['bursts'].pop(0)
                    next_burst_resp = getBurst(client_id, session_id, job['job_id'])
                    if next_burst_resp and next_burst_resp['success']:
                        job['bursts'] = [next_burst_resp['data']] if isinstance(next_burst_resp['data'], dict) else next_burst_resp['data']
                    ready_queue.append(job)

            # Metrics
            elapsed_time = clock - response['start_clock']
            throughput = len(done_jobs) / elapsed_time if elapsed_time > 0 else 0
            avg_wait_time = sum(job_wait_times.values()) / len(job_wait_times) if job_wait_times else 0
            avg_turnaround_time = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0
            cpu_utilization = ((cpu_active_time / num_cores) / elapsed_time) * 100 if elapsed_time > 0 else 0
            fairness = sum(cpu_time_per_job.values()) / len(cpu_time_per_job) if cpu_time_per_job else 0

            layout["clock"].update(render_clock(clock))
            layout["queues"].update(
                render_queues(ready_queue, running_jobs, waiting_queue, io_queue, exit_queue)
            )
            layout["metrics"].update(
                render_metrics(clock, response['start_clock'], throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness)
            )

            live.update(layout)
            print("Press any key to continue...")
            getch()
            clock += 1
