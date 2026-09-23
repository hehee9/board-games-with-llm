[CmdletBinding()]
param(
    [ValidateSet("codex", "claude", "opencode")]
    [string[]]$Agent = @("codex")
)

$ErrorActionPreference = "Stop"

function _GetAgentSkillTarget {
    param([string]$AgentName)

    switch ($AgentName.ToLowerInvariant()) {
        "codex" {
            $configDirectory = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
            $agentLabel = "Codex"
        }
        "claude" {
            $configDirectory = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".claude" }
            $agentLabel = "Claude Code"
        }
        "opencode" {
            $configDirectory = if ($env:OPENCODE_CONFIG_DIR) { $env:OPENCODE_CONFIG_DIR } else { Join-Path $env:USERPROFILE ".config\opencode" }
            $agentLabel = "OpenCode"
        }
    }

    $skillsDirectory = [System.IO.Path]::GetFullPath((Join-Path $configDirectory "skills"))
    $skillDestination = [System.IO.Path]::GetFullPath((Join-Path $skillsDirectory $skillName))
    $skillMarkerPath = Join-Path $skillsDirectory "$skillName.llm-chess-managed"
    $destinationParent = [System.IO.Directory]::GetParent($skillDestination).FullName
    if (-not [System.StringComparer]::OrdinalIgnoreCase.Equals($destinationParent, $skillsDirectory)) {
        throw "$agentLabel 스킬 대상 경로가 skills 폴더 밖을 가리킵니다: $skillDestination"
    }

    New-Item -ItemType Directory -Force -Path $skillsDirectory | Out-Null
    $hasSkillMarker = Test-Path -LiteralPath $skillMarkerPath -PathType Leaf
    if ($hasSkillMarker) {
        $existingSkillMarkerOwner = (Get-Content -LiteralPath $skillMarkerPath -Raw).Trim()
        if ($existingSkillMarkerOwner -ne $skillMarkerOwner) {
            throw "기존 $agentLabel 스킬 소유권 표시를 보존했습니다: $skillMarkerPath"
        }
    }

    if (Test-Path -LiteralPath $skillDestination) {
        if (-not $hasSkillMarker) {
            throw "기존 $agentLabel 스킬을 보존했습니다: $skillDestination"
        }

        $destinationItem = Get-Item -LiteralPath $skillDestination -Force
        if (-not $destinationItem.PSIsContainer -or
            ($destinationItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            throw "관리 대상 $agentLabel 스킬 경로가 일반 폴더가 아닙니다: $skillDestination"
        }
    }

    [pscustomobject]@{
        AgentLabel = $agentLabel
        SkillsDirectory = $skillsDirectory
        SkillDestination = $skillDestination
        SkillMarkerPath = $skillMarkerPath
        HasSkillMarker = $hasSkillMarker
    }
}

function _InstallManagedSkill {
    param(
        [string]$SkillSource,
        [pscustomobject]$Target
    )

    if (-not (Test-Path -LiteralPath (Join-Path $SkillSource "SKILL.md") -PathType Leaf) -or
        ($Target.AgentLabel -eq "Codex" -and -not (Test-Path -LiteralPath (Join-Path $SkillSource "agents\openai.yaml") -PathType Leaf))) {
        throw "$($Target.AgentLabel) 스킬 원본이 완전하지 않습니다: $SkillSource"
    }

    $installId = [System.Guid]::NewGuid().ToString("N")
    $stagingPath = Join-Path $Target.SkillsDirectory "$skillName.installing-$installId"
    $backupPath = Join-Path $Target.SkillsDirectory "$skillName.backup-$installId"
    $hadSkillDestination = Test-Path -LiteralPath $Target.SkillDestination
    $previousSkillMoved = $false
    $newSkillPlaced = $false
    $skillInstalled = $false

    try {
        Copy-Item -LiteralPath $SkillSource -Destination $stagingPath -Recurse
        if (-not (Test-Path -LiteralPath (Join-Path $stagingPath "SKILL.md") -PathType Leaf) -or
            ($Target.AgentLabel -eq "Codex" -and -not (Test-Path -LiteralPath (Join-Path $stagingPath "agents\openai.yaml") -PathType Leaf))) {
            throw "$($Target.AgentLabel) 스킬 복사본이 완전하지 않습니다: $stagingPath"
        }

        if (-not $Target.HasSkillMarker) {
            Set-Content -LiteralPath $Target.SkillMarkerPath -Value $skillMarkerOwner -Encoding ASCII
        }
        if ($hadSkillDestination) {
            Move-Item -LiteralPath $Target.SkillDestination -Destination $backupPath
            $previousSkillMoved = $true
        }
        Move-Item -LiteralPath $stagingPath -Destination $Target.SkillDestination
        $newSkillPlaced = $true
        $skillInstalled = $true
    } catch {
        if ($newSkillPlaced -and (Test-Path -LiteralPath $Target.SkillDestination)) {
            Remove-Item -LiteralPath $Target.SkillDestination -Recurse -Force
        }
        if ($previousSkillMoved -and (Test-Path -LiteralPath $backupPath)) {
            Move-Item -LiteralPath $backupPath -Destination $Target.SkillDestination
        }
        if (-not $Target.HasSkillMarker -and (Test-Path -LiteralPath $Target.SkillMarkerPath -PathType Leaf)) {
            Remove-Item -LiteralPath $Target.SkillMarkerPath -Force
        }
        throw
    } finally {
        if (Test-Path -LiteralPath $stagingPath) {
            Remove-Item -LiteralPath $stagingPath -Recurse -Force
        }
        if ($skillInstalled -and (Test-Path -LiteralPath $backupPath)) {
            Remove-Item -LiteralPath $backupPath -Recurse -Force
        }
    }

    Write-Host "$($Target.AgentLabel) 스킬이 설치되었습니다: $($Target.SkillDestination)"
}

$skillName = "play-llm-chess"
$skillMarkerOwner = "llm-chess:$skillName"
$packageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillTargets = @()
foreach ($agentName in $Agent) {
    $skillTargets += _GetAgentSkillTarget -AgentName $agentName
}

& uv tool install --python 3.13 --force --reinstall-package llm-chess $packageRoot
if ($LASTEXITCODE -ne 0) {
    throw "uv tool install failed with exit code $LASTEXITCODE"
}

$toolDirectory = (& uv tool dir).Trim()
if ($LASTEXITCODE -ne 0 -or -not $toolDirectory) {
    throw "uv tool 설치 환경 폴더를 확인하지 못했습니다."
}
$toolDirectory = [System.IO.Path]::GetFullPath($toolDirectory)
$skillSource = Join-Path $toolDirectory "llm-chess\Lib\site-packages\llm_chess\skills\$skillName"

$binDirectory = Join-Path $env:USERPROFILE "bin"
$chessExecutable = Join-Path $env:USERPROFILE ".local\bin\chess.exe"
$launcherPath = Join-Path $binDirectory "chess.exe"
$markerPath = Join-Path $binDirectory "chess.exe.llm-chess"
$legacyShimPath = Join-Path $binDirectory "chess.cmd"

New-Item -ItemType Directory -Force -Path $binDirectory | Out-Null
if ((Test-Path -LiteralPath $launcherPath) -and -not (Test-Path -LiteralPath $markerPath)) {
    throw "기존 chess.exe를 보존했습니다. 다른 명령 이름을 사용하려면 설치 스크립트를 수정하세요: $launcherPath"
}
Copy-Item -LiteralPath $chessExecutable -Destination $launcherPath -Force
Set-Content -LiteralPath $markerPath -Value "llm-chess launcher" -Encoding ASCII

if (Test-Path -LiteralPath $legacyShimPath) {
    $legacyShim = Get-Content -LiteralPath $legacyShimPath -Raw
    if ($legacyShim -match [regex]::Escape($chessExecutable)) {
        Remove-Item -LiteralPath $legacyShimPath -Force
    }
}

foreach ($skillTarget in $skillTargets) {
    _InstallManagedSkill -SkillSource $skillSource -Target $skillTarget
}

Write-Host "설치가 완료되었습니다: $launcherPath"
