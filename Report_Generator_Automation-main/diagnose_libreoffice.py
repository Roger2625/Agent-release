#!/usr/bin/env python3
"""
LibreOffice Installation Diagnostic Script
This script helps diagnose LibreOffice installation issues.
"""

import os
import sys
import subprocess
import platform

def check_libreoffice_installation():
    """Check if LibreOffice is properly installed and accessible"""
    print("🔍 LibreOffice Installation Diagnostic")
    print("=" * 50)
    
    # System information
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Python Version: {sys.version}")
    print(f"Current Directory: {os.getcwd()}")
    print()
    
    # Check PATH
    print("📁 Checking PATH environment variable...")
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    libreoffice_in_path = False
    
    for path_dir in path_dirs:
        if os.path.exists(path_dir):
            for file in os.listdir(path_dir):
                if any(keyword in file.lower() for keyword in ['libreoffice', 'soffice']):
                    print(f"   ✅ Found: {os.path.join(path_dir, file)}")
                    libreoffice_in_path = True
    
    if not libreoffice_in_path:
        print("   ❌ No LibreOffice executables found in PATH")
    print()
    
    # Try different LibreOffice command variations
    print("🔧 Testing LibreOffice commands...")
    libreoffice_commands = [
        ["libreoffice", "--version"],
        ["soffice", "--version"],
        ["libreoffice7.6", "--version"],
        ["libreoffice7.5", "--version"],
        ["libreoffice7.4", "--version"],
        ["libreoffice7.3", "--version"],
        ["libreoffice7.2", "--version"],
        ["libreoffice7.1", "--version"],
        ["libreoffice7.0", "--version"],
    ]
    
    working_command = None
    for cmd in libreoffice_commands:
        try:
            print(f"   Testing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, timeout=10, text=True)
            if result.returncode == 0:
                print(f"   ✅ SUCCESS: {cmd[0]}")
                print(f"      Output: {result.stdout.strip()}")
                working_command = cmd[0]
                break
            else:
                print(f"   ❌ Failed (return code: {result.returncode})")
                if result.stderr:
                    print(f"      Error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout")
        except FileNotFoundError:
            print(f"   ❌ Not found")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()
    
    # Check common installation paths
    print("📂 Checking common installation paths...")
    common_paths = []
    
    if platform.system() == "Windows":
        common_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice\program\libreoffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\libreoffice.exe",
        ]
    elif platform.system() == "Linux":
        common_paths = [
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/opt/libreoffice/program/soffice",
            "/usr/local/bin/libreoffice",
            "/usr/local/bin/soffice",
        ]
    elif platform.system() == "Darwin":  # macOS
        common_paths = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/Applications/LibreOffice.app/Contents/MacOS/libreoffice",
        ]
    
    found_paths = []
    for path in common_paths:
        if os.path.exists(path):
            print(f"   ✅ Found: {path}")
            found_paths.append(path)
        else:
            print(f"   ❌ Not found: {path}")
    
    print()
    
    # Summary and recommendations
    print("📋 Summary and Recommendations")
    print("=" * 50)
    
    if working_command:
        print(f"✅ LibreOffice is working! Use command: {working_command}")
        print("   The application should be able to launch LibreOffice successfully.")
    elif found_paths:
        print("⚠️  LibreOffice is installed but not in PATH")
        print(f"   Found at: {found_paths[0]}")
        print("   Recommendation: Add LibreOffice to your system PATH")
        if platform.system() == "Windows":
            print("   Windows: Add the LibreOffice program directory to PATH environment variable")
        elif platform.system() == "Linux":
            print("   Linux: Create a symlink or add to PATH in ~/.bashrc or ~/.profile")
        elif platform.system() == "Darwin":
            print("   macOS: LibreOffice should be accessible from Applications folder")
    else:
        print("❌ LibreOffice is not installed")
        print("   Recommendation: Install LibreOffice from https://www.libreoffice.org/download/")
    
    print()
    print("🔧 Troubleshooting Steps:")
    print("1. If LibreOffice is installed but not found, try adding it to PATH")
    print("2. Restart your terminal/command prompt after PATH changes")
    print("3. Try running 'libreoffice --version' manually in terminal")
    print("4. Check if LibreOffice is properly installed and not corrupted")
    print("5. On Windows, try running as administrator")

if __name__ == "__main__":
    check_libreoffice_installation()
