# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['DeleteImageOfCvat_0.0.9v.exe', 'main.py'],
             pathex=['C:\\Users\\Administrator\\Desktop\\DeleteImageOfCvat'],
             binaries=[('KST.png', '.'), ('chromedriver_96.0.4664.35.exe', '.'), ('webcrawler.ui', '.')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='ame',
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
          entitlements_file=None , icon='KST.ico')
