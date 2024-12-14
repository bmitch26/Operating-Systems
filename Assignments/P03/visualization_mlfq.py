### Visualizes the queues

from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console

console = Console()

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

def render_queues(new_queue, priority_queues, running_queue, waiting_queue, io_queue, exit_queue):
    """Renders the job queues dynamically as a rich table."""
    table = Table(expand=True)

    # Define a list of colors to use for the priority queues
    colors = ["cyan", "green", "yellow", "magenta", "blue", "red", "white", "bright_cyan", "bright_green", "bright_yellow"]

    # Add columns for each queue
    table.add_column("[cyan]New Queue[/cyan]", justify="center")    
    for i in range(len(priority_queues)):
        color = colors[i % len(colors)]
        table.add_column(f"[{color}]Priority Queue {i + 1}[/{color}]", justify="center")
    # table.add_column("[green]Ready Queue[/green]", justify="center")
    table.add_column("[green]Running Queue[/green]", justify="center")
    table.add_column("[magenta]Waiting Queue[/magenta]", justify="center")
    table.add_column("[blue]IO Queue[/blue]", justify="center")
    table.add_column("[red]Exit Queue[/red]", justify="center")


    def format_job_display(job):
        """Formats the display of a job with its ID and remaining burst time."""
        job_id = job.get("job_id", "?")
        bursts = job.get("data", {}).get("bursts", [])
        remaining_burst = bursts[0]["duration"] if bursts else "-"
        wait_time = job.get("wait_time", 0)  # Safely retrieve 'wait_time' from the job dictionary
        
        return f"[red]J:{job_id}[/red] [green]B:{remaining_burst}[/green] [yellow]W:{wait_time}[/yellow]"

    # Calculate the maximum number of rows needed
    max_rows = max(
        len(new_queue),
        max(len(queue) for queue in priority_queues),  # Maximum rows in priority queues
        len(running_queue),
        len(waiting_queue),
        len(io_queue),
        len(exit_queue),
    )

    # Populate table rows
    for i in range(max_rows):
        row = [
            format_job_display(new_queue[i]) if i < len(new_queue) else "",
        ]

        # Add jobs from each priority queue
        for queue in priority_queues:
            row.append(format_job_display(queue[i]) if i < len(queue) else "")

        # Add jobs from the remaining queues
        row.extend([
            format_job_display(running_queue[i]) if i < len(running_queue) else "",
            format_job_display(waiting_queue[i]) if i < len(waiting_queue) else "",
            format_job_display(io_queue[i]) if i < len(io_queue) else "",
            str(exit_queue[i]['job_id']) if i < len(exit_queue) else "",  # No burst time needed for exit queue
        ])
        table.add_row(*row)

    # Wrap the table in a panel for better visualization
    panel = Panel(table, title="Job Queue Visualization", expand=True)
    return panel
