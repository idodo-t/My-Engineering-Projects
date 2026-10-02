$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pythonProjects = @(
    'malware-detection',
    'nutrition-detection',
    'agentic-rag-assistant',
    'hotel-occupancy-forecast',
    'bi-etl-warehouse',
    'iot-dashboard',
    'linux-hardening'
)

foreach ($project in $pythonProjects) {
    $projectPath = Join-Path $repositoryRoot $project
    Write-Host "`n=== $project ===" -ForegroundColor Cyan
    Push-Location $projectPath
    try {
        python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) {
            throw "Python tests failed in $project."
        }
        python -m compileall -q .
        if ($LASTEXITCODE -ne 0) {
            throw "Python compilation failed in $project."
        }
    }
    finally {
        Pop-Location
    }
}

$apiProject = Join-Path $repositoryRoot 'medical-appointment-booking\MedicalAppointments.csproj'
Write-Host "`n=== medical-appointment-booking ===" -ForegroundColor Cyan
dotnet build $apiProject --nologo
if ($LASTEXITCODE -ne 0) {
    throw 'The .NET build failed.'
}

Write-Host "`nAll project checks passed." -ForegroundColor Green
