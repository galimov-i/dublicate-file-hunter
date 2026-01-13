# 🕵️ Duplicate File Hunter

A high-performance command-line tool to find duplicate files in a directory tree based on content (MD5 hash). Built with Python and Rich for a beautiful terminal interface.

## Features

- **Performance Optimized**: Uses a "Two-Pass" algorithm to minimize I/O and CPU usage.
  - **Pass 1 (Size Filter)**: Quickly groups files by size. Unique sizes are discarded immediately.
  - **Pass 2 (Hash Check)**: Calculates MD5 hashes only for files that share the same size.
- **Memory Efficient**: Reads files in chunks to handle large files without filling RAM.
- **Beautiful UI**: Uses `rich` for progress bars, colorful output, and summary tables.
- **Cross-Platform**: Works on Windows, Linux, and macOS.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/galimov-i/dublicate-file-hunter.git
    cd dublicate-file-hunter
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script pointing to the directory you want to scan:

```bash
python3 dedupe.py /path/to/scan
```

If no path is provided, it scans the current directory:

```bash
python3 dedupe.py
```

## How It Works

1.  **Scanning**: Recursively walks through the provided directory.
2.  **Filtering**: Identifies files with identical sizes.
3.  **Hashing**: Computes MD5 hashes for the potential duplicates.
4.  **Reporting**: Displays a detailed table of duplicates and the total reclaimable space.

## Requirements

- Python 3.10+
- `rich` library

## License

MIT
