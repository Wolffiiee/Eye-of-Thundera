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
    console=False,
    # Era console=True "porque a tela nova ainda era um teste" — e o
    # Wolf viu o resultado em 16/10/2026: abria uma janela preta (CMD)
    # atras do programa. Agora esta e' a tela de verdade, entao nada de
    # janela de console.
    #
    # Perde-se uma coisa: se o programa quebrar na largada, a janela
    # preta nao aparece para mostrar o erro. Por isso NAO relyamos nisso:
    # a tela nova ja grava `erro.log` sozinho (ver `registrar_erro` em
    # app_web.py / pesquisa_ia.py), que e' onde o erro vai aparecer.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icone.ico'],
)
