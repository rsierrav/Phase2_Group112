$SCRIPT_DIR = (Get-Location).Path

function show_usage {
    Write-Host "Usage:"
    Write-Host "  .\run.ps1 install               - Install dependencies"
    Write-Host "  .\run.ps1 <URL_FILE>            - Process URLs from file"
    Write-Host "  .\run.ps1 dev                   - Run all input files"
    Write-Host "  .\run.ps1 test                  - Run test suite"
    exit 1
}

function install_dependencies {
    Write-Host "Installing dependencies..."
    
    $requirementsPath = "$SCRIPT_DIR\requirements.txt"
    if (-not (Test-Path $requirementsPath)) {
        $content = @"
requests>=2.25.0
beautifulsoup4>=4.9.0
lxml>=4.6.0
python-dateutil>=2.8.0
urllib3>=1.26.0
GitPython>=3.1.0
PyGithub>=1.55.0
huggingface-hub>=0.10.0
"@
        $content | Out-File -FilePath $requirementsPath
    }
    
    if (Get-Command pip3 -ErrorAction SilentlyContinue) {
        pip3 install -r $requirementsPath
    } elseif (Get-Command pip -ErrorAction SilentlyContinue) {
        pip install -r $requirementsPath
    } else {
        Write-Host "Error: pip or pip3 not found"
        exit 1
    }
    
    Write-Host "Dependencies installed successfully"
    exit 0
}

function run_tests {
    Write-Host "Running test suite..."
    
    $testSuitePath = "$SCRIPT_DIR\test_suite.py"
    $testsPath = "$SCRIPT_DIR\tests"
    
    if (Test-Path $testSuitePath) {
        python $testSuitePath
    } elseif (Test-Path $testsPath) {
        python -m pytest $testsPath -v
    } else {
        Write-Host "Error: No test suite found"
        exit 1
    }
    
    Write-Host "All tests passed"
    exit 0
}

function process_urls {
    param([string]$url_file)
    
    $mainScriptPath = "$SCRIPT_DIR\src\init.py"
    if (-not (Test-Path $mainScriptPath)) {
        Write-Host "Error: init.py not found"
        exit 1
    }
    
    python $mainScriptPath $url_file
    exit $?
}

function process_local_files {
    param([string]$input_file)
    
    $mainScriptPath = "$SCRIPT_DIR\src\init.py"
    if (-not (Test-Path $mainScriptPath)) {
        Write-Host "Error: init.py not found"
        exit 1
    }
    
    python $mainScriptPath "dev"
    exit $?
}

if ($args.Count -eq 0) {
    show_usage
}

switch ($args[0]) {
    "install" { install_dependencies }
    "test" { run_tests }
    "dev" { process_local_files }
    default {
        $input = $args[0]
        
        if ($input -match "^https?://") {
            process_urls $input
        } else {
            Write-Host "Error: URL_FILE must be an absolute URL (starting with 'http:// or https://')"
            exit 1
        }
    }
}
