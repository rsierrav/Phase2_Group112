@echo off
setlocal

if "%~1"=="" (
    echo Usage:
    echo   run.cmd install               - Install dependencies
    echo   run.cmd score ^<URL_FILE^>    - Score models from a file
    echo   run.cmd dev                   - Run all input files
    echo   run.cmd test                  - Run test suite
    exit /b 1
)

set SCRIPT_DIR=%~dp0
set MAIN_SCRIPT=%SCRIPT_DIR%src\init.py
set REQUIREMENTS=%SCRIPT_DIR%requirements.txt

if "%~1"=="install" (
    echo Installing dependencies...
    if not exist "%REQUIREMENTS%" (
        >"%REQUIREMENTS%" (
            echo requests>=2.25.0
            echo beautifulsoup4>=4.9.0
            echo lxml>=4.6.0
            echo python-dateutil>=2.8.0
            echo urllib3>=1.26.0
            echo GitPython>=3.1.0
            echo PyGithub>=1.55.0
            echo huggingface-hub>=0.10.0
            echo flake8==7.0.0
            echo black==24.8.0
            echo pre-commit==3.6.2
            echo pytest==8.3.2
        )
    )
    pip install -r "%REQUIREMENTS%"
    exit /b %ERRORLEVEL%
)

if "%~1"=="test" (
    if exist "%SCRIPT_DIR%test_suite.py" (
        python "%SCRIPT_DIR%test_suite.py"
    ) else if exist "%SCRIPT_DIR%tests" (
        python -m pytest "%SCRIPT_DIR%tests" -v
    ) else (
        echo Error: No test suite found
        exit /b 1
    )
    exit /b %ERRORLEVEL%
)

if "%~1"=="dev" (
    if not exist "%MAIN_SCRIPT%" (
        echo Error: init.py not found
        exit /b 1
    )
    python "%MAIN_SCRIPT%" dev
    exit /b %ERRORLEVEL%
)

if "%~1"=="score" (
    if "%~2"=="" (
        echo Error: Missing URL_FILE argument for score command
        exit /b 1
    )
    if not exist "%MAIN_SCRIPT%" (
        echo Error: init.py not found
        exit /b 1
    )
    python "%MAIN_SCRIPT%" "%~2"
    exit /b %ERRORLEVEL%
)

REM Default: pass argument through (e.g. direct URL)
if not exist "%MAIN_SCRIPT%" (
    echo Error: init.py not found
    exit /b 1
)
python "%MAIN_SCRIPT%" "%~1"
exit /b %ERRORLEVEL%
