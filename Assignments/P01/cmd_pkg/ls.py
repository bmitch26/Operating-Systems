# cmd_pkg/ls.py

from pathlib import Path
import stat
from datetime import datetime

def ls(*args):
    # Flags interpretation
    show_all = False  # For -a: Show hidden files
    long_format = False  # For -l: Show detailed info (permissions, owner, size, etc.)
    human_readable = False  # For -h: Show sizes in human-readable format

    # Split args to check for flags
    directory = '.'
    if args:
        for arg in args:
            if arg.startswith('-'):
                if 'a' in arg:
                    show_all = True
                if 'l' in arg:
                    long_format = True
                if 'h' in arg:
                    human_readable = True
            else:
                directory = arg  # Assume non-flag argument is a directory name

    # Using Path from pathlib to list the directory contents
    try:
        path = Path(directory)
        entries = list(path.iterdir())  # Get all file/directory entries

        if show_all:
            # Add the current (.) and parent (..) directories
            entries = [Path('.'), Path('..')] + entries
        else:
            # Filter out hidden files (those that start with a dot)
            entries = [entry for entry in entries if not entry.name.startswith('.')]
    except FileNotFoundError:
        return f"ls: cannot access '{directory}': No such file or directory"

    # If long format is required
    if long_format:
        detailed_entries = []
        for entry in entries:
            stat_info = entry.stat()  # Get file statistics
            permissions = stat.filemode(stat_info.st_mode)
            n_links = stat_info.st_nlink
            size = stat_info.st_size
            if human_readable:
                size = human_readable_size(size)  # Convert size to human-readable format
            last_modified = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')
            name = '.' if entry == Path('.') else '..' if entry == Path('..') else entry.name
            detailed_entries.append(f"{permissions} {n_links} {size:>10} {last_modified} {name}")
        return '\n'.join(detailed_entries)

    # If no long format, return just the list of files
    return '\n'.join('.' if entry == Path('.') else '..' if entry == Path('..') else entry.name for entry in entries)

# Helper function to convert bytes to a human-readable format
def human_readable_size(size):
    # Conversion to human-readable sizes (KB, MB, GB)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"
