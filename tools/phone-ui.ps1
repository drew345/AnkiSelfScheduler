param([int]$X=-1,[int]$Y=-1,[switch]$Back)
$adbPath='C:\AI\Codex\Tools\android-sdk\platform-tools\adb.exe'
if($Back){ & $adbPath shell input keyevent 4 }
if($X -ge 0){ & $adbPath shell input tap $X $Y }
$dumpResult=(& $adbPath shell uiautomator dump /sdcard/Download/anki-current-ui.xml 2>&1 | Out-String)
if($dumpResult -notmatch 'UI hierchary dumped to') { throw "Fresh UI dump unavailable: $dumpResult" }
[xml]$ui=(& $adbPath shell cat /sdcard/Download/anki-current-ui.xml)
$ui.SelectNodes('//node') | Where-Object {$_.text -or $_.'content-desc'} | ForEach-Object { '{0} | {1} | {2} | {3}' -f $_.text,$_.'content-desc',$_.bounds,$_.checked }
