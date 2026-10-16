import subprocess
result = subprocess.run(
    ['powershell', '-Command',
     '(New-Object -ComObject WScript.Shell).CreateShortcut("C:\\Users\\Igor\\Desktop\\Eye of Thundera.lnk").TargetPath'],
    capture_output=True, text=True, timeout=10
)
print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)
print('Return code:', result.returncode)