param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)][string]$Message
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$icon = New-Object System.Windows.Forms.NotifyIcon
try {
    $icon.Icon = [System.Drawing.SystemIcons]::Information
    $icon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
    $icon.BalloonTipTitle = $Title
    $icon.BalloonTipText = $Message
    $icon.Visible = $true
    $icon.ShowBalloonTip(8000)
    Start-Sleep -Seconds 9
} finally {
    $icon.Dispose()
}
