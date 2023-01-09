# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['E:\\github_project\\felionpy\\src\\main.py'],
    pathex=['E:\\github_project\\felionpy\\src'],
    binaries=[],
    datas=[],
    hiddenimports=['felionlib'],
    hookspath=['E:\\github_project\\felionpy\\src\\hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='felionpy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['E:\\github_project\\felionpy\\src\\icons\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='felionpy',
)
