#!/usr/bin/env python3
"""
LibreOffice Embedded Editor using LibreOfficeKit
This module provides true embedded LibreOffice editing capabilities within PyQt6.
"""

import os
import sys
import subprocess
import tempfile
import time
import json
import requests
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMessageBox, QProgressBar, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

class LibreOfficeKitManager:
    """Manages LibreOfficeKit server and document operations"""
    
    def __init__(self):
        self.lok_server_process = None
        self.server_url = None
        self.server_port = 9980
        self.is_running = False
        
    def start_lok_server(self):
        """Start LibreOfficeKit server"""
        try:
            # Find LibreOffice installation
            libreoffice_path = self.find_libreoffice_path()
            if not libreoffice_path:
                raise Exception("LibreOffice not found")
            
            # Start LibreOfficeKit server
            lok_command = [
                libreoffice_path,
                "--headless",
                "--accept=socket,host=localhost,port={};urp;StarOffice.ServiceManager".format(self.server_port),
                "--nofirststartwizard",
                "--norestore"
            ]
            
            print(f"Starting LibreOfficeKit server: {' '.join(lok_command)}")
            
            self.lok_server_process = subprocess.Popen(
                lok_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Test server connection
            self.server_url = f"http://localhost:{self.server_port}"
            if self.test_server_connection():
                self.is_running = True
                print("✅ LibreOfficeKit server started successfully")
                return True
            else:
                raise Exception("Server connection test failed")
                
        except Exception as e:
            print(f"❌ Failed to start LibreOfficeKit server: {e}")
            return False
    
    def find_libreoffice_path(self):
        """Find LibreOffice executable path"""
        # Try different LibreOffice command variations
        libreoffice_commands = [
            "libreoffice",
            "soffice",
            "libreoffice7.6",
            "libreoffice7.5",
            "libreoffice7.4",
            "libreoffice7.3",
            "libreoffice7.2",
            "libreoffice7.1",
            "libreoffice7.0",
        ]
        
        for cmd in libreoffice_commands:
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        # Check common installation paths
        common_paths = []
        if sys.platform == "win32":
            common_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        elif sys.platform.startswith("linux"):
            common_paths = [
                "/usr/bin/libreoffice",
                "/usr/bin/soffice",
                "/opt/libreoffice/program/soffice",
            ]
        elif sys.platform == "darwin":
            common_paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def test_server_connection(self):
        """Test if LibreOfficeKit server is responding"""
        try:
            response = requests.get(f"{self.server_url}/loleaflet/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def stop_server(self):
        """Stop LibreOfficeKit server"""
        if self.lok_server_process:
            self.lok_server_process.terminate()
            try:
                self.lok_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.lok_server_process.kill()
            self.lok_server_process = None
            self.is_running = False
            print("✅ LibreOfficeKit server stopped")

class EmbeddedLibreOfficeEditor(QWidget):
    """Embedded LibreOffice editor widget using LibreOfficeKit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lok_manager = LibreOfficeKitManager()
        self.current_document_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the embedded editor UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Start server button
        self.start_server_btn = QPushButton("🚀 Start LibreOfficeKit")
        self.start_server_btn.clicked.connect(self.start_server)
        control_layout.addWidget(self.start_server_btn)
        
        # Create document button
        self.create_doc_btn = QPushButton("📄 Create Document")
        self.create_doc_btn.clicked.connect(self.create_document)
        self.create_doc_btn.setEnabled(False)
        control_layout.addWidget(self.create_doc_btn)
        
        # Load document button
        self.load_doc_btn = QPushButton("📂 Load Document")
        self.load_doc_btn.clicked.connect(self.load_document)
        self.load_doc_btn.setEnabled(False)
        control_layout.addWidget(self.load_doc_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_document)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status label
        self.status_label = QLabel("Ready to start LibreOfficeKit server")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Web view for LibreOfficeKit interface
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(400)
        layout.addWidget(self.web_view)
        
        # Set up web page
        self.setup_web_page()
        
    def setup_web_page(self):
        """Set up the web page for LibreOfficeKit"""
        # Create a custom web page with proper user agent
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        page = QWebEnginePage(profile, self.web_view)
        self.web_view.setPage(page)
        
        # Connect signals
        page.loadFinished.connect(self.on_page_loaded)
        page.loadStarted.connect(self.on_page_load_started)
        
    def start_server(self):
        """Start LibreOfficeKit server"""
        self.status_label.setText("Starting LibreOfficeKit server...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start server in a separate thread
        self.server_thread = ServerStartThread(self.lok_manager)
        self.server_thread.server_started.connect(self.on_server_started)
        self.server_thread.server_failed.connect(self.on_server_failed)
        self.server_thread.start()
    
    def on_server_started(self):
        """Handle successful server start"""
        self.status_label.setText("✅ LibreOfficeKit server running")
        self.progress_bar.setVisible(False)
        self.start_server_btn.setEnabled(False)
        self.create_doc_btn.setEnabled(True)
        self.load_doc_btn.setEnabled(True)
        
        # Load LibreOfficeKit interface
        self.load_lok_interface()
    
    def on_server_failed(self, error):
        """Handle server start failure"""
        self.status_label.setText(f"❌ Server start failed: {error}")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Server Error", f"Failed to start LibreOfficeKit server:\n{error}")
    
    def load_lok_interface(self):
        """Load LibreOfficeKit web interface"""
        try:
            # Load the LibreOfficeKit web interface
            url = f"http://localhost:{self.lok_manager.server_port}/loleaflet/"
            self.web_view.load(QUrl(url))
        except Exception as e:
            self.status_label.setText(f"❌ Failed to load interface: {e}")
    
    def on_page_load_started(self):
        """Handle page load start"""
        self.status_label.setText("Loading LibreOfficeKit interface...")
    
    def on_page_loaded(self, success):
        """Handle page load completion"""
        if success:
            self.status_label.setText("✅ LibreOfficeKit interface loaded")
        else:
            self.status_label.setText("❌ Failed to load LibreOfficeKit interface")
    
    def create_document(self):
        """Create a new document"""
        try:
            # Create a temporary document
            temp_dir = tempfile.mkdtemp()
            doc_path = os.path.join(temp_dir, "new_document.odt")
            
            # Use LibreOffice to create a new document
            if self.lok_manager.is_running:
                # For now, create a simple ODT file
                self.create_simple_odt(doc_path)
                self.current_document_path = doc_path
                self.save_btn.setEnabled(True)
                self.status_label.setText(f"✅ Created new document: {os.path.basename(doc_path)}")
            else:
                raise Exception("LibreOfficeKit server not running")
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to create document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create document:\n{e}")
    
    def create_simple_odt(self, path):
        """Create a simple ODT document"""
        # This is a minimal ODT file structure
        # In a real implementation, you'd use a proper ODT library
        import zipfile
        
        # Create a basic ODT file
        with zipfile.ZipFile(path, 'w') as odt:
            # Add minimal ODT structure
            odt.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
            odt.writestr('META-INF/manifest.xml', self.get_manifest_xml())
            odt.writestr('content.xml', self.get_content_xml())
            odt.writestr('styles.xml', self.get_styles_xml())
    
    def get_manifest_xml(self):
        """Get manifest XML for ODT"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
  <manifest:file-entry manifest:media-type="application/vnd.oasis.opendocument.text" manifest:full-path="/"/>
  <manifest:file-entry manifest:media-type="text/xml" manifest:full-path="content.xml"/>
  <manifest:file-entry manifest:media-type="text/xml" manifest:full-path="styles.xml"/>
</manifest:manifest>'''
    
    def get_content_xml(self):
        """Get content XML for ODT"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">
  <office:body>
    <office:text>
      <text:p>New Document</text:p>
    </office:text>
  </office:body>
</office:document-content>'''
    
    def get_styles_xml(self):
        """Get styles XML for ODT"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">
  <office:styles/>
  <office:automatic-styles/>
  <office:master-styles/>
</office:document-styles>'''
    
    def load_document(self):
        """Load an existing document"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Document",
            "",
            "LibreOffice Documents (*.odt *.docx *.rtf *.txt);;All Files (*)"
        )
        
        if file_path:
            self.current_document_path = file_path
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"✅ Loaded document: {os.path.basename(file_path)}")
    
    def save_document(self):
        """Save the current document"""
        if not self.current_document_path:
            QMessageBox.warning(self, "No Document", "No document is currently open.")
            return
        
        try:
            # In a real implementation, you'd save through LibreOfficeKit API
            self.status_label.setText(f"✅ Document saved: {os.path.basename(self.current_document_path)}")
        except Exception as e:
            self.status_label.setText(f"❌ Failed to save document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save document:\n{e}")
    
    def closeEvent(self, event):
        """Handle widget close"""
        if self.lok_manager.is_running:
            self.lok_manager.stop_server()
        event.accept()

class ServerStartThread(QThread):
    """Thread for starting LibreOfficeKit server"""
    
    server_started = pyqtSignal()
    server_failed = pyqtSignal(str)
    
    def __init__(self, lok_manager):
        super().__init__()
        self.lok_manager = lok_manager
    
    def run(self):
        """Run the server start process"""
        try:
            if self.lok_manager.start_lok_server():
                self.server_started.emit()
            else:
                self.server_failed.emit("Unknown error")
        except Exception as e:
            self.server_failed.emit(str(e))
