# One-line tables from ordinary command output.
# Show-ConsoleTable fits columns to the window, right-aligns numbers and
# falls back to labelled cards when the window is too narrow.
Import-Module ConsoleMonster

# 1. Real command output, one line: the top processes on this machine right now.
Get-Process |
    Sort-Object WorkingSet64 -Descending |
    Select-Object -First 8 |
    Show-ConsoleTable -Title '[bold]Top processes by memory[/]' -NoSort -Property @(
        @{ Name = 'ProcessName'; Header = 'Process'; Key = $true }
        @{ Name = 'Id' }
        @{ Name = 'MemoryMB'; Header = 'Memory'; Expression = { [math]::Round($_.WorkingSet64 / 1MB, 1) }; Presenter = 'Number'; Unit = 'MB' }
        @{ Name = 'CPU'; Presenter = 'Number'; Unit = 's' }
    )

# 2. A sample service inventory: Status presenter, grouping and a caption.
#    (A fixed dataset so the demo renders the same on Linux and Windows;
#    on Windows you would pipe Get-Service straight in.)
$services = @(
    [pscustomobject] @{ Name = 'WebApi';   Site = 'Primary';  Status = 'Pass'; Restarts = 0; Memory = 412 }
    [pscustomobject] @{ Name = 'Worker';   Site = 'Primary';  Status = 'Pass'; Restarts = 1; Memory = 268 }
    [pscustomobject] @{ Name = 'Archive';  Site = 'Primary';  Status = 'Fail'; Restarts = 4; Memory = 0 }
    [pscustomobject] @{ Name = 'Search';   Site = 'Standby';  Status = 'Pass'; Restarts = 0; Memory = 931 }
    [pscustomobject] @{ Name = 'Reports';  Site = 'Standby';  Status = 'Warn'; Restarts = 2; Memory = 388 }
)
$services | Show-ConsoleTable -Title '[bold]Service inventory[/]' -GroupBy Site -ShowTotals -Caption 'sample data' -Property @(
    @{ Name = 'Name'; Key = $true }
    @{ Name = 'Status'; Presenter = 'Status' }
    @{ Name = 'Restarts'; Presenter = 'Number'; WarnAbove = 1 }
    @{ Name = 'Memory'; Presenter = 'Number'; Unit = 'MB' }
)
