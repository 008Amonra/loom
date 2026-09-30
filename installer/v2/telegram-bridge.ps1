<#
.SYNOPSIS
    45dgof8 Telegram Bridge fuer Windows.

.DESCRIPTION
    Spricht mit dem lokalen opencode-Agenten ueber Telegram. Der Agent laeuft
    auf demselben Rechner, es geht nichts ueber fremde Server.

    Betriebsart poll (Standard): fragt Telegram ab. Braucht keine
    oeffentliche Adresse und funktioniert hinter Firewall und NAT.

    Betriebsart webhook: Telegram schickt Nachrichten an eine oeffentliche
    HTTPS-Adresse, die auf diesen Rechner weiterleitet. Nur sinnvoll, wenn
    bereits ein Tunnel existiert. Der HttpListener braucht dafuer eine
    einmalige elevated Freigabe (siehe -RegisterUrlAcl im Kommentar unten).

    WICHTIG: Der Bot-Token ist ein Fernzugriffsschluessel. Wer ihn besitzt,
    kann den Agenten anweisen, und der Agent handelt mit den Rechten dieses
    Benutzers. Wie einen SSH-Private-Key behandeln: nie ins Git, nie ins Log,
    nie in einen Screenshot.

    Zustand in %LOCALAPPDATA%\45dgof8\telegram-bridge\:
      config   mode, workdir, opencode_bin
      token    Bot-Token. Wie einen SSH-Key behandeln.
      owner    Telegram-User-ID des ersten privaten Absenders
      offset   letzter verarbeiteter Poll-Stand
      session  opencode Session-ID, damit der Gedaechtnisstand bleibt
      bridge.log
#>

[CmdletBinding()]
param(
    [switch]$Once,     # nur einen Poll-Durchlauf, danach beenden
    [switch]$Status    # Status ausgeben und beenden
)

$ErrorActionPreference = 'Stop'

$State = if ($env:45DGOF8_TELEGRAM_STATE) {
    $env:45DGOF8_TELEGRAM_STATE
} else {
    Join-Path $env:LOCALAPPDATA '45dgof8\telegram-bridge'
}
$ConfigFile = Join-Path $State 'config'
$TokenFile  = Join-Path $State 'token'
$OwnerFile  = Join-Path $State 'owner'
$OffsetFile = Join-Path $State 'offset'
$SessionFile = Join-Path $State 'session'
$LogFile    = Join-Path $State 'bridge.log'

$TgLimit       = 4000
$PollTimeout   = 25
$MaxRunSeconds = 1800

function Write-BridgeLog {
    param([string]$Message)
    $line = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    try {
        $dir = Split-Path $LogFile -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Add-Content -Path $LogFile -Value $line -Encoding UTF8
    } catch { }
    Write-Host $line
}

function Get-StateValue {
    param([string]$Path, [string]$Default = '')
    if (Test-Path $Path) {
        $v = (Get-Content $Path -Raw -Encoding UTF8)
        if ($null -ne $v) { return $v.Trim() }
    }
    return $Default
}

function Get-OrDefault {
    param($Value, $Default)
    if ($null -eq $Value) { return $Default }
    $s = [string]$Value
    if ($s.Trim() -eq '') { return $Default }
    return $s
}

function Set-StateValue {
    param([string]$Path, [string]$Value)
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    # Ohne BOM schreiben. Set-Content -Encoding UTF8 setzt unter Windows
    # PowerShell 5.1 ein BOM, und ein BOM im Token macht ihn unbrauchbar.
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $utf8NoBom)
    if ($Path -eq $TokenFile) {
        # Token-Datei: nur fuer diesen Benutzer lesbar
        try {
            $acl = Get-Acl $Path
            $acl.SetAccessRuleProtection($true, $false)
            $rule = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule `
                -ArgumentList $env:USERNAME, 'FullControl', 'Allow'
            $acl.SetAccessRule($rule)
            Set-Acl -Path $Path -AclObject $acl
        } catch { }
    }
}

function Get-BridgeConfig {
    $cfg = @{}
    if (Test-Path $ConfigFile) {
        foreach ($line in (Get-Content $ConfigFile -Encoding UTF8)) {
            $t = $line.Trim()
            if (-not $t -or $t.StartsWith('#')) { continue }
            $i = $t.IndexOf('=')
            if ($i -lt 1) { continue }
            $cfg[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim()
        }
    }
    return $cfg
}

function Find-Opencode {
    $cfg = Get-BridgeConfig
    if ($cfg['opencode_bin'] -and (Test-Path $cfg['opencode_bin'])) { return $cfg['opencode_bin'] }
    if ($env:45DGOF8_OPENCODE -and (Test-Path $env:45DGOF8_OPENCODE)) { return $env:45DGOF8_OPENCODE }
    foreach ($p in @(
        (Join-Path $env:USERPROFILE '.opencode\bin\opencode.exe'),
        (Join-Path $env:USERPROFILE '.opencode\bin\opencode')
    )) { if (Test-Path $p) { return $p } }
    $cmd = Get-Command opencode -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Get-WorkDir {
    $cfg = Get-BridgeConfig
    if ($cfg['workdir'] -and (Test-Path $cfg['workdir'])) { return $cfg['workdir'] }
    foreach ($p in @(
        (Join-Path $env:USERPROFILE '45dgof8-agent'),
        $env:USERPROFILE
    )) { if (Test-Path $p) { return $p } }
    return $env:USERPROFILE
}

function Invoke-TelegramApi {
    param([string]$Token, [string]$Method, [hashtable]$Params)
    $pairs = @()
    foreach ($k in $Params.Keys) {
        $pairs += ('{0}={1}' -f [uri]::EscapeDataString($k), [uri]::EscapeDataString([string]$Params[$k]))
    }
    $url = 'https://api.telegram.org/bot{0}/{1}?{2}' -f $Token, $Method, ($pairs -join '&')
    try {
        return Invoke-RestMethod -Uri $url -Method Get -TimeoutSec ($PollTimeout + 20)
    } catch {
        $code = $null
        try { $code = [int]$_.Exception.Response.StatusCode } catch { }
        $body = $_.ErrorDetails.Message
        if (-not $body) { $body = $_.Exception.Message }
        throw [pscustomobject]@{ StatusCode = $code; Body = $body }
    }
}

function Send-TelegramMessage {
    param([string]$Token, $ChatId, [string]$Text)
    if (-not $Text) { return }
    for ($i = 0; $i -lt $Text.Length; $i += $TgLimit) {
        $len = [Math]::Min($TgLimit, $Text.Length - $i)
        $chunk = $Text.Substring($i, $len)
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            try {
                Invoke-TelegramApi -Token $Token -Method 'sendMessage' -Params @{
                    chat_id = $ChatId; text = $chunk; disable_web_page_preview = 'true'
                } | Out-Null
                break
            } catch {
                Write-BridgeLog ("sendMessage fehlgeschlagen: {0}" -f $_.Body)
                Start-Sleep -Seconds (2 * $attempt)
            }
        }
    }
}

function Invoke-Opencode {
    param([string]$Text)
    $bin = Find-Opencode
    if (-not $bin) {
        return 'Ich finde das opencode-Binary nicht. Bitte opencode_bin in der config setzen.'
    }
    $wd  = Get-WorkDir
    $sid = Get-StateValue $SessionFile
    $ocArgs = @('run')
    if ($sid) { $ocArgs += @('-s', $sid) }
    $ocArgs += $Text

    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()
    try {
        $p = Start-Process -FilePath $bin -ArgumentList $ocArgs -WorkingDirectory $wd `
             -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        if (-not $p.WaitForExit($MaxRunSeconds * 1000)) {
            try { $p.Kill() } catch { }
            return 'Das hat zu lange gedauert, ich habe abgebrochen.'
        }
        $out = (Get-Content $outFile -Raw -Encoding UTF8)
        $err = (Get-Content $errFile -Raw -Encoding UTF8)
        if ($p.ExitCode -ne 0) {
            $tail = ($err -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -Last 1)
            if (-not $tail) { $tail = 'unbekannter Fehler' }
            Write-BridgeLog "opencode run fehlgeschlagen: $tail"
            return ("Fehler beim Antworten: {0}" -f $tail.Substring(0, [Math]::Min(600, $tail.Length)))
        }
        $out = $out.Trim()
        if (-not $out) { return '(leere Antwort)' }
        return $out
    } finally {
        Remove-Item $outFile, $errFile -Force -ErrorAction SilentlyContinue
    }
}

function Set-OpencodeSession {
    $bin = Find-Opencode
    if (-not $bin) { return }
    if (Get-StateValue $SessionFile) { return }
    try {
        $listing = & $bin session list 2>$null
        if ($listing -and $listing.Count -gt 0) {
            $sid = ($listing[0] -split '\s+')[0]
            if ($sid.Length -gt 8) {
                Set-StateValue $SessionFile $sid
                Write-BridgeLog "Session gesetzt: $sid"
            }
        }
    } catch { }
}

$HelpText = @"
Schreib mir einfach deine Frage, ich leite sie an den lokalen Agenten weiter.

Befehle:
/stand  Status der Bruecke
/neu    Neue Unterhaltung, Gedaechtnis weg
/hilfe  Diese Liste
"@

function Invoke-Message {
    param([string]$Token, $Message)
    $chat   = $Message.chat
    $sender = $Message.from
    $text   = if ($Message.text) { [string]$Message.text } else { '' }
    if (-not $text -or $chat.type -ne 'private') { return }

    $owner = Get-StateValue $OwnerFile
    if (-not $owner) {
        Set-StateValue $OwnerFile ([string]$sender.id)
        Write-BridgeLog 'Besitzer gesetzt'
        Send-TelegramMessage -Token $Token -ChatId $chat.id `
            -Text ("Bruecke aktiv. Du bist der Besitzer dieser Brueche.`n`n" + $HelpText)
        return
    }
    if ([string]$sender.id -ne $owner) {
        Write-BridgeLog 'Fremde Nachricht verworfen'
        return
    }

    $t = $text.Trim()
    if ($t.StartsWith('/')) {
        $cmd = ($t -split '\s+')[0].ToLower()
        if ($cmd -in @('/start', '/hilfe', '/help')) {
            Send-TelegramMessage -Token $Token -ChatId $chat.id -Text $HelpText; return
        }
        if ($cmd -eq '/stand') {
            Send-TelegramMessage -Token $Token -ChatId $chat.id -Text (
                "Bruecke laeuft (Modus poll). Session: " +
                (Get-OrDefault (Get-StateValue $SessionFile) 'noch keine')
            ); return
        }
        if ($cmd -eq '/neu') {
            if (Test-Path $SessionFile) { Remove-Item $SessionFile -Force }
            Send-TelegramMessage -Token $Token -ChatId $chat.id -Text 'Neue Unterhaltung. Was steht an?'
            return
        }
    }

    Write-BridgeLog ("Anfrage ({0} Zeichen): {1}" -f $t.Length, $t.Substring(0, [Math]::Min(140, $t.Length)))
    try { Send-TelegramMessage -Token $Token -ChatId $chat.id -Text 'Ich lese das und melde mich.' } catch { }
    $answer = Invoke-Opencode $t
    Set-OpencodeSession
    Send-TelegramMessage -Token $Token -ChatId $chat.id -Text $answer
    Write-BridgeLog 'Antwort gesendet'
}

# ---- main ------------------------------------------------------------------

if (-not (Test-Path $State)) {
    New-Item -ItemType Directory -Path $State -Force | Out-Null
}

$token = Get-StateValue $TokenFile
$bin   = Find-Opencode

if ($Status) {
    $scfg = Get-BridgeConfig
    Write-Host "State:    $State"
    Write-Host "Modus:    $(Get-OrDefault $scfg['mode'] 'poll')"
    Write-Host "Token:    $(if ($token) { 'gesetzt' } else { 'FEHLT' })"
    Write-Host "Besitzer: $(Get-OrDefault (Get-StateValue $OwnerFile) 'noch niemand')"
    Write-Host "Session:  $(Get-OrDefault (Get-StateValue $SessionFile) 'noch keine')"
    Write-Host "opencode: $(if ($bin) { $bin } else { 'NICHT GEFUNDEN' })"
    exit 0
}

if (-not $token) {
    Write-Host 'Kein Bot-Token. Datei anlegen:' -ForegroundColor Yellow
    Write-Host "  $TokenFile"
    Write-Host 'Inhalt: der Token von BotFather.'
    exit 2
}
if (-not $bin) {
    Write-Host 'opencode-Binary nicht gefunden.' -ForegroundColor Yellow
    exit 1
}

Write-BridgeLog 'Bruecke gestartet, Modus poll'
do {
    $offset = 0
    $ov = Get-StateValue $OffsetFile '0'
    if ($ov -match '^\d+$') { $offset = [int]$ov }
    $params = @{ timeout = $PollTimeout }
    if ($offset -gt 0) { $params['offset'] = $offset }

    try {
        $res = Invoke-TelegramApi -Token $token -Method 'getUpdates' -Params $params
    } catch {
        $code = $_.StatusCode
        if ($code -eq 409) {
            Write-BridgeLog 'getUpdates 409: ein Webhook ist aktiv oder ein zweiter Abfrager laeuft. 60s warten.'
            Start-Sleep -Seconds 60
        } elseif ($code -eq 401) {
            Write-BridgeLog 'getUpdates 401: Token ist ungueltig. 30s warten.'
            Start-Sleep -Seconds 30
        } else {
            Write-BridgeLog ("getUpdates Fehler: {0}" -f $_.Body)
            Start-Sleep -Seconds 15
        }
        continue
    }

    foreach ($u in $res.result) {
        Set-StateValue $OffsetFile ([string]([int]$u.update_id + 1))
        $m = $u.message
        if (-not $m) { $m = $u.edited_message }
        if ($m) { Invoke-Message -Token $token -Message $m }
    }
    Start-Sleep -Seconds 1
} while (-not $Once)

exit 0
