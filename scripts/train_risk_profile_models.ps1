param(
  [string]$ArtifactVersion = "v1",
  [switch]$Download
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $RepoRoot "ml")

$Arguments = @("-m", "ml.train", "--artifact-version", $ArtifactVersion)
if ($Download) {
  $Arguments += "--download"
}

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
