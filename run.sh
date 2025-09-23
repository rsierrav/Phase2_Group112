#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function show_usage {
    echo "Usage:"
    echo "  ./run.sh install               - Install dependencies"
    echo "  ./run.sh <URL_FILE>            - Process URLs from file"
    echo "  ./run.sh dev                   - Run all input files"
    echo "  ./run.sh test                  - Run test suite"
    exit 1
}

function install_dependencies {
    echo "Installing dependencies..."

    REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

    if [ ! -f "$REQUIREMENTS" ]; then
        cat <<EOL > "$REQUIREMENTS"
requests>=2.25.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
python-dateutil>=2.8.0
urllib3>=1.26.0
GitPython>=3.1.0
PyGithub>=1.55.0
huggingface-hub>=0.10.0
flake8==7.0.0
black==24.8.0
pre-commit==3.6.2
pytest==8.3.2
EOL
    fi

    if command -v pip3 >/dev/null 2>&1; then
        pip3 install -r "$REQUIREMENTS"
    elif command -v pip >/dev/null 2>&1; then
        pip install -r "$REQUIREMENTS"
    else
        echo "Error: pip or pip3 not found"
        exit 1
    fi

    echo "Dependencies installed successfully"
    exit 0
}

function run_tests {
    echo "Running test suite..."

    TEST_SUITE="$SCRIPT_DIR/test_suite.py"
    TESTS="$SCRIPT_DIR/tests"

    if [ -f "$TEST_SUITE" ]; then
        python "$TEST_SUITE"
    elif [ -d "$TESTS" ]; then
        python -m pytest "$TESTS" -v
    else
        echo "Error: No test suite found"
        exit 1
    fi

    echo "All tests passed"
    exit 0
}

function process_urls {
    URL_FILE="$1"
    MAIN_SCRIPT="$SCRIPT_DIR/src/init.py"

    if [ ! -f "$MAIN_SCRIPT" ]; then
        echo "Error: init.py not found"
        exit 1
    fi

    python "$MAIN_SCRIPT" "$URL_FILE"
    exit $?
}

function process_local_files {
    MAIN_SCRIPT="$SCRIPT_DIR/src/init.py"

    if [ ! -f "$MAIN_SCRIPT" ]; then
        echo "Error: init.py not found"
        exit 1
    fi

    python "$MAIN_SCRIPT" "dev"
    exit $?
}

# Entry point
if [ $# -eq 0 ]; then
    show_usage
fi

case "$1" in
    install)
        install_dependencies
        ;;
    test)
        run_tests
        ;;
    dev)
        process_local_files
        ;;
    http://* | https://*)
        process_urls "$1"
        ;;
    *)
        echo "Error: URL_FILE must be an absolute URL (starting with 'http://' or 'https://')"
        exit 1
        ;;
esac

