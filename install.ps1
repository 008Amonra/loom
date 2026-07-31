# 45dgof8 Agent Services — Windows installer
# Usage: curl -fsSL https://008amonra.github.io/loom/install.ps1 | powershell -c -

$Host.UI.RawUI.ForegroundColor = "Green"
Write-Host "45dgof8 Agent Services — installing for Windows"
Write-Host ""

# ── 1. Install opencode ──
if (Get-Command opencode -ErrorAction SilentlyContinue) {
    Write-Host "✓ opencode already installed"
} else {
    Write-Host "→ Installing opencode..."
    $installScript = Invoke-WebRequest -Uri "https://opencode.ai/install.ps1" -UseBasicParsing
    Invoke-Expression $installScript.Content
    $env:Path += ";$env:USERPROFILE\.opencode\bin"
    [Environment]::SetEnvironmentVariable("Path", $env:Path, [EnvironmentVariableTarget]::User)
    Write-Host "✓ opencode installed"
}

# ── 2. Configure opencode ──
$configDir = "$env:USERPROFILE\.config\opencode"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

Write-Host ""
Write-Host "Select AI provider:"
Write-Host "  0) LM Studio (local, free — needs LM Studio running)"
Write-Host "  1) Anthropic Claude (needs API key)"
Write-Host "  2) OpenAI GPT (needs API key)"
Write-Host "  3) Custom (OpenAI-compatible)"
$choice = Read-Host "Choice [0]"
if (-not $choice) { $choice = "0" }

switch ($choice) {
    "1" {
        $key = Read-Host -AsSecureString "Enter your Anthropic API key (sk-...)"
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
        $config = @"
{
  `"`$schema`": `"https://opencode.ai/config.json`",
  `"provider`": {
    `"anthropic`": {
      `"name`": `"Anthropic Claude`",
      `"apiKey`": `"$plain`"
    }
  }
}
"@
    }
    "2" {
        $key = Read-Host -AsSecureString "Enter your OpenAI API key"
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
        $config = @"
{
  `"`$schema`": `"https://opencode.ai/config.json`",
  `"provider`": {
    `"openai`": {
      `"name`": `"OpenAI`",
      `"apiKey`": `"$plain`"
    }
  }
}
"@
    }
    "3" {
        $name = Read-Host "Custom provider name"
        $url = Read-Host "Base URL"
        $key = Read-Host "API key (leave blank if none)"
        $config = @"
{
  `"`$schema`": `"https://opencode.ai/config.json`",
  `"provider`": {
    `"custom`": {
      `"name`": `"$name`",
      `"options`": {
        `"baseURL`": `"$url`",
        `"apiKey`": `"$key`"
      }
    }
  }
}
"@
    }
    default {
        $config = @"
{
  `"`$schema`": `"https://opencode.ai/config.json`",
  `"provider`": {
    `"lmstudio`": {
      `"npm`": `"@ai-sdk/openai-compatible`",
      `"name`": `"LM Studio (Local)`",
      `"options`": {
        `"baseURL`": `"http://127.0.0.1:1234/v1`",
        `"apiKey`": `"not-needed`"
      }
    }
  }
}
"@
        Write-Host "  Note: Make sure LM Studio is running on port 1234"
    }
}

Set-Content -Path "$configDir\opencode.json" -Value $config
Write-Host "✓ opencode configured"

# ── 3. Install voice-assistant (blind + deaf local assistant) ──
$binDir = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null
$vaPath = "$binDir\voice-assistant"
if (Test-Path $vaPath) {
    Write-Host "✓ voice-assistant already installed"
} else {
    Write-Host "→ Installing voice-assistant (blind + deaf local assistant)..."
    try {
        Invoke-WebRequest -Uri "https://008amonra.github.io/loom/voice-assistant" -OutFile $vaPath -UseBasicParsing
        Write-Host "✓ voice-assistant installed"
    } catch {
        Write-Host "✗ voice-assistant download failed — try manually:"
        Write-Host "    curl -fsSL https://008amonra.github.io/loom/voice-assistant -o $vaPath"
    }
}
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", [EnvironmentVariableTarget]::User)
}

# ── 4. Create project directory ──
$projectDir = "$env:USERPROFILE\45dgof8-agent"
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null
Write-Host "✓ project directory: $projectDir"

# ── 5. Welcome ──
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "  45dgof8 Agent Services — installed   "
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""
Write-Host "  Next steps:"
Write-Host "    1. Open a NEW PowerShell window"
Write-Host "    2. cd $projectDir"
Write-Host "    3. opencode"
Write-Host ""
Write-Host "  Commands:"
Write-Host "    python $vaPath   — blind + deaf assistant (opens in browser)"
Write-Host ""
