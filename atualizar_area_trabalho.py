"""Garante UM atalho na Area de Trabalho para a Eye of Thundera (UI nova em HTML)."""
import os
import shutil
import subprocess
from pathlib import Path

PASTA = Path(r"D:\Projetos\PesquisaIA")
DESKTOP = Path.home() / "Desktop"
LNK = DESKTOP / "Eye of Thundera.lnk"
ICONE = PASTA / "icone.ico"
PYW_ORIGINAL = PASTA / ".venv" / "Scripts" / "pythonw.exe"
PYW = PASTA / ".venv" / "Scripts" / "Eye of Thundera.exe"
EXE_DIST = PASTA / "dist" / "Eye of Thundera.exe"

# Garante que a copia renomeada existe: o Gerenciador de Tarefas mostra o
# nome do executavel (pythonw.exe -> "Python"). Renomear a copia para
# "Eye of Thundera.exe" faz o processo aparecer com o nome do programa.
if not PYW.exists() and PYW_ORIGINAL.exists():
    shutil.copy2(str(PYW_ORIGINAL), str(PYW))
    print("[OK] copia renomeada criada: " + PYW.name)

# Copia os recursos (icone, manifesto, versao) do EXE do PyInstaller para a
# copia renomeada, para o Gerenciador de Tarefas mostrar o icone e o nome
# correto ("Eye of Thundera" em vez de "Python"). Se o EXE nao existir,
# pula (o nome do arquivo ja e' suficiente para a aba Detalhes).
if PYW.exists() and EXE_DIST.exists():
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        kernel32.LoadLibraryExW.restype = wintypes.HMODULE
        kernel32.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
        kernel32.FindResourceW.restype = wintypes.HRSRC
        kernel32.FindResourceW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p]
        kernel32.LoadResource.restype = wintypes.HGLOBAL
        kernel32.LoadResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
        kernel32.LockResource.restype = ctypes.c_void_p
        kernel32.LockResource.argtypes = [wintypes.HGLOBAL]
        kernel32.SizeofResource.restype = wintypes.DWORD
        kernel32.SizeofResource.argtypes = [wintypes.HMODULE, wintypes.HRSRC]
        kernel32.FreeLibrary.restype = wintypes.BOOL
        kernel32.FreeLibrary.argtypes = [wintypes.HMODULE]
        kernel32.BeginUpdateResourceW.restype = wintypes.HANDLE
        kernel32.BeginUpdateResourceW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL]
        kernel32.EndUpdateResourceW.restype = wintypes.BOOL
        kernel32.EndUpdateResourceW.argtypes = [wintypes.HANDLE, wintypes.BOOL]
        kernel32.UpdateResourceW.restype = wintypes.BOOL
        kernel32.UpdateResourceW.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.WORD, ctypes.c_void_p, wintypes.DWORD]

        LOAD_LIBRARY_AS_DATAFILE = 0x00000002

        def read_res(hMod, tipo, nome):
            hrsrc = kernel32.FindResourceW(hMod, ctypes.c_void_p(nome), ctypes.c_void_p(tipo))
            if not hrsrc:
                return None
            size = kernel32.SizeofResource(hMod, hrsrc)
            hglobal = kernel32.LoadResource(hMod, hrsrc)
            ptr = kernel32.LockResource(hglobal)
            if ptr and size > 0:
                return ctypes.string_at(ptr, size)
            return None

        hMod = kernel32.LoadLibraryExW(str(EXE_DIST), None, LOAD_LIBRARY_AS_DATAFILE)
        if hMod:
            # Copia icone (tipo 3, nomes 1..12) e grupo de icone (tipo 14, nome 1)
            # e manifesto (tipo 24, nome 1)
            for tipo in (3, 14, 24):
                if tipo == 3:
                    for i in range(1, 20):
                        data = read_res(hMod, tipo, i)
                        if data:
                            hUpdate = kernel32.BeginUpdateResourceW(str(PYW), False)
                            if hUpdate:
                                buf = (ctypes.c_char * len(data)).from_buffer_copy(data)
                                kernel32.UpdateResourceW(hUpdate, ctypes.c_void_p(tipo), ctypes.c_void_p(i), 1033, buf, len(data))
                                kernel32.EndUpdateResourceW(hUpdate, False)
                else:
                    data = read_res(hMod, tipo, 1)
                    if data:
                        hUpdate = kernel32.BeginUpdateResourceW(str(PYW), False)
                        if hUpdate:
                            buf = (ctypes.c_char * len(data)).from_buffer_copy(data)
                            kernel32.UpdateResourceW(hUpdate, ctypes.c_void_p(tipo), ctypes.c_void_p(1), 1033, buf, len(data))
                            kernel32.EndUpdateResourceW(hUpdate, False)
            kernel32.FreeLibrary(hMod)
            print("[OK] recursos (icone, manifesto) copiados do EXE")
    except Exception as e:
        print("AVISO: nao copiou recursos: %s" % e)

    # Modifica o FileDescription na versao info para "Eye of Thundera"
    try:
        # Le a versao info do pythonw.exe
        hMod2 = kernel32.LoadLibraryExW(str(PYW_ORIGINAL), None, LOAD_LIBRARY_AS_DATAFILE)
        if hMod2:
            hrsrc = kernel32.FindResourceW(hMod2, ctypes.c_void_p(1), ctypes.c_void_p(16))
            if hrsrc:
                size = kernel32.SizeofResource(hMod2, hrsrc)
                hglobal = kernel32.LoadResource(hMod2, hrsrc)
                ptr = kernel32.LockResource(hglobal)
                data = bytearray(ctypes.string_at(ptr, size))
                kernel32.FreeLibrary(hMod2)

                # Substitui "Python" por "Eye of Thundera" no FileDescription
                old_val = "Python".encode('utf-16-le') + b'\x00\x00'
                new_val = "Eye of Thundera".encode('utf-16-le') + b'\x00\x00'
                pos = bytes(data).find(old_val)
                # Encontra a ocorrencia correta (a do FileDescription, segunda ocorrencia)
                # Busca pela segunda ocorrencia
                first = bytes(data).find(old_val)
                second = bytes(data).find(old_val, first + 1)
                if second >= 0:
                    # Verifica que e' realmente o FileDescription (precedido por "FileDescription\0")
                    key = "FileDescription".encode('utf-16-le')
                    key_pos = bytes(data).rfind(key, 0, second)
                    if key_pos >= 0 and second - key_pos < 40:
                        # Substitui
                        old_total = 16  # 14 + 2 padding
                        new_total = 36  # 34 + 2 padding
                        size_diff = new_total - old_total
                        part1 = data[:second]
                        part2 = new_val + b'\x00\x00' * ((new_total - len(new_val)) // 2)
                        old_end = second + old_total
                        part3 = data[old_end:]
                        new_data = part1 + part2 + part3

                        # Atualiza wLength da entrada FileDescription
                        import struct
                        entry_start = key_pos - 6
                        new_entry_wLength = struct.unpack('<H', new_data[entry_start:entry_start+2])[0] + size_diff
                        struct.pack_into('<H', new_data, entry_start, new_entry_wLength)
                        struct.pack_into('<H', new_data, entry_start + 2, 17)  # wValueLength

                        # StringFileInfo wLength
                        sf_key = 'StringFileInfo'.encode('utf-16-le')
                        sf_pos = bytes(new_data).find(sf_key)
                        sf_entry_start = sf_pos - 6
                        sf_wLength = struct.unpack('<H', new_data[sf_entry_start:sf_entry_start+2])[0]
                        struct.pack_into('<H', new_data, sf_entry_start, sf_wLength + size_diff)

                        # StringTable wLength
                        st_key = '000004b0'.encode('utf-16-le')
                        st_pos = bytes(new_data).find(st_key)
                        if st_pos >= 0:
                            st_entry_start = st_pos - 6
                            st_wLength = struct.unpack('<H', new_data[st_entry_start:st_entry_start+2])[0]
                            struct.pack_into('<H', new_data, st_entry_start, st_wLength + size_diff)

                        # VS_VERSIONINFO wLength
                        vs_wLength = struct.unpack('<H', new_data[0:2])[0]
                        struct.pack_into('<H', new_data, 0, vs_wLength + size_diff)

                        # Escreve
                        hUpdate = kernel32.BeginUpdateResourceW(str(PYW), False)
                        if hUpdate:
                            buf = (ctypes.c_char * len(new_data)).from_buffer_copy(bytes(new_data))
                            ok = kernel32.UpdateResourceW(hUpdate, ctypes.c_void_p(16), ctypes.c_void_p(1), 1033, buf, len(new_data))
                            if ok:
                                kernel32.EndUpdateResourceW(hUpdate, False)
                                print("[OK] FileDescription alterado para 'Eye of Thundera'")
                            else:
                                kernel32.EndUpdateResourceW(hUpdate, True)
                                print("AVISO: nao consegui atualizar versao info")
    except Exception as e:
        print("AVISO: nao modificou versao info: %s" % e)

_base = (PASTA / "_arquivo_morto")
_base.mkdir(exist_ok=True)

# Mover duplicados/extras (nunca apagar)
for dup in (DESKTOP / "Eye of Thundera (Nova Tela).lnk",
            DESKTOP / "Wolf.lnk",
            DESKTOP / "Eye of Thundera.exe"):
    if dup.exists():
        dest = _base / (dup.stem + " (atalho antigo)" + dup.suffix)
        try:
            os.replace(str(dup), str(dest))
            print("[OK] extra guardado em _arquivo_morto: " + dup.name)
        except Exception as e:
            print("AVISO: nao moveu %s: %s" % (dup, e))

# Recria atalho unico via PowerShell (nao depende de win32com)
ps_script = (
    "$s = New-Object -ComObject WScript.Shell; "
    "$lnk = $s.CreateShortcut('"
    + str(LNK)
    + "'); "
    "$lnk.TargetPath = '"
    + str(PYW)
    + "'; "
    "$lnk.Arguments = 'app_web.py'; "
    "$lnk.WorkingDirectory = '"
    + str(PASTA)
    + "'; "
    "$lnk.IconLocation = '"
    + str(ICONE)
    + "'; "
    "$lnk.Description = 'Eye of Thundera - interface nova'; "
    "$lnk.Save(); "
    'Write-Output "ATUALIZADO: " + $lnk.TargetPath'
)
result = subprocess.run(
    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
    capture_output=True,
    text=True,
)
out = (result.stdout or "").strip()
err = (result.stderr or "").strip()
if out:
    print("[OK] " + out)
if err:
    print("ERRO: " + err)
print("[OK] Atalho final: " + str(LNK))
print("     -> UM icone de Eye of Thundera na Area de Trabalho.")
