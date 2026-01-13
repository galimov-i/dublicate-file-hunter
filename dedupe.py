#!/usr/bin/env python3
"""
Duplicate File Hunter
=====================

A command-line tool to find duplicate files in a directory tree based on content hash.
Uses a two-pass algorithm for performance optimization.
"""

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Generator

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table
from rich import box

# Initialize Rich Console
console = Console()

def get_file_hash(path: Path, chunk_size: int = 8192) -> str:
    """
    Calculate the MD5 hash of a file.
    
    Args:
        path: Path to the file.
        chunk_size: Size of chunks to read from file to avoid memory issues.
        
    Returns:
        The hexadecimal MD5 hash string.
    """
    hasher = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""

def scan_directory(root_path: Path) -> Dict[int, List[Path]]:
    """
    Pass 1: Scan directory and group files by size.
    
    Args:
        root_path: Directory to scan.
        
    Returns:
        Dictionary mapping file size to list of file paths.
    """
    files_by_size: Dict[int, List[Path]] = defaultdict(list)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning file sizes...", total=None)
        
        try:
            for path in root_path.rglob("*"):
                if path.is_file():
                    try:
                        # Skip symbolic links to avoid loops and confusion
                        if path.is_symlink():
                            continue
                        
                        size = path.stat().st_size
                        # Ignore empty files, they are trivial duplicates
                        if size > 0:
                            files_by_size[size].append(path)
                            progress.update(task, description=f"Found {path.name}")
                    except (PermissionError, OSError):
                        continue
        except KeyboardInterrupt:
            console.print("[bold red]Scan interrupted by user.[/bold red]")
            sys.exit(1)
            
    return files_by_size

def find_duplicates(files_by_size: Dict[int, List[Path]]) -> Dict[str, List[Path]]:
    """
    Pass 2: Calculate hashes for files with same size to find actual duplicates.
    
    Args:
        files_by_size: Dictionary mapping file size to list of file paths.
        
    Returns:
        Dictionary mapping hash to list of duplicate file paths.
    """
    # Filter out unique sizes - no need to hash them
    candidates = {size: paths for size, paths in files_by_size.items() if len(paths) > 1}
    total_candidates = sum(len(paths) for paths in candidates.values())
    
    duplicates: Dict[str, List[Path]] = defaultdict(list)
    
    if not candidates:
        return duplicates

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
    ) as progress:
        task = progress.add_task("Hashing candidates...", total=total_candidates)
        
        for size, paths in candidates.items():
            # Hash files with the same size
            hashes_for_size: Dict[str, List[Path]] = defaultdict(list)
            
            for path in paths:
                file_hash = get_file_hash(path)
                if file_hash: # If hash calculation succeeded
                    hashes_for_size[file_hash].append(path)
                progress.advance(task)
            
            # Only keep groups where hash collision occurred (actual duplicates)
            for file_hash, file_paths in hashes_for_size.items():
                if len(file_paths) > 1:
                    duplicates[file_hash].extend(file_paths)
                    
    return duplicates

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def print_results(duplicates: Dict[str, List[Path]]):
    """
    Display the results in a Rich table.
    
    Args:
        duplicates: Dictionary mapping hash to list of duplicate file paths.
    """
    if not duplicates:
        console.print("\n[bold green]No duplicates found![/bold green]")
        return

    table = Table(title="Duplicate Files Found", box=box.ROUNDED)
    table.add_column("Filename", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Size", justify="right", style="magenta")

    total_wasted_size = 0
    total_duplicates_count = 0

    for file_hash, paths in duplicates.items():
        # Get size from first file (all have same size)
        try:
            size = paths[0].stat().st_size
            wasted_size = size * (len(paths) - 1)
            total_wasted_size += wasted_size
            total_duplicates_count += len(paths) - 1
            
            # Add a visual separator row for the group
            table.add_section()
            table.add_row(f"[bold red]Group ({file_hash[:8]}...)[/bold red]", "", "")
            
            for path in paths:
                table.add_row(path.name, str(path.parent), format_size(size))
                
        except (OSError, IndexError):
            continue

    console.print(table)
    
    console.print(f"\n[bold green]Found {len(duplicates)} groups of duplicates.[/bold green]")
    console.print(f"[bold green]Total duplicate files: {total_duplicates_count}[/bold green]")
    console.print(f"[bold green]Reclaimable space: {format_size(total_wasted_size)}[/bold green]")

def main():
    parser = argparse.ArgumentParser(description="Find duplicate files in a directory tree.")
    parser.add_argument("root_path", nargs="?", default=".", help="Root directory to scan (default: current directory)")
    args = parser.parse_args()
    
    root = Path(args.root_path).resolve()
    
    if not root.exists() or not root.is_dir():
        console.print(f"[bold red]Error: Directory '{root}' not found or is not a directory.[/bold red]")
        sys.exit(1)
        
    console.print(f"[bold]Starting scan in: {root}[/bold]")
    
    # Pass 1: Size Filter
    files_by_size = scan_directory(root)
    count_files = sum(len(paths) for paths in files_by_size.values())
    console.print(f"Scanned {count_files} files. Filtering by size...")
    
    # Pass 2: Hash Check
    duplicates = find_duplicates(files_by_size)
    
    # Report
    print_results(duplicates)

if __name__ == "__main__":
    main()
