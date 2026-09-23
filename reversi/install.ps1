[CmdletBinding()]
param(
    [string]$WheelPath,
    [ValidateSet("codex", "claude", "opencode")]
    [string[]]$Agent = @("codex")
)

$ErrorActionPreference = "Stop"
$skillName = "play-llm-reversi"
$packageName = "llm-reversi"
$skillMarkerOwner = "$packageName`:$skillName"

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
    $skillMarkerPath = Join-Path $skillsDirectory "$skillName.$packageName-managed"
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

$skillTargets = @()
foreach ($agentName in $Agent) {
    $skillTargets += _GetAgentSkillTarget -AgentName $agentName
}

$packageRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "."))
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv를 찾을 수 없습니다. https://docs.astral.sh/uv/의 설치 안내를 먼저 확인하세요."
}

$installTarget = $packageRoot
if ($WheelPath) {
    $wheelCandidate = if ([System.IO.Path]::IsPathRooted($WheelPath)) {
        $WheelPath
    } else {
        Join-Path (Get-Location) $WheelPath
    }
    $installTarget = [System.IO.Path]::GetFullPath($wheelCandidate)
    if (-not (Test-Path -LiteralPath $installTarget -PathType Leaf) -or
        [System.IO.Path]::GetExtension($installTarget) -ne ".whl") {
        throw "wheel 파일을 찾을 수 없습니다: $installTarget"
    }
}

$toolBin = (& uv tool dir --bin).Trim()
if ($LASTEXITCODE -ne 0 -or -not $toolBin) {
    throw "uv tool 실행 파일 폴더를 확인하지 못했습니다."
}
$toolBin = [System.IO.Path]::GetFullPath($toolBin)

$existingReversi = Get-Command reversi -ErrorAction SilentlyContinue
if ($existingReversi) {
    if ($existingReversi.CommandType -notin @("Application", "ExternalScript") -or -not $existingReversi.Path) {
        throw "기존 reversi 명령을 보존했습니다. 명령 유형을 확인하세요: $($existingReversi.CommandType)"
    }
    $existingPath = [System.IO.Path]::GetFullPath($existingReversi.Path)
    $toolBinPrefix = $toolBin.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $isUvToolCommand = $existingPath.StartsWith($toolBinPrefix, [System.StringComparison]::OrdinalIgnoreCase)
    $installedTools = (& uv tool list | Out-String)
    if (-not $isUvToolCommand -or $installedTools -notmatch "(?m)^llm-reversi(?:\s|$)") {
        throw "기존 reversi 명령을 보존했습니다. 기존 명령을 확인하세요: $existingPath"
    }
}

& uv tool install --force --reinstall-package llm-reversi $installTarget
if ($LASTEXITCODE -ne 0) {
    throw "uv tool install이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

& uv tool update-shell
if ($LASTEXITCODE -ne 0) {
    throw "reversi 실행 경로 등록이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

$reversiExecutable = Join-Path $toolBin "reversi.exe"
if (-not (Test-Path -LiteralPath $reversiExecutable -PathType Leaf)) {
    $reversiExecutable = Join-Path $toolBin "reversi"
}
if (-not (Test-Path -LiteralPath $reversiExecutable -PathType Leaf)) {
    throw "설치된 reversi 실행 파일을 찾지 못했습니다: $toolBin"
}
& $reversiExecutable --help
if ($LASTEXITCODE -ne 0) {
    throw "설치된 reversi --help 검증이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

if ($skillTargets.Count -gt 0) {
    $toolDirectory = (& uv tool dir).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $toolDirectory) {
        throw "uv tool 설치 환경 폴더를 확인하지 못했습니다."
    }
    $toolDirectory = [System.IO.Path]::GetFullPath($toolDirectory)
    $skillSource = Join-Path $toolDirectory "llm-reversi\Lib\site-packages\llm_reversi\skills\$skillName"
    foreach ($skillTarget in $skillTargets) {
        _InstallManagedSkill -SkillSource $skillSource -Target $skillTarget
    }
}

Write-Host "설치가 완료되었습니다: $reversiExecutable"
Write-Host "소스 또는 wheel에서 설치했습니다: $installTarget"
Write-Host "새 터미널에서 reversi start를 실행하세요."
