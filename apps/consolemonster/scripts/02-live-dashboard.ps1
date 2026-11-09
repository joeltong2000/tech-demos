# A live-updating dashboard: Invoke-ConsoleDashboard runs the worker script
# in its own runspace while the screen redraws ~15 times a second.
# Update-Console and Write-ConsoleLogEntry are the only update API you need;
# Write-Host lands in the log region instead of tearing the screen.
# All work is simulated so the demo runs anywhere and always tells the same story.
param(
    # Seconds between simulated work steps; lower it to finish faster.
    [double] $StepSeconds = 0.35
)
Import-Module ConsoleMonster

$files = @(
    @{ Name = 'orders.csv';    Rows = 1200; Outcome = 'Pass' }
    @{ Name = 'customers.csv'; Rows = 840;  Outcome = 'Pass' }
    @{ Name = 'invoices.csv';  Rows = 2050; Outcome = 'Warn' }
    @{ Name = 'payments.csv';  Rows = 640;  Outcome = 'Pass' }
    @{ Name = 'stock.csv';     Rows = 1530; Outcome = 'Fail' }
    @{ Name = 'shipping.csv';  Rows = 410;  Outcome = 'Pass' }
)

$dashboard = New-ConsoleDashboard -Title '[bold]Nightly import[/]' -Subtitle 'simulated data' -Content {
    New-ConsoleStatusList -Layout Strip -WidgetId phases -Content { 'Scan', 'Validate', 'Load', 'Report' }
    New-ConsoleColumns -Content {
        New-ConsolePanel -Title 'Progress' -Content {
            New-ConsoleProgress -WidgetId progress -Label 'Files' -Total 6
        }
        New-ConsolePanel -Title 'Rows per second' -Content {
            New-ConsoleChart -WidgetId rate -Type Sparkline -Unit '/s'
        }
    }
    New-ConsolePanel -Title 'Files' -Content {
        New-ConsoleTable -WidgetId files -Live -KeyProperty File -Border Minimal -Property @(
            'File'
            @{ Name = 'Rows'; Presenter = 'Number' }
            @{ Name = 'Status'; Presenter = 'Status' }
        )
    }
    New-ConsolePanel -Title 'Log' -Fill -Content { New-ConsoleLogRegion -Height 6 }
}

Invoke-ConsoleDashboard $dashboard {
    $files = $using:files
    $step = $using:StepSeconds
    $random = New-Object System.Random 42

    Update-Console phases -Key Scan -Status Running
    Write-ConsoleLogEntry 'Scanning the drop folder'
    Wait-ConsoleDashboard ($step * 2)
    Write-ConsoleLogEntry "Found $($files.Count) files"
    Update-Console phases -Key Scan -Status Pass -Detail "$($files.Count) files"

    Update-Console phases -Key Validate -Status Running
    foreach ($file in $files) {
        Update-Console files -Row ([pscustomobject] @{ File = $file.Name; Rows = $file.Rows; Status = 'Running' })
        Wait-ConsoleDashboard $step
        Update-Console files -Row ([pscustomobject] @{ File = $file.Name; Rows = $file.Rows; Status = 'Pending' })
    }
    Update-Console phases -Key Validate -Status Pass

    Update-Console phases -Key Load -Status Running
    $done = 0
    foreach ($file in $files) {
        Update-Console progress -Value $done -Label "Loading $($file.Name)"
        Update-Console files -Row ([pscustomobject] @{ File = $file.Name; Rows = $file.Rows; Status = 'Running' })
        Wait-ConsoleDashboard $step
        Update-Console rate -Append -Value ($random.Next(800, 2600))
        Update-Console files -Row ([pscustomobject] @{ File = $file.Name; Rows = $file.Rows; Status = $file.Outcome })
        switch ($file.Outcome) {
            'Warn' { Write-ConsoleLogEntry "$($file.Name): 3 rows had an unknown currency, defaulted to EUR" -Level warn }
            'Fail' { Write-ConsoleLogEntry "$($file.Name): 12 rows rejected (missing item number)" -Level error }
            default { Write-ConsoleLogEntry "$($file.Name): $($file.Rows) rows loaded" }
        }
        $done++
        Update-Console progress -Value $done -Label 'Files'
    }
    Update-Console phases -Key Load -Status Warn -Detail '1 file failed'

    Update-Console phases -Key Report -Status Running
    Write-ConsoleLogEntry 'Writing import report'
    Wait-ConsoleDashboard ($step * 2)
    Update-Console phases -Key Report -Status Pass
    Write-ConsoleLogEntry 'Done: 5 of 6 files imported'
    Wait-ConsoleDashboard ($step * 2)
}
