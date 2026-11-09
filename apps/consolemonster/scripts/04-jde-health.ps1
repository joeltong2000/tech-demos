# A mock "JD Edwards EnterpriseOne server health" dashboard for a JDE admin:
# enterprise/HTML/AIS server status, job queue counts and UBE runs, replayed
# from data/jde-health.json. No real JDE connection, no credentials — every
# number comes from the JSON file.
param(
    # Seconds per replay tick; lower it to finish faster.
    [double] $TickSeconds = 0.5
)
Import-Module ConsoleMonster

$dataPath = Join-Path $PSScriptRoot '..' 'data' 'jde-health.json'
$data = Get-Content $dataPath -Raw | ConvertFrom-Json
$tickCount = $data.metrics.aisMs.Count

$dashboard = New-ConsoleDashboard -Title '[bold]JDE EnterpriseOne · server health[/]' -Subtitle $data.environment -Content {
    New-ConsoleSummaryBar -WidgetId summary -Total $data.ubeJobs.Count -DoneLabel 'UBE runs' -Counter ([ordered] @{
        done = 0
        warnings = 0
        errors = 0
    })
    New-ConsoleColumns -Content {
        New-ConsolePanel -Title 'Servers' -Weight 1.2 -Content {
            New-ConsoleStatusList -WidgetId servers -Content {
                foreach ($server in $data.servers) {
                    [pscustomobject] @{ Key = $server.name; Label = "$($server.name) · $($server.type)"; Detail = $server.detail }
                }
            }
        }
        New-ConsolePanel -Title 'Job queues' -Weight 1 -Content {
            New-ConsoleRows -Content {
                New-ConsoleTable -WidgetId queues -Live -KeyProperty Queue -Border Minimal -NoSort -Property @(
                    'Queue'
                    @{ Name = 'Active'; Presenter = 'Number' }
                    @{ Name = 'Waiting'; Presenter = 'Number'; WarnAbove = 1 }
                    @{ Name = 'Max'; Presenter = 'Number' }
                )
                New-ConsoleRule
                New-ConsoleKeyValue -WidgetId facts -InputObject ([ordered] @{
                    'Interactive users' = '—'
                    'AIS response'      = '—'
                })
            }
        }
        New-ConsolePanel -Title 'AIS response (ms)' -Weight 1 -Content {
            New-ConsoleChart -WidgetId ais -Type Sparkline -Unit 'ms'
        }
    }
    New-ConsolePanel -Title 'UBE runs (Work with Submitted Jobs)' -Content {
        New-ConsoleTable -WidgetId ube -Live -KeyProperty Key -Border Minimal -MaxRows 7 -Property @(
            @{ Name = 'Job' }
            @{ Name = 'Version' }
            @{ Name = 'User' }
            @{ Name = 'Queue' }
            @{ Name = 'Status'; Presenter = 'Status' }
        )
    }
    New-ConsolePanel -Title 'Server log' -Fill -Content { New-ConsoleLogRegion -Height 6 }
}

Invoke-ConsoleDashboard $dashboard {
    $data = $using:data
    $tickSeconds = $using:TickSeconds
    $tickCount = $using:tickCount

    foreach ($server in $data.servers) {
        Update-Console servers -Key $server.name -Status Pass -Detail $server.detail
    }
    Write-ConsoleLogEntry "Connected to mock health feed for $($data.environment)"

    $counters = [ordered] @{ done = 0; warnings = 0; errors = 0 }
    for ($tick = 0; $tick -lt $tickCount; $tick++) {
        # Server status changes scheduled for this tick.
        foreach ($event in @($data.serverEvents | Where-Object tick -EQ $tick)) {
            Update-Console servers -Key $event.server -Status $event.status -Detail $event.detail
            Write-ConsoleLogEntry $event.log -Level $event.level
        }

        # UBE job lifecycle: submitted -> processing -> done/warn/error.
        foreach ($job in $data.ubeJobs) {
            $key = "$($job.job)/$($job.version)/$($job.submitTick)"
            $row = [ordered] @{ Key = $key; Job = $job.job; Version = $job.version; User = $job.user; Queue = $job.queue }
            if ($tick -eq $job.submitTick) {
                $row.Status = 'Pending'
                Update-Console ube -Row ([pscustomobject] $row)
                Write-ConsoleLogEntry "$($job.user) submitted $($job.job) $($job.version) to $($job.queue)"
            } elseif ($tick -eq $job.startTick) {
                $row.Status = 'Running'
                Update-Console ube -Row ([pscustomobject] $row)
            } elseif ($tick -eq $job.endTick) {
                $row.Status = $job.outcome
                Update-Console ube -Row ([pscustomobject] $row)
                $level = switch ($job.outcome) { 'Warn' { 'warn' } 'Fail' { 'error' } default { 'info' } }
                Write-ConsoleLogEntry "$($job.job) $($job.version): $($job.note)" -Level $level
                $counters.done++
                if ($job.outcome -eq 'Warn') { $counters.warnings++ }
                if ($job.outcome -eq 'Fail') { $counters.errors++ }
                Update-Console summary -Value $counters.done -Counter $counters
            }
        }

        # Queue depths derived from the same job schedule.
        foreach ($queue in $data.queues) {
            $active  = @($data.ubeJobs | Where-Object { $_.queue -eq $queue.name -and $_.startTick -le $tick -and $_.endTick -gt $tick }).Count
            $waiting = @($data.ubeJobs | Where-Object { $_.queue -eq $queue.name -and $_.submitTick -le $tick -and $_.startTick -gt $tick }).Count
            Update-Console queues -Row ([pscustomobject] @{ Queue = $queue.name; Active = $active; Waiting = $waiting; Max = $queue.maxJobs })
        }

        # Metrics sampled once per tick.
        Update-Console ais -Append -Value $data.metrics.aisMs[$tick]
        Update-Console facts -Key 'Interactive users' -Value $data.metrics.users[$tick]
        Update-Console facts -Key 'AIS response' -Value "$($data.metrics.aisMs[$tick]) ms"

        Wait-ConsoleDashboard $tickSeconds
    }
    Write-ConsoleLogEntry "Replay finished: $($counters.done) UBE runs, $($counters.warnings) warning(s), $($counters.errors) error(s)"
    Wait-ConsoleDashboard ($tickSeconds * 2)
}

# A scrollback summary a reviewer can read after the dashboard closes.
$data.ubeJobs | Show-ConsoleTable -Title '[bold]UBE run summary[/]' -Caption 'mock data from data/jde-health.json' -Property @(
    @{ Name = 'job'; Header = 'Job'; Key = $true }
    @{ Name = 'version'; Header = 'Version' }
    @{ Name = 'user'; Header = 'User' }
    @{ Name = 'queue'; Header = 'Queue' }
    @{ Name = 'outcome'; Header = 'Outcome'; Presenter = 'Status' }
    @{ Name = 'note'; Header = 'Note' }
)
