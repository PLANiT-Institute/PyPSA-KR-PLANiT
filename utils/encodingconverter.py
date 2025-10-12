import os
import sys
from pathlib import Path


def convert_euckr_to_utf8(file_path, backup=True):
    """
    Convert a file from EUC-KR (CP949/51949) to UTF-8 encoding.

    Args:
        file_path: Path to the file to convert
        backup: Whether to create a backup file with .bak extension

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        # Create backup first if requested
        if backup:
            backup_path = f"{file_path}.bak"
            with open(file_path, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            print(f"Created backup: {backup_path}")

        # Read file with EUC-KR encoding (try both euc-kr and cp949)
        content = None
        for encoding in ['cp949', 'euc-kr']:
            try:
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    content = f.read()
                print(f"Read file using {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            print(f"✗ Error: Could not decode {file_path} with EUC-KR or CP949")
            return False

        # Write file in UTF-8 with BOM for better Excel compatibility
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(content)

        print(f"✓ Converted {file_path} to UTF-8 with BOM")

        # Verify the conversion
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            verify = f.read()
        if len(verify) == len(content):
            print(f"✓ Verification passed ({len(content)} characters)")
        else:
            print(f"⚠ Warning: Character count mismatch")

        return True

    except Exception as e:
        print(f"✗ Error converting {file_path}: {e}")
        # Restore from backup if conversion failed
        if backup:
            try:
                with open(f"{file_path}.bak", 'rb') as src:
                    with open(file_path, 'wb') as dst:
                        dst.write(src.read())
                print(f"Restored from backup")
            except:
                pass
        return False


def convert_directory(directory_path, file_extensions=None, backup=True):
    """
    Convert all files in a directory from EUC-KR to UTF-8.

    Args:
        directory_path: Path to the directory
        file_extensions: List of file extensions to convert (e.g., ['.csv', '.txt'])
                        If None, converts all files
        backup: Whether to create backup files

    Returns:
        Tuple of (converted_count, failed_count)
    """
    directory = Path(directory_path)

    if not directory.exists():
        print(f"Error: Directory {directory_path} does not exist")
        return 0, 0

    if not directory.is_dir():
        print(f"Error: {directory_path} is not a directory")
        return 0, 0

    converted_count = 0
    failed_count = 0

    # Find all files to convert
    files_to_convert = []
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            # Skip backup files
            if file_path.suffix == '.bak':
                continue

            # Check file extension if filter is specified
            if file_extensions and file_path.suffix not in file_extensions:
                continue

            files_to_convert.append(file_path)

    print(f"\nFound {len(files_to_convert)} files to convert")
    print(f"Converting from EUC-KR (CP949/51949) to UTF-8...\n")

    # Convert each file
    for file_path in files_to_convert:
        if convert_euckr_to_utf8(file_path, backup=backup):
            converted_count += 1
        else:
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"Conversion complete:")
    print(f"  ✓ Converted: {converted_count} files")
    print(f"  ✗ Failed: {failed_count} files")
    print(f"{'='*60}")

    return converted_count, failed_count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python encodingconverter.py <file_or_directory> [extensions]")
        print("\nExamples:")
        print("  python encodingconverter.py data/2024/")
        print("  python encodingconverter.py data/2024/ .csv,.txt")
        print("  python encodingconverter.py data/2024/file.csv")
        sys.exit(1)

    target_path = Path(sys.argv[1])

    if not target_path.exists():
        print(f"Error: {target_path} does not exist")
        sys.exit(1)

    # Parse extensions if provided
    extensions = None
    if len(sys.argv) > 2:
        ext_str = sys.argv[2].strip()
        extensions = [ext.strip() if ext.strip().startswith('.') else f'.{ext.strip()}'
                     for ext in ext_str.split(',')]

    # Convert single file or directory
    if target_path.is_file():
        convert_euckr_to_utf8(target_path, backup=True)
    else:
        convert_directory(target_path, file_extensions=extensions, backup=True)
