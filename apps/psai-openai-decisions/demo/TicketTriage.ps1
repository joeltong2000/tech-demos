#Requires -Version 7.0
<#
.SYNOPSIS
    Pipes a batch of support tickets through PSAIOpenAIDecisions: a yes/no
    gate, multiple-choice routing, and ordered urgency scoring.
.DESCRIPTION
    Runs against a local mock of the OpenAI Decisions API by default (no key
    needed). Set PSAI_MODE=real and OPENAI_API_KEY to hit the real API.
    The endpoint redirect uses the module's own -Endpoint parameter via
    $PSDefaultParameterValues; the module itself is unmodified.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------- mode setup
$realMode = ($env:PSAI_MODE -eq 'real') -and -not [string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)
if ($realMode) {
    $endpoint = 'https://api.openai.com/v1/decisions'
} else {
    $port = if ($env:PSAI_MOCK_PORT) { $env:PSAI_MOCK_PORT } else { '4100' }
    $endpoint = if ($env:PSAI_DECISIONS_ENDPOINT) { $env:PSAI_DECISIONS_ENDPOINT } else { "http://127.0.0.1:$port/v1/decisions" }
    if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
        # The module refuses to run with an empty key; the mock accepts any value.
        $env:OPENAI_API_KEY = 'mock-key-no-credentials-needed'
    }
}

if (-not (Get-Module -ListAvailable -Name PSAIOpenAIDecisions)) {
    Write-Host 'Installing PSAIOpenAIDecisions from PowerShell Gallery (first run only)...' -ForegroundColor Yellow
    try { Install-PSResource -Name PSAIOpenAIDecisions -Scope CurrentUser -TrustRepository -Quiet }
    catch { Install-Module -Name PSAIOpenAIDecisions -Scope CurrentUser -Force -AllowClobber }
}
Import-Module PSAIOpenAIDecisions

# Pipeline commands (Test/Select/Get-*) call Invoke-OpenAIDecision internally
# without exposing -Endpoint. A caller-scope PSDefaultParameterValues entry is
# invisible to calls made inside the module, so set the default parameter
# value in the module's own session state instead. The module is unmodified.
& (Get-Module PSAIOpenAIDecisions) {
    param($Endpoint)
    $script:PSDefaultParameterValues = @{ 'Invoke-OpenAIDecision:Endpoint' = $Endpoint }
} $endpoint

function Write-Section([string]$Title) {
    Write-Host ''
    Write-Host "== $Title " -ForegroundColor Cyan -NoNewline
    Write-Host ('=' * [math]::Max(1, 68 - $Title.Length)) -ForegroundColor DarkCyan
}

try {
    $modeLabel = if ($realMode) { 'REAL (live OpenAI Decisions API)' } else { 'MOCK (local, offline, deterministic)' }
    Write-Host ''
    Write-Host 'PSAIOpenAIDecisions demo: support-ticket triage' -ForegroundColor Green
    Write-Host "  Mode     : $modeLabel"
    Write-Host "  Endpoint : $endpoint"

    $tickets = Import-Csv -Path (Join-Path $PSScriptRoot '..' 'data' 'tickets.csv') | ForEach-Object {
        [pscustomobject]@{
            Id      = $_.Id
            From    = $_.From
            Subject = $_.Subject
            Text    = '{0}. {1}' -f $_.Subject, $_.Body
        }
    }
    Write-Host "  Tickets  : $($tickets.Count) loaded from data/tickets.csv"

    # ------------------------------------------------- 1. one ticket, 3 shapes
    Write-Section 'One ticket, three question types in a single request'
    $questions = @(
        New-OpenAIYesNoQuestion -Name blocked -Question 'Is the customer blocked from using the product right now?'
        New-OpenAIDecisionQuestion -Type Choice -Name queue -Instructions 'Which team should handle this ticket?' -Choices @(
            @{ value = 'billing';   description = 'Charges, invoices, refunds, payments, or subscriptions' }
            @{ value = 'technical'; description = 'Errors, bugs, crashes, timeouts, or broken integrations' }
            @{ value = 'account';   description = 'Login, password, sign-in, or account access issues' }
        )
        New-OpenAIDecisionQuestion -Type Score -Name urgency -Instructions 'How urgent is this ticket?' -Levels 'Low', 'Medium', 'High', 'Critical'
    )
    $sample = $tickets[0]
    Write-Host "  [$($sample.Id)] $($sample.Subject)"
    $decision = Invoke-OpenAIDecision -Input $sample.Text -Question $questions -Endpoint $endpoint
    Write-Host ('    blocked : probability {0:p0}' -f $decision.blocked) -ForegroundColor Yellow
    Write-Host "    queue   : $($decision.queue)" -ForegroundColor Yellow
    Write-Host "    urgency : $($decision.urgency) of 3" -ForegroundColor Yellow

    # ------------------------------------------------------- 2. yes/no gate
    Write-Section 'Yes/no gate: Select-OpenAIDecision keeps blocked customers'
    $blocked = $tickets | Select-OpenAIDecision 'Is the customer completely blocked from working right now?' 0.7
    foreach ($ticket in $blocked) {
        Write-Host "  KEPT  [$($ticket.Id)] $($ticket.Subject)" -ForegroundColor Red
    }
    Write-Host "  -> $($blocked.Count) of $($tickets.Count) tickets pass the 0.7 probability threshold"

    # ------------------------------------------------ 3. multiple-choice route
    Write-Section 'Multiple choice: Get-OpenAIDecisionChoice routes every ticket'
    $queues = $tickets | Get-OpenAIDecisionChoice 'Which team should handle this ticket?' general billing technical account
    for ($i = 0; $i -lt $tickets.Count; $i++) {
        Write-Host ('  [{0}] -> {1,-9} {2}' -f $tickets[$i].Id, $queues[$i], $tickets[$i].Subject)
    }

    # --------------------------------------------------------- 4. scoring
    Write-Section 'Scoring: Get-OpenAIDecisionScore rates urgency on 4 levels'
    $levels = 'Low', 'Medium', 'High', 'Critical'
    $scores = $tickets | Get-OpenAIDecisionScore 'How urgent is this ticket?' Low Medium High Critical
    for ($i = 0; $i -lt $tickets.Count; $i++) {
        Write-Host ('  [{0}] -> {1} ({2})' -f $tickets[$i].Id, $scores[$i], $levels[[int]$scores[$i]])
    }

    # ------------------------------------------------------- triage board
    Write-Section 'Triage board (sorted by urgency)'
    $blockedIds = @($blocked | ForEach-Object Id)
    $board = for ($i = 0; $i -lt $tickets.Count; $i++) {
        [pscustomobject]@{
            Id      = $tickets[$i].Id
            Urgency = $levels[[int]$scores[$i]]
            Queue   = $queues[$i]
            Blocked = if ($blockedIds -contains $tickets[$i].Id) { 'YES' } else { '' }
            Subject = $tickets[$i].Subject
            Score   = $scores[$i]
        }
    }
    $board | Sort-Object Score -Descending | Format-Table Id, Urgency, Queue, Blocked, Subject -AutoSize | Out-String | Write-Host

    Write-Host 'Done: 3 decision shapes (predicate, choice, score) over the same pipeline.' -ForegroundColor Green
}
finally {
    & (Get-Module PSAIOpenAIDecisions) { $script:PSDefaultParameterValues = @{} }
}
