# Raw Image Converter: Detailed Workflow

This document provides a detailed step-by-step explanation of how the Raw Image Converter processes files, with a focus on the core RAW to JPEG conversion process.

## Overall Process Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Initialization │────▶│  File Discovery │────▶│ File Processing │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Final Cleanup  │◀────│   Log Saving    │◀────│ Progress Update │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 1. Initialization Phase

1. **Parse Command-Line Arguments**
   - Get the starting directory (`--dir`)
   - Get minimum disk space requirement (`--space`)
   - Check if force conversion is enabled (`--force`)

2. **Set Up Logging**
   - Configure logging to both console and file
   - Apply custom filter to suppress pyexiv2 warnings
   - Create log file in the specified directory

3. **Check Disk Space**
   - Calculate available disk space
   - Compare with required minimum (default: 500MB)
   - If insufficient and not forced, exit with warning
   - If insufficient but forced, continue with warning

4. **Load Previous Logs**
   - Load conversion log (`conversion_log.json`)
   - Load corrupt files log (`corrupt_files.json`)
   - These logs are used to track progress and avoid redundant work

## 2. File Discovery Phase

1. **Count Total Raw Files**
   - Walk through all directories and subdirectories
   - Count files with raw extensions (.cr2, .rw2, .arw, .nef, .orf, .dng, .raf, .pef, .srw)
   - Display total count to user

2. **Initialize Progress Tracking**
   - Set up counters for converted, skipped, and error files
   - Initialize timing for speed calculations
   - Display start message

## 3. File Processing Phase (Core Conversion)

For each raw file found, the converter follows these exact steps, with integrated disk space monitoring:

1. **File Eligibility Check**
   - Check if file has already been processed (in conversion log)
   - Check if output JPEG already exists
   - If either is true, skip file and continue to next

2. **Read Original File Information**
   - Get file stats (size, timestamps)
   - These will be preserved in the output file

3. **Raw File Reading**
   - Open raw file using rawpy library
   - Attempt to extract basic metadata

4. **Image Processing**
   - Process raw data to RGB using camera white balance
   - Apply automatic brightness adjustment
   - Set output to 8 bits per channel (standard for JPEG)

5. **JPEG Creation**
   - Save processed image as JPEG with 95% quality
   - This creates the initial JPEG file

6. **Timestamp Preservation**
   - Apply original file's timestamps to new JPEG
   - Ensures file appears with original creation/modification dates

7. **Metadata Transfer**
   - Temporarily redirect stderr to suppress warnings
   - Open source (raw) and target (JPEG) files with pyexiv2
   - Read EXIF, IPTC, and XMP metadata from source
   - Write all available metadata to target
   - Close both files and restore stderr

8. **Conversion Logging and Space Monitoring**
   - Add entry to conversion log with:
     - Output path
     - Conversion timestamp
     - Original file size
   - Save log every 5 files to prevent data loss
   - Track converted JPEG file sizes for space prediction
   - Perform adaptive disk space check based on current space status
   - Calculate estimated space needed for remaining files
   - If space is predicted to be insufficient:
     - Pause conversion and present options to the user:
       1. Free up space and continue
       2. Force continue despite warning
       3. Save progress and exit

9. **Progress Update**
   - Increment converted count
   - Calculate and display progress percentage
   - Calculate and display conversion speed
   - Periodically show estimated time remaining

## 4. Error Handling

The converter has two levels of error handling:

1. **Raw File Errors**
   - Catches specific errors: LibRawFileUnsupportedError, LibRawError, OSError, IOError
   - These typically indicate corrupt or unsupported raw files
   - Logs error details to corrupt_files.json
   - Continues to next file

2. **General Errors**
   - Catches any other unexpected exceptions
   - Logs full error details
   - Continues to next file without stopping the entire process

## 5. Final Phase

1. **Save Final Logs**
   - Save complete conversion log
   - Save corrupt files log

2. **Display Summary**
   - Show total files processed
   - Show conversion statistics (converted, skipped, errors)
   - Show total processing time and speed

## Important Notes

1. **Continuous Disk Space Monitoring**
   - Disk space is checked both at the beginning and throughout the conversion process
   - The frequency of checks adapts based on available space:
     - Normal conditions: Every 5 files
     - Warning level (< 2× required space): Every 3 files
     - Critical level (< required space): Every file
   - Predictive warnings estimate if there's enough space for all remaining files
   - Pause and resume capability when space runs low

2. **File Skipping Logic**
   - Files are skipped if they appear in the conversion log OR if the output JPEG already exists
   - This allows for safely rerunning the converter without duplicating work

3. **Memory Management**
   - Files are processed one at a time to minimize memory usage
   - Each raw file is closed after processing before moving to the next

4. **Log Persistence**
   - Conversion log is saved every 5 files to prevent data loss if the process is interrupted
   - Final logs are saved at the end of the process

This workflow ensures efficient, reliable conversion of raw image files to high-quality JPEGs while preserving important metadata and providing clear progress information to the user.
