### Visualizes the queues

from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

def render_metrics(clock, start_clock, throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness):
    """Renders the key metrics dynamically as a rich table."""
    table = Table(title="Simulation Metrics", expand=True)

    # Add columns for metric names and their current values
    table.add_column("Metric", justify="left")
    table.add_column("Value", justify="center")

    # Add rows for each metric
    table.add_row("Start Clock", f"{start_clock} ticks")  # Display Start Clock first
    table.add_row("Clock", f"{clock} ticks")
    table.add_row("Throughput", f"{throughput:.2f} jobs/tick")
    table.add_row("Average Wait Time", f"{avg_wait_time:.2f} ticks")
    table.add_row("Average Turnaround Time", f"{avg_turnaround_time:.2f} ticks")
    table.add_row("CPU Utilization (%)", f"{cpu_utilization:.2f}%")
    table.add_row("Fairness", f"{fairness:.2f} ticks/job")

    # Wrap the table in a panel for better visualization
    panel = Panel(table, title="Key Metrics", expand=True)
    return panel

def render_queues(new_queue, ready_queue, running_queue, waiting_queue, io_queue, exit_queue):
    """Renders the job queues dynamically as a rich table."""
    table = Table(title="Job Queues", expand=True)

    # Add columns for queues
    table.add_column("New Queue", justify="center")
    table.add_column("Ready Queue", justify="center")
    table.add_column("Running Queue", justify="center")
    table.add_column("Waiting Queue", justify="center")
    table.add_column("IO Queue", justify="center")
    table.add_column("Exit Queue", justify="center")

    def format_job_display(job):
        """Formats the display of a job with its ID and remaining burst time."""
        job_id = job.get("job_id", "?")
        bursts = job.get("data", {}).get("bursts", [])
        remaining_burst = bursts[0]["duration"] if bursts else "-"
        return f"{job_id} - {remaining_burst}"

    # Calculate the maximum number of rows needed
    max_rows = max(
        len(new_queue),
        len(ready_queue),
        len(running_queue),
        len(waiting_queue),
        len(io_queue),
        len(exit_queue),
    )

    # Populate table rows
    for i in range(max_rows):
        row = [
            format_job_display(new_queue[i]) if i < len(new_queue) else "",
            format_job_display(ready_queue[i]) if i < len(ready_queue) else "",
            format_job_display(running_queue[i]) if i < len(running_queue) else "",
            format_job_display(waiting_queue[i]) if i < len(waiting_queue) else "",
            format_job_display(io_queue[i]) if i < len(io_queue) else "",
            str(exit_queue[i]['job_id']) if i < len(exit_queue) else "",  # No burst time needed for exit queue
        ]
        table.add_row(*row)

    # Wrap the table in a panel for better visualization
    panel = Panel(table, title="Queue Visualization", expand=True)
    return panel


def render_mlfq_queues(queues):
    """Renders the MLFQ queues dynamically."""
    table = Table(title="MLFQ Queues", expand=True)

    for i, queue in enumerate(queues):
        table.add_column(f"Queue {i + 1}", justify="center")

    max_rows = max(len(queue) for queue in queues)
    for i in range(max_rows):
        row = [str(queues[q][i]["job_id"]) if i < len(queues[q]) else "" for q in range(len(queues))]
        table.add_row(*row)

    return Panel(table, title="Multi-Level Feedback Queues", expand=True)
