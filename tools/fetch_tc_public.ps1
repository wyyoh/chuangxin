$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$RawDir = Join-Path $Root "data\raw"
$OutDir = Join-Path $Root "data"
$Archive = Join-Path $RawDir "tc_public.rar"
$Url = "https://cpipc.acge.org.cn/sysFile/downFile.do?fileId=b73864c9391847ec94e208ab7f3ee5cc"

New-Item -ItemType Directory -Force $RawDir | Out-Null

if (-not (Test-Path $Archive)) {
    Write-Output "Downloading public cases..."
    try {
        Invoke-WebRequest -Uri $Url -OutFile $Archive -UseBasicParsing -TimeoutSec 120
    } catch {
        Write-Error "Download failed. Put tc_public.rar at $Archive and rerun. Error: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Output "Using existing archive: $Archive"
}

if (Test-Path (Join-Path $OutDir "tc_public")) {
    Remove-Item -LiteralPath (Join-Path $OutDir "tc_public") -Recurse -Force
}

Write-Output "Extracting archive..."
tar -xf $Archive -C $OutDir

$Cases = Get-ChildItem -Path (Join-Path $OutDir "tc_public") -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName "input.blif") }
$Count = @($Cases).Count
Write-Output "Found $Count public cases."
if ($Count -ne 30) {
    Write-Error "Expected 30 public cases, found $Count"
    exit 1
}

