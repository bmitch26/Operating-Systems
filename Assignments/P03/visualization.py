### Visualizes the queues

from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

def render_metrics(clock, start_clock, throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness):
    """Renders the key metrics dynamically as a rich table."""
    table = Table(expand=True)

    # Add columns for metric names and their current values
    table.add_column("[orange1]Metric[/orange1]", justify="left")
    table.add_column("[thistle3]Value[/thistle3]", justify="center")

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
    table = Table(expand=True)

    # Add columns for queues
    table.add_column("[cyan]New Queue[/cyan]", justify="center")
    table.add_column("[green]Ready Queue[/green]", justify="center")
    table.add_column("[yellow]Running Queue[/yellow]", justify="center")
    table.add_column("[magenta]Waiting Queue[/magenta]", justify="center")
    table.add_column("[blue]IO Queue[/blue]", justify="center")
    table.add_column("[red]Exit Queue[/red]", justify="center")

    def format_job_display(job):
        """Formats the display of a job with its ID and remaining burst time."""
        job_id = job.get("job_id", "?")
        bursts = job.get("data", {}).get("bursts", [])
        remaining_burst = bursts[0]["duration"] if bursts else "-"
        # return f"{job_id} - {remaining_burst}"
        wait_time = job.get("wait_time", 0)  # Safely retrieve 'wait_time' from the job dictionary
        
        return f"[red]J:{job_id}[/red] [green]B:{remaining_burst}[/green] [yellow]W:{wait_time}[/yellow]"

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
    panel = Panel(table, title="Job Queue Visualization", expand=True)
    return panel
