# -*- mode: python ; coding: utf-8 -*-
import os

# Dynamically resolve absolute paths
spec_dir = os.path.dirname(os.path.abspath(SPEC)) if 'SPEC' in globals() else os.path.abspath('.')
workspace_root = os.path.abspath(os.path.join(spec_dir, '../..'))

a = Analysis(
    ['main.py'],
    pathex=[workspace_root, spec_dir],
    binaries=[],
    datas=[('assets', 'assets'), ('data', 'data')],
    hiddenimports=['pynput.keyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'google',
        'google.generativeai',
        'google.genai',
        'google.protobuf',
        'googleapiclient',
        'openai',
        'anthropic',
        'fastapi',
        'pydantic',
        'uvicorn',
        'email_validator',
        'dnspython',
        'numpy',
        'pandas',
        'matplotlib',
        'ipython',
        'jedi',
        'black',
        'pylint',
        'tensorflow',
        'torch',
        'keras',
        'scipy',
        'h5py',
        'tensorboard',
        'sympy',
        'sklearn',
        'scikit-learn',
        'numba',
        'llvmlite',
        'docutils',
        'sphinx',
        'git',
        'gitdb',
        'kivy',
        'jnius',
        'pyjnius',
        'plyer',
        'android'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DevBuddy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DevBuddy',
)
