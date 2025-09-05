# Suggested Commands for Sanskrit SRT Processor

## Primary Development Commands

### Basic Processing (Core Functionality)
```bash
# Process SRT with basic corrections only
python3 simple_cli.py input.srt output.srt --lexicons lexicons

# With verbose output
python3 simple_cli.py input.srt output.srt --lexicons lexicons --verbose
```

### Enhanced Processing (With External Services)
```bash
# Full processing with MCP/API services
python3 enhanced_cli.py input.srt output.srt --config config.yaml

# With verbose output
python3 enhanced_cli.py input.srt output.srt --config config.yaml --verbose

# Check service status only
python3 enhanced_cli.py --status-only
```

### Testing
```bash
# Run basic test using sample file
python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose

# Windows testing (if on Windows)
test_windows.bat
# or
test_windows.ps1

# Run Python tests (if pytest tests exist)
pytest
pytest --cov
```

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Check Python version compatibility
python3 --version
```

### Configuration
```bash
# Edit main configuration
vim config.yaml

# Edit lexicons for corrections
vim lexicons/corrections.yaml

# Edit proper nouns
vim lexicons/proper_nouns.yaml
```

## Windows-specific Commands
```cmd
# Command Prompt usage
python simple_cli.py input.srt output.srt --lexicons lexicons
python enhanced_cli.py input.srt output.srt --config config.yaml

# If 'python' not found, try:
python3 simple_cli.py --help
# or
py simple_cli.py --help
```