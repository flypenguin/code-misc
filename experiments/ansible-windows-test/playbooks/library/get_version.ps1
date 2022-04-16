#!powershell
# WANT_JSON
# POWERSHELL_COMMON
$ErrorActionPreference = "Stop"
$params = Parse-Args $args -supports_check_mode $true
$MajorVer = Get-AnsibleParam -obj $params -name "major" -type "str"
$MinorVer = Get-AnsibleParam -obj $params -name "minor" -type "str"
$BuildVer = Get-AnsibleParam -obj $params -name "build" -type "str"
#Should validate input parameters here naturally
$Vers = (Get-Host).Version
$Message = $Message = "Windows OS is at desired version"
$BelowMin = $false
if ($Vers.Major -lt $MajorVer) { $BelowMin = $true }
if ($Vers.Minor -lt $MinorVer) { $BelowMin = $true }
if ($Vers.Build -lt $BuildVer) { $BelowMin = $true }
if ($BelowMin) { $Message = "Windows OS below desired version" }
$result = @{
  changed = $BelowMin
  version = $Vers
  message = $Message
  desired_major_ver = $MajorVer
  desired_minor_ver = $MinorVer
  desired_build_ver = $BuildVer
}
Exit-Json $result
