# Optional PowerShell client: same two calls as the Bun demo (sync, then
# fire-and-forget via "jde__jobQueue": "JDE__ASYNCH").
#
# Start the mock AIS server first in another terminal:
#   bun run mock          (listens on http://localhost:9208 by default)
# Then:
#   pwsh scripts/demo.ps1
#   pwsh scripts/demo.ps1 -BaseUrl https://real-ais:7078 -Username JDE -Password (Read-Host -AsSecureString ... )
param(
    [string]$BaseUrl = $(if ($env:AIS_BASE_URL) { $env:AIS_BASE_URL } else { "http://localhost:9208" }),
    [string]$Username = $(if ($env:AIS_USERNAME) { $env:AIS_USERNAME } else { "DEMO" }),
    [string]$Password = $(if ($env:AIS_PASSWORD) { $env:AIS_PASSWORD } else { "demo-only" }),
    [string]$Orchestration = "ORCH_DemoSlowLookup"
)

$ErrorActionPreference = "Stop"
$uri = "$BaseUrl/jderest/v3/orchestrator/$Orchestration"
$headers = @{
    Authorization            = "Basic " + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${Username}:${Password}"))
    "jde-AIS-MonitorRequest" = "monitorRequestIO"
}

function Invoke-Orchestration([hashtable]$Body, [string]$Label) {
    Write-Host "`n[$Label] POST $uri" -ForegroundColor Cyan
    Write-Host "  body: $($Body | ConvertTo-Json -Compress)"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    # Invoke-WebRequest (not Invoke-RestMethod) so we can show the HTTP status code.
    $response = Invoke-WebRequest -Method Post -Uri $uri -Headers $headers `
        -ContentType "application/json" -Body ($Body | ConvertTo-Json -Compress)
    $sw.Stop()
    Write-Host ("  -> HTTP {0} after {1:n0} ms" -f [int]$response.StatusCode, $sw.Elapsed.TotalMilliseconds) -ForegroundColor Green
    if ($response.Content) { Write-Host "  output: $($response.Content)" }
    else { Write-Host "  output: (empty — fire and forget)" }
    return $sw.Elapsed.TotalMilliseconds
}

$syncMs  = Invoke-Orchestration @{ orderNumber = "12345" } "1/2 synchronous"
$asyncMs = Invoke-Orchestration @{ orderNumber = "12345"; jde__jobQueue = "JDE__ASYNCH" } "2/2 JDE__ASYNCH"

Write-Host ("`nSync: {0:n0} ms (HTTP 200, full output)   Async: {1:n0} ms (HTTP 202, no output)" -f $syncMs, $asyncMs) -ForegroundColor Yellow
