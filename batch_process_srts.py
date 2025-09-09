#!/usr/bin/env python3
"""
Batch SRT Processor for Sanskrit Transcriptions
Processes all SRT files in a specified directory using the Sanskrit processor.
"""

import os
import sys
import glob
import subprocess
from pathlib import Path
import time

def find_main_srt_files(directory):
    """Find main SRT files, excluding backups and test files."""
    pattern = os.path.join(directory, "*.srt")
    all_files = glob.glob(pattern)
    
    # Filter out backup files and test subdirectories
    main_files = []
    for file in all_files:
        filename = os.path.basename(file)
        if not any(exclude in filename.lower() for exclude in ['backup', 'old', 'test_']):
            # Also exclude files in test_outputs subdirectory
            if 'test_outputs' not in file:
                main_files.append(file)
    
    return sorted(main_files)

def process_srt_file(input_file, output_dir, mode='simple', verbose=True):
    """Process a single SRT file."""
    input_path = Path(input_file)
    output_filename = f"{input_path.stem}_processed.srt"
    output_file = os.path.join(output_dir, output_filename)
    
    # Prepare command
    cmd = ['python3', 'cli.py', input_file, output_file]
    if mode == 'simple':
        cmd.append('--simple')
    else:
        cmd.extend(['--config', 'config.yaml'])
    
    if verbose:
        cmd.append('--verbose')
    
    print(f"Processing: {input_path.name}")
    print(f"Output: {output_filename}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if verbose and result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True, None
        else:
            print("❌ FAILED")
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"Error: {error_msg}")
            return False, error_msg
    
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT (5 minutes)")
        return False, "Processing timeout"
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False, str(e)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch_process_srts.py <input_directory> [output_directory] [--enhanced] [--dry-run]")
        print("Example: python3 batch_process_srts.py '/mnt/c/Users/miked/Transcription_Project/Scripts/Web_Whisper/daily_outputs'")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "processed_outputs"
    
    # Parse options
    mode = 'enhanced' if '--enhanced' in sys.argv else 'simple'
    dry_run = '--dry-run' in sys.argv
    
    if not os.path.exists(input_directory):
        print(f"❌ Input directory not found: {input_directory}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_directory, exist_ok=True)
    
    # Find SRT files
    srt_files = find_main_srt_files(input_directory)
    
    if not srt_files:
        print("❌ No SRT files found in the specified directory")
        sys.exit(1)
    
    print(f"📁 Found {len(srt_files)} SRT files to process")
    print(f"📤 Output directory: {output_directory}")
    print(f"⚙️  Processing mode: {mode}")
    print("-" * 60)
    
    if dry_run:
        print("🔍 DRY RUN - Files that would be processed:")
        for i, file in enumerate(srt_files, 1):
            print(f"{i:2d}. {os.path.basename(file)}")
        return
    
    # Process files
    processed = 0
    failed = 0
    errors = []
    
    start_time = time.time()
    
    for i, srt_file in enumerate(srt_files, 1):
        print(f"\n[{i}/{len(srt_files)}] " + "="*50)
        success, error = process_srt_file(srt_file, output_directory, mode)
        
        if success:
            processed += 1
        else:
            failed += 1
            errors.append((os.path.basename(srt_file), error))
    
    # Summary
    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*60)
    print(f"✅ Successfully processed: {processed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"📁 Output directory: {output_directory}")
    
    if errors:
        print(f"\n❌ FAILED FILES:")
        for filename, error in errors:
            print(f"  • {filename}: {error}")

if __name__ == "__main__":
    main()