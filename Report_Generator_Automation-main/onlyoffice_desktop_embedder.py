#!/usr/bin/env python3
"""
LibreOffice Desktop Embedder for PyQt6
Embeds LibreOffice directly into PyQt6 applications for document preview
"""

import os
import sys
import json
import subprocess
import time
import tempfile
import shutil
import logging
import platform
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWindow

# For document handling
from docx import Document


class CollaboraOfficeEmbedder:
    """Handles embedding LibreOffice into PyQt6 widgets"""
    
    def __init__(self):
        self.collabora_process = None
        self.temp_file_path = None
        self.window_id = None
        self.embedded_widget = None
        
    def find_collabora_executable(self):
        """Find LibreOffice executable on the system"""
        import platform
        system = platform.system().lower()
        
        # Common installation paths
        if system == "windows":
            paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                r"C:\Program Files\Collabora Office\program\soffice.exe",
                r"C:\Program Files (x86)\Collabora Office\program\soffice.exe"
            ]
            
            # Also try to find from Start Menu shortcuts
            start_menu_paths = [
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\LibreOffice\LibreOffice Writer.lnk",
                r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\LibreOffice\LibreOffice.lnk",
                r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\LibreOffice\LibreOffice Writer.lnk",
                r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\LibreOffice\LibreOffice.lnk"
            ]
            
            # Try direct paths first
            for path in paths:
                if os.path.exists(path):
                    print(f"✅ Found LibreOffice at: {path}")
                    return path
            
            # Try to resolve shortcuts
            for shortcut_path in start_menu_paths:
                expanded_path = os.path.expandvars(shortcut_path)
                print(f"🔍 Checking shortcut: {expanded_path}")
                if os.path.exists(expanded_path):
                    print(f"✅ Shortcut exists: {expanded_path}")
                    try:
                        # Try to resolve the shortcut target
                        import win32com.client
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(expanded_path)
                        target_path = shortcut.Targetpath
                        print(f"📋 Shortcut target: {target_path}")
                        if os.path.exists(target_path):
                            print(f"✅ Found LibreOffice via shortcut: {target_path}")
                            return target_path
                        else:
                            print(f"❌ Target path does not exist: {target_path}")
                    except Exception as e:
                        print(f"⚠️ Could not resolve shortcut {expanded_path}: {e}")
                        continue
                else:
                    print(f"❌ Shortcut does not exist: {expanded_path}")
            
            # Try using 'where' command
            try:
                result = subprocess.run(['where', 'soffice'], capture_output=True, text=True)
                if result.returncode == 0:
                    soffice_path = result.stdout.strip().split('\n')[0]
                    if os.path.exists(soffice_path):
                        print(f"✅ Found LibreOffice via 'where' command: {soffice_path}")
                        return soffice_path
            except Exception as e:
                print(f"⚠️ 'where' command failed: {e}")
                
        elif system == "linux":
            paths = [
                "/usr/bin/libreoffice",
                "/usr/bin/collaboraoffice",
                "/snap/bin/libreoffice",
                "/opt/libreoffice/program/soffice",
                "/opt/collaboraoffice/program/soffice"
            ]
        elif system == "darwin":  # macOS
            paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/Applications/Collabora Office.app/Contents/MacOS/soffice"
            ]
        else:
            return None
            
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        import platform
        system = platform.system().lower()
        
        dependencies = {
            'libreoffice': self.find_collabora_executable() is not None,
            'win32gui': False,
            'xdotool': False,
            'osascript': False
        }
        
        if system == "windows":
            try:
                import win32gui
                dependencies['win32gui'] = True
            except ImportError:
                pass
        elif system == "linux":
            try:
                result = subprocess.run(['which', 'xdotool'], capture_output=True)
                dependencies['xdotool'] = result.returncode == 0
            except:
                pass
        elif system == "darwin":
            try:
                result = subprocess.run(['which', 'osascript'], capture_output=True)
                dependencies['osascript'] = result.returncode == 0
            except:
                pass
        
        return dependencies
        
    def launch_collabora_with_file(self, file_path, embed=True):
        """Launch LibreOffice with the specified file"""
        executable = self.find_collabora_executable()
        if not executable:
            raise FileNotFoundError("LibreOffice not found. Please install LibreOffice.")
        
        print(f"🔍 Checking LibreOffice installation...")
        print(f"✅ LibreOffice found at: {executable}")
        
        # Test if LibreOffice can be launched
        try:
            test_process = subprocess.Popen([executable, "--version"], 
                                          capture_output=True, text=True, timeout=10)
            stdout, stderr = test_process.communicate()
            if test_process.returncode == 0:
                print(f"✅ LibreOffice version: {stdout.strip()}")
            else:
                print(f"⚠️ LibreOffice test failed: {stderr}")
        except Exception as e:
            print(f"⚠️ Could not test LibreOffice: {e}")
        
        # Test if we can launch LibreOffice Writer directly
        try:
            print(f"🧪 Testing LibreOffice Writer launch...")
            test_writer_process = subprocess.Popen([executable, "--writer", "--version"], 
                                                 capture_output=True, text=True, timeout=10)
            stdout, stderr = test_writer_process.communicate()
            if test_writer_process.returncode == 0:
                print(f"✅ LibreOffice Writer test successful")
            else:
                print(f"⚠️ LibreOffice Writer test failed: {stderr}")
        except Exception as e:
            print(f"⚠️ Could not test LibreOffice Writer: {e}")
            
        # Create temporary copy of the file
        temp_dir = tempfile.mkdtemp()
        self.temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copy2(file_path, self.temp_file_path)
        
        # Store the file path for later use
        self.original_file_path = file_path
        
        if embed:
            # Launch LibreOffice with minimal flags to ensure visible window
            print(f"🚀 Launching LibreOffice with: {self.temp_file_path}")
            
            # Try different launch methods
            launch_methods = [
                # Method 1: Direct document opening
                [executable, "--writer", self.temp_file_path],
                # Method 2: With show flag
                [executable, "--show", "--writer", self.temp_file_path],
                # Method 3: Force new instance
                [executable, "--nologo", "--norestore", "--writer", self.temp_file_path],
                # Method 4: Simple launch (fallback)
                [executable, self.temp_file_path]
            ]
            
            for i, cmd in enumerate(launch_methods):
                try:
                    print(f"🔄 Trying launch method {i+1}: {' '.join(cmd)}")
                    self.collabora_process = subprocess.Popen(cmd)
                    print(f"✅ LibreOffice process started with PID: {self.collabora_process.pid}")
                    
                    # Wait longer for LibreOffice to fully start and open the document
                    print(f"⏳ Waiting for LibreOffice to open document...")
                    time.sleep(5)
                    if self.find_collabora_window_id():
                        print(f"✅ Window found with method {i+1}")
                        break
                    else:
                        print(f"❌ No window found with method {i+1}, trying next...")
                        self.collabora_process.terminate()
                        self.collabora_process.wait(timeout=3)
                except Exception as e:
                    print(f"❌ Method {i+1} failed: {e}")
                    continue
            
            return self.collabora_process
            else:
            # Launch normally
            subprocess.Popen([executable, self.temp_file_path])
            return None
        
    def find_collabora_window_id(self):
        """Find the LibreOffice window ID"""
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            return self._find_windows_collabora_window()
        elif system == "linux":
            return self._find_linux_collabora_window()
        elif system == "darwin":
            return self._find_macos_collabora_window()
        else:
            return None
    
    def _find_windows_collabora_window(self):
        """Find LibreOffice window on Windows"""
        try:
            import win32gui
            import win32process
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # Get process ID first
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        
                        # Check if this is our LibreOffice process
                        if self.collabora_process and pid == self.collabora_process.pid:
                            print(f"✅ Found our LibreOffice process window: '{window_text}' (PID: {pid})")
                            windows.append(hwnd)
                            return True
                        
                        # Also look for any LibreOffice-related window
                        libreoffice_keywords = ['libreoffice', 'collabora', 'writer', 'calc', 'impress', 'soffice', 'document']
                        if any(keyword in window_text.lower() for keyword in libreoffice_keywords) or \
                           any(keyword in class_name.lower() for keyword in libreoffice_keywords):
                            
                            print(f"Found LibreOffice window: '{window_text}' (PID: {pid})")
                            windows.append(hwnd)
                            
                        # Specifically look for document windows (windows with file extensions in title)
                        if self.temp_file_path and os.path.basename(self.temp_file_path) in window_text:
                            print(f"✅ Found document window: '{window_text}' (PID: {pid})")
                            windows.insert(0, hwnd)  # Put document windows first
                            
                    except Exception as e:
                        print(f"Could not get process ID for window '{window_text}': {e}")
                
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            print(f"Found {len(windows)} LibreOffice windows")
            
            # Return the first matching window
            if windows:
                return windows[0]
            
            # If still no windows, try to find ANY window from our process
            print("🔍 Searching for ANY window from our process...")
            def find_any_window_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if self.collabora_process and pid == self.collabora_process.pid:
                            window_text = win32gui.GetWindowText(hwnd)
                            print(f"Found ANY window from our process: '{window_text}' (PID: {pid})")
                            windows.append(hwnd)
                    except:
                        pass
                return True
            
            windows = []
            win32gui.EnumWindows(find_any_window_callback, windows)
            
            # Return the first window from our process, but prefer windows with titles
            if windows:
                # First try to find a window with a title
                for hwnd in windows:
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_text and len(window_text.strip()) > 0:
                        print(f"✅ Selected window with title: '{window_text}'")
                        return hwnd
                
                # If no window with title, return the first one
                print(f"✅ Selected first available window")
                return windows[0]
        
        return None
    
        except ImportError:
            logging.warning("win32gui not available for Windows window detection")
            return None
        except Exception as e:
            logging.error(f"Error in Windows window detection: {e}")
            return None
            
    def _find_linux_collabora_window(self):
        """Find LibreOffice window on Linux"""
        try:
            result = subprocess.run(['xdotool', 'search', '--name', 'LibreOffice'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                window_ids = result.stdout.strip().split('\n')
                return int(window_ids[0]) if window_ids else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logging.warning("xdotool not available for Linux window detection")
        return None
    
    def _find_macos_collabora_window(self):
        """Find LibreOffice window on macOS"""
        try:
            script = '''
            tell application "System Events"
                set officeWindows to windows of processes whose name contains "LibreOffice"
                if officeWindows is not {} then
                    return id of first item of officeWindows
                end if
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return int(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logging.warning("AppleScript not available for macOS window detection")
        return None
        
    def embed_libreoffice_window(self, parent_widget):
        """Embed LibreOffice window into the parent widget"""
        print("🔍 Starting LibreOffice window embedding process...")
        
        # Wait for LibreOffice to start and show window
        print("⏳ Waiting for LibreOffice to start...")
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            print(f"⏳ Waiting... ({i+1}/30)")
            
            # Try to find the window
            self.window_id = self.find_collabora_window_id()
            if self.window_id:
                print(f"✅ Found LibreOffice window: {self.window_id}")
                # Wait a bit more for the window to fully render
                print("⏳ Waiting for window to fully render...")
                time.sleep(3)
                break
        else:
            print("❌ Could not find LibreOffice window after 30 seconds")
            print("📋 Using fallback preview with detailed status...")
            return self.create_fallback_preview(QWidget(parent_widget), QVBoxLayout())
            
        # Create a container widget
        container = QWidget(parent_widget)
        layout = QVBoxLayout(container)
        
        try:
            print("🔗 Attempting to embed LibreOffice window...")
            # Try to embed the window using platform-specific methods
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                self._embed_windows_window(container, layout)
            elif system == "linux":
                self._embed_linux_window(container, layout)
            elif system == "darwin":
                self._embed_macos_window(container, layout)
            else:
                # Fallback to HTML preview
                return self.create_fallback_preview(container, layout)
            
            print("✅ LibreOffice window embedded successfully!")
            return container
                    
        except Exception as e:
            print(f"❌ Error embedding LibreOffice window: {e}")
            logging.error(f"Error embedding LibreOffice window: {e}")
            # Fallback to HTML preview
            return self.create_fallback_preview(container, layout)
    
    def _embed_windows_window(self, container, layout):
        """Embed window on Windows"""
        try:
            import win32gui
            import win32con
            from PyQt6.QtGui import QWindow
            
            print(f"🔗 Embedding Windows window with handle: {self.window_id}")
            
            # Get the window handle
            hwnd = self.window_id
            
            # Get window info for debugging
            window_text = win32gui.GetWindowText(hwnd)
            print(f"📋 Window title: '{window_text}'")
            
            # Set window style to allow embedding
            try:
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_MDICHILD)
                print("✅ Window style set for embedding")
            except Exception as e:
                print(f"⚠️ Could not set window style: {e}")
                logging.warning(f"Could not set window style: {e}")
            
            # Create QWindow from the window handle
            print("🔗 Creating QWindow from window handle...")
            window = QWindow.fromWinId(hwnd)
            
            # Create container widget
            print("🔗 Creating container widget...")
            widget = QWidget.createWindowContainer(window, container)
            
            # Set minimum size to ensure visibility
            widget.setMinimumSize(800, 600)
            layout.addWidget(widget)
            
            # Force a repaint to ensure the window is visible
            widget.repaint()
            container.repaint()
            
            # Store reference
            self.embedded_widget = widget
            print("✅ Windows window embedded successfully!")
            
        except ImportError:
            print("❌ win32gui not available for Windows window embedding")
            logging.warning("win32gui not available for Windows window embedding")
            raise
        except Exception as e:
            print(f"❌ Error embedding Windows window: {e}")
            logging.error(f"Error embedding Windows window: {e}")
            raise
            
    def _embed_linux_window(self, container, layout):
        """Embed window on Linux"""
        try:
            from PyQt6.QtGui import QWindow
            from PyQt6.QtX11Extras import QX11Info
            
            # Create QWindow from the window ID
            window = QWindow.fromWinId(self.window_id)
            
            # Create container widget
            widget = QWidget.createWindowContainer(window, container)
            layout.addWidget(widget)
            
            # Store reference
            self.embedded_widget = widget
            
        except ImportError:
            logging.warning("QtX11Extras not available for Linux window embedding")
            raise
            
    def _embed_macos_window(self, container, layout):
        """Embed window on macOS"""
        try:
            from PyQt6.QtGui import QWindow
            from PyQt6.QtCocoaExtras import QCocoaWindow
            
            # Create QWindow from the window ID
            window = QWindow.fromWinId(self.window_id)
            
            # Create container widget
            widget = QWidget.createWindowContainer(window, container)
            layout.addWidget(widget)
            
            # Store reference
            self.embedded_widget = widget
            
        except ImportError:
            logging.warning("QtCocoaExtras not available for macOS window embedding")
            raise
    
    def create_fallback_preview(self, container, layout):
        """Create a fallback preview when embedding is not available"""
        # Create a text browser for basic preview
        from PyQt6.QtWidgets import QTextBrowser
        
        preview_browser = QTextBrowser()
        preview_browser.setMinimumHeight(400)
        preview_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                color: #000000;
                font-family: 'Calibri', Arial, sans-serif;
                font-size: 12px;
                padding: 15px;
                border: 1px solid #444444;
            }
        """)
        
        # Create informative content
        content = f"""
📄 Document Preview: {os.path.basename(self.temp_file_path)}

🔍 LibreOffice Embedding Status:
   • LibreOffice Process: {'✅ Running' if self.collabora_process else '❌ Not Running'}
   • Process ID: {self.collabora_process.pid if self.collabora_process else 'N/A'}
   • Window Found: {'✅ Yes' if self.window_id else '❌ No'}
   • Window ID: {self.window_id if self.window_id else 'N/A'}

📋 Document Content:
"""
        
        # Try to extract text content
        try:
            from docx import Document
            doc = Document(self.temp_file_path)
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content += paragraph.text + "\n\n"
            
        except Exception as e:
            content += f"Error reading document: {str(e)}\n\n"
            content += "Please ensure the document is a valid Word (.docx) file."
        
        preview_browser.setPlainText(content)
        layout.addWidget(preview_browser)
        
        # Store reference to the embedder for cleanup
        container.embedder = self
        container.preview_browser = preview_browser
        
        return container
        
    def open_document_in_collabora(self):
        """Open the document in LibreOffice"""
        try:
            executable = self.find_collabora_executable()
            if executable:
                # Launch LibreOffice with the document
                cmd = [executable, self.temp_file_path]
                subprocess.Popen(cmd)
            else:
                # Fallback to system default
                import platform
                if platform.system() == "Windows":
                    os.startfile(self.temp_file_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", self.temp_file_path])
                else:  # Linux
                    subprocess.run(["xdg-open", self.temp_file_path])
        except Exception as e:
            logging.error(f"Error opening document in LibreOffice: {e}")
        
    def refresh_preview(self):
        """Refresh the embedded preview"""
        if self.embedded_widget:
            # Force a repaint
            self.embedded_widget.repaint()
            
            # Alternatively, restart LibreOffice with the file
            if self.collabora_process:
                self.collabora_process.terminate()
                self.collabora_process.wait()
                
            self.launch_collabora_with_file(self.original_file_path, embed=True)
            self.embed_libreoffice_window(self.embedded_widget.parent())
        
    def cleanup(self):
        """Clean up resources"""
        if self.collabora_process:
            try:
                self.collabora_process.terminate()
                self.collabora_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.collabora_process.kill()
            self.collabora_process = None
            
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                os.rmdir(os.path.dirname(self.temp_file_path))
            except OSError:
                pass


class TemplatePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.embedder = None
        self.template_path = None
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Template Preview")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Status information
        self.status_label = QLabel("Checking dependencies...")
        self.status_label.setStyleSheet("color: #666666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Preview area
        self.preview_area = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_area)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.preview_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("Upload Template")
        self.upload_btn.clicked.connect(self.upload_template)
        button_layout.addWidget(self.upload_btn)
        
        self.refresh_btn = QPushButton("Refresh Preview")
        self.refresh_btn.clicked.connect(self.refresh_preview)
        self.refresh_btn.setEnabled(False)
        button_layout.addWidget(self.refresh_btn)
        
        self.open_external_btn = QPushButton("Open in LibreOffice")
        self.open_external_btn.clicked.connect(self.open_in_external)
        self.open_external_btn.setEnabled(False)
        button_layout.addWidget(self.open_external_btn)
        
        layout.addLayout(button_layout)
        
        # Initial placeholder
        self.placeholder = QLabel("No template loaded")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #888888; font-style: italic;")
        self.preview_layout.addWidget(self.placeholder)
        
        # Check dependencies after UI is created
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check and display dependency status"""
        if not hasattr(self, 'embedder'):
            self.embedder = CollaboraOfficeEmbedder()
        
        dependencies = self.embedder.check_dependencies()
        
        status_parts = []
        if dependencies['libreoffice']:
            status_parts.append("✅ LibreOffice")
        else:
            status_parts.append("❌ LibreOffice")
            
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            if dependencies['win32gui']:
                status_parts.append("✅ Windows embedding")
            else:
                status_parts.append("❌ Windows embedding (install pywin32)")
        elif system == "linux":
            if dependencies['xdotool']:
                status_parts.append("✅ Linux embedding")
            else:
                status_parts.append("❌ Linux embedding (install xdotool)")
        elif system == "darwin":
            if dependencies['osascript']:
                status_parts.append("✅ macOS embedding")
            else:
                status_parts.append("❌ macOS embedding")
        
        self.status_label.setText(" | ".join(status_parts))
        
        # Enable/disable upload button based on LibreOffice availability
        self.upload_btn.setEnabled(dependencies['libreoffice'])
        
        if not dependencies['libreoffice']:
            self.placeholder.setText("LibreOffice not found. Please install LibreOffice to use template preview.")
            self.placeholder.setStyleSheet("color: #ff0000; font-style: italic;")
    
    def upload_template(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Template", "", "Word Documents (*.docx)"
        )
        
        if file_path:
            self.load_template(file_path)
    
    def load_template(self, file_path):
        # Clean up previous embedder
        if self.embedder:
            self.embedder.cleanup()
            
        # Clear preview area
        for i in reversed(range(self.preview_layout.count())): 
            self.preview_layout.itemAt(i).widget().setParent(None)
            
        # Store template path
        self.template_path = file_path
        
        # Create new embedder
        self.embedder = CollaboraOfficeEmbedder()
        
        # Update status
        self.status_label.setText("Loading template...")
        
        try:
            # Launch LibreOffice with the file
            self.embedder.launch_collabora_with_file(file_path, embed=True)
            
            # Embed the window
            embedded_widget = self.embedder.embed_libreoffice_window(self.preview_area)
            
            if embedded_widget:
                self.preview_layout.addWidget(embedded_widget)
                self.refresh_btn.setEnabled(True)
                self.open_external_btn.setEnabled(True)
                self.status_label.setText(f"Template loaded: {os.path.basename(file_path)}")
            else:
                # Fallback to HTML preview
                self.placeholder.setText("Template loaded. Using text preview (embedding not available).")
                self.placeholder.setStyleSheet("color: #ff6600; font-style: italic;")
                self.preview_layout.addWidget(self.placeholder)
                self.refresh_btn.setEnabled(True)
                self.open_external_btn.setEnabled(True)
                self.status_label.setText(f"Template loaded (fallback mode): {os.path.basename(file_path)}")
                
        except Exception as e:
            error_msg = f"Failed to load template: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
            self.placeholder.setText(f"Error: {str(e)}")
            self.placeholder.setStyleSheet("color: #ff0000; font-style: italic;")
            self.preview_layout.addWidget(self.placeholder)
            self.status_label.setText("Template loading failed")
    
    def refresh_preview(self):
        if self.embedder and self.template_path:
            self.embedder.refresh_preview()
    
    def open_in_external(self):
        if self.embedder and self.template_path:
            self.embedder.open_document_in_collabora()
    
    def cleanup(self):
        if self.embedder:
            self.embedder.cleanup()


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = QMainWindow()
    main_window.setWindowTitle("LibreOffice Template Preview Demo")
    main_window.setGeometry(100, 100, 1200, 800)
    
    # Create and set the template preview widget
    template_preview = TemplatePreviewWidget()
    main_window.setCentralWidget(template_preview)
    
    # Print diagnostic information
    print("🔍 LibreOffice Integration Diagnostics:")
    print("=" * 50)
    
    embedder = CollaboraOfficeEmbedder()
    
    # Check LibreOffice installation
    libreoffice_path = embedder.find_collabora_executable()
    if libreoffice_path:
        print(f"✅ LibreOffice found at: {libreoffice_path}")
    else:
        print("❌ LibreOffice not found")
    
    # Check dependencies
    dependencies = embedder.check_dependencies()
    print("\n📋 Dependencies:")
    for dep, available in dependencies.items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")
    
    # Platform-specific checks
    import platform
    system = platform.system()
    print(f"\n🖥️  Platform: {system}")
    
    if system == "Windows":
        try:
            import win32gui
            print("✅ win32gui available")
        except ImportError:
            print("❌ win32gui not available - install with: pip install pywin32")
    elif system == "Linux":
        try:
            result = subprocess.run(['which', 'xdotool'], capture_output=True)
            if result.returncode == 0:
                print("✅ xdotool available")
            else:
                print("❌ xdotool not available - install with: sudo apt-get install xdotool")
        except:
            print("❌ xdotool check failed")
    
    print("\n" + "=" * 50)
    
    main_window.show()
    sys.exit(app.exec())
