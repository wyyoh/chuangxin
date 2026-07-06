param(
    [string]$AbcDir = "third_party\abc"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$AbsAbcDir = Join-Path $Root $AbcDir
if (-not (Test-Path $AbsAbcDir)) {
    Write-Error "ABC source directory not found: $AbsAbcDir"
    exit 1
}

Push-Location $AbsAbcDir
try {
    $gitUsrBin = "D:\Git\usr\bin"
    $gitBin = "D:\Git\bin"
    if (Test-Path $gitUsrBin) {
        $env:PATH = "$gitUsrBin;$gitBin;$env:PATH"
        $env:SHELL = "$gitUsrBin\bash.exe"
    }
    $make = Get-Command mingw32-make -ErrorAction SilentlyContinue
    if ($make) {
        Write-Output "Building ABC with mingw32-make..."
        & $make.Source -j 8 ABC_USE_NO_READLINE=1 ABC_USE_NO_CUDD=1 ABC_USE_NO_PTHREADS=1 ABC_USE_STDINT_H=1 ARCHFLAGS="-DABC_USE_STDINT_H=1 -DWIN32_NO_DLL=1" SHELL="D:/Git/usr/bin/bash.exe"
    } else {
        $make = Get-Command make -ErrorAction SilentlyContinue
        if (-not $make) {
            Write-Error "No make or mingw32-make found."
            exit 1
        }
        Write-Output "Building ABC with make..."
        & $make.Source -j 8 ABC_USE_NO_READLINE=1 ABC_USE_NO_CUDD=1 ABC_USE_NO_PTHREADS=1 ABC_USE_STDINT_H=1 ARCHFLAGS="-DABC_USE_STDINT_H=1 -DWIN32_NO_DLL=1"
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$ExeWin = Join-Path $AbsAbcDir "abc.exe"
$ExeUnix = Join-Path $AbsAbcDir "abc"
if (Test-Path $ExeWin) {
    Write-Output "ABC executable: $ExeWin"
} elseif (Test-Path $ExeUnix) {
    Write-Output "ABC executable: $ExeUnix"
} else {
    Write-Error "ABC build completed but executable was not found."
    exit 1
}
