# Story 4.2: Batch Processing Optimization

**Epic**: Content Enhancement  
**Story Points**: 3  
**Priority**: Low (Optional)  
**Status**: ⏳ Todo

⚠️ **MANDATORY**: Read `../LEAN_ARCHITECTURE_GUIDELINES.md` before implementation

## 📋 User Story

**As a** content manager  
**I want** efficient multi-file processing capabilities  
**So that** large collections of SRT files can be processed in batches with consolidated reporting

## 🎯 Business Value

- **Efficiency**: Process multiple files without manual intervention
- **Scalability**: Handle large content collections systematically  
- **Productivity**: Batch operations save significant time
- **Reporting**: Consolidated metrics across multiple files
- **Automation**: Enable workflow automation and scripting

## ✅ Acceptance Criteria

### **AC 1: Multi-File Processing**
- [ ] Process all SRT files in a directory with single command
- [ ] Support glob patterns for file selection (*.srt, lecture_*.srt)
- [ ] Recursive directory processing option
- [ ] Skip already processed files (optional incremental mode)
- [ ] Parallel processing for improved performance (optional)

### **AC 2: Progress Tracking**
- [ ] Real-time progress display with current file name
- [ ] Percentage completion and ETA calculation  
- [ ] Processing speed metrics (files/minute, segments/second)
- [ ] Memory usage monitoring during batch runs
- [ ] Graceful handling of interruptions (Ctrl+C)

### **AC 3: Error Isolation & Recovery**
- [ ] Continue processing remaining files if one file fails
- [ ] Collect and report all errors at the end
- [ ] Option to stop on first error vs continue processing
- [ ] Detailed error reporting with file names and line numbers
- [ ] Resume capability for interrupted batch runs

### **AC 4: Consolidated Reporting**  
- [ ] Summary report across all processed files
- [ ] Aggregated metrics: total corrections, processing time, quality scores
- [ ] Per-file breakdown with individual metrics
- [ ] Export consolidated results to JSON/CSV
- [ ] Comparison reports between batch runs

### **AC 5: CLI Integration**
- [ ] Batch processing flags in enhanced_cli.py  
- [ ] Directory-based input instead of single file
- [ ] Output directory structure mirroring input
- [ ] Dry-run mode to preview what will be processed
- [ ] Verbose and quiet modes for different use cases

## 🏗️ Implementation Plan

### **Phase 1: File Discovery & Validation (30 minutes)**
```python
class BatchProcessor:
    def discover_files(self, input_path: str, pattern: str = "*.srt") -> List[Path]:
        # Find all matching SRT files
        # Validate files are readable
        # Return sorted list for consistent processing
        
    def validate_batch(self, files: List[Path]) -> List[Path]:
        # Check file accessibility
        # Estimate processing time and memory needs  
        # Warn about potential issues
```

### **Phase 2: Progress Tracking System (45 minutes)**
```python
class ProgressTracker:
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.current_file = 0
        self.start_time = time.time()
        
    def update(self, file_name: str, segments_processed: int):
        # Update progress display
        # Calculate ETA and processing speed
        # Show memory usage if requested
        
    def display_progress(self):
        # Real-time progress bar
        # Current file and overall progress
        # Speed and ETA information
```

### **Phase 3: Batch Processing Engine (60 minutes)**  
```python
def process_batch(self, input_dir: Path, output_dir: Path, 
                 pattern: str = "*.srt") -> BatchResult:
    """Process multiple SRT files in batch."""
    files = self.discover_files(input_dir, pattern)
    results = []
    errors = []
    
    with ProgressTracker(len(files)) as progress:
        for file_path in files:
            try:
                result = self.process_single_file(file_path, output_dir)
                results.append(result)
                progress.update(file_path.name, result.segments_processed)
                
            except Exception as e:
                errors.append({"file": file_path, "error": str(e)})
                if self.stop_on_error:
                    break
                    
    return BatchResult(results, errors)
```

### **Phase 4: Reporting & CLI Integration (45 minutes)**
```python
class BatchReporter:
    def generate_summary(self, batch_result: BatchResult) -> str:
        # Consolidated metrics across all files
        # Success/failure breakdown  
        # Performance statistics
        
    def export_detailed_report(self, batch_result: BatchResult, format: str):
        # JSON or CSV export
        # Per-file metrics
        # Error details
```

## 📁 Files to Create/Modify

### **New Files:**
- `services/batch_processor.py` - Core batch processing logic
- `services/progress_tracker.py` - Progress display and tracking
- `services/batch_reporter.py` - Consolidated reporting  
- `tests/test_batch_processing.py` - Unit and integration tests

### **Modified Files:**
- `enhanced_cli.py` - Add batch processing command-line options
- `enhanced_processor.py` - Integration with batch processor
- `README.md` - Document batch processing capabilities

## 🔧 Technical Specifications

### **CLI Interface Design:**
```bash
# Basic batch processing
python enhanced_cli.py batch input_dir/ output_dir/ --config config.yaml

# Advanced options
python enhanced_cli.py batch lectures/ processed/ \
    --pattern "lecture_*.srt" \
    --recursive \
    --parallel 4 \
    --incremental \
    --verbose

# Reporting options  
python enhanced_cli.py batch input/ output/ \
    --export-report results.json \
    --export-format csv \
    --dry-run
```

### **Batch Result Data Structure:**
```python
@dataclass
class BatchFileResult:
    file_path: Path
    output_path: Path  
    processing_result: ProcessingResult
    processing_time: float
    file_size: int
    success: bool
    error: Optional[str] = None

@dataclass
class BatchResult:
    files_processed: List[BatchFileResult]
    total_files: int
    successful_files: int
    failed_files: int
    total_processing_time: float
    total_corrections: int
    average_quality_score: float
    errors: List[Dict[str, Any]]
```

### **Progress Display Format:**
```
🔄 Processing Batch: 47/156 files (30.1%) 

📁 Current: lecture_bhagavad_gita_ch2.srt
   ├─ Segments: 89/127 (70.1%)  
   ├─ Speed: 2,340 segments/sec
   └─ ETA: 2m 15s remaining

📊 Batch Progress:
   ├─ Files completed: 46 ✅ | 1 ❌  
   ├─ Total corrections: 1,247
   ├─ Processing speed: 12.3 files/min
   ├─ Memory usage: 23.4 MB
   └─ Overall ETA: 8m 42s

Press Ctrl+C to stop gracefully...
```

### **Performance Optimizations:**

#### **Parallel Processing (Optional):**
```python
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

def process_batch_parallel(self, files: List[Path], max_workers: int = 4):
    """Process files in parallel for improved performance."""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.process_single_file, file_path): file_path 
            for file_path in files
        }
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                self.handle_error(futures[future], e)
                
    return results
```

#### **Memory Management:**
```python
def process_with_memory_management(self, files: List[Path]):
    """Process files with memory usage monitoring."""
    for i, file_path in enumerate(files):
        # Process file
        result = self.process_single_file(file_path)
        
        # Memory cleanup every N files  
        if i % 50 == 0:
            gc.collect()
            
        # Memory usage check
        if self.get_memory_usage() > self.max_memory_mb:
            self.logger.warning("High memory usage detected, forcing cleanup")
            gc.collect()
```

## 🧪 Test Cases

### **Unit Tests:**
```python
def test_file_discovery():
    batch_processor = BatchProcessor()
    
    # Create test directory with various files
    test_dir = create_test_directory_with_srt_files()
    
    files = batch_processor.discover_files(test_dir, "*.srt")
    assert len(files) == 5  # Expected number of SRT files
    assert all(f.suffix == '.srt' for f in files)

def test_progress_tracking():
    tracker = ProgressTracker(10)
    
    tracker.update("file1.srt", 100)
    assert tracker.current_file == 1
    assert tracker.get_percentage() == 10.0
    
    tracker.update("file5.srt", 200)  
    assert tracker.current_file == 2
    assert tracker.get_percentage() == 20.0

def test_error_isolation():
    batch_processor = BatchProcessor()
    
    # Mix of valid and invalid files
    files = [valid_file_1, invalid_file, valid_file_2]  
    
    result = batch_processor.process_batch(files)
    
    assert result.successful_files == 2
    assert result.failed_files == 1
    assert len(result.errors) == 1

def test_batch_reporting():
    batch_result = create_test_batch_result()  
    reporter = BatchReporter()
    
    summary = reporter.generate_summary(batch_result)
    assert "Total files processed: 10" in summary
    assert "Success rate: 90%" in summary
    
    # Test JSON export
    json_report = reporter.export_detailed_report(batch_result, "json")
    assert "files_processed" in json_report
```

### **Integration Tests:**
```python
def test_full_batch_workflow():
    # Create test directory with multiple SRT files
    test_input_dir = create_test_srt_directory(num_files=5)
    test_output_dir = create_temp_directory()
    
    # Run batch processing
    cli_result = run_cli_command([
        "enhanced_cli.py", "batch", 
        str(test_input_dir), str(test_output_dir),
        "--verbose"
    ])
    
    assert cli_result.returncode == 0
    
    # Verify all files were processed
    output_files = list(test_output_dir.glob("*.srt"))
    assert len(output_files) == 5
    
    # Verify processing results
    for output_file in output_files:
        assert output_file.stat().st_size > 0  # File has content

def test_incremental_processing():
    # Test that already processed files are skipped
    # Test resume functionality after interruption
    pass

def test_parallel_processing_performance():
    # Compare sequential vs parallel processing times
    # Verify results are identical
    pass
```

## 📊 Success Metrics

- **Processing Speed**: 10+ files per minute for typical SRT files
- **Memory Efficiency**: < 100MB memory usage for batches of 100 files  
- **Error Resilience**: Process 99% of valid files even with some corrupted files
- **User Experience**: Clear progress indication and accurate ETA
- **Scalability**: Handle 1000+ files in single batch run

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Memory exhaustion with large batches | High | Memory monitoring, periodic cleanup, file streaming |
| Processing interruption/crashes | Medium | Resume capability, progress saving, graceful shutdown |
| Disk space exhaustion | Medium | Pre-flight disk space check, incremental processing |
| Performance degradation | Low | Parallel processing option, performance monitoring |

## 🔄 Story Progress Tracking

- [ ] **Started**: Implementation begun
- [ ] **File Discovery**: Directory scanning and file validation working
- [ ] **Progress Tracking**: Real-time progress display implemented  
- [ ] **Batch Processing**: Core batch processing engine functional
- [ ] **Error Handling**: Robust error isolation and recovery  
- [ ] **Reporting**: Consolidated reporting across files
- [ ] **CLI Integration**: Command-line interface enhanced
- [ ] **Testing**: Comprehensive test coverage
- [ ] **Performance**: Speed and memory optimization completed

## 📝 Implementation Notes

### **Design Considerations:**

#### **Sequential vs Parallel Processing:**
- **Sequential**: Simpler, predictable memory usage, easier debugging
- **Parallel**: Faster for I/O bound operations, more complex error handling  
- **Hybrid**: Sequential by default, parallel as opt-in for power users

#### **Memory Management:**
- Stream processing for large files
- Periodic garbage collection
- Memory usage monitoring and warnings
- Configurable memory limits

#### **User Experience:**  
- Clear progress indicators
- Meaningful error messages
- Estimated completion times
- Graceful interruption handling

### **Configuration Options:**
```yaml
batch_processing:
  max_parallel_workers: 4
  max_memory_mb: 512
  progress_update_interval: 1.0  # seconds
  enable_incremental: false
  stop_on_error: false
  export_format: "json"  # json, csv
```

### **Future Enhancements:**
- Integration with workflow systems (Apache Airflow, etc.)
- Cloud storage support (S3, Google Drive)  
- Distributed processing across multiple machines
- Web-based batch monitoring interface
- Automated quality assurance checks across batches

---

**Dependencies**: None (can run independently)  
**Estimated completion**: Day 5 of sprint (optional/stretch goal)