$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$lambdaDirectory = Join-Path $projectRoot "briefing-service"
$lambdaFile = Join-Path $lambdaDirectory "lambda_function.py"
$rulesFile = Join-Path $lambdaDirectory "rules.py"
$aiInputFile = Join-Path $lambdaDirectory "ai_input.py"
$schemaFile = Join-Path $lambdaDirectory "briefing_schema.py"
$promptBuilderFile = Join-Path $lambdaDirectory "prompt_builder.py"
$bedrockClientFile = Join-Path $lambdaDirectory "bedrock_client.py"
$validatorFile = Join-Path $lambdaDirectory "briefing_validator.py"
$zipPath = Join-Path $lambdaDirectory "briefing-lambda.zip"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path $lambdaFile, $rulesFile, $aiInputFile, $schemaFile, $promptBuilderFile, $bedrockClientFile, $validatorFile -DestinationPath $zipPath

$archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $entry = $archive.GetEntry("lambda_function.py")
    if ($null -eq $entry) {
        throw "The ZIP does not contain lambda_function.py at its root."
    }
    $rulesEntry = $archive.GetEntry("rules.py")
    if ($null -eq $rulesEntry) {
        throw "The ZIP does not contain rules.py at its root."
    }
    foreach ($name in @("ai_input.py", "briefing_schema.py", "prompt_builder.py", "bedrock_client.py", "briefing_validator.py")) {
        if ($null -eq $archive.GetEntry($name)) {
            throw "The ZIP does not contain $name at its root."
        }
    }
}
finally {
    $archive.Dispose()
}