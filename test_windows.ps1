# PowerShell script for easy testing of Sanskrit Processor
# Usage: .\test_windows.ps1

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "Sanskrit SRT Processor - Windows PowerShell Test" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python or try 'python3' command." -ForegroundColor Red
    Write-Host "Try running: python3 simple_cli.py --help" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Testing basic processor with sample file..." -ForegroundColor Yellow
Write-Host ""

# Run the test
try {
    python simple_cli.py sample_test.srt test_output_windows.srt --lexicons lexicons --verbose
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "======================================================" -ForegroundColor Green
        Write-Host "SUCCESS! Processing completed successfully." -ForegroundColor Green
        Write-Host ""
        Write-Host "Check 'test_output_windows.srt' for results." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To process your own files, use:" -ForegroundColor White
        Write-Host "  python simple_cli.py input.srt output.srt --lexicons lexicons" -ForegroundColor Gray
        Write-Host ""
        Write-Host "For enhanced features:" -ForegroundColor White
        Write-Host "  python enhanced_cli.py input.srt output.srt --config config.yaml" -ForegroundColor Gray
        Write-Host "======================================================" -ForegroundColor Green
    } else {
        throw "Processing failed"
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: Processing failed. Check the error messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "  1. Make sure you're in the correct directory" -ForegroundColor White
    Write-Host "  2. Try: python3 simple_cli.py --help" -ForegroundColor White
    Write-Host "  3. Try: py simple_cli.py --help" -ForegroundColor White
    Write-Host "  4. Install dependencies: pip install -r requirements.txt" -ForegroundColor White
}

Write-Host ""
Read-Host "Press Enter to exit"