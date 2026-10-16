import subprocess, sys, os
exe = r"D:\Projetos\PesquisaIA\.venv\Scripts\pythonw.exe"
py = r"D:\Projetos\PesquisaIA\app_web.py"
print("Running:", exe, py)
proc = subprocess.Popen([exe, py], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = proc.communicate(timeout=5)
print("STDOUT:", stdout.decode('utf-8', errors='replace')[:500])
print("STDERR:", stderr.decode('utf-8', errors='replace')[:500])
print("Return code:", proc.returncode)