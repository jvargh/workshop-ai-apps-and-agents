[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)]
    [string]$LabPath,

    [Parameter(Position = 1)]
    [string]$Script,

    [switch]$Install,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$ScriptArguments
)

$ErrorActionPreference = "Stop"

$environmentPath = Join-Path $PSScriptRoot ".labenv"
$python = Join-Path $environmentPath "Scripts\python.exe"
$activate = Join-Path $environmentPath "Scripts\Activate.ps1"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    $bootstrapPython = Get-Command "python" -ErrorAction SilentlyContinue
    if (-not $bootstrapPython) {
        $bootstrapPython = Get-Command "py" -ErrorAction SilentlyContinue
    }

    if (-not $bootstrapPython) {
        throw "Python was not found on PATH. Install Python before running this script."
    }

    Write-Host "Creating shared Python environment at $environmentPath"
    & $bootstrapPython.Source -m venv $environmentPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the shared Python environment."
    }
}

if (-not (Test-Path -LiteralPath $activate -PathType Leaf)) {
    throw "Virtual environment activation script not found: $activate"
}

. $activate

$labPath = if ([System.IO.Path]::IsPathRooted($LabPath)) {
    [System.IO.Path]::GetFullPath($LabPath)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $LabPath))
}

if (-not (Test-Path -LiteralPath $labPath -PathType Container)) {
    throw "Lab folder not found: $labPath"
}

if ($Install) {
    $requirements = Join-Path $labPath "requirements.txt"
    if (-not (Test-Path -LiteralPath $requirements -PathType Leaf)) {
        throw "Requirements file not found: $requirements"
    }

    & $python -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($Script) {
    $scriptPath = Join-Path $labPath $Script
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) {
        throw "Python script not found: $scriptPath"
    }
} else {
    $pythonFiles = @(Get-ChildItem -LiteralPath $labPath -Filter "*.py" -File)
    if ($pythonFiles.Count -eq 0) {
        throw "No Python scripts were found in $labPath"
    }

    if ($pythonFiles.Count -gt 1) {
        $names = $pythonFiles.Name -join ", "
        throw "More than one Python script was found: $names. Specify the script name as the second argument."
    }

    $scriptPath = $pythonFiles[0].FullName
}

Push-Location $labPath
try {
    & $python $scriptPath @ScriptArguments
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
