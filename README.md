# Raw Image Converter

A powerful Python tool for converting raw image files to high-quality JPEGs while preserving timestamps, metadata, and handling errors gracefully.

## Features

- **Multiple Raw Format Support**: Converts CR2, RW2, ARW, NEF, ORF, DNG, RAF, PEF, and SRW raw formats
- **Metadata Preservation**: Maintains all important metadata (camera info, exposure settings, etc.)
- **Timestamp Preservation**: Keeps original file timestamps intact
- **Progress Tracking**: Clear progress updates showing completion percentage and time estimation
- **Partial Conversion Handling**: Tracks converted files to avoid redundant processing
- **Corrupt File Detection**: Identifies problematic files without moving them
- **Disk Space Checking**: Ensures sufficient space before starting conversion
- **Directory-Specific Logs**: All logs are saved in the directory being processed
- **Separate Deletion Tool**: Safely remove original raw files when ready

## Requirements

- Python 3.6+
- Required packages (install via `pip install -r requirements.txt`):
  - rawpy
  - imageio
  - pyexiv2
  - tqdm

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Converting Raw Images

Basic usage (starts from the script's directory):
```
python convert_raw_images.py
```

Specify a custom starting directory:
```
python convert_raw_images.py --dir "C:\Path\To\Your\Photos"
```

Additional options:
```
python convert_raw_images.py --dir "C:\Path\To\Your\Photos" --space 1000 --force
```

#### Progress Tracking

The script provides clear progress updates that show:
- Total number of raw files found
- Current conversion progress (count and percentage)
- Processing speed (files per second)
- Estimated time remaining

Example output:
```
Scanning directories for raw files...
Found 157 raw files to process
Starting conversion of 157 raw files...
Converted: IMG_2554.CR2 -> IMG_2554.jpg
Converted: IMG_2557.CR2 -> IMG_2557.jpg
Progress: 10/157 files (6.4%) - 1.25 files/sec - Est. remaining: 117.6 min
Converted: IMG_2558.CR2 -> IMG_2558.jpg
```

#### Command-line Arguments

- `--dir`, `-d`: Starting directory for conversion (default: script location)
- `--space`, `-s`: Required free space in MB (default: 500)
- `--force`, `-f`: Force conversion even with low disk space

### Deleting Original Raw Files

After verifying your conversions, you can safely delete the original raw files:
```
python delete_raw_files.py
```

Additional options:
```
python delete_raw_files.py --force --batch 100
```

#### Command-line Arguments

- `--dir`, `-d`: Directory containing the conversion logs (default: script location)
- `--log`: Name of the conversion log file (default: conversion_log.json)
- `--force`: Delete without confirmation prompt
- `--batch`: Limit the number of files to delete in one run

## How It Works

### Conversion Process

1. The script recursively walks through the specified directory and its subdirectories
2. For each raw file found, it:
   - Checks if it's already been converted (using conversion_log.json)
   - Reads the raw file using rawpy
   - Processes it to a high-quality RGB image
   - Saves it as a JPEG with 95% quality
   - Preserves all metadata (EXIF, IPTC, XMP)
   - Maintains original timestamps
   - Logs the successful conversion

### Metadata Preservation

The script uses pyexiv2 to extract and transfer all metadata from the raw files to the converted JPEGs, including:
- Camera make and model
- Lens information
- ISO, aperture, shutter speed
- Date and time information
- GPS coordinates (if available)
- Copyright information

### Corrupt File Handling

When a corrupt or unsupported file is detected:
1. The error is logged with details
2. The file path and error information are saved to corrupt_files.json
3. The original file remains in place

### Deletion Process

The separate deletion script:
1. Reads the conversion log to identify successfully converted files
2. Verifies that both the original and converted files exist
3. Shows a summary of files to be deleted, grouped by directory
4. Asks for confirmation before proceeding (unless --force is used)
5. Deletes the original files and logs the deletion details

## Log Files

- **conversion_log.json**: Records all successful conversions
- **corrupt_files.json**: Tracks problematic files and their errors
- **deletion_log.json**: Records all deleted files with timestamps
- **raw_conversion.log**: Detailed text log of the conversion process
- **deletion_log.log**: Detailed text log of the deletion process

All log files are stored in the directory being processed, not in the script's location. This allows you to maintain separate logs for different photo collections and ensures that when you run the deletion tool, it will find the correct conversion logs.

## Examples

### Converting a specific folder of raw images:
```
python convert_raw_images.py --dir "C:\Users\Photos\Vacation2023"
```

### Deleting raw files from the same directory:
```
python delete_raw_files.py --dir "C:\Users\Photos\Vacation2023"
```

### Deleting raw files in batches:
```
python delete_raw_files.py --dir "C:\Users\Photos\Vacation2023" --batch 50
```

## Troubleshooting

- **Low disk space warning**: Increase available space or use the `--force` flag
- **Corrupt file errors**: Check corrupt_files.json for details on problematic files
- **Missing metadata**: Some cameras use proprietary metadata that may not transfer completely

## License

This project is licensed under the MIT License - see the LICENSE file for details.
