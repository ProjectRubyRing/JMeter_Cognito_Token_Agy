<#
.SYNOPSIS
    Generates JMeter 5.6.3 Test Plan (.jmx) from an OpenAPI Specification (YAML or JSON).
    Target OS: Windows 11 (PowerShell 5.1 / PowerShell 7+).

.DESCRIPTION
    This script automates the creation of JMeter 5.6.3 scenarios from OpenAPI definitions.
    Features:
    - Minimal Thread Group setting (1 thread, 1 loop, 1s ramp-up) to verify 1 request.
    - Default target endpoint: http://localhost:8080.
    - Random test data generation based on OpenAPI schema data types (string, integer, boolean, array, object).
    - Fixed header: X-API-KEY with initial default 'XXXXXXXXXXXX'.
    - Authentication flow: Obtains AWS Cognito Access Token first (Client Credentials grant), extracts
      access_token via JSON Extractor & RegEx Extractor into ${cognito_access_token}, and passes
      'Authorization: Bearer ${cognito_access_token}' to subsequent API Gateway calls.
    - Result reporting: JTL (results.jtl) and Log (jmeter.log) output, viewable in JMeter GUI.

.PARAMETER InputFile
    Path to the OpenAPI specification file (.yaml, .yml, or .json). Required.

.PARAMETER OutputFile
    Path to the output JMeter scenario (.jmx). Default is 'scenario.jmx'.

.PARAMETER HostName
    Target API server hostname or IP address. Default is 'localhost'.

.PARAMETER Port
    Target API server port. Default is 8080.

.PARAMETER Protocol
    Protocol to use (http or https). Default is 'http'.

.PARAMETER ApiKey
    Fixed X-API-KEY value. Default is 'XXXXXXXXXXXX'.

.PARAMETER CognitoTokenUrl
    Cognito OAuth2 Token Endpoint URL. Default is 'https://auth.example.com/oauth2/token'.

.PARAMETER CognitoClientId
    Cognito App Client ID. Default is 'your_cognito_client_id'.

.PARAMETER CognitoClientSecret
    Cognito App Client Secret. Default is 'your_cognito_client_secret'.

.PARAMETER CognitoScope
    OAuth2 Scopes. Default is 'api/read api/write'.

.PARAMETER JtlPath
    Path to write JTL results file. Default is 'results.jtl'.

.PARAMETER LogPath
    Path to write JMeter log file. Default is 'jmeter.log'.

.EXAMPLE
    .\generate_jmx_from_openapi.ps1 -InputFile sample_openapi.yaml -OutputFile my_test.jmx
    .\generate_jmx_from_openapi.ps1 -InputFile sample_openapi.json -HostName localhost -Port 8080 -ApiKey XXXXXXXXXXXX
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0, HelpMessage = "OpenAPI specification file (.yaml, .yml, or .json)")]
    [ValidateNotNullOrEmpty()]
    [string]$InputFile,

    [Parameter(Mandatory = $false)]
    [string]$OutputFile = "scenario.jmx",

    [Parameter(Mandatory = $false)]
    [string]$HostName = "localhost",

    [Parameter(Mandatory = $false)]
    [int]$Port = 8080,

    [Parameter(Mandatory = $false)]
    [ValidateSet("http", "https")]
    [string]$Protocol = "http",

    [Parameter(Mandatory = $false)]
    [string]$ApiKey = "XXXXXXXXXXXX",

    [Parameter(Mandatory = $false)]
    [string]$CognitoTokenUrl = "https://auth.example.com/oauth2/token",

    [Parameter(Mandatory = $false)]
    [string]$CognitoClientId = "your_cognito_client_id",

    [Parameter(Mandatory = $false)]
    [string]$CognitoClientSecret = "your_cognito_client_secret",

    [Parameter(Mandatory = $false)]
    [string]$CognitoScope = "api/read api/write",

    [Parameter(Mandatory = $false)]
    [string]$JtlPath = "results.jtl",

    [Parameter(Mandatory = $false)]
    [string]$LogPath = "jmeter.log"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Banner
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " OpenAPI to JMeter 5.6.3 Scenario Generator (Windows 11)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Resolve Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnginePath = Join-Path $ScriptDir "openapi_to_jmx.py"

if (-not (Test-Path $InputFile)) {
    Write-Error "[ERROR] Input OpenAPI specification file not found: $InputFile"
    exit 1
}

if (-not (Test-Path $EnginePath)) {
    Write-Error "[ERROR] Python conversion engine not found: $EnginePath"
    exit 1
}

# Check Python executable
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Error "[ERROR] Python 3 was not found in PATH. Please install Python 3.9+ on Windows 11."
    exit 1
}

# Display Configuration
Write-Host "Input File        : " -NoNewline; Write-Host $InputFile -ForegroundColor Yellow
Write-Host "Output JMX File   : " -NoNewline; Write-Host $OutputFile -ForegroundColor Yellow
Write-Host "Target Endpoint   : " -NoNewline; Write-Host "$($Protocol)://${HostName}:$Port" -ForegroundColor Yellow
Write-Host "Fixed X-API-KEY   : " -NoNewline; Write-Host $ApiKey -ForegroundColor Yellow
Write-Host "Cognito Token URL : " -NoNewline; Write-Host $CognitoTokenUrl -ForegroundColor Yellow
Write-Host "Results (JTL/Log) : " -NoNewline; Write-Host "$JtlPath / $LogPath" -ForegroundColor Yellow
Write-Host "Thread Group      : " -NoNewline; Write-Host "1 thread, 1 loop, 1s ramp-up (single request check)" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray

# Step 1: Run Python Engine
Write-Host "[1/3] Generating JMeter 5.6.3 test plan XML..." -ForegroundColor Green

& python "$EnginePath" `
    --input "$InputFile" `
    --output "$OutputFile" `
    --host "$HostName" `
    --port $Port `
    --protocol "$Protocol" `
    --api-key "$ApiKey" `
    --cognito-token-url "$CognitoTokenUrl" `
    --cognito-client-id "$CognitoClientId" `
    --cognito-client-secret "$CognitoClientSecret" `
    --cognito-scope "$CognitoScope" `
    --jtl "$JtlPath" `
    --log "$LogPath"

if ($LASTEXITCODE -ne 0) {
    Write-Error "[ERROR] Generator script failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

# Step 2: Validate Output XML
Write-Host "[2/3] Validating generated XML structure for JMeter 5.6.3..." -ForegroundColor Green
if (-not (Test-Path $OutputFile)) {
    Write-Error "[ERROR] Output file was not created: $OutputFile"
    exit 1
}

try {
    [xml]$XmlContent = Get-Content -Path $OutputFile -Raw -Encoding UTF8
    if ($XmlContent.jmeterTestPlan.jmeter -ne "5.6.3") {
        Write-Warning "JMeter version in XML is '$($XmlContent.jmeterTestPlan.jmeter)', expected '5.6.3'."
    } else {
        Write-Host "[VALID] JMeter 5.6.3 XML validated successfully!" -ForegroundColor Green
    }
} catch {
    Write-Error "[ERROR] Generated file is not valid XML: $_"
    exit 1
}

# Step 3: Instructions for Windows 11 Users
Write-Host "[3/3] Execution instructions:" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Successfully generated: $OutputFile" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host @"

[How to execute and inspect results on Windows 11]:

1. GUI Execution & Graphical Inspection (Recommended):
   - Start JMeter GUI by running 'jmeter.bat' (from your JMeter bin directory).
   - In JMeter GUI: Click [File] -> [Open] and select '$OutputFile'.
   - Click the green 'Start' button (or Ctrl+R) to execute the scenario.
   - Click 'View Results Tree' listener in the left tree.
   - Inspect the request and response data for:
       00_Cognito_Token_Acquisition (Extracts `$cognito_access_token)
       Subsequent API calls with Authorization: Bearer `$cognito_access_token
   - You can also click 'Browse...' in View Results Tree and select '$JtlPath' to load historical test results.

2. Non-GUI (CLI) Execution (Recommended for automated tests):
   jmeter -n -t $OutputFile -l $JtlPath -j $LogPath

3. Overriding Parameters via Command Line without editing the script:
   jmeter -n -t $OutputFile -JTARGET_HOST=localhost -JTARGET_PORT=8080 -JAPI_KEY=XXXXXXXXXXXX
"@ -ForegroundColor White
