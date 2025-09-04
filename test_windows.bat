@echo off
REM Windows batch file for easy testing of Sanskrit Processor
REM Usage: test_windows.bat

echo.
echo ======================================================
echo Sanskrit SRT Processor - Windows Test Script
echo ======================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python or use 'python3' or 'py' command.
    echo Try running: python3 simple_cli.py --help
    pause
    exit /b 1
)

echo Testing basic processor with sample file...
echo.

REM Run the test
python simple_cli.py sample_test.srt test_output_windows.srt --lexicons lexicons --verbose

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo SUCCESS! Processing completed successfully.
    echo.
    echo Check 'test_output_windows.srt' for results.
    echo.
    echo To process your own files, use:
    echo   python simple_cli.py input.srt output.srt --lexicons lexicons
    echo.
    echo For enhanced features:
    echo   python enhanced_cli.py input.srt output.srt --config config.yaml
    echo ======================================================
) else (
    echo.
    echo ERROR: Processing failed. Check the error messages above.
    echo.
    echo Common solutions:
    echo   1. Make sure you're in the correct directory
    echo   2. Try: python3 simple_cli.py --help
    echo   3. Try: py simple_cli.py --help
    echo   4. Install dependencies: pip install -r requirements.txt
)

echo.
pause