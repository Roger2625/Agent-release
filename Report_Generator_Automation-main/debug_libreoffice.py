#!/usr/bin/env python3
"""
Debug script for LibreOffice window detection
"""

import os
import sys
import subprocess
import time
import win32gui
import win32process

def find_libreoffice():
    """Find LibreOffice executable"""
    paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def launch_libreoffice(file_path):
    """Launch LibreOffice with a file"""
    executable = find_libreoffice()
    if not executable:
        print("❌ LibreOffice not found")
        return None
    
    print(f"🚀 Launching LibreOffice: {executable}")
    print(f"📄 File: {file_path}")
    
    # Launch LibreOffice
    process = subprocess.Popen([executable, file_path])
    print(f"✅ Process started with PID: {process.pid}")
    return process

def find_windows_by_process(pid):
    """Find all windows belonging to a specific process"""
    windows = []
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    windows.append({
                        'hwnd': hwnd,
                        'text': window_text,
                        'class': class_name,
                        'pid': window_pid
                    })
            except Exception as e:
                print(f"Error getting window info: {e}")
        return True
    
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows

def main():
    print("🔍 LibreOffice Window Detection Debug")
    print("=" * 50)
    
    # Check if test file exists
    test_file = "test_template.docx"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("Please run test_template.py first to create the test document")
        return
    
    # Launch LibreOffice
    process = launch_libreoffice(test_file)
    if not process:
        return
    
    # Wait for LibreOffice to start
    print("\n⏳ Waiting for LibreOffice to start...")
    for i in range(10):
        time.sleep(1)
        print(f"⏳ Waiting... ({i+1}/10)")
        
        # Check for windows
        windows = find_windows_by_process(process.pid)
        if windows:
            print(f"\n✅ Found {len(windows)} windows from LibreOffice process:")
            for i, window in enumerate(windows):
                print(f"  Window {i+1}:")
                print(f"    Handle: {window['hwnd']}")
                print(f"    Title: '{window['text']}'")
                print(f"    Class: '{window['class']}'")
                print(f"    PID: {window['pid']}")
            break
    else:
        print("\n❌ No windows found from LibreOffice process")
        
        # Try to find ANY LibreOffice windows
        print("\n🔍 Searching for ANY LibreOffice windows...")
        all_windows = []
        
        def enum_all_windows_callback(hwnd, all_windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                libreoffice_keywords = ['libreoffice', 'writer', 'calc', 'impress', 'soffice']
                if any(keyword in window_text.lower() for keyword in libreoffice_keywords) or \
                   any(keyword in class_name.lower() for keyword in libreoffice_keywords):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        all_windows.append({
                            'hwnd': hwnd,
                            'text': window_text,
                            'class': class_name,
                            'pid': pid
                        })
                    except:
                        pass
            return True
        
        win32gui.EnumWindows(enum_all_windows_callback, all_windows)
        
        if all_windows:
            print(f"Found {len(all_windows)} LibreOffice-related windows:")
            for window in all_windows:
                print(f"  - '{window['text']}' (PID: {window['pid']})")
        else:
            print("No LibreOffice windows found at all")
    
    print("\n" + "=" * 50)
    print("Debug complete!")

if __name__ == "__main__":
    main()
