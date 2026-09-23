[CmdletBinding()]
param(
    [string]$WheelPath
)

$ErrorActionPreference = "Stop"

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

$existingBaduk = Get-Command baduk -ErrorAction SilentlyContinue
if ($existingBaduk) {
    if ($existingBaduk.CommandType -notin @("Application", "ExternalScript") -or -not $existingBaduk.Path) {
        throw "기존 baduk 명령을 보존했습니다. 명령 유형을 확인하세요: $($existingBaduk.CommandType)"
    }
    $existingPath = [System.IO.Path]::GetFullPath($existingBaduk.Path)
    $toolBinPrefix = $toolBin.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $isUvToolCommand = $existingPath.StartsWith($toolBinPrefix, [System.StringComparison]::OrdinalIgnoreCase)
    $installedTools = (& uv tool list | Out-String)
    if (-not $isUvToolCommand -or $installedTools -notmatch "(?m)^llm-baduk(?:\s|$)") {
        throw "기존 baduk 명령을 보존했습니다. 다른 명령 이름을 사용하려면 설치 대상을 수정하세요: $existingPath"
    }
}

& uv tool install --force --reinstall-package llm-baduk $installTarget
if ($LASTEXITCODE -ne 0) {
    throw "uv tool install이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

& uv tool update-shell
if ($LASTEXITCODE -ne 0) {
    throw "baduk 실행 경로 등록이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

$badukExecutable = Join-Path $toolBin "baduk.exe"
if (-not (Test-Path -LiteralPath $badukExecutable -PathType Leaf)) {
    $badukExecutable = Join-Path $toolBin "baduk"
}
if (-not (Test-Path -LiteralPath $badukExecutable -PathType Leaf)) {
    throw "설치된 baduk 실행 파일을 찾지 못했습니다: $toolBin"
}
& $badukExecutable --help
if ($LASTEXITCODE -ne 0) {
    throw "설치된 baduk --help 검증이 종료 코드 $LASTEXITCODE로 실패했습니다."
}

Write-Host "설치가 완료되었습니다: $badukExecutable"
Write-Host "소스 또는 wheel에서 설치했습니다: $installTarget"
Write-Host "새 터미널에서 baduk start를 실행하세요."
