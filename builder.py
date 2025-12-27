import os
import sys
import shutil
import subprocess
from pathlib import Path
import json
from datetime import datetime


class AIBridgeBuilder:
    """Build AIBridge application to executable"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.app_name = "AI Translation Bridge"
        self.app_filename = "AI_Translation_Bridge"
        self.version = "1.0.0"

        # PyInstaller options
        self.build_options = {
            'console': False,
            'onefile': True,
            'icon': None,
            'upx': True,
            'clean': True
        }

    def check_requirements(self):
        """Check if all required tools are installed"""
        print("Checking requirements...")

        # Check PyInstaller
        try:
            import PyInstaller
            print(f"✓ PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            print("✗ PyInstaller not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

        # Check if icon exists
        icon_path = self.project_root / "assets" / "icon.ico"
        if icon_path.exists():
            self.build_options['icon'] = str(icon_path).replace('\\', '\\\\')  # Escape backslashes
            print(f"✓ Icon found: {icon_path}")
        else:
            print("! Icon not found, will use default")

        return True

    def create_spec_file(self):
        """Create PyInstaller spec file with custom configuration"""

        # Prepare icon line for spec file
        icon_line = ""
        if self.build_options['icon']:
            icon_line = f"icon='{self.build_options['icon']}',"

        # Prepare version line
        version_line = ""
        if (self.project_root / "version_info.txt").exists():
            version_line = "version='version_info.txt',"

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['{str(self.project_root).replace(chr(92), chr(92)*2)}'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        {'("bot_settings.json", ".") if os.path.exists("bot_settings.json") else ("", ""),'}
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
    hooksconfig={{}},
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
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx={self.build_options['upx']},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={self.build_options['console']},
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {icon_line}
    {version_line}
)
'''

        spec_file = self.project_root / f"{self.app_filename}.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)

        print(f"✓ Spec file created: {spec_file}")
        return spec_file

    def create_version_info(self):
        """Create Windows version information file"""
        version_info = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AIBridge'),
        StringStruct(u'FileDescription', u'AI Translation Bridge Application'),
        StringStruct(u'FileVersion', u'{self.version}'),
        StringStruct(u'InternalName', u'{self.app_filename}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
        StringStruct(u'OriginalFilename', u'{self.app_name}.exe'),
        StringStruct(u'ProductName', u'AI Translation Bridge'),
        StringStruct(u'ProductVersion', u'{self.version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''

        version_file = self.project_root / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info)

        print(f"✓ Version info created: {version_file}")
        return version_file

    def clean_temp_files(self):
        """Clean temporary build files after build"""
        print("\nCleaning temporary files...")

        # Remove build directory
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"  ✓ Removed: {self.build_dir}")

        # Remove ALL spec files (cả tên cũ và mới)
        spec_files = [
            self.project_root / f"{self.app_filename}.spec",
            self.project_root / "AIBridge.spec",  # Tên cũ
            self.project_root / "AI_Bridge.spec"  # Có thể có
        ]

        for spec_file in spec_files:
            if spec_file.exists():
                spec_file.unlink()
                print(f"  ✓ Removed: {spec_file}")

        # Remove version_info.txt
        version_file = self.project_root / "version_info.txt"
        if version_file.exists():
            version_file.unlink()
            print(f"  ✓ Removed: {version_file}")

        # Remove __pycache__ directories
        for pycache in self.project_root.rglob("__pycache__"):
            shutil.rmtree(pycache)
            print(f"  ✓ Removed: {pycache}")

    def clean_all_build_files(self):
        """Clean all build files including dist"""
        print("Cleaning all build files...")

        # Clean temp files
        self.clean_temp_files()

        # Remove dist directory
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"  ✓ Removed: {self.dist_dir}")

    def build(self, console=False, onefile=True):
        """Build the executable"""
        self.build_options['console'] = console
        self.build_options['onefile'] = onefile

        print("\n" + "="*50)
        print(f"Building {self.app_name} v{self.version}")
        print(f"Mode: {'Console' if console else 'Windowed'}")
        print(f"Type: {'Single File' if onefile else 'Directory'}")
        print("="*50 + "\n")

        # Clean all previous build files first
        self.clean_all_build_files()

        # Check requirements
        if not self.check_requirements():
            print("Requirements check failed!")
            return False

        # Create version info
        version_file = self.create_version_info()

        # Create spec file
        spec_file = self.create_spec_file()

        # Run PyInstaller
        print("\nRunning PyInstaller...")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Build completed successfully!")

                # Show output location
                exe_path = self.dist_dir / f"{self.app_name}.exe"

                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    print(f"\nExecutable created:")
                    print(f"  Path: {exe_path}")
                    print(f"  Size: {size_mb:.2f} MB")

                    # Create output folder with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_dir = self.project_root / "releases" / f"{self.app_filename}_{self.version}_{timestamp}"
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Copy executable to releases folder
                    final_exe = output_dir / f"{self.app_name}.exe"
                    shutil.copy2(exe_path, final_exe)

                    # Copy assets folder to output
                    assets_src = self.project_root / "assets"
                    assets_dst = output_dir / "assets"
                    if assets_src.exists():
                        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
                        print(f"  ✓ Assets copied to: {assets_dst}")

                    print(f"\n✓ Release package created: {output_dir}")
                    print(f"  Final executable: {final_exe}")

                    # Clean temporary files after successful build
                    self.clean_temp_files()

                    # Also remove dist folder after copying
                    if self.dist_dir.exists():
                        shutil.rmtree(self.dist_dir)
                        print(f"  ✓ Cleaned dist folder")

                    print("\n✓ All temporary build files cleaned")

                    return True
                else:
                    print("✗ Executable not found after build!")
                    self.clean_temp_files()
                    return False

            else:
                print("✗ Build failed!")
                print("Error output:")
                print(result.stderr)
                self.clean_temp_files()
                return False

        except Exception as e:
            print(f"✗ Build error: {e}")
            self.clean_temp_files()
            return False


def main():
    """Main function for builder - auto build windowed app"""
    builder = AIBridgeBuilder()

    print("AI Translation Bridge - Builder")
    print("================================\n")

    # Auto build windowed application without asking
    print("Starting automatic build (Windowed application)...")

    success = builder.build(console=False, onefile=True)

    if success:
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("BUILD FAILED!")
        print("="*50)

if __name__ == "__main__":
    main()