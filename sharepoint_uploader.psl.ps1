Param(
    [string]$SiteUrl = "https://yourtenant.sharepoint.com/sites/YourSite",  # Replace with actual SharePoint site URL
    [string]$Library = "Shared Documents/CultureCards",
    [string]$LocalFolder = "sharepoint_output",
    [string[]]$FileExtensions = @(".html", ".json"),
    [switch]$WhatIf = $false,
    [string]$EmailTo = "",
    [string]$EmailFrom = "",
    [string]$SmtpServer = ""
)

# Log rotation
$today = Get-Date -Format "yyyy-MM-dd"
$OldLogFile = "upload_log.txt"
if (Test-Path $OldLogFile) {
    Rename-Item -Path $OldLogFile -NewName "upload_log_$today.txt" -Force
}
$LogFile = "upload_log.txt"
$CsvLogFile = "upload_log_$today.csv"

# Timestamp tracking
$TimestampFile = "last_upload_timestamp.txt"
$lastRun = if (Test-Path $TimestampFile) { Get-Content $TimestampFile | Out-String | [datetime] } else { [datetime]::MinValue }
$thisRun = Get-Date

# Ensure PnP PowerShell module is available
if (-not (Get-Module -ListAvailable -Name "PnP.PowerShell")) {
    Install-Module -Name "PnP.PowerShell" -Force -Scope CurrentUser
}
Import-Module PnP.PowerShell

# Authenticate with SharePoint
Connect-PnPOnline -Url $SiteUrl -Interactive

# Collect changed files
$allFiles = @()
foreach ($ext in $FileExtensions) {
    $allFiles += Get-ChildItem -Path $LocalFolder -Filter "*$ext" -Recurse | Where-Object { $_.LastWriteTime -gt $lastRun }
}

$total = $allFiles.Count
$counter = 0
$csvRows = @()

foreach ($file in $allFiles) {
    $counter++
    Write-Progress -Activity "Uploading files to SharePoint" -Status "$counter of $total" -PercentComplete (($counter / $total) * 100)

    $relativePath = $file.FullName.Substring((Resolve-Path $LocalFolder).Path.Length).TrimStart('\','/')
    $spFolder = Join-Path $Library ([System.IO.Path]::GetDirectoryName($relativePath) -replace '\\','/')
    $spFolder = $spFolder -replace '^[\\/]+',''
    $targetPath = "$spFolder/$($file.Name)"

    if ($WhatIf) {
        $msg = "$(Get-Date -Format s) WHATIF: Would upload $($file.FullName) -> $targetPath"
        Write-Host $msg -ForegroundColor Yellow
        $msg | Add-Content $LogFile
        $csvRows += [PSCustomObject]@{
            Timestamp = Get-Date -Format s
            File = $file.FullName
            Target = $targetPath
            Status = "SKIPPED (WhatIf)"
        }
        continue
    }

    try {
        Add-PnPFile -Path $file.FullName -Folder $spFolder -Force
        $msg = "$(Get-Date -Format s) SUCCESS: $($file.FullName) -> $targetPath"
        Write-Host $msg -ForegroundColor Green
        $msg | Add-Content $LogFile
        $csvRows += [PSCustomObject]@{
            Timestamp = Get-Date -Format s
            File = $file.FullName
            Target = $targetPath
            Status = "Uploaded"
        }
    } catch {
        $msg = "$(Get-Date -Format s) ERROR: $($file.FullName) -> $targetPath -- $($_.Exception.Message)"
        Write-Host $msg -ForegroundColor Red
        $msg | Add-Content $LogFile
        $csvRows += [PSCustomObject]@{
            Timestamp = Get-Date -Format s
            File = $file.FullName
            Target = $targetPath
            Status = "ERROR: $($_.Exception.Message)"
        }
    }
}

# Write CSV log
$csvRows | Export-Csv -Path $CsvLogFile -NoTypeInformation

# Update last run timestamp (if not dry run)
if (-not $WhatIf) {
    $thisRun.ToString("s") | Out-File $TimestampFile -Force
}

# Email log if settings provided
if ($EmailTo -and $EmailFrom -and $SmtpServer) {
    try {
        $body = Get-Content $LogFile -Raw
        Send-MailMessage -To $EmailTo -From $EmailFrom -SmtpServer $SmtpServer `
            -Subject "SharePoint Upload Report - $today" -Body $body
        Write-Host "Email sent to $EmailTo" -ForegroundColor Cyan
    } catch {
        Write-Host "Failed to send email: $($_.Exception.Message)" -ForegroundColor Red
    }
}
