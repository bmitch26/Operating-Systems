# visualization_rms.py

from rich.table import Table
from rich.panel import Panel
from rich.console import Console

console = Console()

def render_metrics(clock, start_clock, throughput, avg_wait_time, avg_turnaround_time, cpu_utilization, fairness):
    table = Table(expand=True)
    table.add_column("[orange1]Metric[/orange1]", justify="left")
    table.add_column("[thistle3]Value[/thistle3]", justify="center")
    table.add_row("Start Clock", f"{start_clock} ticks")
    table.add_row("Clock", f"{clock} ticks")
    table.add_row("Throughput", f"{throughput:.2f} jobs/tick")
    table.add_row("Average Wait Time", f"{avg_wait_time:.2f} ticks")
    table.add_row("Average Turnaround Time", f"{avg_turnaround_time:.2f} ticks")
    table.add_row("CPU Utilization (%)", f"{cpu_utilization:.2f}%")
    table.add_row("Fairness", f"{fairness:.2f} ticks/job")
    return Panel(table, title="Key Metrics", expand=True)

def render_queues(ready_queue, running_queue, waiting_queue, io_queue, exit_queue):
    table = Table(expand=True)
    table.add_column("[cyan]Ready Queue[/cyan]", justify="center")
    table.add_column("[green]Running Queue[/green]", justify="center")
    table.add_column("[magenta]Waiting Queue[/magenta]", justify="center")
    table.add_column("[blue]IO Queue[/blue]", justify="center")
    table.add_column("[red]Exit Queue[/red]", justify="center")

    def fmt(job):
        job_id = job.get("job_id", "?")
        bursts = job.get("bursts", [])
        remaining = bursts[0]["duration"] if bursts else "-"
        return f"J:{job_id} B:{remaining}"

    max_rows = max(len(ready_queue), len(running_queue), len(waiting_queue), len(io_queue), len(exit_queue))
    for i in range(max_rows):
        row = [
            fmt(ready_queue[i]) if i < len(ready_queue) else "",
            fmt(running_queue[i]) if i < len(running_queue) else "",
            fmt(waiting_queue[i]) if i < len(waiting_queue) else "",
            fmt(io_queue[i]) if i < len(io_queue) else "",
            str(exit_queue[i]['job_id']) if i < len(exit_queue) else "",
        ]
        table.add_row(*row)

    return Panel(table, title="Job Queue Visualization", expand=True)
