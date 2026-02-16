# X Knowledge Graph - Automated Testing Setup
# Run this as Administrator to set up daily testing

$taskName = "XKG Daily Validation"
$scriptPath = "C:\xkg-testing\run-validation.ps1"
$logPath = "C:\xkg-testing\daily-test.log"

# Create the validation script
@"
# Daily XKG Validation Script
`$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"`n=== XKG Validation - `\$timestamp ===" | Out-File -FilePath "$logPath" -Append

cd "C:\xkg-testing"
python validate.py 2>&1 | Out-File -FilePath "$logPath" -Append

"=== Complete ===" | Out-File -FilePath "$logPath" -Append
"-" * 50 | Out-File -FilePath "$logPath" -Append
"@ | Out-File -FilePath $scriptPath -Encoding utf8

# Register the scheduled task (requires Admin)
try {
    $action = New-ScheduledTaskAction -Execute "powershell" -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At "8am"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -ErrorAction Stop
    
    Write-Host "SUCCESS: Task '$taskName' created" -ForegroundColor Green
    Write-Host "Runs daily at 8:00 AM" -ForegroundColor Cyan
    Write-Host "Logs to: $logPath" -ForegroundColor Cyan
}
catch {
    Write-Host "ERROR: Could not create task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "`nTo run manually:" -ForegroundColor White
    Write-Host "  schtasks /create /tn `"$taskName`" /tr `"powershell -ExecutionPolicy Bypass -File `"$scriptPath`"`" /sc daily /st 08:00 /ru SYSTEM" -ForegroundColor Gray
}
