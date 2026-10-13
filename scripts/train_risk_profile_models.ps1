param(
  [string]$ArtifactVersion = "v1",
  [switch]$Offline,
  [string[]]$PhivolcsCsv = @(),
  [string[]]$UsgsCsv = @()
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

$Arguments = @("-m", "ml.train", "--artifact-version", $ArtifactVersion)
if ($Offline) {
  $Arguments += "--offline"
}
foreach ($CsvPath in $PhivolcsCsv) {
  $Arguments += @("--phivolcs-csv", (Resolve-Path -LiteralPath $CsvPath).Path)
}
foreach ($CsvPath in $UsgsCsv) {
  $Arguments += @("--usgs-csv", (Resolve-Path -LiteralPath $CsvPath).Path)
}

Set-Location (Join-Path $RepoRoot "ml")

$PreviousPythonPath = $env:PYTHONPATH
if ([string]::IsNullOrWhiteSpace($PreviousPythonPath)) {
  $env:PYTHONPATH = "src"
} else {
  $env:PYTHONPATH = "src;$PreviousPythonPath"
}

$PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PythonLauncher) {
  & py -3.11 @Arguments
} else {
  & python @Arguments
}

exit $LASTEXITCODE
