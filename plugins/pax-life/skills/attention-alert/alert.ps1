# Attention alert (Windows): a flashing, shaking, always-on-top pop-up with sound. Click anywhere to dismiss.
# Usage: powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File alert.ps1 -Message "Your turn: sign in"
# Optional: -Title "YOUR ENVOY NEEDS YOU"  -Seconds 120 (auto-closes after this many seconds)
param([string]$Message = "Claude needs you", [string]$Title = "CLAUDE NEEDS YOU", [int]$Seconds = 120)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$colors = @([Drawing.Color]::FromArgb(0x77,0x37,0x2e), [Drawing.Color]::FromArgb(0x7f,0x41,0x7d),
            [Drawing.Color]::FromArgb(0xff,0xd7,0x00), [Drawing.Color]::FromArgb(0x00,0xe5,0xff))

$f = New-Object Windows.Forms.Form
$f.FormBorderStyle = 'None'; $f.TopMost = $true; $f.StartPosition = 'CenterScreen'
$f.Size = New-Object Drawing.Size(900, 420); $f.ShowInTaskbar = $true; $f.Text = $Title

$l = New-Object Windows.Forms.Label
$l.Dock = 'Fill'; $l.TextAlign = 'MiddleCenter'; $l.ForeColor = [Drawing.Color]::White
$l.Font = New-Object Drawing.Font('Segoe UI Black', 26, [Drawing.FontStyle]::Bold)
$l.Text = "$Title`n`n$Message`n`n(click to dismiss)"
$f.Controls.Add($l)

$script:i = 0; $script:start = Get-Date
$t = New-Object Windows.Forms.Timer; $t.Interval = 350
$t.Add_Tick({
    $script:i++
    $f.BackColor = $colors[$script:i % $colors.Count]
    $l.ForeColor = if ($script:i % 2) { [Drawing.Color]::White } else { [Drawing.Color]::Black }
    $f.Left += (Get-Random -Minimum -6 -Maximum 7); $f.Top += (Get-Random -Minimum -6 -Maximum 7)   # shake
    if ($script:i % 6 -eq 0) { [Media.SystemSounds]::Exclamation.Play() }
    if (((Get-Date) - $script:start).TotalSeconds -gt $Seconds) { $f.Close() }
})
$l.Add_Click({ $f.Close() }); $f.Add_Click({ $f.Close() })
$f.Add_Shown({ $f.Activate(); $t.Start() })
[void]$f.ShowDialog()
