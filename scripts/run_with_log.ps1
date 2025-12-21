param (
    [Parameter(Mandatory=$true)]
    [string]$CommandToRun
)

$LogFile = "$PSScriptRoot\..\error_log.md"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Initialize Log File if missing
if (-not (Test-Path $LogFile)) {
    "# Error & Warning Log`nThis log is auto-generated for LLM analysis.`n" | Out-File $LogFile -Encoding utf8
}

# Execute the command and capture all streams (*>) to the error variable
# We use Invoke-Expression to handle arguments within the string
try {
    Write-Host "Executing: $CommandToRun" -ForegroundColor Cyan
    
    # Run command, capture STDOUT and STDERR joined
    $Output = Invoke-Expression "$CommandToRun 2>&1" 
    
    # Print to console so you still see it live
    $Output | Write-Host

    # Check if the output contains typical error keywords
    # (Adjust keywords based on your specific stack, e.g., 'Exception', 'Failed')
    $ErrorKeywords = @("error", "warning", "fail", "exception", "fatal")
    $ContainsErrors = $Output | Select-String -Pattern $ErrorKeywords -SimpleMatch

    if ($ContainsErrors -or $LASTEXITCODE -ne 0) {
        $LogEntry = "## Execution: ``$CommandToRun```n**Time:** $Timestamp`n`n```console`n$($Output | Out-String)`n``` `n`n---`n"
        $LogEntry | Out-File -FilePath $LogFile -Append -Encoding utf8
    }
}
catch {
    # Catch script execution errors
    $Err = $_.Exception.Message
    $LogEntry = "## CRITICAL FAILURE: ``$CommandToRun```n**Time:** $Timestamp`n`n```console`n$Err`n``` `n`n---`n"
    $LogEntry | Out-File -FilePath $LogFile -Append -Encoding utf8
    Write-Error $Err
}