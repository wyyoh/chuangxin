$ErrorActionPreference = "Continue"

Write-Output "CPIPC Problem 10 environment check"
Write-Output "Timestamp: $(Get-Date -Format o)"
Write-Output "PWD: $(Get-Location)"
Write-Output "OS: $([System.Environment]::OSVersion.VersionString)"
Write-Output "PowerShell: $($PSVersionTable.PSVersion)"
Write-Output ""

$cmds = @("python", "git", "gcc", "make", "mingw32-make", "cmake", "curl", "tar", "coderabbit")
foreach ($cmd in $cmds) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        Write-Output "${cmd}: $($found.Source)"
        try {
            if ($cmd -eq "python") { & $found.Source --version }
            elseif ($cmd -eq "git") { & $found.Source --version }
            elseif ($cmd -eq "gcc") { & $found.Source --version | Select-Object -First 1 }
            elseif ($cmd -eq "mingw32-make") { & $found.Source --version | Select-Object -First 1 }
            elseif ($cmd -eq "cmake") { & $found.Source --version | Select-Object -First 1 }
            elseif ($cmd -eq "coderabbit") { & $found.Source --version }
        } catch {
            Write-Output "  version check failed: $($_.Exception.Message)"
        }
    } else {
        Write-Output "${cmd}: NOT FOUND"
    }
}

Write-Output ""
Write-Output "Python module quick check:"
@'
mods = ["yaml", "openpyxl", "psutil"]
for mod in mods:
    try:
        __import__(mod)
        print(f"{mod}: available")
    except Exception as exc:
        print(f"{mod}: missing ({exc.__class__.__name__})")
'@ | python -
