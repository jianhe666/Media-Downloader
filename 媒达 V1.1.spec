# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('媒达.ico', '.'), ('ffmpeg', 'ffmpeg')]
binaries = []
hiddenimports = ['douyin_extractor', 'playwright', 'customtkinter']
tmp_ret = collect_all('yt_dlp')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['media_downloader.py'],
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
    [],
    exclude_binaries=True,
    name='媒达 V1.1',
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
    icon=['媒达.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='媒达 V1.1',
)

# --- Post-build: sign the exe ---
import subprocess, os as _os, tempfile
_exe_path = os.path.join('dist', '媒达 V1.1', '媒达 V1.1.exe')
if _os.path.exists(_exe_path):
    _ps = f'''
$cert = Get-ChildItem -Path Cert:\\CurrentUser\\My | Where-Object {{ $_.Subject -like '*jianhe666*' }} | Select-Object -First 1
if ($cert) {{
    Set-AuthenticodeSignature -FilePath '{_exe_path}' -Certificate $cert -TimestampServer http://timestamp.digicert.com
    Write-Host 'Signed: {_exe_path}'
}} else {{
    Write-Host 'WARNING: signing cert not found, run create-cert.ps1 first'
}}
'''
    _tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8')
    _tmp.write(_ps)
    _tmp.close()
    subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', _tmp.name], check=False)
    _os.unlink(_tmp.name)
