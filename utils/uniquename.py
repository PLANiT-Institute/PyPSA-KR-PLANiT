import sys
import csv
from pathlib import Path
from collections import defaultdict


def find_duplicate_names_in_csv(file_path):
    """
    Find duplicate values in the 'name' column of a CSV file.

    Args:
        file_path: Path to the CSV file

    Returns:
        Dictionary mapping name to list of row indices where it appears
    """
    name_to_indices = defaultdict(list)

    try:
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)

            if 'name' not in reader.fieldnames:
                return {}

            for idx, row in enumerate(reader):
                name = row.get('name', '').strip()
                if name:  # Skip empty names
                    name_to_indices[name].append(idx)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {}

    # Filter to only duplicates
    duplicates = {name: indices for name, indices in name_to_indices.items() if len(indices) > 1}

    return duplicates


def make_csv_names_unique(file_path, dry_run=False, backup=True):
    """
    Make all values in the 'name' column unique by adding _1, _2, _n suffixes.

    Args:
        file_path: Path to the CSV file
        dry_run: If True, only show what would be changed without actually changing
        backup: If True, create a backup file with .bak extension

    Returns:
        Tuple of (modified_count, error_count)
    """
    duplicates = find_duplicate_names_in_csv(file_path)

    if not duplicates:
        return 0, 0

    try:
        # Read all rows
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if 'name' not in fieldnames:
            print(f"  No 'name' column found in {file_path}")
            return 0, 1

        # Track name occurrences to add suffixes
        name_counters = defaultdict(int)
        modified_count = 0

        # Process each row
        for idx, row in enumerate(rows):
            original_name = row['name'].strip()

            if not original_name:
                continue

            # Check if this name has duplicates
            if original_name in duplicates:
                occurrence = name_counters[original_name]
                name_counters[original_name] += 1

                # Add suffix to ALL occurrences (starting from _1)
                new_name = f"{original_name}_{occurrence + 1}"
                row['name'] = new_name
                modified_count += 1

                if dry_run:
                    print(f"    Row {idx + 2}: '{original_name}' -> '{new_name}'")

        if dry_run:
            return modified_count, 0

        # Create backup if requested
        if backup and modified_count > 0:
            backup_path = f"{file_path}.bak"
            with open(file_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())

        # Write updated CSV
        if modified_count > 0:
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        return modified_count, 0

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return 0, 1


def process_directory(directory_path, file_extensions=None, dry_run=False, backup=True):
    """
    Process all CSV files in a directory to make 'name' column values unique.

    Args:
        directory_path: Path to the directory
        file_extensions: List of file extensions to process (default: ['.csv'])
        dry_run: If True, only show what would be changed
        backup: If True, create backup files

    Returns:
        Tuple of (files_modified, total_modifications, errors)
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Error: Directory {directory_path} does not exist")
        return 0, 0, 1

    if not directory.is_dir():
        print(f"Error: {directory_path} is not a directory")
        return 0, 0, 1

    if file_extensions is None:
        file_extensions = ['.csv']

    # Find all CSV files
    csv_files = []
    for ext in file_extensions:
        csv_files.extend(directory.rglob(f'*{ext}'))

    # Filter out backup files
    csv_files = [f for f in csv_files if not f.name.endswith('.bak')]

    if not csv_files:
        print(f"No CSV files found in {directory_path}")
        return 0, 0, 0

    print(f"\nProcessing {len(csv_files)} CSV file(s)...")
    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")
    print(f"{'='*60}\n")

    files_modified = 0
    total_modifications = 0
    total_errors = 0

    for csv_file in sorted(csv_files):
        # Check for duplicates first
        duplicates = find_duplicate_names_in_csv(csv_file)

        if not duplicates:
            continue

        print(f"File: {csv_file.relative_to(directory)}")
        print(f"  Found {len(duplicates)} duplicate name(s):")

        for name, indices in sorted(duplicates.items()):
            print(f"    '{name}': {len(indices)} occurrence(s)")

        modified_count, error_count = make_csv_names_unique(csv_file, dry_run=dry_run, backup=backup)

        if modified_count > 0:
            files_modified += 1
            total_modifications += modified_count
            if not dry_run:
                print(f"  ✓ Modified {modified_count} name(s)")

        if error_count > 0:
            total_errors += error_count

        print()

    print(f"{'='*60}")
    if dry_run:
        print(f"DRY RUN Summary:")
        print(f"  Would modify {files_modified} file(s)")
        print(f"  Would change {total_modifications} name(s)")
    else:
        print(f"Summary:")
        print(f"  ✓ Modified: {files_modified} file(s)")
        print(f"  ✓ Changed: {total_modifications} name(s)")
        if total_errors > 0:
            print(f"  ✗ Errors: {total_errors}")
    print(f"{'='*60}")

    return files_modified, total_modifications, total_errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python uniquename.py <directory> [options]")
        print("\nMakes all values in the 'name' column of CSV files unique")
        print("by adding _1, _2, _n suffixes to duplicate names.")
        print("\nOptions:")
        print("  --dry-run       Show what would be changed without modifying files")
        print("  --no-backup     Don't create .bak backup files")
        print("\nExamples:")
        print("  python uniquename.py data/2024/")
        print("  python uniquename.py data/2024/ --dry-run")
        print("  python uniquename.py data/2024/ --no-backup")
        sys.exit(1)

    directory_path = sys.argv[1]

    # Parse options
    dry_run = "--dry-run" in sys.argv
    backup = "--no-backup" not in sys.argv

    process_directory(directory_path, dry_run=dry_run, backup=backup)
