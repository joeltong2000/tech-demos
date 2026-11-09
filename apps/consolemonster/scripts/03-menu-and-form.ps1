# An interactive menu and a form from the same grammar.
# Show-ConsoleMenu runs a small app: sidebar, content pane, footer with live
# key hints. A menu item can open a page, a form, or run an action.
# Run with -FormOnly to show the standalone form (Read-ConsoleForm) instead.
# In redirected or non-interactive sessions the menu prints once and exits.
param(
    [switch] $FormOnly
)
Import-Module ConsoleMonster

$environments = @(
    [pscustomobject] @{ Name = 'Development'; Servers = 2; About = 'Safe to break' }
    [pscustomobject] @{ Name = 'Staging';     Servers = 3; About = 'Mirrors production' }
    [pscustomobject] @{ Name = 'Production';  Servers = 8; About = 'Change window required' }
)

# The form: every field type checked as you type, with a review page that
# shows the equivalent command before anything runs.
$form = New-ConsoleForm 'Restart service' -Command 'Restart-AppService' -SubmitText 'Restart' -Content {
    New-ConsoleField Environment 'Environment' -Type Select -Required -Choices $environments `
        -Display Name -CommandValue Name -Describe About -Badge { "$($_.Servers) servers" } `
        -ParameterName Environment
    New-ConsoleField Service 'Service' -Type Select -Required -Choices 'WebApi', 'Worker', 'Search', 'Reports' `
        -ParameterName Name
    New-ConsoleField Drain 'Drain connections first' -Type Toggle -Default $true -ParameterName Drain
    New-ConsoleField Reason 'Change reason' -Required -MinLength 5 -Placeholder 'Why this restart is needed' `
        -ParameterName Reason
}

if ($FormOnly) {
    $answers = Read-ConsoleForm $form
    if ($answers) {
        [pscustomobject] @{
            Environment = $answers.Environment
            Service     = $answers.Service
            Drain       = $answers.Drain
            Reason      = $answers.Reason
        } | Show-ConsoleTable -Title '[bold]Submitted (nothing really restarts)[/]'
    } else {
        Write-Host 'Cancelled.'
    }
    return
}

$menu = New-ConsoleMenu 'Service toolbox' -Subtitle 'demo — nothing really restarts' -Content {
    New-ConsoleMenuItem 'Environments' -Hotkey e -IconName List `
        -Description 'A read-only page rendered with the same widgets.' -Page {
        $environments | New-ConsoleTable -Property @(
            'Name'
            @{ Name = 'Servers'; Presenter = 'Number' }
            'About'
        ) -Border Minimal
    }
    New-ConsoleMenuItem 'Restart a service' -Hotkey r -IconName Run `
        -Description 'Opens the form; the review page shows the equivalent command.' `
        -Form $form -OnSubmit {
        $MenuContext.Toast("Would restart $($Values.Service) in $($Values.Environment)")
    }
    New-ConsoleMenuItem 'Current time' -Hotkey t -IconName Item `
        -Description 'A plain action: runs and shows a toast.' -Action {
        $MenuContext.Toast((Get-Date).ToString('u'))
    }
    New-ConsoleMenuItem -Separator
    New-ConsoleMenuItem 'Quit' -Exit
}

Show-ConsoleMenu $menu -Layout Shell -AppName 'ConsoleMonster service toolbox demo'
