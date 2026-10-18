# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('icone.ico', '.'), ('avatar_usuario.png', '.'), ('web', 'web')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('spellchecker')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ddgs')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# O microfone precisa das DLLs do PortAudio que vem dentro da propria
# biblioteca sounddevice (_sounddevice_data). Sem isso o .exe abre mas o
# botao de microfone reclama que nao ha som.
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('_sounddevice_data')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# Leitura de PDF (arrastar um PDF para a conversa). O modulo local e' a
# ponte da tela; a pypdf faz a extracao do texto, tudo local.
hiddenimports += ['pdf_leitor']
tmp_ret = collect_all('pypdf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# Lembretes ("me lembra amanha as 9h de ..."): modulo local, tudo local.
hiddenimports += ['lembretes']
# Documento aberto (perguntar sobre PDF longo): modulo local.
hiddenimports += ['documento']
# OCR local de PDF digitalizado (uma foto da pagina): renderiza a pagina com
# a DLL do PDFium (pypdfium2) e le com o OCR do proprio Windows (winsdk),
# tudo em memoria. Sem eles o programa so avisa que o PDF pode ser digitalizado.
tmp_ret = collect_all('pypdfium2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# winsdk e' pacote de namespace: lista os modulos usados para a analise
# estatica do PyInstaller nao depender so do import.
hiddenimports += ['winsdk.windows.media.ocr', 'winsdk.windows.globalization',
                  'winsdk.windows.graphics.imaging',
                  'winsdk.windows.storage.streams', 'winsdk.windows.foundation']


a = Analysis(
    ['app_web.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Eye of Thundera',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icone.ico'],
)

