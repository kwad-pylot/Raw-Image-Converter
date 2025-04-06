import os
import json
import logging
import argparse
from datetime import datetime

# Set up logging - will be configured when the script runs with the correct directory

def load_conversion_log(directory, log_file='conversion_log.json'):
    """
    Load the conversion log from a JSON file in the specified directory.
    Returns a dictionary of successfully converted files.
    """
    log_path = os.path.join(directory, log_file)
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading conversion log: {e}")
            return {}
    else:
        logging.error(f"Conversion log file not found: {log_path}")
        return {}

def delete_raw_files(directory, conversion_log_name='conversion_log.json', confirm=True, batch_size=None):
    """
    Delete original raw files that have been successfully converted.
    
    Args:
        conversion_log_path: Path to the conversion log JSON file
        confirm: Whether to ask for confirmation before deletion
        batch_size: Optional limit on how many files to delete in one run
    
    Returns:
        tuple: (deleted_count, skipped_count, error_count)
    """
    # Load the conversion log
    conversion_log = load_conversion_log(directory, conversion_log_name)
    
    if not conversion_log:
        logging.warning("No converted files found in the log. Nothing to delete.")
        return 0, 0, 0
    
    # Group files by directory for easier review
    files_by_dir = {}
    raw_files_to_delete = []
    
    for raw_path, info in conversion_log.items():
        # Only include files that still exist
        if os.path.exists(raw_path):
            # Check if the converted file also exists
            jpeg_path = info.get('output_path')
            if jpeg_path and os.path.exists(jpeg_path):
                raw_files_to_delete.append(raw_path)
                
                # Group by directory for display
                directory = os.path.dirname(raw_path)
                if directory not in files_by_dir:
                    files_by_dir[directory] = []
                files_by_dir[directory].append(os.path.basename(raw_path))
    
    # Apply batch size limit if specified
    if batch_size and len(raw_files_to_delete) > batch_size:
        logging.info(f"Limiting deletion to first {batch_size} files of {len(raw_files_to_delete)} total")
        raw_files_to_delete = raw_files_to_delete[:batch_size]
        # Rebuild the directory grouping
        files_by_dir = {}
        for raw_path in raw_files_to_delete:
            directory = os.path.dirname(raw_path)
            if directory not in files_by_dir:
                files_by_dir[directory] = []
            files_by_dir[directory].append(os.path.basename(raw_path))
    
    # Show summary
    print("\nRaw files to be deleted:")
    for directory, files in files_by_dir.items():
        print(f"\nDirectory: {directory}")
        for i, filename in enumerate(files, 1):
            print(f"  {i}. {filename}")
    
    total_files = len(raw_files_to_delete)
    print(f"\nTotal files to delete: {total_files}")
    
    # Ask for confirmation if required
    if confirm:
        user_input = input("Proceed with deletion? (yes/no): ")
        if user_input.lower() != 'yes':
            print("Deletion cancelled.")
            return 0, total_files, 0
    
    # Proceed with deletion
    deleted_count = 0
    skipped_count = 0
    error_count = 0
    deletion_log = {}
    
    for raw_path in raw_files_to_delete:
        try:
            # Get file info before deletion for logging
            file_size = os.path.getsize(raw_path)
            file_info = conversion_log.get(raw_path, {})
            
            # Delete the file
            os.remove(raw_path)
            
            # Log the deletion
            deletion_log[raw_path] = {
                "deleted_at": datetime.now().isoformat(),
                "original_size": file_size,
                "converted_to": file_info.get('output_path', 'unknown')
            }
            
            logging.info(f"Deleted: {raw_path}")
            deleted_count += 1
            
        except FileNotFoundError:
            logging.warning(f"File not found (already deleted?): {raw_path}")
            skipped_count += 1
        except PermissionError:
            logging.error(f"Permission denied when deleting: {raw_path}")
            error_count += 1
        except Exception as e:
            logging.error(f"Failed to delete {raw_path}: {e}")
            error_count += 1
    
    # Save deletion log
    try:
        deletion_log_path = os.path.join(directory, 'deletion_log.json')
        with open(deletion_log_path, 'w') as f:
            json.dump(deletion_log, f, indent=4)
        logging.info(f"Deletion log saved to {deletion_log_path}")
    except Exception as e:
        logging.error(f"Failed to save deletion log: {e}")
    
    # Print summary
    print(f"\nDeletion Summary:")
    print(f"  Deleted: {deleted_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors:  {error_count}")
    
    return deleted_count, skipped_count, error_count

def main():
    parser = argparse.ArgumentParser(description='Delete raw image files that have been successfully converted')
    parser.add_argument('--dir', '-d', dest='directory',
                        help='Directory containing the conversion logs (default: script location)',
                        default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument('--log', default='conversion_log.json', help='Name of the conversion log file')
    parser.add_argument('--force', action='store_true', help='Delete without confirmation')
    parser.add_argument('--batch', type=int, help='Limit the number of files to delete in one run')
    args = parser.parse_args()
    
    # Validate the directory
    if not os.path.isdir(args.directory):
        print(f"Error: The specified directory '{args.directory}' does not exist or is not a directory.")
        exit(1)
    
    # Set up logging with log file in the target directory
    log_file = os.path.join(args.directory, 'deletion_log.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    delete_raw_files(
        directory=args.directory,
        conversion_log_name=args.log,
        confirm=not args.force,
        batch_size=args.batch
    )

if __name__ == "__main__":
    main()
