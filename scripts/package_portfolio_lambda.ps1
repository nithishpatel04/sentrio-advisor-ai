$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$lambdaDirectory = Join-Path $projectRoot "portfolio-api"
$zipPath = Join-Path $lambdaDirectory "portfolio-lambda.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Push-Location $lambdaDirectory
try {
    Compress-Archive -Path "lambda_function.py", "lambda_data" -DestinationPath $zipPath
}
finally {
    Pop-Location
}