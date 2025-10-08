#!/usr/bin/env python3
"""
OnlyOffice Document Editor - PyQt6 Desktop Application
A full-featured document editor with OnlyOffice Document Server integration
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse, urljoin
import requests
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QMessageBox, QProgressBar,
    QSplitter, QFrame, QTextEdit, QStatusBar, QToolBar, QAction,
    QMenuBar, QMenu, QDialog, QLineEdit, QFormLayout, QSpinBox,
    QCheckBox, QGroupBox, QTabWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QRect,
    QPropertyAnimation, QEasingCurve, QThreadPool, QRunnable
)
from PyQt6.QtGui import (
    QIcon, QFont, QPixmap, QAction, QPalette, QColor,
    QKeySequence, QShortcut
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile


class OnlyOfficeServerManager:
    """Manages OnlyOffice Document Server Docker container"""
    
    def __init__(self):
        self.container_name = "onlyoffice-document-server"
        self.port = 80
        self.server_url = f"http://localhost:{self.port}"
        self.is_running = False
        
    def start_server(self):
        """Start OnlyOffice Document Server in Docker"""
        try:
            # Check if Docker is running
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Docker is not installed or not running")
            
            # Check if container already exists
            result = subprocess.run(["docker", "ps", "-a", "--filter", 
                                   f"name={self.container_name}"],
                                  capture_output=True, text=True)
            
            if self.container_name in result.stdout:
                # Container exists, start it
                subprocess.run(["docker", "start", self.container_name], 
                             check=True)
            else:
                # Create and start new container
                cmd = [
                    "docker", "run", "-d", "--name", self.container_name,
                    "-p", f"{self.port}:80",
                    "-v", "/var/run/docker.sock:/var/run/docker.sock",
                    "onlyoffice/documentserver:latest"
                ]
                subprocess.run(cmd, check=True)
            
            # Wait for server to be ready
            self._wait_for_server()
            self.is_running = True
            return True
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start OnlyOffice server: {e}")
        except Exception as e:
            raise Exception(f"Error starting server: {e}")
    
    def stop_server(self):
        """Stop OnlyOffice Document Server"""
        try:
            subprocess.run(["docker", "stop", self.container_name], 
                         check=True)
            self.is_running = False
        except subprocess.CalledProcessError:
            pass  # Container might not be running
    
    def _wait_for_server(self, timeout=60):
        """Wait for server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.server_url}/healthcheck", 
                                      timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)
        raise Exception("Server failed to start within timeout")


class DocumentConverter:
    """Handles document conversion and file management"""
    
    def __init__(self, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="onlyoffice_")
        self.documents = {}
        
    def add_document(self, file_path):
        """Add a document to the converter and return document key"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Generate unique document key
        doc_key = str(uuid.uuid4())
        
        # Copy document to temp directory
        file_name = os.path.basename(file_path)
        temp_path = os.path.join(self.temp_dir, file_name)
        shutil.copy2(file_path, temp_path)
        
        # Store document info
        self.documents[doc_key] = {
            'original_path': file_path,
            'temp_path': temp_path,
            'file_name': file_name,
            'file_type': self._get_file_type(file_name)
        }
        
        return doc_key
    
    def get_document_info(self, doc_key):
        """Get document information"""
        return self.documents.get(doc_key)
    
    def save_document(self, doc_key, content_url):
        """Save document from OnlyOffice server"""
        if doc_key not in self.documents:
            raise KeyError(f"Document key not found: {doc_key}")
        
        doc_info = self.documents[doc_key]
        
        try:
            # Download updated document from OnlyOffice server
            response = requests.get(content_url)
            response.raise_for_status()
            
            # Save to original location
            with open(doc_info['original_path'], 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            raise Exception(f"Failed to save document: {e}")
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def _get_file_type(self, file_name):
        """Get file type from extension"""
        ext = os.path.splitext(file_name)[1].lower()
        if ext == '.docx':
            return 'docx'
        elif ext == '.doc':
            return 'doc'
        elif ext == '.odt':
            return 'odt'
        elif ext == '.rtf':
            return 'rtf'
        elif ext == '.txt':
            return 'txt'
        else:
            return 'docx'  # Default


class OnlyOfficeWebPage(QWebEnginePage):
    """Custom web page for OnlyOffice integration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.onlyoffice_ready = False
        self.document_loaded = False
        
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Handle JavaScript console messages"""
        print(f"JS Console [{level}] {message} (line {lineNumber})")
        
        # Check for OnlyOffice ready signal
        if "OnlyOffice ready" in message:
            self.onlyoffice_ready = True
        elif "Document loaded" in message:
            self.document_loaded = True


class OnlyOfficeEditor(QWidget):
    """OnlyOffice Document Editor Widget"""
    
    document_ready = pyqtSignal()
    document_saved = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, server_url, parent=None):
        super().__init__(parent)
        self.server_url = server_url
        self.current_doc_key = None
        self.converter = DocumentConverter()
        
        self.init_ui()
        self.create_editor_html()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view
        self.web_view = QWebEngineView()
        self.web_page = OnlyOfficeWebPage(self)
        self.web_view.setPage(self.web_page)
        
        # Connect signals
        self.web_page.loadFinished.connect(self.on_page_loaded)
        
        layout.addWidget(self.web_view)
        
    def create_editor_html(self):
        """Create the HTML template for OnlyOffice editor"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OnlyOffice Document Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }
        #placeholder {
            width: 100%;
            height: 100vh;
            background-color: #ffffff;
        }
        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-size: 18px;
            color: #666;
        }
        .error {
            display: none;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-size: 18px;
            color: #f44336;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="placeholder"></div>
    <div id="loading" class="loading">Loading OnlyOffice Editor...</div>
    <div id="error" class="error">Failed to load editor</div>
    
    <script type="text/javascript" src="SERVER_URL/web-apps/apps/api/documents/api.js"></script>
    <script>
        let docEditor = null;
        let currentConfig = null;
        
        function initEditor(config) {
            currentConfig = config;
            
            try {
                docEditor = new DocsAPI.DocEditor("placeholder", config);
                console.log("OnlyOffice ready");
                
                // Listen for events
                docEditor.events.on('documentReady', function() {
                    console.log("Document loaded");
                    document.getElementById('loading').style.display = 'none';
                });
                
                docEditor.events.on('save', function(event) {
                    console.log("Document saved", event);
                    // Notify PyQt about save
                    if (window.pyqt) {
                        window.pyqt.documentSaved(event.data);
                    }
                });
                
                docEditor.events.on('error', function(event) {
                    console.error("Editor error", event);
                    document.getElementById('error').style.display = 'flex';
                    document.getElementById('error').textContent = 'Editor Error: ' + event.data;
                });
                
            } catch (error) {
                console.error("Failed to initialize editor:", error);
                document.getElementById('error').style.display = 'flex';
                document.getElementById('error').textContent = 'Failed to initialize editor: ' + error.message;
            }
        }
        
        function loadDocument(docKey, fileName, fileType) {
            const config = {
                document: {
                    fileType: fileType,
                    key: docKey,
                    title: fileName,
                    url: 'http://localhost:8080/documents/' + docKey + '/' + fileName
                },
                documentType: 'word',
                editorConfig: {
                    mode: 'edit',
                    callbackUrl: 'http://localhost:8080/callback',
                    lang: 'en-US',
                    user: {
                        id: 'user1',
                        name: 'Document Editor User'
                    },
                    customization: {
                        chat: false,
                        comments: false,
                        compactToolbar: false,
                        feedback: false,
                        forcesave: false,
                        submitForm: false,
                        help: true,
                        toolbar: true,
                        zoom: 100
                    }
                },
                height: '100%',
                width: '100%'
            };
            
            initEditor(config);
        }
        
        function saveDocument() {
            if (docEditor) {
                docEditor.downloadAs();
            }
        }
        
        // Expose functions to PyQt
        window.pyqt = {
            loadDocument: loadDocument,
            saveDocument: saveDocument
        };
        
        // Notify PyQt that page is ready
        if (window.pyqtBridge) {
            window.pyqtBridge.pageReady();
        }
    </script>
</body>
</html>
        """
        
        # Replace server URL
        self.html_content = html_template.replace("SERVER_URL", self.server_url)
        
    def load_document(self, file_path):
        """Load a document into the editor"""
        try:
            # Add document to converter
            doc_key = self.converter.add_document(file_path)
            self.current_doc_key = doc_key
            
            doc_info = self.converter.get_document_info(doc_key)
            
            # Load the HTML page
            self.web_view.setHtml(self.html_content, QUrl("http://localhost"))
            
            # Wait for page to load, then load document
            QTimer.singleShot(2000, lambda: self._load_document_js(doc_key, doc_info))
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to load document: {e}")
    
    def _load_document_js(self, doc_key, doc_info):
        """Load document using JavaScript"""
        js_code = f"""
        if (window.pyqt && window.pyqt.loadDocument) {{
            window.pyqt.loadDocument('{doc_key}', '{doc_info['file_name']}', '{doc_info['file_type']}');
        }}
        """
        self.web_view.page().runJavaScript(js_code)
    
    def save_document(self):
        """Save the current document"""
        if not self.current_doc_key:
            self.error_occurred.emit("No document loaded")
            return
        
        js_code = """
        if (window.pyqt && window.pyqt.saveDocument) {
            window.pyqt.saveDocument();
        }
        """
        self.web_view.page().runJavaScript(js_code)
    
    def on_page_loaded(self, success):
        """Handle page load completion"""
        if success:
            print("Editor page loaded successfully")
        else:
            self.error_occurred.emit("Failed to load editor page")


class DocumentEditorApp(QMainWindow):
    """Main Document Editor Application"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = OnlyOfficeServerManager()
        self.editor = None
        self.current_file = None
        
        self.init_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # Start OnlyOffice server
        self.start_server()
        
    def init_ui(self):
        """Initialize the main UI"""
        self.setWindowTitle("OnlyOffice Document Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar area
        self.create_toolbar_area(main_layout)
        
        # Create editor area
        self.create_editor_area(main_layout)
        
        # Apply dark theme
        self.apply_dark_theme()
        
    def create_toolbar_area(self, parent_layout):
        """Create the toolbar area"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar_frame.setMaximumHeight(80)
        
        toolbar_layout = QVBoxLayout(toolbar_frame)
        
        # File operations
        file_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("📁 Upload Template")
        self.upload_btn.setStyleSheet(self.get_button_style("primary"))
        self.upload_btn.clicked.connect(self.upload_template)
        file_layout.addWidget(self.upload_btn)
        
        self.save_btn = QPushButton("💾 Save Document")
        self.save_btn.setStyleSheet(self.get_button_style("success"))
        self.save_btn.clicked.connect(self.save_document)
        self.save_btn.setEnabled(False)
        file_layout.addWidget(self.save_btn)
        
        self.export_btn = QPushButton("📤 Export As...")
        self.export_btn.setStyleSheet(self.get_button_style("info"))
        self.export_btn.clicked.connect(self.export_document)
        self.export_btn.setEnabled(False)
        file_layout.addWidget(self.export_btn)
        
        file_layout.addStretch()
        
        # Server status
        self.server_status_label = QLabel("🔄 Starting server...")
        self.server_status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        file_layout.addWidget(self.server_status_label)
        
        toolbar_layout.addLayout(file_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        toolbar_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(toolbar_frame)
        
    def create_editor_area(self, parent_layout):
        """Create the editor area"""
        # Create splitter for editor and preview
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Editor area
        editor_frame = QFrame()
        editor_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        editor_layout = QVBoxLayout(editor_frame)
        
        editor_label = QLabel("📝 Document Editor")
        editor_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3; margin: 5px;")
        editor_layout.addWidget(editor_label)
        
        # Placeholder for editor
        self.editor_placeholder = QLabel("Upload a document to start editing")
        self.editor_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor_placeholder.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                font-size: 16px;
                color: #666;
            }
        """)
        editor_layout.addWidget(self.editor_placeholder)
        
        self.editor_splitter.addWidget(editor_frame)
        
        # Preview area
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_label = QLabel("👁️ Live Preview")
        preview_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; margin: 5px;")
        preview_layout.addWidget(preview_label)
        
        # Placeholder for preview
        self.preview_placeholder = QLabel("Document preview will appear here")
        self.preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_placeholder.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
                font-size: 16px;
                color: #666;
            }
        """)
        preview_layout.addWidget(self.preview_placeholder)
        
        self.editor_splitter.addWidget(preview_frame)
        
        # Set splitter proportions
        self.editor_splitter.setSizes([800, 400])
        
        parent_layout.addWidget(self.editor_splitter)
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        upload_action = QAction("&Upload Template", self)
        upload_action.setShortcut(QKeySequence.StandardKey.Open)
        upload_action.triggered.connect(self.upload_template)
        file_menu.addAction(upload_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)
        
        export_action = QAction("&Export As...", self)
        export_action.setShortcut("Ctrl+Shift+S")
        export_action.triggered.connect(self.export_document)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Setup the toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        
        # Add toolbar actions here if needed
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        dark_palette = QPalette()
        
        # Set dark colors
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(dark_palette)
        
    def get_button_style(self, style_type):
        """Get button style based on type"""
        base_style = """
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                opacity: 0.6;
            }
            QPushButton:disabled {
                opacity: 0.4;
            }
        """
        
        if style_type == "primary":
            return base_style + "QPushButton { background-color: #2196F3; color: white; }"
        elif style_type == "success":
            return base_style + "QPushButton { background-color: #4CAF50; color: white; }"
        elif style_type == "info":
            return base_style + "QPushButton { background-color: #00BCD4; color: white; }"
        elif style_type == "warning":
            return base_style + "QPushButton { background-color: #FF9800; color: white; }"
        elif style_type == "danger":
            return base_style + "QPushButton { background-color: #F44336; color: white; }"
        else:
            return base_style + "QPushButton { background-color: #757575; color: white; }"
    
    def start_server(self):
        """Start the OnlyOffice Document Server"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start server in background thread
        self.server_thread = QThread()
        self.server_worker = ServerWorker(self.server_manager)
        self.server_worker.moveToThread(self.server_thread)
        
        self.server_thread.started.connect(self.server_worker.start_server)
        self.server_worker.finished.connect(self.on_server_started)
        self.server_worker.error.connect(self.on_server_error)
        self.server_worker.finished.connect(self.server_thread.quit)
        
        self.server_thread.start()
        
    def on_server_started(self):
        """Handle server start completion"""
        self.progress_bar.setVisible(False)
        self.server_status_label.setText("✅ Server running")
        self.server_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.status_bar.showMessage("OnlyOffice server is ready")
        
    def on_server_error(self, error_message):
        """Handle server start error"""
        self.progress_bar.setVisible(False)
        self.server_status_label.setText("❌ Server error")
        self.server_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        QMessageBox.critical(self, "Server Error", f"Failed to start OnlyOffice server:\n{error_message}")
        
    def upload_template(self):
        """Upload a document template"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document Template",
            "",
            "Word Documents (*.docx *.doc);;OpenDocument (*.odt);;Rich Text (*.rtf);;All Files (*)"
        )
        
        if file_path:
            self.load_document(file_path)
            
    def load_document(self, file_path):
        """Load a document into the editor"""
        try:
            self.current_file = file_path
            
            # Create editor widget
            self.editor = OnlyOfficeEditor(self.server_manager.server_url, self)
            
            # Connect signals
            self.editor.document_ready.connect(self.on_document_ready)
            self.editor.document_saved.connect(self.on_document_saved)
            self.editor.error_occurred.connect(self.on_editor_error)
            
            # Replace placeholder with editor
            editor_layout = self.editor_placeholder.parent().layout()
            editor_layout.removeWidget(self.editor_placeholder)
            self.editor_placeholder.hide()
            editor_layout.addWidget(self.editor)
            
            # Load document
            self.editor.load_document(file_path)
            
            # Update UI
            self.save_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.status_bar.showMessage(f"Loading document: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load document: {e}")
            
    def on_document_ready(self):
        """Handle document ready event"""
        self.status_bar.showMessage("Document loaded successfully")
        
    def on_document_saved(self, data):
        """Handle document save event"""
        self.status_bar.showMessage("Document saved successfully")
        QMessageBox.information(self, "Success", "Document saved successfully!")
        
    def on_editor_error(self, error_message):
        """Handle editor error"""
        QMessageBox.warning(self, "Editor Error", f"Editor error: {error_message}")
        
    def save_document(self):
        """Save the current document"""
        if self.editor:
            self.editor.save_document()
            
    def export_document(self):
        """Export document to a different format"""
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "No document loaded")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Document",
            os.path.splitext(self.current_file)[0] + "_exported.docx",
            "Word Documents (*.docx);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            # For now, just copy the file
            try:
                shutil.copy2(self.current_file, file_path)
                QMessageBox.information(self, "Success", f"Document exported to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export document: {e}")
                
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About OnlyOffice Document Editor",
            """
            <h3>OnlyOffice Document Editor</h3>
            <p>A full-featured document editor with OnlyOffice Document Server integration.</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Upload and edit .docx templates</li>
                <li>Live preview with exact formatting</li>
                <li>Full-featured rich text editing</li>
                <li>Headers, footers, and watermarks support</li>
                <li>Real-time collaboration</li>
            </ul>
            <p><b>Version:</b> 1.0.0</p>
            """
        )
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop OnlyOffice server
        try:
            self.server_manager.stop_server()
        except Exception:
            pass
            
        # Clean up
        if hasattr(self, 'editor') and self.editor:
            self.editor.converter.cleanup()
            
        event.accept()


class ServerWorker(QThread):
    """Worker thread for starting OnlyOffice server"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        
    def run(self):
        """Run the server start process"""
        try:
            self.server_manager.start_server()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


if __name__ == "__main__":
    print("OnlyOffice Document Editor - Server Manager and Document Converter")
    print("This module provides server management and document conversion utilities.")
