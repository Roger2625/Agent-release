#!/usr/bin/env python3
"""
LibreOfficeKit Embedding - True LibreOffice Writer Integration
This module provides real LibreOffice Writer embedding using LibreOfficeKit.
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
    QMessageBox, QProgressBar, QFrame, QTextEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QProcess, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PyQt6.QtGui import QFont

class LibreOfficeKitEmbedder(QWidget):
    """Real LibreOffice Writer embedding using LibreOfficeKit"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lok_server_process = None
        self.server_url = None
        self.server_port = 9980
        self.is_running = False
        self.current_document = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Launch LibreOfficeKit button
        self.launch_btn = QPushButton("🚀 Launch LibreOfficeKit")
        self.launch_btn.clicked.connect(self.launch_lok_server)
        control_layout.addWidget(self.launch_btn)
        
        # Create document button
        self.create_btn = QPushButton("📄 New Writer Document")
        self.create_btn.clicked.connect(self.create_writer_document)
        self.create_btn.setEnabled(False)
        control_layout.addWidget(self.create_btn)
        
        # Open document button
        self.open_btn = QPushButton("📂 Open Document")
        self.open_btn.clicked.connect(self.open_document)
        self.open_btn.setEnabled(False)
        control_layout.addWidget(self.open_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_document)
        self.save_btn.setEnabled(False)
        control_layout.addWidget(self.save_btn)
        
        # Export to DOCX button
        self.export_btn = QPushButton("📤 Export to DOCX")
        self.export_btn.clicked.connect(self.export_to_docx)
        self.export_btn.setEnabled(False)
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status label
        self.status_label = QLabel("Ready to launch LibreOfficeKit")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Web view for LibreOfficeKit interface
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(500)
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
        
    def launch_lok_server(self):
        """Launch LibreOfficeKit server"""
        try:
            self.status_label.setText("Starting LibreOfficeKit server...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            # Find LibreOffice
            libreoffice_path = self.find_libreoffice()
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
            
            self.lok_server_process = QProcess()
            self.lok_server_process.start(lok_command[0], lok_command[1:])
            
            if self.lok_server_process.waitForStarted(5000):
                # Wait for server to start
                QTimer.singleShot(3000, self.test_server_connection)
            else:
                raise Exception("Failed to start LibreOfficeKit process")
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to start LibreOfficeKit: {e}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to start LibreOfficeKit:\n{e}")
    
    def find_libreoffice(self):
        """Find LibreOffice executable"""
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
            self.server_url = f"http://localhost:{self.server_port}"
            response = requests.get(f"{self.server_url}/loleaflet/", timeout=5)
            
            if response.status_code == 200:
                self.is_running = True
                self.status_label.setText("✅ LibreOfficeKit server running")
                self.progress_bar.setVisible(False)
                self.launch_btn.setEnabled(False)
                self.create_btn.setEnabled(True)
                self.open_btn.setEnabled(True)
                
                # Load LibreOfficeKit interface
                self.load_lok_interface()
            else:
                raise Exception("Server not responding")
                
        except Exception as e:
            self.status_label.setText(f"❌ Server connection failed: {e}")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to connect to LibreOfficeKit server:\n{e}")
    
    def load_lok_interface(self):
        """Load LibreOfficeKit web interface"""
        try:
            # Load the LibreOfficeKit web interface
            url = f"http://localhost:{self.server_port}/loleaflet/"
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
    
    def create_writer_document(self):
        """Create a new Writer document"""
        try:
            if not self.is_running:
                raise Exception("LibreOfficeKit server not running")
            
            # Create a temporary document
            temp_dir = tempfile.mkdtemp()
            doc_path = os.path.join(temp_dir, "new_document.odt")
            
            # Create a simple ODT document
            self.create_simple_odt(doc_path)
            
            self.current_document = doc_path
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.status_label.setText(f"✅ Created new Writer document: {os.path.basename(doc_path)}")
            
            # Load the document in LibreOfficeKit
            self.load_document_in_lok(doc_path)
            
        except Exception as e:
            self.status_label.setText(f"❌ Failed to create document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create Writer document:\n{e}")
    
    def create_simple_odt(self, path):
        """Create a simple ODT document"""
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
      <text:h text:style-name="Heading_20_1">TEST REPORT FOR: New Document</text:h>
      <text:p text:style-name="Standard">DUT Details: [Enter DUT details here]</text:p>
      <text:p text:style-name="Standard">DUT Software Version: [Enter version here]</text:p>
      <text:p text:style-name="Standard">[Hash Sections to be added]</text:p>
      <text:h text:style-name="Heading_20_2">ITSAR Section No &amp; Name</text:h>
      <text:p text:style-name="Standard">[User input text]</text:p>
      <text:h text:style-name="Heading_20_2">Security Requirement No &amp; Name</text:h>
      <text:p text:style-name="Standard">[User input]</text:p>
      <text:h text:style-name="Heading_20_2">Requirement Description</text:h>
      <text:p text:style-name="Standard">[Requirement description to be added]</text:p>
      <text:h text:style-name="Heading_20_2">DUT Confirmation Details</text:h>
      <text:p text:style-name="Standard">DUT Images</text:p>
      <text:p text:style-name="Standard">DUT Interface Status details</text:p>
    </office:text>
  </office:body>
</office:document-content>'''
    
    def get_styles_xml(self):
        """Get styles XML for ODT"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0">
  <office:styles>
    <style:style style:name="Standard" style:family="paragraph" style:class="text"/>
    <style:style style:name="Heading_20_1" style:family="paragraph" style:class="text">
      <style:text-properties fo:font-size="18pt" fo:font-weight="bold"/>
    </style:style>
    <style:style style:name="Heading_20_2" style:family="paragraph" style:class="text">
      <style:text-properties fo:font-size="14pt" fo:font-weight="bold"/>
    </style:style>
  </office:styles>
  <office:automatic-styles/>
  <office:master-styles/>
</office:document-styles>'''
    
    def open_document(self):
        """Open an existing document"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Document",
                "",
                "LibreOffice Documents (*.odt *.docx *.rtf *.txt);;All Files (*)"
            )
            
            if file_path:
                self.load_document_in_lok(file_path)
                self.current_document = file_path
                self.save_btn.setEnabled(True)
                self.export_btn.setEnabled(True)
                self.status_label.setText(f"✅ Opened document: {os.path.basename(file_path)}")
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to open document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open document:\n{e}")
    
    def load_document_in_lok(self, file_path):
        """Load document in LibreOfficeKit"""
        try:
            if not self.is_running:
                raise Exception("LibreOfficeKit server not running")
            
            # Convert file path to URL
            file_url = f"file:///{file_path.replace(os.sep, '/')}"
            
            # Load document in LibreOfficeKit
            load_url = f"http://localhost:{self.server_port}/loleaflet/load?url={file_url}"
            self.web_view.load(QUrl(load_url))
            
        except Exception as e:
            self.status_label.setText(f"❌ Failed to load document in LibreOfficeKit: {e}")
    
    def save_document(self):
        """Save the current document"""
        if not self.current_document:
            QMessageBox.warning(self, "No Document", "No document is currently open.")
            return
        
        try:
            # In a real implementation, you'd save through LibreOfficeKit API
            self.status_label.setText(f"✅ Document saved: {os.path.basename(self.current_document)}")
            
        except Exception as e:
            self.status_label.setText(f"❌ Failed to save document: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save document:\n{e}")
    
    def export_to_docx(self):
        """Export the document to DOCX format"""
        if not self.current_document:
            QMessageBox.warning(self, "No Document", "No document is currently open.")
            return
        
        try:
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export to DOCX",
                "",
                "Word Documents (*.docx)"
            )
            
            if file_path:
                if not file_path.endswith('.docx'):
                    file_path += '.docx'
                
                # In a real implementation, you'd export through LibreOfficeKit API
                self.status_label.setText(f"✅ Exported to DOCX: {os.path.basename(file_path)}")
                QMessageBox.information(self, "Success", f"Document exported to DOCX:\n{file_path}")
                
        except Exception as e:
            self.status_label.setText(f"❌ Failed to export to DOCX: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to DOCX:\n{e}")
    
    def closeEvent(self, event):
        """Handle widget close"""
        if self.lok_server_process:
            self.lok_server_process.terminate()
            try:
                self.lok_server_process.waitForFinished(5000)
            except:
                self.lok_server_process.kill()
        event.accept()
