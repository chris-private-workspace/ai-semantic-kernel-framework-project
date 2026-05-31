<#
.SYNOPSIS
    Bootstrap the Claude Workflow Kit into a target project.

.DESCRIPTION
    Copies the generic sprint-workflow / CI / PR-template / lint-framework /
    claudedocs skeleton from kit/ into a target repository, then replaces all
    {{TOKEN}} placeholders with project-specific values.

    Two-layer principle: this kit carries ONLY the methodology layer. Project-
    specific content (domain rules, calibration history) must be added by hand
    after injection — see TEMPLATE-GUIDE.md sections 2 and 4.

.PARAMETER TargetPath
    Destination project root (must exist; should be a git repo).

.PARAMETER Force
    Overwrite files that already exist in the target. Default: skip existing
    files (so re-injection never clobbers your customized CLAUDE.md / rules).

.EXAMPLE
    .\init-workflow.ps1 -TargetPath "C:\code\my-new-project"

.EXAMPLE
    .\init-workflow.ps1 -TargetPath "C:\code\my-app" -ProjectName "my-app" `
        -PrimaryLanguage "TypeScript" -LintCmd "npm run lint" `
        -TypecheckCmd "tsc --noEmit" -TestCmd "npm test" -FormatCmd "prettier --write ."
#>
param(
    [Parameter(Mandatory = $true)][string]$TargetPath,
    [string]$ProjectName,
    [string]$ProjectDesc,
    [string]$PrimaryLanguage,
    [string]$FormatCmd,
    [string]$LintCmd,
    [string]$TypecheckCmd,
    [string]$TestCmd,
    [string]$DefaultBranch = "main",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# --- Resolve paths -----------------------------------------------------------
$KitRoot = Join-Path $PSScriptRoot "kit"
if (-not (Test-Path $KitRoot)) {
    throw "kit/ folder not found next to this script at: $KitRoot"
}
if (-not (Test-Path $TargetPath)) {
    throw "TargetPath does not exist: $TargetPath"
}
$TargetPath = (Resolve-Path $TargetPath).Path

# --- Prompt for missing required tokens (interactive) ------------------------
function Get-OrAsk([string]$value, [string]$prompt, [string]$default) {
    if ($value) { return $value }
    $answer = Read-Host "$prompt$([string]::IsNullOrEmpty($default) ? '' : " [$default]")"
    if ([string]::IsNullOrWhiteSpace($answer) -and $default) { return $default }
    return $answer
}

$ProjectName     = Get-OrAsk $ProjectName     "Project name"                    (Split-Path $TargetPath -Leaf)
$ProjectDesc     = Get-OrAsk $ProjectDesc     "One-line project description"    "TODO: describe this project"
$PrimaryLanguage = Get-OrAsk $PrimaryLanguage "Primary language (Python/TypeScript/Go/...)" "Python"
$FormatCmd       = Get-OrAsk $FormatCmd       "Format command"                  "black ."
$LintCmd         = Get-OrAsk $LintCmd         "Lint command"                    "flake8 src"
$TypecheckCmd    = Get-OrAsk $TypecheckCmd    "Type-check command"              "mypy src --strict"
$TestCmd         = Get-OrAsk $TestCmd         "Test command"                    "pytest"

$today = (Get-Date).ToString("yyyy-MM-dd")

$tokens = @{
    '{{PROJECT_NAME}}'     = $ProjectName
    '{{PROJECT_DESC}}'     = $ProjectDesc
    '{{PRIMARY_LANGUAGE}}' = $PrimaryLanguage
    '{{FORMAT_CMD}}'       = $FormatCmd
    '{{LINT_CMD}}'         = $LintCmd
    '{{TYPECHECK_CMD}}'    = $TypecheckCmd
    '{{TEST_CMD}}'         = $TestCmd
    '{{DEFAULT_BRANCH}}'   = $DefaultBranch
    '{{DATE}}'             = $today
}

# --- Copy + token-replace ----------------------------------------------------
$textExt = @('.md', '.py', '.json', '.yml', '.yaml', '.txt', '.ts', '.tsx', '.js')
$copied = 0; $skipped = 0; $replaced = 0

Get-ChildItem -Path $KitRoot -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($KitRoot.Length).TrimStart('\', '/')
    $dest = Join-Path $TargetPath $relative
    $destDir = Split-Path $dest -Parent

    if ((Test-Path $dest) -and (-not $Force)) {
        Write-Host "  skip (exists): $relative" -ForegroundColor DarkYellow
        $skipped++
        return
    }

    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    if ($textExt -contains $_.Extension.ToLower()) {
        $content = Get-Content -Raw -Encoding UTF8 $_.FullName
        foreach ($k in $tokens.Keys) {
            if ($content.Contains($k)) {
                $content = $content.Replace($k, $tokens[$k])
                $replaced++
            }
        }
        # Write UTF-8 without BOM
        [System.IO.File]::WriteAllText($dest, $content, [System.Text.UTF8Encoding]::new($false))
    }
    else {
        Copy-Item $_.FullName $dest -Force
    }
    Write-Host "  inject: $relative" -ForegroundColor Green
    $copied++
}

# --- Summary -----------------------------------------------------------------
Write-Host ""
Write-Host "Done. $copied file(s) injected, $skipped skipped (already existed), $replaced token-replacement(s)." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps (see TEMPLATE-GUIDE.md section 4):" -ForegroundColor Cyan
Write-Host "  1. Edit CLAUDE.md  -> fill Mission / tech stack / core constraints"
Write-Host "  2. Edit .claude/rules/anti-patterns-checklist.md -> add project-specific anti-patterns"
Write-Host "  3. Verify .github/workflows/ci.yml toolchain commands"
Write-Host "  4. On GitHub: add CI job names to branch protection required status checks"
Write-Host "  5. git add . && git commit -m 'chore(workflow): bootstrap sprint workflow kit'"
