<#
.SYNOPSIS
    Cai dat Claude Code Telegram Notification vao ~/.claude/ (toan cuc).
#>

$ErrorActionPreference = "Stop"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir  = Join-Path $env:USERPROFILE ".claude"
$ConfigFile = Join-Path $ClaudeDir "config.json"
$SettingsFile = Join-Path $ClaudeDir "settings.json"
$ScriptDst  = Join-Path $ClaudeDir "telegram_notify.py"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Claude Code - Telegram Notification  " -ForegroundColor Cyan
Write-Host "  Global Install -> $ClaudeDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiem tra thu muc ~/.claude ton tai
if (-not (Test-Path $ClaudeDir)) {
    Write-Host "[!] Khong tim thay $ClaudeDir" -ForegroundColor Red
    Write-Host "    Hay cai dat Claude Code truoc." -ForegroundColor Red
    exit 1
}

# ── Buoc 1: Nhap Bot Token va Chat ID ─────────────────────────────────────────
Write-Host "BUOC 1: Cau hinh Telegram Bot" -ForegroundColor Yellow
Write-Host "  - Lay bot token tu @BotFather tren Telegram"
Write-Host "  - Lay chat ID tu @userinfobot tren Telegram"
Write-Host ""

$BotToken = ""
$ChatId   = ""

# Doc tu config.json hien tai neu da co
if (Test-Path $ConfigFile) {
    try {
        $existingCfg = Get-Content $ConfigFile -Raw | ConvertFrom-Json
        $existingToken = $existingCfg.bot_token
        $existingChatId = $existingCfg.chat_id
        if ($existingToken -and $existingToken -notlike "*YOUR_*") {
            Write-Host "  Da co config.json voi bot_token hien tai." -ForegroundColor DarkYellow
            $keep = Read-Host "  Giu nguyen? (Y/n)"
            if ($keep -eq "" -or $keep -match "^[Yy]") {
                $BotToken = $existingToken
                $ChatId   = $existingChatId
                Write-Host "  [=] Giu nguyen config hien tai." -ForegroundColor DarkYellow
            }
        }
    } catch {}
}

if (-not $BotToken) {
    $BotToken = Read-Host "  Nhap Bot Token"
    $BotToken = $BotToken.Trim()
    if (-not $BotToken) {
        Write-Host "[!] Bot Token khong duoc de trong." -ForegroundColor Red
        exit 1
    }
    $ChatId = Read-Host "  Nhap Chat ID"
    $ChatId = $ChatId.Trim()
    if (-not $ChatId) {
        Write-Host "[!] Chat ID khong duoc de trong." -ForegroundColor Red
        exit 1
    }
}

# ── Buoc 2: Copy script ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "BUOC 2: Cai dat files" -ForegroundColor Yellow

Copy-Item -Path (Join-Path $ScriptDir "telegram_notify.py") -Destination $ScriptDst -Force
Write-Host "  [+] telegram_notify.py -> $ScriptDst" -ForegroundColor Green

# ── Buoc 3: Ghi config.json ───────────────────────────────────────────────────
$configContent = [ordered]@{
    bot_token = $BotToken
    chat_id   = $ChatId
}
$configContent | ConvertTo-Json | Set-Content $ConfigFile -Encoding UTF8
Write-Host "  [+] config.json -> $ConfigFile" -ForegroundColor Green

# ── Buoc 4: Merge hook vao settings.json ──────────────────────────────────────
# Dung duong dan tuyet doi de tranh van de bien moi truong
$hookCmd = "python `"$ScriptDst`""

if (Test-Path $SettingsFile) {
    $settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json

    # Kiem tra da co hook chua
    $hasHook = $false
    if ($settings.hooks -and $settings.hooks.Stop) {
        foreach ($grp in $settings.hooks.Stop) {
            foreach ($h in $grp.hooks) {
                if ($h.command -like "*telegram_notify*") { $hasHook = $true }
            }
        }
    }

    if ($hasHook) {
        Write-Host "  [=] settings.json da co Telegram hook - giu nguyen" -ForegroundColor DarkYellow
    } else {
        $newEntry = [PSCustomObject]@{
            hooks = @([PSCustomObject]@{
                type          = "command"
                command       = $hookCmd
                timeout       = 15
                statusMessage = "Sending Telegram notification..."
            })
        }

        if (-not $settings.hooks) {
            $settings | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{}) -Force
        }
        if ($settings.hooks.Stop) {
            $list = [System.Collections.ArrayList]@($settings.hooks.Stop)
            $list.Add($newEntry) | Out-Null
            $settings.hooks.Stop = $list.ToArray()
        } else {
            $settings.hooks | Add-Member -NotePropertyName "Stop" -NotePropertyValue @($newEntry) -Force
        }

        $settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
        Write-Host "  [+] Da them Telegram hook vao settings.json" -ForegroundColor Green
    }
} else {
    $newSettings = [PSCustomObject]@{
        hooks = [PSCustomObject]@{
            Stop = @([PSCustomObject]@{
                hooks = @([PSCustomObject]@{
                    type          = "command"
                    command       = $hookCmd
                    timeout       = 15
                    statusMessage = "Sending Telegram notification..."
                })
            })
        }
    }
    $newSettings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile -Encoding UTF8
    Write-Host "  [+] Da tao settings.json voi Telegram hook" -ForegroundColor Green
}

# ── Ket qua ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Cai dat hoan tat!                    " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Restart lai Claude Code de hook co hieu luc." -ForegroundColor Cyan
Write-Host ""

