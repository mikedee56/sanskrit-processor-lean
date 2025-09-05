# Task Completion Checklist

## Before Committing Changes

### Basic Validation
1. **Test Basic Functionality**: Run `python3 simple_cli.py sample_test.srt test_output.srt --lexicons lexicons --verbose`
2. **Test Enhanced Features**: Run `python3 enhanced_cli.py sample_test.srt test_output.srt --config config.yaml --verbose`
3. **Verify Output**: Check that test_output.srt contains expected corrections

### Code Quality
1. **Python Syntax**: Ensure no syntax errors with `python3 -m py_compile <filename>`
2. **Dependencies**: Verify all imports work correctly
3. **Configuration**: Validate YAML files are properly formatted

### Cross-Platform Compatibility
1. **Windows Testing**: Run `test_windows.bat` or `test_windows.ps1` if available
2. **Path Handling**: Ensure file paths work on Windows/Linux/WSL2
3. **Python Command**: Test both `python` and `python3` commands work

### Service Integration (if applicable)
1. **MCP Services**: Test `python3 enhanced_cli.py --status-only`
2. **Circuit Breakers**: Verify graceful degradation when services unavailable
3. **Configuration**: Ensure external service settings are properly configured

### Documentation
1. **README Updates**: Update README.md if functionality changes
2. **Configuration**: Update config.yaml comments if new options added
3. **Lexicon Updates**: Document any new lexicon entries

## Performance Verification
- Processing speed should maintain 2,600+ segments/second
- Memory usage should stay under 50MB for typical processing
- No memory leaks during batch processing

## Error Scenarios to Test
1. **Missing Files**: Test with non-existent input files
2. **Invalid Configuration**: Test with malformed YAML
3. **Service Failures**: Test behavior when external services are down
4. **Permission Issues**: Test file permission problems