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

## Command Reference

### All Available Commands

#### Converting Raw Images

| Command | Description |
|---------|-------------|
| `python convert_raw_images.py` | Basic conversion (starts in current directory) |
| `python convert_raw_images.py --dir "PATH"` | Convert raw files in specified directory |
| `python convert_raw_images.py --space 1000` | Set minimum required disk space (MB) |
| `python convert_raw_images.py --force` | Force conversion despite low disk space |
| `python convert_raw_images.py --dir "PATH" --space 1000 --force` | Combined options |

#### Deleting Original Raw Files

| Command | Description |
|---------|-------------|
| `python delete_raw_files.py` | Delete raw files (interactive mode) |
| `python delete_raw_files.py --dir "PATH"` | Delete raw files in specified directory |
| `python delete_raw_files.py --force` | Delete without confirmation prompts |
| `python delete_raw_files.py --batch 100` | Limit deletion to 100 files per run |
| `python delete_raw_files.py --log "custom_log.json"` | Use custom log filename |
| `python delete_raw_files.py --dir "PATH" --force --batch 50` | Combined options |

### Common Examples

```bash
# Basic conversion in current directory
python convert_raw_images.py

# Convert photos in a specific folder
python convert_raw_images.py --dir "C:\Users\Photos\Vacation2023"

# Convert with low disk space override
python convert_raw_images.py --dir "C:\Users\Photos\Vacation2023" --force

# Delete raw files after verifying conversions
python delete_raw_files.py --dir "C:\Users\Photos\Vacation2023"

# Delete in batches without confirmation
python delete_raw_files.py --dir "C:\Users\Photos\Vacation2023" --batch 50 --force
```

### Progress Tracking

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



## Troubleshooting

- **Low disk space warning**: Increase available space or use the `--force` flag
- **Corrupt file errors**: Check corrupt_files.json for details on problematic files
- **Missing metadata**: Some cameras use proprietary metadata that may not transfer completely

## License

This project is licensed under the MIT License - see the LICENSE file for details.
