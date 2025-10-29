import sys
from pathlib import Path
import pandas as pd


def csv_to_excel(csv_path, output_path=None, sheet_name='Sheet1'):
    """
    Convert a single CSV file to Excel format.

    Args:
        csv_path: Path to the CSV file to convert
        output_path: Path for the output Excel file. If None, uses same name with .xlsx extension
        sheet_name: Name of the sheet in the Excel file

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        csv_path = Path(csv_path)

        if not csv_path.exists():
            print(f"✗ Error: File {csv_path} does not exist")
            return False

        if not csv_path.suffix.lower() == '.csv':
            print(f"✗ Error: {csv_path} is not a CSV file")
            return False

        # Determine output path
        if output_path is None:
            output_path = csv_path.with_suffix('.xlsx')
        else:
            output_path = Path(output_path)

        # Read CSV file
        print(f"Reading {csv_path.name}...")
        df = pd.read_csv(csv_path)

        # Write to Excel
        print(f"Writing to {output_path.name}...")
        df.to_excel(output_path, sheet_name=sheet_name, index=False, engine='openpyxl')

        print(f"✓ Converted {csv_path.name} to {output_path.name} ({len(df)} rows, {len(df.columns)} columns)")
        return True

    except Exception as e:
        print(f"✗ Error converting {csv_path}: {e}")
        return False


def convert_directory(directory_path, output_dir=None, recursive=False, separate_files=True):
    """
    Convert all CSV files in a directory to Excel format.

    Args:
        directory_path: Path to the directory containing CSV files
        output_dir: Output directory for Excel files. If None, saves in same directory
        recursive: Whether to search subdirectories recursively
        separate_files: If True, creates separate .xlsx files for each CSV.
                       If False, creates a single .xlsx with multiple sheets.

    Returns:
        Tuple of (converted_count, failed_count)
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"✗ Error: Directory {directory_path} does not exist")
        return 0, 0

    if not directory.is_dir():
        print(f"✗ Error: {directory_path} is not a directory")
        return 0, 0

    # Set output directory
    if output_dir is None:
        output_dir = directory
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Find all CSV files
    pattern = '**/*.csv' if recursive else '*.csv'
    csv_files = list(directory.glob(pattern))

    if not csv_files:
        print(f"✗ No CSV files found in {directory_path}")
        return 0, 0

    print(f"\nFound {len(csv_files)} CSV file(s) in {directory_path}")
    print(f"{'='*60}")

    converted_count = 0
    failed_count = 0

    if separate_files:
        # Convert each CSV to a separate Excel file
        for csv_file in csv_files:
            # Maintain relative path structure in output
            if recursive:
                relative_path = csv_file.relative_to(directory)
                output_path = output_dir / relative_path.with_suffix('.xlsx')
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                output_path = output_dir / csv_file.with_suffix('.xlsx').name

            if csv_to_excel(csv_file, output_path):
                converted_count += 1
            else:
                failed_count += 1
            print()

    else:
        # Convert all CSVs to a single Excel file with multiple sheets
        output_path = output_dir / f"{directory.name}_combined.xlsx"
        print(f"Creating combined Excel file: {output_path.name}...\n")

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for csv_file in csv_files:
                    try:
                        print(f"Adding {csv_file.name}...")
                        df = pd.read_csv(csv_file)

                        # Use filename without extension as sheet name
                        # Excel sheet names can't exceed 31 chars
                        sheet_name = csv_file.stem[:31]

                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        print(f"✓ Added sheet '{sheet_name}' ({len(df)} rows, {len(df.columns)} columns)")
                        converted_count += 1
                    except Exception as e:
                        print(f"✗ Error adding {csv_file.name}: {e}")
                        failed_count += 1
                    print()

            print(f"✓ Created combined Excel file: {output_path}")

        except Exception as e:
            print(f"✗ Error creating combined Excel file: {e}")
            return 0, len(csv_files)

    print(f"{'='*60}")
    print(f"Conversion complete:")
    print(f"  ✓ Converted: {converted_count} file(s)")
    print(f"  ✗ Failed: {failed_count} file(s)")
    print(f"{'='*60}")

    return converted_count, failed_count


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("CSV to Excel Converter")
        print("=" * 60)
        print("\nUsage: python csv_to_excel.py <path> [options]")
        print("\nArguments:")
        print("  path                  Path to CSV file or directory")
        print("\nOptions:")
        print("  --output-dir <dir>    Output directory (default: same as input)")
        print("  --recursive           Search subdirectories recursively")
        print("  --combined            Combine all CSVs into one Excel file with multiple sheets")
        print("\nExamples:")
        print("  python csv_to_excel.py data/2024/buses.csv")
        print("  python csv_to_excel.py data/2024/")
        print("  python csv_to_excel.py data/2024/ --recursive")
        print("  python csv_to_excel.py data/2024/ --combined")
        print("  python csv_to_excel.py data/2024/ --output-dir output/")
        sys.exit(0)

    # Parse arguments
    target_path = Path(sys.argv[1])
    output_dir = None
    recursive = False
    combined = False

    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--output-dir':
            if i + 1 < len(sys.argv):
                output_dir = sys.argv[i + 1]
                i += 2
            else:
                print("✗ Error: --output-dir requires a path argument")
                sys.exit(1)
        elif arg == '--recursive':
            recursive = True
            i += 1
        elif arg == '--combined':
            combined = True
            i += 1
        else:
            print(f"✗ Error: Unknown option '{arg}'")
            sys.exit(1)

    # Check if path exists
    if not target_path.exists():
        print(f"✗ Error: {target_path} does not exist")
        sys.exit(1)

    # Convert single file or directory
    if target_path.is_file():
        if csv_to_excel(target_path, output_dir):
            print("\n✓ Conversion successful!")
        else:
            print("\n✗ Conversion failed!")
            sys.exit(1)
    else:
        _, failed = convert_directory(
            target_path,
            output_dir=output_dir,
            recursive=recursive,
            separate_files=not combined
        )
        if failed > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
