# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['.\\mainapp.py'],
             pathex=['.\\', '..\\SimFrame'],
             binaries=[],
             datas=[
             ('..\\SimFrame\\SimulationFramework\\Codes\\Elegant\\*.yaml', 'SimulationFramework\\Codes\\Elegant'),
             ('..\\SimFrame\\SimulationFramework\\Codes\\CSRTrack\\*.yaml', 'SimulationFramework\\Codes\\CSRTrack'),
             ('..\\SimFrame\\SimulationFramework\\Codes\\*.yaml', 'SimulationFramework\\Codes'),
				('..\\SimFrame\\MasterLattice\\YAML\\*.yaml', 'MasterLattice\\YAML'),
				('..\\SimFrame\\MasterLattice\\Codes\\*.*', 'MasterLattice\\Codes'),
				('..\\SimFrame\\MasterLattice\\Data_Files\\bas_gun.txt', 'MasterLattice\\Data_Files'),
				('..\\SimFrame\\MasterLattice\\Data_Files\\TWS_S-DL.dat', 'MasterLattice\\Data_Files'),
        ('..\\SimFrame\\MasterLattice\\Data_Files\\SzSx5um10mm.*', 'MasterLattice\\Data_Files'),
        ('..\\SimFrame\\MasterLattice\\Data_Files\\Sx5um10mm.*', 'MasterLattice\\Data_Files'),
        ('..\\SimFrame\\MasterLattice\\Data_Files\\Sz5um10mm.*', 'MasterLattice\\Data_Files'),
				('..\\SimFrame\\MasterLattice\\Data_Files\\Measured_Main_Solenoid_2019.txt', 'MasterLattice\\Data_Files'),
				('..\\SimFrame\\MasterLattice\\Data_Files\\Measured_Bucking_Solenoid_2019.txt', 'MasterLattice\\Data_Files'),
				('..\\SimFrame\\MasterLattice\\Data_Files\\SwissFEL_linac_sols.dat', 'MasterLattice\\Data_Files'),
				('.\\data\\CLA10-BA1_OM.def', 'MasterLattice\\data'),
			],
             hiddenimports=['scipy.special.cython_special', 'munch'],
             hookspath=['.\\hooks'],
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
          name='mainapp',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
