# -*- mode: python ; coding: utf-8 -*-
# .exe da TELA NOVA (HTML). De proposito e' um spec SEPARADO do
# "Pesquisa IA.spec": o programa de sempre (tkinter) continua com o
# .exe dele, que ja funciona. Se a tela nova der problema, o programa do
# Wolf nao e afetado.
from PyInstaller.utils.hooks import collect_all

datas = [('icone.ico', '.'), ('avatar_usuario.png', '.')]
datas.append(('web', 'web'))
binaries = []
hiddenimports = []
for pacote in ('spellchecker', 'ddgs', 'sounddevice', '_sounddevice_data'):
    tmp = collect_all(pacote)
    datas += tmp[0]
    binaries += tmp[1]
    hiddenimports += tmp[2]
# A tela e' uma pagina de navegador dentro da janela: o pywebview traz
# junto os arquivos da interface dele e o motor do navegador.
tmp = collect_all('webview')
datas += tmp[0]
binaries += tmp[1]
hiddenimports += tmp[2]
hiddenimports += ['webview.platforms.edgechromium', 'clr_loader']


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
    name='Pesquisa IA Tela Nova',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # a tela nova ainda e' um teste: mostra erros
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icone.ico'],
)
