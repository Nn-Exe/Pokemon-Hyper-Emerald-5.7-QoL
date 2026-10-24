# Runs test_paulgift.lua once in the scripting mGBA, muted and out of sight (..\..\..\_testrun\hidden.ps1), and
# stops only the emulator it started.
#   run.ps1 -Rom <rom.gba> -Tag new [-Out <folder>] [-Timeout 240]
# The ROM's .sav (same name) is the save it plays from. Logs and screenshots go to -Out (default: the game folder's
# _testrun\paulgift).
param([string]$Rom, [string]$Tag = "new", [string]$Out = "", [int]$Timeout = 240)
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$game = Resolve-Path (Join-Path $here "..\..\..")
. (Join-Path $game "_testrun\hidden.ps1")
if (-not $Out) { $Out = Join-Path $game "_testrun\paulgift" }
if (-not (Test-Path $Out)) { New-Item -ItemType Directory -Force $Out | Out-Null }
$mgba = "C:\Users\nonth\AppData\Local\Temp\mgba-dev\mGBA-build-2026-07-06-win64-9086-5157ce208a5965e8a47bf5b48b5aae5198c22a5e\mGBA.exe"
$done = Join-Path $Out ("paulgift_{0}_done.txt" -f $Tag)
$log = Join-Path $Out ("paulgift_{0}_log.txt" -f $Tag)
foreach ($f in @($done, $log)) { if (Test-Path $f) { Remove-Item $f -Confirm:$false } }
$env:SDL_AUDIODRIVER = "dummy"
$env:TAG = $Tag
$env:DIR = ($Out -replace "\\", "/") + "/"
$env:HERE = ($here -replace "\\", "/") + "/"
$lua = Join-Path $here "test_paulgift.lua"
$a = "-C mute=1 -C volume=0 -C fastForwardVolume=0 -C audioDriver=1 -C fpsTarget=2000 -C audioSync=0 -C videoSync=0 " +
     "-C pauseOnMinimize=0 -C pauseOnFocusLost=0 --script `"$lua`" `"$Rom`""
$p = Get-Process -Id (Start-Hidden $mgba $a $Out)
$sw = [Diagnostics.Stopwatch]::StartNew()
while (-not (Test-Path $done) -and $sw.Elapsed.TotalSeconds -lt $Timeout -and -not $p.HasExited) { Start-Sleep -Milliseconds 200 }
$state = "TIMEOUT"
if (Test-Path $done) { $state = "done" } elseif ($p.HasExited) { $state = "EMULATOR EXITED" }
Start-Sleep -Milliseconds 300
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Confirm:$false }
Close-Hidden
"{0}: {1} after {2:n0} s" -f $Tag, $state, $sw.Elapsed.TotalSeconds
if (Test-Path $log) { Get-Content $log }
