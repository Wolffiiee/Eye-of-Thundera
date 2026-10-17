import subprocess
result = subprocess.run(
    ['powershell', '-Command',
     '(New-Object -ComObject WScript.Shell).CreateShortcut("C:\\Users\\Igor\\Desktop\\Eye of Thundera.lnk").IconLocation'],
    capture_output=True, text=True, timeout=10
)
print('IconLocation:', result.stdout.strip())
print('STDERR:', result.stderr.strip())