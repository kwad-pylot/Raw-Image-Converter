
import os
import rawpy
import imageio
import json
import shutil
import time
import argparse
import sys
from datetime import datetime
import logging
import pyexiv2
from tqdm import tqdm

# Create a custom filter to suppress pyexiv2 warnings
class PyExiv2Filter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        if '[warn]' in message and ('Exif tag' in message or 'Directory Thumbnail' in message):
            return False
        return True

# Set up logging - will be configured when the script runs with the correct directory

def check_disk_space(directory, required_mb=500):
    """
    Check if there's enough disk space in the specified directory.
    By default, requires at least 500MB free.
    """
    try:
        # Get disk usage statistics
        total, used, free = shutil.disk_usage(directory)
        free_mb = free / (1024 * 1024)  # Convert to MB
        
        if free_mb < required_mb:
            logging.warning(f"Low disk space: Only {free_mb:.2f}MB available, {required_mb}MB recommended")
            return False, free_mb
        return True, free_mb
    except Exception as e:
        logging.error(f"Error checking disk space: {e}")
        return False, 0

def load_conversion_log(root_directory, log_file='conversion_log.json'):
    """
    Load the conversion log from a JSON file in the specified root directory.
    Returns a dictionary of successfully converted files.
    """
    log_path = os.path.join(root_directory, log_file)
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading conversion log: {e}")
    return {}

def save_conversion_log(conversion_log, root_directory, log_file='conversion_log.json'):
    """
    Save the conversion log to a JSON file in the specified root directory.
    """
    log_path = os.path.join(root_directory, log_file)
    try:
        with open(log_path, 'w') as f:
            json.dump(conversion_log, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving conversion log: {e}")

def load_corrupt_files_log(root_directory, log_file='corrupt_files.json'):
    """
    Load the list of corrupt files from a JSON file in the specified root directory.
    Returns a dictionary with corrupt file paths and error details.
    """
    log_path = os.path.join(root_directory, log_file)
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading corrupt files log: {e}")
    return {}

def save_corrupt_files_log(corrupt_files_log, root_directory, log_file='corrupt_files.json'):
    """
    Save the corrupt files log to a JSON file in the specified root directory.
    """
    log_path = os.path.join(root_directory, log_file)
    try:
        with open(log_path, 'w') as f:
            json.dump(corrupt_files_log, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving corrupt files log: {e}")

def convert_raw_to_jpeg(root_directory):
    """
    Recursively converts raw image files (.CR2, .RW2) in the root directory and all subdirectories
    to high-quality JPEGs and saves them in the same location as the original files.
    """
    converted_count = 0
    skipped_count = 0
    error_count = 0
    processed_directories = 0
    corrupt_files = []
    
    # Check for sufficient disk space
    has_space, free_mb = check_disk_space(root_directory)
    if not has_space:
        logging.warning(f"Proceeding with low disk space ({free_mb:.2f}MB). Some conversions may fail.")
    
    # Load conversion log to resume partial conversions
    conversion_log = load_conversion_log(root_directory)
    logging.info(f"Loaded conversion log with {len(conversion_log)} previously converted files")
    
    # Load corrupt files log
    corrupt_files_log = load_corrupt_files_log(root_directory)
    logging.info(f"Loaded corrupt files log with {len(corrupt_files_log)} previously identified corrupt files")

    # First, count the total number of raw files for the progress bar
    total_raw_files = 0
    print("Scanning directories for raw files...")
    for root, _, files in os.walk(root_directory):
        for file in files:
            if file.lower().endswith((".cr2", ".rw2", ".arw", ".nef", ".orf", ".dng", ".raf", ".pef", ".srw")):
                total_raw_files += 1
    
    print(f"Found {total_raw_files} raw files to process")
    
    # Create a progress bar for the overall conversion process
    main_progress = tqdm(total=total_raw_files, desc="Converting raw files", unit="file")
    
    # Walk through all directories and subdirectories
    for current_dir, subdirs, files in os.walk(root_directory):
        processed_directories += 1
        
        # Process files in the current directory
        raw_files_found = False
        for filename in files:
            # Check for raw image extensions
            if filename.lower().endswith((".cr2", ".rw2", ".arw", ".nef", ".orf", ".dng", ".raf", ".pef", ".srw")):
                raw_files_found = True
                input_path = os.path.join(current_dir, filename)
                output_filename = os.path.splitext(filename)[0] + ".jpg"
                output_path = os.path.join(current_dir, output_filename)

                # Check if file was previously converted successfully (from log)
                if input_path in conversion_log:
                    logging.info(f"Skipping {filename} (found in conversion log)")
                    skipped_count += 1
                    continue
                    
                # Check if the converted file already exists
                if os.path.exists(output_path):
                    logging.info(f"Skipping {filename} (output file already exists)")
                    skipped_count += 1
                    continue

                try:
                    # Only log processing in file log, not console
                    if logging.getLogger().isEnabledFor(logging.DEBUG):
                        logging.info(f"Processing {filename}...")
                    
                    # Get original file stats for timestamp preservation
                    original_stats = os.stat(input_path)
                    
                    # Read the raw file
                    with rawpy.imread(input_path) as raw:
                        # Try to extract metadata (basic approach)
                        metadata = {}
                        try:
                            if hasattr(raw, 'metadata') and raw.metadata is not None:
                                metadata = raw.metadata
                        except Exception as meta_err:
                            logging.warning(f"Could not extract metadata from {filename}: {meta_err}")
                        
                        # Postprocess the raw image data to get an RGB image
                        # use_camera_wb=True uses the white balance set by the camera
                        # no_auto_bright=False allows automatic brightness adjustment
                        # output_bps=8 sets the output bit depth to 8 bits per channel (standard for JPEG)
                        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=False, output_bps=8)

                    # Save the image as JPEG with high quality
                    # quality=95 is generally considered high quality for JPEG
                    imageio.imwrite(output_path, rgb, format='JPEG', quality=95)
                    
                    # Preserve original timestamps
                    os.utime(output_path, (original_stats.st_atime, original_stats.st_mtime))
                    
                    # Copy detailed metadata from raw file to JPEG
                    try:
                        # Temporarily redirect stderr to suppress pyexiv2 warnings
                        original_stderr = sys.stderr
                        null_file = open(os.devnull, 'w')
                        sys.stderr = null_file
                        
                        # Open both source and target images
                        source_metadata = pyexiv2.Image(input_path)
                        target_image = pyexiv2.Image(output_path)
                        
                        # Read all metadata from source
                        exif_data = source_metadata.read_exif()
                        iptc_data = source_metadata.read_iptc()
                        xmp_data = source_metadata.read_xmp()
                        
                        # Write metadata to target
                        if exif_data:
                            target_image.modify_exif(exif_data)
                        if iptc_data:
                            target_image.modify_iptc(iptc_data)
                        if xmp_data:
                            target_image.modify_xmp(xmp_data)
                            
                        # Save changes
                        target_image.close()
                        source_metadata.close()
                        
                        # Restore stderr
                        null_file.close()
                        sys.stderr = original_stderr
                        
                        logging.info(f"Preserved metadata for {filename}")
                    except Exception as e:
                        logging.warning(f"Could not preserve metadata for {filename}: {e}")
                    
                    # Add to conversion log
                    conversion_log[input_path] = {
                        "output_path": output_path,
                        "converted_at": datetime.now().isoformat(),
                        "file_size": original_stats.st_size
                    }
                    
                    # Save log periodically (every 5 files)
                    if converted_count % 5 == 0:
                        save_conversion_log(conversion_log, root_directory)
                    
                    # Use a cleaner format for console output with ASCII characters only
                    logging.info(f"Converted: {filename} -> {output_filename}")
                    converted_count += 1
                    
                    # Update the progress bar
                    main_progress.update(1)
                except (rawpy.LibRawFileUnsupportedError, rawpy.LibRawError, OSError, IOError) as e:
                    # Handle all types of raw file errors
                    error_msg = f"Error: Could not process {filename}. File format might be unsupported or corrupted: {e}"
                    logging.error(error_msg)
                    
                    # Add to corrupt files log instead of moving the file
                    corrupt_files_log[input_path] = {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "detected_at": datetime.now().isoformat(),
                        "file_size": os.path.getsize(input_path)
                    }
                    corrupt_files.append(input_path)
                    error_count += 1
                    
                    # Update the progress bar for errors
                    main_progress.update(1)
                    
                except Exception as e:
                    # Handle general conversion errors
                    error_msg = f"Error converting {filename}: {e}"
                    logging.error(error_msg)
                    
                    # Add to corrupt files log
                    corrupt_files_log[input_path] = {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "detected_at": datetime.now().isoformat(),
                        "file_size": os.path.getsize(input_path)
                    }
                    corrupt_files.append(input_path)
                    error_count += 1
                    
                    # Update the progress bar for errors
                    main_progress.update(1)
        
        if not raw_files_found and len(files) > 0:
            print(f"No raw image files found in directory: {current_dir}")

    # Close the progress bar
    main_progress.close()
    
    # Save the final conversion log
    save_conversion_log(conversion_log, root_directory)
    
    # Save the corrupt files log
    if corrupt_files:
        save_corrupt_files_log(corrupt_files_log, root_directory)
    
    # Final summary
    logging.info("\nConversion Summary:")
    logging.info(f"  Directories processed: {processed_directories}")
    logging.info(f"  Converted: {converted_count}")
    logging.info(f"  Skipped:   {skipped_count}")
    logging.info(f"  Errors:    {error_count}")
    
    if corrupt_files:
        logging.info(f"  Corrupt files identified: {len(corrupt_files)}")
        for file in corrupt_files:
            logging.info(f"    - {file}")
        logging.info(f"  Details saved to corrupt_files.json")
    
    return converted_count, skipped_count, error_count

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Convert raw image files to high-quality JPEGs')
    parser.add_argument('--dir', '-d', dest='directory', 
                        help='Starting directory for conversion (default: script location)',
                        default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument('--space', '-s', dest='required_space', type=int,
                        help='Required free space in MB (default: 500)',
                        default=500)
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force conversion even with low disk space')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate the directory
    if not os.path.isdir(args.directory):
        print(f"Error: The specified directory '{args.directory}' does not exist or is not a directory.")
        exit(1)
        
    # Set up logging with log file in the target directory
    log_file = os.path.join(args.directory, 'raw_conversion.log')
    
    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            # Custom stream handler with our filter
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add our custom filter to the root logger's handlers
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.addFilter(PyExiv2Filter())
            # Use a cleaner format for console output
            handler.setFormatter(logging.Formatter('%(message)s'))
    
    start_time = time.time()
    logging.info("Starting raw image conversion process")
    logging.info(f"Starting directory: {args.directory}")
    
    # Check disk space before starting
    has_space, free_mb = check_disk_space(args.directory, required_mb=args.required_space)
    logging.info(f"Available disk space: {free_mb:.2f}MB")
    
    if not has_space and not args.force:
        proceed = input(f"Low disk space warning: Only {free_mb:.2f}MB available. Proceed anyway? (y/n): ")
        if proceed.lower() != 'y':
            logging.info("Conversion cancelled due to low disk space")
            exit(0)
    
    convert_raw_to_jpeg(args.directory)
    
    elapsed_time = time.time() - start_time
    logging.info(f"Conversion process completed in {elapsed_time:.2f} seconds")
