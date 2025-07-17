#!/usr/bin/env python3

import os
import sys
from collections import defaultdict

# --- Configuration ---
# File extensions to count lines for (include the dot)
TARGET_EXTENSIONS = {".go", ".py", ".sql", ".md", ".js", ".html"}

# Directory *names* to completely exclude from traversal and counting,
# regardless of where they appear in the directory tree.
EXCLUDE_DIRS = {"__pycache__", "venv", ".venv", ".git", ".history", ".pytest_cache", "node_modules"}

# Starting directory ('.' means current directory)
START_DIR = "."
# --- End Configuration ---

def count_lines_in_file(filepath):
    """Counts lines in a file, mimicking 'wc -l'. Handles potential encoding errors."""
    try:
        with open(filepath, 'rb') as f:  # Read in binary mode to count '\n' bytes
            line_count = f.read().count(b'\n')
        return line_count
    except OSError as e:
        print(f"Warning: Could not read file {filepath}: {e}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Warning: Error processing file {filepath}: {e}", file=sys.stderr)
        return 0

def main():
    """Traverses directories and counts lines for specified file types."""
    line_counts = defaultdict(int)
    total_files_processed = 0
    folder_counts = defaultdict(lambda: defaultdict(int))

    # Get absolute start path mainly for display purposes
    start_path_abs_display = os.path.abspath(START_DIR)

    print(f"Starting line count in '{start_path_abs_display}'...")
    print(f"Target extensions: {', '.join(sorted(TARGET_EXTENSIONS))}")
    print(f"Excluding directories named: {', '.join(sorted(EXCLUDE_DIRS))}") # Clarified message
    print("-" * 20)

    # We walk the START_DIR (potentially relative path like '.')
    for dirpath, dirnames, filenames in os.walk(START_DIR, topdown=True):

        # --- Pruning Logic (Corrected) ---
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        # --- End Pruning Logic ---

        # --- File Processing ---
        for filename in filenames:
            _ , extension = os.path.splitext(filename)

            if extension in TARGET_EXTENSIONS:
                relative_dirpath = os.path.relpath(dirpath, START_DIR)
                # Get the top-level folder name
                folder_parts = relative_dirpath.split(os.sep)
                top_folder = folder_parts[0] if folder_parts[0] != '.' else 'root'

                filepath = os.path.join(dirpath, filename)
                lines = count_lines_in_file(filepath)
                line_counts[extension] += lines
                folder_counts[top_folder][extension] += lines
                total_files_processed += 1
        # --- End File Processing ---

    # --- Print Results ---

    # Print folder-by-folder breakdown
    print("-" * 20)
    print("Line counts by folder:")
    if not folder_counts:
        print("  (None)")
    else:
        # Sort folders for consistent output
        for folder in sorted(folder_counts.keys()):
            # Build the formatted string for this folder
            ext_strings = []
            for ext in sorted(folder_counts[folder].keys()):
                ext_name = ext[1:]  # Remove the dot
                count = folder_counts[folder][ext]
                ext_strings.append(f"{ext_name}: {count:,}")
            
            folder_total = sum(folder_counts[folder].values())
            print(f"  {folder} ({', '.join(ext_strings)})")

    print("-" * 20)
    print("Overall line counts by extension:")
    if not line_counts:
        print("  No files found matching the target extensions.")
        grand_total_lines = 0 # Explicitly set total to 0 if no files
    else:
        # Calculate grand total by summing values in the dictionary
        grand_total_lines = sum(line_counts.values())

        # Sort extensions for consistent output order
        for ext in sorted(line_counts.keys()):
            # Use :, format specifier for comma separators
            print(f"  Total lines of {ext}: {line_counts[ext]:,}")

        print("-" * 10) # Add a small separator before the total
        # Print the grand total, also formatted with commas
        print(f"  GRAND TOTAL: {grand_total_lines:,}")

    # Use :, format specifier for comma separators
    print(f"\nProcessed {total_files_processed:,} files.")


if __name__ == "__main__":
    main()