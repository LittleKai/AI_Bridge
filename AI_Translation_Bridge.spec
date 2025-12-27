# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['D:\\Dev\\Python\\AI_Bridge'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ("bot_settings.json", ".") if os.path.exists("bot_settings.json") else ("", ""),
    ],
    hiddenimports=[
        'tkinter',
        'pandas',
        'openpyxl',
        'numpy',
        'PIL',
        'cv2',
        'pyautogui',
        'pyperclip',
        'keyboard',
        'cryptography',
        'requests',
        'docx',
        'ebooklib',
        'bs4',
        'lxml',
        'html5lib'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pytest',
        'ipython',
        'jupyter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI Translation Bridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='D:\\Dev\\Python\\AI_Bridge\\assets\\icon.ico',
    version='version_info.txt',
)
