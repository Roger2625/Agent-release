#1
#!/usr/bin/env python3
"""
Standalone Export Code and Files Pages
Extracted from Security Report Generator

This file contains the "Export Code" and "Files" pages functionality
that can be integrated into other PyQt6 applications.
"""

import os
import sys
import json
import shutil
import zipfile
import mimetypes
import subprocess
import platform
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHeaderView, QTextEdit, QDialog, QFileDialog, QInputDialog,
    QMessageBox, QMenu, QSplitter, QStackedWidget, QListWidget,
    QListWidgetItem, QTextBrowser, QGroupBox, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPixmap, QAction, QIcon, QPainter
from PyQt6.QtWidgets import QApplication
from PyQt6.QtSvg import QSvgRenderer

# --- Logging Setup ---
def setup_export_logging():
    """Setup logging to save debug logs to ~/.wingzai/logs/ with timestamps"""
    try:
        # Create logs directory
        logs_dir = os.path.expanduser("~/.wingzai/logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"export_code_and_files_{timestamp}.log"
        log_path = os.path.join(logs_dir, log_filename)
        
        # Clear any existing handlers to avoid conflicts
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Also log to console
            ],
            force=True  # Force reconfiguration
        )
        
        # Create logger for export code and files
        logger = logging.getLogger('export_code_and_files')
        logger.setLevel(logging.DEBUG)
        logger.info(f"Export Code and Files logging initialized. Log file: {log_path}")
        
        return logger
    except Exception as e:
        print(f"Failed to setup export logging: {e}")
        return None

# Initialize logging
export_logger = setup_export_logging()

def log_debug(message):
    """Log debug message to both file and console"""
    if export_logger:
        export_logger.debug(message)
    else:
        print(f"DEBUG: {message}")

def log_info(message):
    """Log info message to both file and console"""
    if export_logger:
        export_logger.info(message)
    else:
        print(f"INFO: {message}")

def log_warning(message):
    """Log warning message to both file and console"""
    if export_logger:
        export_logger.warning(message)
    else:
        print(f"WARNING: {message}")

def log_error(message):
    """Log error message to both file and console"""
    if export_logger:
        export_logger.error(message)
    else:
        print(f"ERROR: {message}")


# SVG Icon Helper Class
class SVGIconHelper:
    """Helper class to generate SVG icons as QPixmap objects"""
    
    @staticmethod
    def create_icon_from_svg(svg_content, size=24):
        """Convert SVG content to QPixmap icon"""
        try:
            renderer = QSvgRenderer()
            if not renderer.load(svg_content.encode('utf-8')):
                print(f"Warning: Failed to load SVG content for icon")
                return None
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return pixmap
        except Exception as e:
            print(f"Error creating SVG icon: {e}")
            return None
    
    @staticmethod
    def get_icon(icon_name, size=24):
        """Get icon by name"""
        icons = {
            'folder': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>''',
            
            'file': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
            </svg>''',
            
            'image': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21,15 16,10 5,21"/>
            </svg>''',
            
            'pdf': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
            </svg>''',
            
            'package': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                <polyline points="3.27,6.96 12,12.01 20.73,6.96"/>
                <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>''',
            
            'search': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
            </svg>''',
            
            'refresh': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23,4 23,10 17,10"/>
                <polyline points="1,20 1,14 7,14"/>
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
            </svg>''',
            
            'download': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>''',
            
            'list': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
                <line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/>
                <line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>''',
            
            'grid': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="7" height="7"/>
                <rect x="14" y="3" width="7" height="7"/>
                <rect x="14" y="14" width="7" height="7"/>
                <rect x="3" y="14" width="7" height="7"/>
            </svg>''',
            
            'eye': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
            </svg>''',
            
            'edit': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>''',
            
            'trash': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3,6 5,6 21,6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                <line x1="10" y1="11" x2="10" y2="17"/>
                <line x1="14" y1="11" x2="14" y2="17"/>
            </svg>''',
            
            'arrow-left': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"/>
                <polyline points="12,19 5,12 12,5"/>
            </svg>''',
            
            'arrow-right': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12,5 19,12 12,19"/>
            </svg>''',
            
            'upload': '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17,8 12,3 7,8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>'''
        }
        
        if icon_name in icons:
            return SVGIconHelper.create_icon_from_svg(icons[icon_name], size)
        return None

class ScrollableComboBox(QComboBox):
    """Custom ComboBox that handles scroll events properly"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def wheelEvent(self, event):
        """Override wheel event to prevent page scrolling when combo box is focused"""
        # Only handle wheel events when the combo box is focused or its popup is open
        if self.hasFocus() or self.view().isVisible():
            # Let the combo box handle its own scrolling
            super().wheelEvent(event)
            event.accept()
        else:
            # Pass the event to parent for normal page scrolling
            event.ignore()

class ExportCodeAndFilesPages:
    """Standalone class containing Export Code and Files pages functionality"""
    
    def __init__(self, parent_widget=None):
        """Initialize the pages with optional parent widget"""
        self.parent = parent_widget
        self.content_stack = None
        self.current_path = None
        self.tmp_root = None
        self.selected_items = []
        self.view_mode = "list"
        self.navigation_history = []
        self.current_history_index = 0
        
        # Initialize file manager state
        if parent_widget:
            self.current_path = os.path.join(os.getcwd(), "tmp")
            self.tmp_root = self.current_path
            self.navigation_history = [self.current_path]
    
    def create_export_code_page(self):
        """Create the Export Code page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(0)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Page title
        title = QLabel("Export Code")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 40px;
                text-align: center;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add stretch to center content
        layout.addStretch()
        
        # Main content container - increased size and spacious design
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 2px solid #444444;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        content_container.setFixedWidth(800)
        content_container.setFixedHeight(450)

        content_layout = QVBoxLayout(content_container)
        content_layout.setSpacing(25)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Description text at the top - increased padding and spacing
        description = QLabel("This will generate a JSON file and an automation script based on your inputs.")
        description.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: 400;
                text-align: center;
                padding: 20px 25px;
                background-color: #3a3a3a;
                border-radius: 10px;
                border: 1px solid #505050;
                line-height: 1.5;
            }
        """)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setMinimumHeight(80)
        content_layout.addWidget(description, alignment=Qt.AlignmentFlag.AlignCenter)

        # Get dynamic counts
        config_count = self.get_configuration_count()
        essential_count = self.get_essential_questions_count()
        execution_count = self.get_execution_step_questions_count()

        # Store references to labels for real-time updates
        self.config_label = None
        self.essential_label = None
        self.execution_label = None

        # Status indicators - full width horizontal layout with equal spacing and better padding
        # Create horizontal layout for the 3 status items with full width stretching
        status_layout = QHBoxLayout()
        status_layout.setSpacing(25)  # Increased spacing for better visual balance
        status_layout.setContentsMargins(15, 15, 15, 15)

        # Configuration count label
        config_label = QLabel(f"Configuration ({config_count} filled)")
        config_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 12px 20px;
                min-width: 180px;
                min-height: 20px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        config_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(config_label, 1)  # Equal stretch factor
        self.config_label = config_label

        # Essential Questions count label
        essential_label = QLabel(f"Essential Questions ({essential_count} filled)")
        essential_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 12px 20px;
                min-width: 200px;
                min-height: 20px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        essential_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(essential_label, 1)  # Equal stretch factor
        self.essential_label = essential_label

        # Execution Step Questions count label
        execution_label = QLabel(f"Execution Step Questions ({execution_count} filled)")
        execution_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 12px 20px;
                min-width: 220px;
                min-height: 20px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        execution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(execution_label, 1)  # Equal stretch factor
        self.execution_label = execution_label

        # Automatic Images (Placeholders) count label
        automatic_images_count = self.get_automatic_images_count()
        automatic_images_label = QLabel(f"Placeholders ({automatic_images_count} added)")
        automatic_images_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
                padding: 12px 20px;
                min-width: 180px;
                min-height: 20px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        automatic_images_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(automatic_images_label, 1)  # Equal stretch factor
        self.automatic_images_label = automatic_images_label

        # Add the horizontal layout directly to the vertical content layout with center alignment
        content_layout.addLayout(status_layout)
        
        # Buttons directly in content layout with better spacing and center alignment
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 30, 0, 10)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Generate button
        generate_btn = QPushButton("GENERATE")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 15px 35px;
                font-weight: bold;
                font-size: 15px;
                min-width: 160px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border: 1px solid #66bb6a;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #3d8b40;
                transform: translateY(0px);
            }
        """)
        generate_btn.clicked.connect(self.generate_export_files)
        button_layout.addWidget(generate_btn)

        # Test Placeholders button
        test_placeholders_btn = QPushButton("🧪 Test Placeholders")
        test_placeholders_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 15px 25px;
                font-weight: bold;
                font-size: 13px;
                min-width: 140px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #F57C00;
                border: 1px solid #FFB74D;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #EF6C00;
                transform: translateY(0px);
            }
        """)
        test_placeholders_btn.clicked.connect(self.add_test_placeholders)
        button_layout.addWidget(test_placeholders_btn)

        # Collect All Placeholders button
        collect_placeholders_btn = QPushButton("Collect All Placeholders")
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('search', 16)
            if icon_pixmap:
                collect_placeholders_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load search icon: {e}")
        collect_placeholders_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                margin: 5px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(156, 39, 176, 0.3);
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
                transform: translateY(0px);
            }
        """)
        collect_placeholders_btn.clicked.connect(self.collect_all_placeholders_manual)
        button_layout.addWidget(collect_placeholders_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('refresh', 16)
            if icon_pixmap:
                refresh_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load refresh icon: {e}")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 15px 25px;
                font-weight: bold;
                font-size: 13px;
                min-width: 140px;
                min-height: 45px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border: 1px solid #64b5f6;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #1565C0;
                transform: translateY(0px);
            }
        """)
        refresh_btn.clicked.connect(self.refresh_counts)
        button_layout.addWidget(refresh_btn)

        # Add the button layout directly to the vertical content layout with center alignment
        content_layout.addLayout(button_layout)
        
        # Center the content container
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.addStretch()
        center_layout.addWidget(content_container)
        center_layout.addStretch()
        
        layout.addWidget(center_widget)
        layout.addStretch()
        
        return page
    
    def get_configuration_count(self):
        """Get the count of filled configuration fields"""
        try:
            if hasattr(self.parent, 'get_dut_config_data'):
                config_data = self.parent.get_dut_config_data()
                if config_data:
                    # Count non-empty configuration fields
                    filled_count = 0
                    for field in config_data:
                        # Check if key, label, or description is filled
                        if (field.get('key', '').strip() or 
                            field.get('label', '').strip() or 
                            field.get('description', '').strip()):
                            filled_count += 1
                    return filled_count
            return 0
        except Exception as e:
            print(f"Error getting configuration count: {e}")
            return 0
    
    def get_essential_questions_count(self):
        """Get the count of filled essential questions"""
        try:
            if hasattr(self.parent, 'get_essential_questions_data'):
                questions_data = self.parent.get_essential_questions_data()
                if questions_data and 'questions' in questions_data:
                    # Count non-empty essential questions
                    filled_count = 0
                    for question in questions_data['questions']:
                        if question.get('question', '').strip():
                            filled_count += 1
                    return filled_count
            return 0
        except Exception as e:
            print(f"Error getting essential questions count: {e}")
            return 0
    
    def get_execution_step_questions_count(self):
        """Get the count of filled execution step questions"""
        try:
            if hasattr(self.parent, 'get_execution_step_questions_data'):
                execution_data = self.parent.get_execution_step_questions_data()
                if execution_data:
                    # Count non-empty execution step questions
                    filled_count = 0
                    for step in execution_data:
                        if step.get('name', '').strip():
                            filled_count += 1
                    return filled_count
            return 0
        except Exception as e:
            print(f"Error getting execution step questions count: {e}")
            return 0
    
    def get_automatic_images_count(self):
        """Get the count of automatic images (placeholders)"""
        try:
            if hasattr(self.parent, 'automatic_images'):
                return len(self.parent.automatic_images)
            return 0
        except Exception as e:
            print(f"Error getting automatic images count: {e}")
            return 0
    
    def generate_export_files(self):
        """Show preview popup and generate both JSON and script.py files"""
        try:
            # Show preview popup first
            if self.show_generation_preview():
                # User confirmed, proceed with generation
                self.perform_generation()
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Generation Error",
                f"Failed to generate files:\n{str(e)}"
            )
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Error generating files: {str(e)}")
    
    def show_generation_preview(self):
        """Show preview popup with all configuration data"""
        try:
            # Create preview dialog
            preview_dialog = QDialog(self.parent)
            preview_dialog.setWindowTitle("Generation Preview - Confirm Configuration")
            preview_dialog.setModal(True)
            preview_dialog.resize(900, 700)
            preview_dialog.setStyleSheet("""
                QDialog {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #444444;
                    background-color: #1a1a1a;
                }
                QTabBar::tab {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QTabBar::tab:selected {
                    background-color: #404040;
                    border-bottom: 2px solid #1976d2;
                }
                QTabBar::tab:hover {
                    background-color: #505050;
                }
                QTextEdit {
                    background-color: #2a2a2a;
                    color: #ffffff;
                    border: 1px solid #444444;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }
                QPushButton {
                    background-color: #404040;
                    border: 1px solid #606060;
                    border-radius: 4px;
                    color: #ffffff;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
            """)
            
            layout = QVBoxLayout(preview_dialog)
            
            # Title
            title = QLabel("Review Configuration Before Generation")
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)
            
            # Create tab widget for different sections
            tab_widget = QTabWidget()
            
            # Configuration tab
            config_tab = self.create_configuration_preview_tab()
            tab_widget.addTab(config_tab, "Configuration")
            
            # Essential Questions tab
            essential_tab = self.create_essential_questions_preview_tab()
            tab_widget.addTab(essential_tab, "Essential Questions")
            
            # Execution Steps tab
            execution_tab = self.create_execution_steps_preview_tab()
            tab_widget.addTab(execution_tab, "Execution Steps")
            
            layout.addWidget(tab_widget)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            confirm_btn = QPushButton("Confirm & Generate")
            confirm_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            confirm_btn.clicked.connect(preview_dialog.accept)
            button_layout.addWidget(confirm_btn)
            
            button_layout.addStretch()
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            cancel_btn.clicked.connect(preview_dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Show dialog and return result
            result = preview_dialog.exec()
            return result == QDialog.DialogCode.Accepted
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Preview Error", f"Failed to show preview: {str(e)}")
            return False
    
    def create_configuration_preview_tab(self):
        """Create configuration preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Get configuration data
        config_data = self.get_configuration_data()
        
        if not config_data:
            no_data_label = QLabel("No configuration data found")
            no_data_label.setStyleSheet("color: #ffa500; font-size: 14px; padding: 20px;")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data_label)
            return tab
        
        # Create table for configuration
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Key", "Label", "Type"])
        table.setRowCount(len(config_data))

        # Make table read-only for view only
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Enable word wrap and auto row resizing for consistency
        table.setWordWrap(True)
        table.resizeRowsToContents()
        table.verticalHeader().setDefaultSectionSize(50)  # Default row height
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #444444;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        # Populate table
        for row, field in enumerate(config_data):
            # ID
            id_item = QTableWidgetItem(field.get('id', ''))
            table.setItem(row, 0, id_item)

            # Key
            key_item = QTableWidgetItem(field.get('key', ''))
            table.setItem(row, 1, key_item)

            # Label - Enable word wrap
            label_item = QTableWidgetItem(field.get('label', ''))
            label_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            table.setItem(row, 2, label_item)

            # Type
            type_item = QTableWidgetItem(field.get('type', ''))
            table.setItem(row, 3, type_item)

        # Set column widths
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(table)
        return tab
    
    def create_essential_questions_preview_tab(self):
        """Create essential questions preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Get essential questions data
        questions_data = self.get_essential_questions_data()
        
        if not questions_data or 'questions' not in questions_data:
            no_data_label = QLabel("No essential questions data found")
            no_data_label.setStyleSheet("color: #ffa500; font-size: 14px; padding: 20px;")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data_label)
            return tab
        
        questions = questions_data.get('questions', [])
        
        if not questions:
            no_data_label = QLabel("No essential questions found")
            no_data_label.setStyleSheet("color: #ffa500; font-size: 14px; padding: 20px;")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data_label)
            return tab
        
                # Create table for essential questions
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Question", "Help Text", "Question Type"])
        table.setRowCount(len(questions))

        # Make table read-only for view only
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Enable word wrap and auto row resizing
        table.setWordWrap(True)
        table.resizeRowsToContents()
        table.verticalHeader().setDefaultSectionSize(60)  # Default row height
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #444444;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        # Populate table
        for row, question in enumerate(questions):
            # Question
            question_text = question.get('question', '')
            question_item = QTableWidgetItem(question_text)
            table.setItem(row, 0, question_item)

            # Help Text - Enable word wrap
            help_text = question.get('help_text', '')
            help_item = QTableWidgetItem(help_text)
            help_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            table.setItem(row, 1, help_item)

            # Question Type
            question_type = question.get('question_type', '')
            type_item = QTableWidgetItem(question_type)
            table.setItem(row, 2, type_item)

        # Set column widths
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(table)
        return tab
    
    def create_execution_steps_preview_tab(self):
        """Create execution steps preview tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Get execution step questions data
        questions_data = self.get_execution_steps_data()
        
        if not questions_data:
            no_data_label = QLabel("No execution step questions found")
            no_data_label.setStyleSheet("color: #ffa500; font-size: 14px; padding: 20px;")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data_label)
            return tab

        # Create table for execution step questions
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Question", "Help Text", "Question Type"])
        table.setRowCount(len(questions_data))

        # Make table read-only for view only
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        # Enable word wrap and auto row resizing
        table.setWordWrap(True)
        table.resizeRowsToContents()
        table.verticalHeader().setDefaultSectionSize(60)  # Default row height
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Style the table
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 6px;
                border: 1px solid #444444;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        # Populate table
        for row, question in enumerate(questions_data):
            # Question
            question_text = question.get('question', '')
            question_item = QTableWidgetItem(question_text)
            table.setItem(row, 0, question_item)

            # Help Text - Enable word wrap
            help_text = question.get('help_text', '')
            help_item = QTableWidgetItem(help_text)
            help_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            table.setItem(row, 1, help_item)

            # Question Type
            question_type = question.get('question_type', '')
            type_item = QTableWidgetItem(question_type)
            table.setItem(row, 2, type_item)

        # Set column widths
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(table)
        return tab
    
    def perform_generation(self):
        """Perform the actual file generation"""
        try:
            # Collect all data
            export_data = {
                "ui": {
                    "title": "NO CGI OR OTHER SCRIPTING FOR UPLOADS"
                },
                "questions": self.get_essential_questions_data(),
                "metadata": {
                    "total_questions": len(self.get_essential_questions_data()),
                    "description": "FortiAP device setup and verification questions",
                    "version": "1.0"
                },
                "configuration": {
                    "fields": self.get_configuration_data()
                },
                "execution_steps": self.get_execution_steps_data(),
                "automatic_images": self.get_automatic_images_data()
            }
            
            # Create the code folder structure
            code_folder_path = self.create_code_folder()
            
            if code_folder_path:
                # Create images folder alongside code folder
                project_dir = os.path.dirname(code_folder_path)
                images_folder_path = os.path.join(project_dir, "images")
                os.makedirs(images_folder_path, exist_ok=True)
                
                # Copy pending scripts to the export folder
                self.copy_pending_scripts_to_export_folder(code_folder_path)
                
                # Copy pending images to the export folder  
                self.copy_pending_images_to_export_folder(images_folder_path)
                
                # Also copy scripts directly from step widgets (fallback method)
                self.copy_scripts_from_step_widgets(code_folder_path)
                
                # Also copy images directly from step widgets (fallback method)
                self.copy_images_from_step_widgets(images_folder_path)
                
                # Save JSON file (ensure no original_path fields are persisted)
                json_file_path = os.path.join(code_folder_path, "questions_config.json")
                def _strip_original_path(obj):
                    if isinstance(obj, dict):
                        obj.pop('original_path', None)
                        return {k: _strip_original_path(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [_strip_original_path(x) for x in obj]
                    return obj
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(_strip_original_path(export_data), f, indent=2, ensure_ascii=False)
                
                # Save script.py file
                script_file_path = os.path.join(code_folder_path, "script.py")
                script_content = self.generate_script_py_content()
                with open(script_file_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                # Show success message
                QMessageBox.information(
                    self.parent,
                    "Generation Successful",
                    f"Generated successfully:\n\nJSON: {json_file_path}\nScript: {script_file_path}"
                )
                
                # Update status bar
                if hasattr(self.parent, 'statusBar'):
                    self.parent.statusBar().showMessage("Generated JSON file and automation script successfully!")
            else:
                QMessageBox.warning(
                    self.parent,
                    "Generation Warning",
                    "Could not create code folder. Please check permissions."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Generation Error",
                f"Failed to generate files:\n{str(e)}"
            )
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Error generating files: {str(e)}")
    
    def refresh_counts(self):
        """Refresh the counts in real-time"""
        try:
            # Get updated counts
            config_count = self.get_configuration_count()
            essential_count = self.get_essential_questions_count()
            execution_count = self.get_execution_step_questions_count()
            automatic_images_count = self.get_automatic_images_count()
            
            # Update labels if they exist
            if hasattr(self, 'config_label') and self.config_label:
                self.config_label.setText(f"Configuration ({config_count} filled)")
            
            if hasattr(self, 'essential_label') and self.essential_label:
                self.essential_label.setText(f"Essential Questions ({essential_count} filled)")
            
            if hasattr(self, 'execution_label') and self.execution_label:
                self.execution_label.setText(f"Execution Step Questions ({execution_count} filled)")
            
            if hasattr(self, 'automatic_images_label') and self.automatic_images_label:
                self.automatic_images_label.setText(f"Placeholders ({automatic_images_count} added)")
            
            # Show status message
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Counts refreshed: Config={config_count}, Essential={essential_count}, Execution={execution_count}, Placeholders={automatic_images_count}")
                
        except Exception as e:
            print(f"Error refreshing counts: {e}")
            if hasattr(self.parent, 'statusBar'):
                self.parent.statusBar().showMessage(f"Error refreshing counts: {str(e)}")
    
    def create_files_page(self):
        """Create the Files page with file manager functionality and Push/Pull sections"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Initialize file manager state
        self.current_path = os.path.join(os.getcwd(), "tmp")
        self.tmp_root = self.current_path
        self.selected_items = []
        self.view_mode = "list"
        self.navigation_history = [self.current_path]
        self.current_history_index = 0
        
        # Create main tab widget
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #404040;
                border-bottom: 2px solid #1976d2;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """)
        
        # Create File Manager tab
        self.create_file_manager_tab()
        
        layout.addWidget(self.main_tab_widget)
        
        return page
    
    def create_files_toolbar(self, parent_layout):
        """Create the files toolbar"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(5)
        toolbar_layout.setContentsMargins(2, 2, 2, 2)
        
        # Common button style
        button_style = """
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 4px;
                color: #ffffff;
                font-size: 11px;
                padding: 6px 8px;
                min-width: 35px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #888888;
            }
        """

        # Navigation buttons
        self.view_mode_btn = QPushButton("")
        self.view_mode_btn.setToolTip("Toggle view mode (List/Grid)")
        self.view_mode_btn.setFixedSize(35, 30)
        self.view_mode_btn.setStyleSheet(button_style)
        # Set initial list icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('list', 16)
            if icon_pixmap:
                self.view_mode_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load list icon: {e}")
        self.view_mode_btn.clicked.connect(self.toggle_view_mode)
        toolbar_layout.addWidget(self.view_mode_btn)

        back_btn = QPushButton("")
        back_btn.setToolTip("Go back (Previous folder)")
        back_btn.setFixedSize(35, 30)
        back_btn.setStyleSheet(button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('arrow-left', 16)
            if icon_pixmap:
                back_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load arrow-left icon: {e}")
        back_btn.clicked.connect(self.go_back)
        toolbar_layout.addWidget(back_btn)

        up_btn = QPushButton("↑")
        up_btn.setToolTip("Go up (Parent folder)")
        up_btn.setFixedSize(35, 30)
        up_btn.setStyleSheet(button_style)
        up_btn.clicked.connect(self.go_up)
        toolbar_layout.addWidget(up_btn)

        home_btn = QPushButton("⌂")
        home_btn.setToolTip("Go to tmp root")
        home_btn.setFixedSize(35, 30)
        home_btn.setStyleSheet(button_style)
        home_btn.clicked.connect(self.go_home)
        toolbar_layout.addWidget(home_btn)

        toolbar_layout.addSpacing(15)

        # Action buttons
        new_folder_btn = QPushButton("")
        new_folder_btn.setToolTip("Create new folder")
        new_folder_btn.setFixedSize(35, 30)
        new_folder_btn.setStyleSheet(button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('folder', 16)
            if icon_pixmap:
                new_folder_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load folder icon: {e}")
        new_folder_btn.clicked.connect(self.create_new_folder)
        toolbar_layout.addWidget(new_folder_btn)

        upload_btn = QPushButton("")
        upload_btn.setToolTip("Upload file")
        upload_btn.setFixedSize(35, 30)
        upload_btn.setStyleSheet(button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('upload', 16)
            if icon_pixmap:
                upload_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load upload icon: {e}")
        upload_btn.clicked.connect(self.upload_file)
        toolbar_layout.addWidget(upload_btn)

        # Push button
        push_btn = QPushButton("Push")
        push_btn.setToolTip("Push files to backend")
        push_btn.setFixedSize(50, 30)
        push_btn.setStyleSheet(button_style)
        push_btn.clicked.connect(self.show_push_options_dialog)
        toolbar_layout.addWidget(push_btn)

        # Pull button
        pull_btn = QPushButton("Pull")
        pull_btn.setToolTip("Pull files from backend")
        pull_btn.setFixedSize(50, 30)
        pull_btn.setStyleSheet(button_style)
        pull_btn.clicked.connect(self.pull_files)
        toolbar_layout.addWidget(pull_btn)

        toolbar_layout.addSpacing(15)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files...")
        self.search_box.setFixedHeight(25)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #1976d2;
            }
        """)
        self.search_box.textChanged.connect(self.search_files)
        toolbar_layout.addWidget(self.search_box)
        
        # Sort dropdown
        self.sort_combo = ScrollableComboBox()
        self.sort_combo.addItems(["Name", "Size", "Date", "Type"])
        self.sort_combo.setFixedHeight(25)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px 8px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
        """)
        self.sort_combo.currentTextChanged.connect(self.sort_files)
        toolbar_layout.addWidget(self.sort_combo)
        
        # Refresh button
        refresh_btn = QPushButton("↻")
        refresh_btn.setToolTip("Refresh current folder")
        refresh_btn.setFixedSize(35, 30)
        refresh_btn.setStyleSheet(button_style)
        refresh_btn.clicked.connect(self.refresh_files)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()

        # Bulk actions
        self.download_zip_btn = QPushButton("")
        self.download_zip_btn.setToolTip("Download selected files as ZIP")
        self.download_zip_btn.setFixedSize(35, 30)
        self.download_zip_btn.setStyleSheet(button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('download', 16)
            if icon_pixmap:
                self.download_zip_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load download icon: {e}")
        self.download_zip_btn.clicked.connect(self.download_selected_as_zip)
        self.download_zip_btn.setEnabled(False)
        toolbar_layout.addWidget(self.download_zip_btn)

        self.delete_btn = QPushButton("")
        self.delete_btn.setToolTip("Delete selected files/folders")
        self.delete_btn.setFixedSize(35, 30)
        self.delete_btn.setStyleSheet(button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('trash', 16)
            if icon_pixmap:
                self.delete_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load trash icon: {e}")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        toolbar_layout.addWidget(self.delete_btn)
        
        parent_layout.addWidget(toolbar)
    
    def create_files_breadcrumb(self, parent_layout):
        """Create the files breadcrumb"""
        breadcrumb_widget = QWidget()
        breadcrumb_layout = QHBoxLayout(breadcrumb_widget)
        breadcrumb_layout.setSpacing(2)
        breadcrumb_layout.setContentsMargins(2, 2, 2, 2)
        
        self.breadcrumb_label = QLabel("tmp")
        self.breadcrumb_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 3px 8px;
                color: #ffffff;
                font-size: 11px;
            }
        """)
        breadcrumb_layout.addWidget(self.breadcrumb_label)
        breadcrumb_layout.addStretch()
        
        parent_layout.addWidget(breadcrumb_widget)
    
    def create_files_list_widget(self, parent_layout):
        """Create the files list widget"""
        # Create table widget for list view
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "Modified", "Actions"])
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setShowGrid(False)
        self.files_table.setSortingEnabled(True)
        # Disable editing of table items to prevent accidental rename mode
        self.files_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.files_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.files_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.files_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.files_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set column widths
        header = self.files_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.files_table.setColumnWidth(4, 120)
        
        # Style the table
        self.files_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 2px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #1976d2;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #444444;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        
        parent_layout.addWidget(self.files_table)
    
    def create_files_status_bar(self, parent_layout):
        """Create the files status bar"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(2, 2, 2, 2)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.items_count_label = QLabel("0 items")
        self.items_count_label.setStyleSheet("color: #cccccc; font-size: 10px;")
        status_layout.addWidget(self.items_count_label)
        
        parent_layout.addWidget(status_widget)
    

    
    def create_file_manager_tab(self):
        """Create the File Manager tab"""
        file_manager_widget = QWidget()
        layout = QVBoxLayout(file_manager_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create toolbar
        self.create_files_toolbar(layout)
        
        # Create breadcrumb
        self.create_files_breadcrumb(layout)
        
        # Create file list widget
        self.create_files_list_widget(layout)
        
        # Create status bar
        self.create_files_status_bar(layout)
        
        # Load initial directory
        self.load_directory(self.current_path)
        
        # Add to main tab widget
        self.main_tab_widget.addTab(file_manager_widget, "File Manager")
    def load_directory(self, path):
        """Load directory contents"""
        try:
            # Validate path is within tmp directory
            if not self.is_path_safe(path):
                self.status_label.setText("Error: Invalid path")
                return
            
            # Add to navigation history only if it's a different path
            if path != self.current_path:
                # Remove any forward history if we're navigating to a new path
                if self.current_history_index < len(self.navigation_history) - 1:
                    self.navigation_history = self.navigation_history[:self.current_history_index + 1]
                
                self.navigation_history.append(path)
                self.current_history_index = len(self.navigation_history) - 1
            
            self.current_path = path
            self.update_breadcrumb()
            
            # Load directory contents
            self.load_directory_contents(path)
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def load_directory_contents(self, path):
        """Load and display directory contents"""
        try:
            # Get directory contents
            entries = []
            if os.path.exists(path):
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.exists(item_path):
                        stat = os.stat(item_path)
                        is_dir = os.path.isdir(item_path)
                        
                        # Get file size
                        size = stat.st_size if not is_dir else 0
                        size_str = self.format_file_size(size) if not is_dir else ""
                        
                        # Get modification time
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        mtime_str = mtime.strftime("%Y-%m-%d %H:%M")
                        
                        # Get MIME type
                        mime_type = self.get_mime_type(item_path) if not is_dir else "directory"
                        
                        entries.append({
                            'name': item,
                            'path': os.path.relpath(item_path, self.tmp_root),
                            'isDir': is_dir,
                            'size': size,
                            'size_str': size_str,
                            'mtime': mtime,
                            'mtime_str': mtime_str,
                            'mime': mime_type
                        })
            
            # Sort entries
            self.sort_entries(entries)
            
            # Populate table
            self.populate_files_table(entries)
            
            self.status_label.setText(f"Loaded {len(entries)} items")
            self.items_count_label.setText(f"{len(entries)} items")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def is_path_safe(self, path):
        """Check if path is safe (within tmp directory)"""
        try:
            real_path = os.path.realpath(path)
            real_tmp = os.path.realpath(self.tmp_root)
            return real_path.startswith(real_tmp)
        except:
            return False
    
    def format_file_size(self, size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_mime_type(self, file_path):
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def sort_entries(self, entries):
        """Sort entries based on current sort setting"""
        sort_by = self.sort_combo.currentText().lower()
        
        if sort_by == "name":
            entries.sort(key=lambda x: x['name'].lower())
        elif sort_by == "size":
            entries.sort(key=lambda x: x['size'], reverse=True)
        elif sort_by == "date":
            entries.sort(key=lambda x: x['mtime'], reverse=True)
        elif sort_by == "type":
            entries.sort(key=lambda x: x['mime'])
        
        # Always put directories first
        entries.sort(key=lambda x: not x['isDir'])
    
    def populate_files_table(self, entries):
        """Populate the files table with entries"""
        self.files_table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            # Name column with icon
            name_item = QTableWidgetItem()
            if entry['isDir']:
                icon_name = "folder"
                icon_pixmap = SVGIconHelper.get_icon('folder', 16)
            else:
                icon_name = self.get_file_icon(entry['mime'])
                icon_pixmap = SVGIconHelper.get_icon(icon_name, 16)
            
            name_item.setText(entry['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, entry)
            
            # Set SVG icon
            try:
                if icon_pixmap:
                    name_item.setIcon(QIcon(icon_pixmap))
            except Exception as e:
                print(f"Warning: Could not load icon for {icon_name}: {e}")
            
            self.files_table.setItem(row, 0, name_item)
            
            # Type column
            type_item = QTableWidgetItem(entry['mime'])
            self.files_table.setItem(row, 1, type_item)
            
            # Size column
            size_item = QTableWidgetItem(entry['size_str'])
            self.files_table.setItem(row, 2, size_item)
            
            # Modified column
            mtime_item = QTableWidgetItem(entry['mtime_str'])
            self.files_table.setItem(row, 3, mtime_item)
            
            # Actions column
            actions_widget = self.create_actions_widget(entry)
            self.files_table.setCellWidget(row, 4, actions_widget)
    
    def get_file_icon(self, mime_type):
        """Get appropriate icon for file type"""
        if mime_type.startswith('image/'):
            return "image"
        elif mime_type.startswith('text/'):
            return "file"
        elif mime_type == 'application/pdf':
            return "pdf"
        elif mime_type.startswith('application/'):
            return "package"
        else:
            return "file"
    
    def create_actions_widget(self, entry):
        """Create actions widget for a file entry"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Action button style
        action_button_style = """
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 2px;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                padding: 1px;
                min-width: 16px;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
        """
        
        # Download button
        download_btn = QPushButton("")
        download_btn.setToolTip("Download file")
        download_btn.setFixedSize(20, 20)
        download_btn.setStyleSheet(action_button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('download', 14)
            if icon_pixmap:
                download_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load download icon: {e}")
        download_btn.clicked.connect(lambda: self.download_file(entry))
        layout.addWidget(download_btn)
        
        # Preview button
        preview_btn = QPushButton("")
        preview_btn.setToolTip("Preview file")
        preview_btn.setFixedSize(20, 20)
        preview_btn.setStyleSheet(action_button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('eye', 14)
            if icon_pixmap:
                preview_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load eye icon: {e}")
        preview_btn.clicked.connect(lambda: self.preview_file(entry))
        layout.addWidget(preview_btn)
        
        # Rename button
        rename_btn = QPushButton("")
        rename_btn.setToolTip("Rename file/folder")
        rename_btn.setFixedSize(20, 20)
        rename_btn.setStyleSheet(action_button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('edit', 14)
            if icon_pixmap:
                rename_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load edit icon: {e}")
        rename_btn.clicked.connect(lambda: self.rename_file(entry))
        layout.addWidget(rename_btn)
        
        # Delete button
        delete_btn = QPushButton("")
        delete_btn.setToolTip("Delete file/folder")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet(action_button_style)
        # Set SVG icon
        try:
            icon_pixmap = SVGIconHelper.get_icon('trash', 14)
            if icon_pixmap:
                delete_btn.setIcon(QIcon(icon_pixmap))
        except Exception as e:
            print(f"Warning: Could not load trash icon: {e}")
        delete_btn.clicked.connect(lambda: self.delete_file(entry))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        return widget
    
    def update_breadcrumb(self):
        """Update the breadcrumb display"""
        rel_path = os.path.relpath(self.current_path, self.tmp_root)
        if rel_path == ".":
            breadcrumb = "tmp"
        else:
            breadcrumb = f"tmp / {rel_path.replace(os.sep, ' / ')}"
        self.breadcrumb_label.setText(breadcrumb)
    
    def toggle_view_mode(self):
        """Toggle between list and grid view"""
        if self.view_mode == "list":
            self.view_mode = "grid"
            # Set grid icon
            try:
                icon_pixmap = SVGIconHelper.get_icon('grid', 16)
                if icon_pixmap:
                    self.view_mode_btn.setIcon(QIcon(icon_pixmap))
                self.view_mode_btn.setText("")
            except Exception as e:
                print(f"Warning: Could not load grid icon: {e}")
            self.view_mode_btn.setToolTip("Switch to list view")
        else:
            self.view_mode = "list"
            # Set list icon
            try:
                icon_pixmap = SVGIconHelper.get_icon('list', 16)
                if icon_pixmap:
                    self.view_mode_btn.setIcon(QIcon(icon_pixmap))
                self.view_mode_btn.setText("")
            except Exception as e:
                print(f"Warning: Could not load list icon: {e}")
            self.view_mode_btn.setToolTip("Switch to grid view")
        
        # Reload current directory
        self.load_directory(self.current_path)
    
    def go_back(self):
        """Go back in history"""
        if self.current_history_index > 0:
            self.current_history_index -= 1
            previous_path = self.navigation_history[self.current_history_index]
            
            # Update current path and reload
            self.current_path = previous_path
            self.update_breadcrumb()
            
            # Clear and reload the file list
            self.files_table.setRowCount(0)
            self.load_directory_contents(previous_path)
            
            self.status_label.setText(f"Went back to: {os.path.basename(previous_path)}")
    
    def go_up(self):
        """Go up one directory"""
        parent = os.path.dirname(self.current_path)
        if self.is_path_safe(parent):
            self.load_directory(parent)
    
    def go_home(self):
        """Go to tmp root"""
        self.load_directory(self.tmp_root)
    
    def create_new_folder(self):
        """Create a new folder"""
        name, ok = QInputDialog.getText(self.parent, "Create Folder", "Folder name:")
        if ok and name:
            try:
                new_folder_path = os.path.join(self.current_path, name)
                if self.is_path_safe(new_folder_path):
                    os.makedirs(new_folder_path, exist_ok=True)
                    self.load_directory(self.current_path)
                    self.status_label.setText(f"Created folder: {name}")
                else:
                    QMessageBox.warning(self.parent, "Error", "Invalid folder name")
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to create folder: {str(e)}")
    
    def upload_file(self):
        """Upload a file"""
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Select file to upload")
        if file_path:
            try:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.current_path, filename)
                
                if self.is_path_safe(dest_path):
                    shutil.copy2(file_path, dest_path)
                    self.load_directory(self.current_path)
                    self.status_label.setText(f"Uploaded: {filename}")
                else:
                    QMessageBox.warning(self.parent, "Error", "Invalid destination")
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to upload file: {str(e)}")
    
    def search_files(self):
        """Search files in current directory"""
        query = self.search_box.text().lower()
        if query:
            # Filter visible items
            for row in range(self.files_table.rowCount()):
                item = self.files_table.item(row, 0)
                if item:
                    entry = item.data(Qt.ItemDataRole.UserRole)
                    if entry and query in entry['name'].lower():
                        self.files_table.setRowHidden(row, False)
                    else:
                        self.files_table.setRowHidden(row, True)
        else:
            # Show all items
            for row in range(self.files_table.rowCount()):
                self.files_table.setRowHidden(row, False)
    
    def sort_files(self):
        """Sort files based on dropdown selection"""
        self.load_directory(self.current_path)
    
    def refresh_files(self):
        """Refresh the current directory"""
        self.load_directory(self.current_path)
    
    def on_item_double_clicked(self, item):
        """Handle double-click on item"""
        if item.column() == 0:  # Name column
            entry = item.data(Qt.ItemDataRole.UserRole)
            if entry:
                if entry['isDir']:
                    # Open folder
                    new_path = os.path.join(self.current_path, entry['name'])
                    if self.is_path_safe(new_path):
                        self.load_directory(new_path)
                else:
                    # Preview file based on type
                    self.preview_file(entry)
    
    def on_selection_changed(self):
        """Handle selection change"""
        selected_rows = set(item.row() for item in self.files_table.selectedItems())
        self.selected_items = []
        
        for row in selected_rows:
            item = self.files_table.item(row, 0)
            if item:
                entry = item.data(Qt.ItemDataRole.UserRole)
                if entry:
                    self.selected_items.append(entry)
        
        # Enable/disable bulk action buttons
        has_selection = len(self.selected_items) > 0
        self.download_zip_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def show_context_menu(self, position):
        """Show context menu for right-click"""
        item = self.files_table.itemAt(position)
        if item:
            entry = item.data(Qt.ItemDataRole.UserRole)
            if entry:
                menu = QMenu(self.parent)
                
                if entry['isDir']:
                    menu.addAction("Open", lambda: self.open_folder(entry))
                else:
                    menu.addAction("Download", lambda: self.download_file(entry))
                    menu.addAction("Preview", lambda: self.preview_file(entry))
                
                # Add copy, cut, and paste options
                menu.addSeparator()
                menu.addAction("Copy", lambda: self.copy_file(entry))
                menu.addAction("Cut", lambda: self.cut_file(entry))
                
                # Add paste option if we have something in clipboard
                if self.has_file_in_clipboard():
                    menu.addAction("Paste", lambda: self.paste_file(entry))
                    menu.addAction("Clear Clipboard", lambda: self.clear_clipboard())
                
                menu.addSeparator()
                menu.addAction("Rename", lambda: self.rename_file(entry))
                menu.addAction("Delete", lambda: self.delete_file(entry))
                
                menu.exec(self.files_table.mapToGlobal(position))
    
    def download_file(self, entry):
        """Download a file"""
        try:
            file_path = os.path.join(self.tmp_root, entry['path'])
            if os.path.exists(file_path):
                save_path, _ = QFileDialog.getSaveFileName(
                    self.parent, "Save file", entry['name']
                )
                if save_path:
                    shutil.copy2(file_path, save_path)
                    self.status_label.setText(f"Downloaded: {entry['name']}")
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to download: {str(e)}")
    
    def copy_file(self, entry):
        """Copy a file to clipboard"""
        try:
            file_path = os.path.join(self.tmp_root, entry['path'])
            if os.path.exists(file_path):
                # Store file info in clipboard
                clipboard_data = {
                    'action': 'copy',
                    'source_path': file_path,
                    'source_name': entry['name'],
                    'source_relative_path': entry['path'],
                    'is_dir': entry['isDir']
                }
                
                # Store in our internal clipboard for easier access
                self._clipboard_data = clipboard_data
                
                # Also store in system clipboard as text for debugging
                clipboard = QApplication.clipboard()
                clipboard.setText(f"Copied: {entry['name']}")
                
                self.status_label.setText(f"Copied: {entry['name']}")
            else:
                QMessageBox.warning(self.parent, "Error", "File not found")
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to copy: {str(e)}")
    
    def cut_file(self, entry):
        """Cut a file to clipboard (copy and mark for deletion after paste)"""
        try:
            file_path = os.path.join(self.tmp_root, entry['path'])
            if os.path.exists(file_path):
                # Store file info in clipboard with cut action
                clipboard_data = {
                    'action': 'cut',
                    'source_path': file_path,
                    'source_name': entry['name'],
                    'source_relative_path': entry['path'],
                    'is_dir': entry['isDir']
                }
                
                # Store in our internal clipboard for easier access
                self._clipboard_data = clipboard_data
                
                # Also store in system clipboard as text for debugging
                clipboard = QApplication.clipboard()
                clipboard.setText(f"Cut: {entry['name']}")
                
                self.status_label.setText(f"Cut: {entry['name']}")
            else:
                QMessageBox.warning(self.parent, "Error", "File not found")
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to cut: {str(e)}")
    
    def paste_file(self, target_entry):
        """Paste a file from clipboard - supports all file types and folders"""
        try:
            if not hasattr(self, '_clipboard_data') or not self._clipboard_data:
                QMessageBox.warning(self.parent, "Error", "No file in clipboard")
                return
            
            clipboard_data = self._clipboard_data
            source_path = clipboard_data['source_path']
            source_name = clipboard_data['source_name']
            
            # Verify source still exists
            if not os.path.exists(source_path):
                QMessageBox.warning(self.parent, "Error", f"Source file no longer exists: {source_name}")
                self._clipboard_data = None
                return
            
            # Determine target directory - paste in the same directory where the target is located
            if target_entry['isDir']:
                # If right-clicking on a folder, paste in the same directory as that folder
                # This means paste alongside the folder, not inside it
                parent_dir = os.path.dirname(target_entry['path'])
                if parent_dir == '':
                    # Root level - paste in tmp_root
                    target_dir = self.tmp_root
                else:
                    # Subdirectory - paste in the parent directory
                    target_dir = os.path.join(self.tmp_root, parent_dir)
            else:
                # If right-clicking on a file, paste in the same directory as the file
                parent_dir = os.path.dirname(target_entry['path'])
                if parent_dir == '':
                    # Root level - paste in tmp_root
                    target_dir = self.tmp_root
                else:
                    # Subdirectory - paste in the parent directory
                    target_dir = os.path.join(self.tmp_root, parent_dir)
            
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Create target path
            target_path = os.path.join(target_dir, source_name)
            
            # Handle duplicate names for both files and folders
            counter = 1
            original_target_path = target_path
            while os.path.exists(target_path):
                if clipboard_data['is_dir']:
                    # For directories, just add _copy suffix
                    target_path = os.path.join(target_dir, f"{source_name}_copy{counter}")
                else:
                    # For files, preserve extension
                    name, ext = os.path.splitext(source_name)
                    target_path = os.path.join(target_dir, f"{name}_copy{counter}{ext}")
                counter += 1
                # Safety check to prevent infinite loop
                if counter > 1000:
                    QMessageBox.critical(self.parent, "Error", "Too many duplicate files/folders")
                    return
            
            # Copy the file or directory
            success = False
            if os.path.isfile(source_path):
                # Handle all file types (text, binary, images, documents, etc.)
                shutil.copy2(source_path, target_path)
                file_size = os.path.getsize(target_path)
                self.status_label.setText(f"Pasted file: {os.path.basename(target_path)} ({self.format_file_size(file_size)})")
                success = True
            elif os.path.isdir(source_path):
                # Handle directories and all their contents recursively
                try:
                    # Use dirs_exist_ok=False since we've already handled duplicates
                    shutil.copytree(source_path, target_path, dirs_exist_ok=False)
                    # Count items in directory
                    total_items = sum([len(files) + len(dirs) for _, dirs, files in os.walk(target_path)])
                    self.status_label.setText(f"Pasted folder: {os.path.basename(target_path)} ({total_items} items)")
                    success = True
                except FileExistsError:
                    # This shouldn't happen since we handled duplicates, but just in case
                    QMessageBox.warning(self.parent, "Error", f"Target folder already exists: {os.path.basename(target_path)}")
                    return
                except Exception as e:
                    QMessageBox.critical(self.parent, "Copy Error", f"Failed to copy folder: {str(e)}")
                    return
            else:
                QMessageBox.warning(self.parent, "Error", f"Unsupported file type: {source_path}")
                return
            
            # If it was a cut action, delete the original file/folder
            if success and clipboard_data['action'] == 'cut':
                try:
                    if os.path.isfile(source_path):
                        os.remove(source_path)
                        self.status_label.setText(f"Moved file: {os.path.basename(target_path)}")
                    elif os.path.isdir(source_path):
                        shutil.rmtree(source_path)
                        self.status_label.setText(f"Moved folder: {os.path.basename(target_path)}")
                    
                    # Clear clipboard after successful cut operation
                    self._clipboard_data = None
                except Exception as e:
                    QMessageBox.warning(self.parent, "Warning", f"File copied but failed to delete original: {str(e)}")
            
            # For copy operations, don't clear clipboard (allow multiple pastes)
            if clipboard_data['action'] == 'copy':
                pass  # Keep clipboard data for multiple pastes
            
            # Refresh the file list
            self.refresh_files()
                
        except Exception as e:
            QMessageBox.critical(self.parent, "Paste Error", f"Failed to paste: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def has_file_in_clipboard(self):
        """Check if there's a file in clipboard"""
        return hasattr(self, '_clipboard_data') and self._clipboard_data is not None
    
    def clear_clipboard(self):
        """Clear the file clipboard"""
        self._clipboard_data = None
        self.status_label.setText("Clipboard cleared")
    
    def preview_file(self, entry):
        """Preview a file based on its type"""
        try:
            file_path = os.path.join(self.tmp_root, entry['path'])
            if not os.path.exists(file_path):
                QMessageBox.warning(self.parent, "Error", "File not found")
                return
            
            mime_type = entry['mime']
            file_extension = os.path.splitext(entry['name'])[1].lower()
            
            # Create preview dialog
            preview_dialog = QDialog(self.parent)
            preview_dialog.setWindowTitle(f"Preview: {entry['name']}")
            preview_dialog.setModal(True)
            preview_dialog.resize(800, 600)
            
            layout = QVBoxLayout(preview_dialog)
            
            # Handle different file types
            if mime_type.startswith('text/') or file_extension in ['.py', '.json', '.txt', '.md', '.xml', '.html', '.css', '.js']:
                # Text files
                self.preview_text_file(file_path, layout)
                
            elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
                # Image files
                self.preview_image_file(file_path, layout)
                
            elif file_extension in ['.pdf']:
                # PDF files
                self.preview_pdf_file(file_path, layout)
                
            elif file_extension in ['.docx', '.doc']:
                # Word documents
                self.preview_docx_file(file_path, layout)
                
            else:
                # Unsupported file type
                self.preview_unsupported_file(entry, layout)
            
            # Add action buttons
            button_layout = QHBoxLayout()
            
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda: self.download_file(entry))
            button_layout.addWidget(download_btn)
            
            open_btn = QPushButton("Open in System")
            open_btn.clicked.connect(lambda: self.open_file_in_system(file_path))
            button_layout.addWidget(open_btn)
            
            button_layout.addStretch()
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(preview_dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            preview_dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to preview: {str(e)}")
    
    def preview_text_file(self, file_path, layout):
        """Preview text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)  # First 50KB
            
            text_edit = QTextEdit()
            text_edit.setPlainText(content)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #ffffff;
                    border: 1px solid #444444;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            layout.addWidget(text_edit)
            
        except Exception as e:
            error_label = QLabel(f"Error reading file: {str(e)}")
            error_label.setStyleSheet("color: #ff6b6b;")
            layout.addWidget(error_label)
    
    def preview_image_file(self, file_path, layout):
        """Preview image files"""
        try:
            # Create image label
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("""
                QLabel {
                    background-color: #1a1a1a;
                    border: 1px solid #444444;
                }
            """)
            
            # Load and scale image
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale image to fit dialog while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(700, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
                
                # Add image info
                info_label = QLabel(f"Size: {pixmap.width()}x{pixmap.height()} | File: {os.path.basename(file_path)}")
                info_label.setStyleSheet("color: #cccccc; padding: 5px;")
                layout.addWidget(info_label)
            else:
                image_label.setText("Unable to load image")
                image_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
            
            layout.addWidget(image_label)
            
        except Exception as e:
            error_label = QLabel(f"Error loading image: {str(e)}")
            error_label.setStyleSheet("color: #ff6b6b;")
            layout.addWidget(error_label)
    
    def preview_pdf_file(self, file_path, layout):
        """Preview PDF files"""
        try:
            # Try to use system PDF viewer
            self.open_file_in_system(file_path)
            
            # Fallback: show file info
            info_label = QLabel(f"PDF file: {os.path.basename(file_path)}")
            info_label.setStyleSheet("color: #cccccc; padding: 20px;")
            layout.addWidget(info_label)
            
            note_label = QLabel("PDF opened in system viewer. Use 'Open in System' button to open again.")
            note_label.setStyleSheet("color: #ffa500; padding: 10px;")
            layout.addWidget(note_label)
            
        except Exception as e:
            error_label = QLabel(f"Error opening PDF: {str(e)}")
            error_label.setStyleSheet("color: #ff6b6b;")
            layout.addWidget(error_label)
    
    def preview_docx_file(self, file_path, layout):
        """Preview DOCX files by opening in LibreOffice"""
        try:
            # Try to open with LibreOffice
            success = self.open_docx_in_libreoffice(file_path)
            
            if success:
                info_label = QLabel(f"DOCX file opened in LibreOffice: {os.path.basename(file_path)}")
                info_label.setStyleSheet("color: #4CAF50; padding: 20px; font-weight: bold;")
                layout.addWidget(info_label)
                
                note_label = QLabel("Document opened in LibreOffice. You can close this preview dialog.")
                note_label.setStyleSheet("color: #2196F3; padding: 10px;")
                layout.addWidget(note_label)
            else:
                # Fallback: show file info and manual open option
                info_label = QLabel(f"DOCX file: {os.path.basename(file_path)}")
                info_label.setStyleSheet("color: #cccccc; padding: 20px;")
                layout.addWidget(info_label)
                
                note_label = QLabel("LibreOffice not found. Use 'Open in System' button to open manually.")
                note_label.setStyleSheet("color: #ffa500; padding: 10px;")
                layout.addWidget(note_label)
                
        except Exception as e:
            error_label = QLabel(f"Error opening DOCX: {str(e)}")
            error_label.setStyleSheet("color: #ff6b6b; padding: 20px;")
            layout.addWidget(error_label)
    
    def preview_unsupported_file(self, entry, layout):
        """Preview unsupported file types"""
        info_label = QLabel(f"Preview not supported for: {entry['name']}")
        info_label.setStyleSheet("color: #ffa500; padding: 20px;")
        layout.addWidget(info_label)
        
        mime_label = QLabel(f"MIME Type: {entry['mime']}")
        mime_label.setStyleSheet("color: #cccccc; padding: 5px;")
        layout.addWidget(mime_label)
    
    def open_file_in_system(self, file_path):
        """Open file in system default application"""
        try:
            system = platform.system()
            
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
                
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to open file in system: {str(e)}")
    
    def open_docx_in_libreoffice(self, file_path):
        """Open DOCX file specifically in LibreOffice"""
        try:
            system = platform.system()
            
            if system == "Linux":
                # Try different LibreOffice commands
                libreoffice_commands = [
                    "libreoffice",
                    "soffice",
                    "/usr/bin/libreoffice",
                    "/usr/bin/soffice"
                ]
                
                for cmd in libreoffice_commands:
                    try:
                        result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            # LibreOffice found, open the document
                            subprocess.Popen([cmd, file_path], start_new_session=True)
                            return True
                    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                        continue
                
                # If LibreOffice not found, try system default
                try:
                    subprocess.run(["xdg-open", file_path])
                    return True
                except:
                    return False
                    
            elif system == "Windows":
                # Try LibreOffice on Windows
                libreoffice_paths = [
                    r"C:\Program Files\LibreOffice\program\soffice.exe",
                    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
                ]
                
                for path in libreoffice_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path, file_path], start_new_session=True)
                        return True
                
                # Fallback to system default
                os.startfile(file_path)
                return True
                
            elif system == "Darwin":  # macOS
                # Try LibreOffice on macOS
                try:
                    subprocess.run(["/Applications/LibreOffice.app/Contents/MacOS/soffice", file_path])
                    return True
                except:
                    # Fallback to system default
                    subprocess.run(["open", file_path])
                    return True
            
            return True
            
        except Exception as e:
            print(f"Error opening DOCX in LibreOffice: {str(e)}")
            return False
    
    def rename_file(self, entry):
        """Rename a file or folder"""
        new_name, ok = QInputDialog.getText(self.parent, "Rename", "New name:", text=entry['name'])
        if ok and new_name and new_name != entry['name']:
            try:
                old_path = os.path.join(self.tmp_root, entry['path'])
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                
                if self.is_path_safe(new_path):
                    os.rename(old_path, new_path)
                    self.load_directory(self.current_path)
                    self.status_label.setText(f"Renamed: {entry['name']} → {new_name}")
                else:
                    QMessageBox.warning(self.parent, "Error", "Invalid new name")
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to rename: {str(e)}")
    
    def delete_file(self, entry):
        """Delete a file or folder"""
        reply = QMessageBox.question(
            self.parent, "Confirm Delete", 
            f"Are you sure you want to delete '{entry['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                file_path = os.path.join(self.tmp_root, entry['path'])
                if entry['isDir']:
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                
                self.load_directory(self.current_path)
                self.status_label.setText(f"Deleted: {entry['name']}")
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to delete: {str(e)}")
    
    def download_selected_as_zip(self):
        """Download selected files as ZIP"""
        if not self.selected_items:
            return
        
        try:
            save_path, _ = QFileDialog.getSaveFileName(
                self.parent, "Save ZIP file", "files.zip", "ZIP Files (*.zip)"
            )
            if save_path:
                with zipfile.ZipFile(save_path, 'w') as zipf:
                    for entry in self.selected_items:
                        file_path = os.path.join(self.tmp_root, entry['path'])
                        if os.path.exists(file_path):
                            zipf.write(file_path, entry['name'])
                
                self.status_label.setText(f"Downloaded ZIP with {len(self.selected_items)} files")
        except Exception as e:
            QMessageBox.warning(self.parent, "Error", f"Failed to create ZIP: {str(e)}")
    
    def delete_selected(self):
        """Delete selected files"""
        if not self.selected_items:
            return
        
        reply = QMessageBox.question(
            self.parent, "Confirm Delete", 
            f"Are you sure you want to delete {len(self.selected_items)} items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for entry in self.selected_items:
                    file_path = os.path.join(self.tmp_root, entry['path'])
                    if entry['isDir']:
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                
                self.load_directory(self.current_path)
                self.status_label.setText(f"Deleted {len(self.selected_items)} items")
                self.selected_items = []
            except Exception as e:
                QMessageBox.warning(self.parent, "Error", f"Failed to delete: {str(e)}")
    
    def open_folder(self, entry):
        """Open a folder"""
        if entry['isDir']:
            new_path = os.path.join(self.current_path, entry['name'])
            if self.is_path_safe(new_path):
                self.load_directory(new_path)
    
    # Export Code functionality
    def export_json_data(self):
        """Export configuration, questions, and execution steps as JSON"""
        try:
            # Collect all data
            # Get automatic images data using the dedicated method
            print("DEBUG: About to get automatic_images_data")
            automatic_images_data = self.get_automatic_images_data()
            print(f"DEBUG: Automatic images data: {automatic_images_data}")
            print(f"DEBUG: Parent object: {self.parent}")
            print(f"DEBUG: Parent has automatic_images: {hasattr(self.parent, 'automatic_images')}")
            if hasattr(self.parent, 'automatic_images'):
                print(f"DEBUG: Parent automatic_images: {self.parent.automatic_images}")
            else:
                print("DEBUG: Parent does not have automatic_images attribute")
                # Try to access it directly
                try:
                    if hasattr(self.parent, '__dict__'):
                        print(f"DEBUG: Parent attributes: {list(self.parent.__dict__.keys())}")
                except Exception as e:
                    print(f"DEBUG: Error accessing parent attributes: {e}")
            
            # Ensure automatic_images is always included
            if not automatic_images_data:
                automatic_images_data = []
                print("DEBUG: Using empty automatic_images array as fallback")
            
            # Create the complete export data structure
            export_data = {
                "ui": {
                    "title": "NO CGI OR OTHER SCRIPTING FOR UPLOADS"
                },
                "questions": {
                    "ui": {
                        "title": "NO CGI OR OTHER SCRIPTING FOR UPLOADS"
                    },
                    "questions": self.get_essential_questions_data(),
                    "metadata": {
                        "total_questions": len(self.get_essential_questions_data()),
                        "description": "Automation questions configuration",
                        "version": "1.0"
                    },
                    "configuration": {
                        "fields": self.get_configuration_data()
                    },
                    "Summary": {
                        "result_1": "none",
                        "remark_1": "Automatically generated summary based on Section 1 testcase scenario: none"
                    }
                },
                "metadata": {
                    "total_questions": 5,
                    "description": "FortiAP device setup and verification questions",
                    "version": "1.0"
                },
                "configuration": {
                    "fields": self.get_configuration_data()
                },
                "execution_steps": self.get_execution_steps_data(),
                "test_bed_diagram": self.get_test_bed_diagram_data(),
                "automatic_images": automatic_images_data
            }
            
            # Create the code folder structure
            code_folder_path = self.create_code_folder()
            
            if code_folder_path:
                # Create images folder alongside code folder
                project_dir = os.path.dirname(code_folder_path)
                images_folder_path = os.path.join(project_dir, "images")
                os.makedirs(images_folder_path, exist_ok=True)
                
                # Copy pending images to the export folder  
                self.copy_pending_images_to_export_folder(images_folder_path)
                
                # Also copy images directly from step widgets (fallback method)
                self.copy_images_from_step_widgets(images_folder_path)
                
                # Save JSON file in the code folder
                json_file_path = os.path.join(code_folder_path, "questions_config.json")
                
                # Debug: Print the export data before writing
                print(f"DEBUG: Final export_data keys: {list(export_data.keys())}")
                print(f"DEBUG: automatic_images in export_data: {export_data.get('automatic_images', 'NOT FOUND')}")
                print(f"DEBUG: Full export_data structure:")
                for key, value in export_data.items():
                    if key == 'automatic_images':
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: {type(value)}")
                
                # Write JSON file (ensure no original_path fields are persisted)
                def _strip_original_path(obj):
                    if isinstance(obj, dict):
                        obj.pop('original_path', None)
                        return {k: _strip_original_path(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [_strip_original_path(x) for x in obj]
                    return obj
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(_strip_original_path(export_data), f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self.parent,
                    "Export Successful",
                    f"JSON data exported successfully to:\n{json_file_path}"
                )
            else:
                QMessageBox.warning(
                    self.parent,
                    "Export Warning",
                    "Could not create code folder. Please check permissions."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Export Error",
                f"Failed to export JSON data:\n{str(e)}"
            )
    
    def export_script_py(self):
        """Export script.py functionality"""
        try:
            # Create the code folder structure
            code_folder_path = self.create_code_folder()
            
            if code_folder_path:
                # Create images folder alongside code folder
                project_dir = os.path.dirname(code_folder_path)
                images_folder_path = os.path.join(project_dir, "images")
                os.makedirs(images_folder_path, exist_ok=True)
                
                # Copy pending images to the export folder  
                self.copy_pending_images_to_export_folder(images_folder_path)
                
                # Also copy images directly from step widgets (fallback method)
                self.copy_images_from_step_widgets(images_folder_path)
                
                # Save script.py file in the code folder
                script_file_path = os.path.join(code_folder_path, "script.py")
                
                # Create a basic script.py template
                script_content = self.generate_script_py_content()
                
                # Write script.py file
                with open(script_file_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                
                QMessageBox.information(
                    self.parent,
                    "Script.py Export Successful",
                    f"Script.py file exported successfully to:\n{script_file_path}"
                )
            else:
                QMessageBox.warning(
                    self.parent,
                    "Export Warning",
                    "Could not create code folder. Please check permissions."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Export Error",
                f"Failed to export script.py:\n{str(e)}"
            )
    
    def get_configuration_data(self):
        """Get configuration fields data from main application"""
        if hasattr(self.parent, 'get_dut_config_data'):
            return self.parent.get_dut_config_data()
        return []
    
    def get_essential_questions_data(self):
        """Get essential questions data from main application"""
        try:
            if hasattr(self.parent, 'get_essential_questions_data'):
                data = self.parent.get_essential_questions_data()
                print(f"Essential questions data: {data}")  # Debug print
                return data if data else {'questions': []}
            else:
                print("Warning: get_essential_questions_data method not found on parent")
                return {'questions': []}
        except Exception as e:
            print(f"Error getting essential questions data: {e}")
            return {'questions': []}

    def get_execution_steps_data(self):
        """Get execution steps data from main application"""
        try:
            # First try to get the actual question data for review
            if hasattr(self.parent, 'get_execution_step_questions_for_review'):
                data = self.parent.get_execution_step_questions_for_review()
                print(f"Execution step questions for review: {data}")  # Debug print
                if data:
                    return data
            
            # Fallback to the original method if the new method doesn't exist
            if hasattr(self.parent, 'get_execution_step_questions_data'):
                data = self.parent.get_execution_step_questions_data()
                print(f"Execution steps data: {data}")  # Debug print
                
                # If the data is already in the correct format, return it
                if data and isinstance(data, list):
                    # Check if the first item has question data
                    if data and len(data) > 0 and 'question' in data[0]:
                        return data
                    
                    # If not, try to extract question data from the execution steps
                    questions = []
                    for step in data:
                        if isinstance(step, dict):
                            # Try to extract question data from the step
                            if 'question' in step:
                                questions.append(step)
                            elif 'name' in step and 'description' in step:
                                # Convert execution step to question format
                                questions.append({
                                    'question': step.get('name', ''),
                                    'help_text': step.get('description', ''),
                                    'question_type': 'execution_step'
                                })
                    
                    return questions if questions else data
                
                return data if data else []
            else:
                print("Warning: get_execution_step_questions_data method not found on parent")
                return []
        except Exception as e:
            print(f"Error getting execution steps data: {e}")
            return []
    
    def get_automatic_images_data(self):
        """Get automatic images data from main application"""
        try:
            print(f"DEBUG: get_automatic_images_data called")
            print(f"DEBUG: self.parent = {self.parent}")
            
            # CRITICAL FIX: Collect all placeholders from all sections before returning data
            if hasattr(self.parent, 'collect_all_section_placeholders'):
                print("DEBUG: Calling collect_all_section_placeholders to gather all placeholders")
                new_placeholders_added = self.parent.collect_all_section_placeholders()
                print(f"DEBUG: collect_all_section_placeholders added {new_placeholders_added} new placeholders")
            else:
                print("DEBUG: collect_all_section_placeholders method not found in parent")
            
            if hasattr(self.parent, 'automatic_images'):
                data = self.parent.automatic_images
                print(f"DEBUG: Found automatic_images: {data}")
                print(f"DEBUG: Total placeholders in automatic_images: {len(data)}")
                return data
            print(f"DEBUG: automatic_images not found in parent")
            return []
        except Exception as e:
            print(f"Error getting automatic images data: {e}")
            return []
    
    def add_test_placeholders(self):
        """Add test placeholders for debugging"""
        try:
            if hasattr(self.parent, 'add_test_placeholders'):
                self.parent.add_test_placeholders()
            else:
                print("DEBUG: add_test_placeholders method not found in parent")
                # Add placeholders directly
                if hasattr(self.parent, 'automatic_images'):
                    test_placeholders = [
                        "amazon_screenshot",
                        "test_bed_diagram",
                        "network_topology",
                        "security_scan_results"
                    ]
                    
                    for placeholder in test_placeholders:
                        placeholder_info = {
                            "placeholder": placeholder,
                            "image_path": None
                        }
                        self.parent.automatic_images.append(placeholder_info)
                    
                    print(f"DEBUG: Added {len(test_placeholders)} test placeholders")
                    print(f"DEBUG: Total placeholders: {len(self.parent.automatic_images)}")
                    
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self.parent,
                        "Test Placeholders Added",
                        f"Added {len(test_placeholders)} test placeholders.\n\nTotal placeholders: {len(self.parent.automatic_images)}"
                    )
                    
                    # Also refresh the counts to show the new placeholders
                    self.refresh_counts()
        except Exception as e:
            print(f"Error adding test placeholders: {e}")
    
    def collect_all_placeholders_manual(self):
        """Manual method to collect all placeholders from all sections"""
        try:
            if hasattr(self.parent, 'collect_all_placeholders_manual'):
                self.parent.collect_all_placeholders_manual()
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    "Placeholder collection method not found in parent application."
                )
        except Exception as e:
            print(f"Error in collect_all_placeholders_manual: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.parent,
                "Error",
                f"An error occurred while collecting placeholders:\n{str(e)}"
            )
    
    def create_code_folder(self):
        """Create the code folder structure in tmp/<testcase_name>/code/"""
        try:
            # Get the current testcase name from the parent application
            project_name = "Unknown_Test_Case"  # Default name
            
            # Try to get testcase name from parent application
            if hasattr(self.parent, 'get_test_case_title'):
                try:
                    testcase_name = self.parent.get_test_case_title()
                    if testcase_name and testcase_name.strip():
                        project_name = testcase_name.strip()
                        print(f"DEBUG: Using testcase name from parent: {project_name}")
                except Exception as e:
                    print(f"DEBUG: Error getting testcase name from parent: {e}")
            
            # Fallback: try to get from 1.json
            if project_name == "Unknown_Test_Case":
                try:
                    import json
                    config_path = os.path.expanduser('~/1.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            config = json.load(f)
                            if 'testcase_title' in config:
                                project_name = config['testcase_title']
                                print(f"DEBUG: Using testcase name from 1.json: {project_name}")
                except Exception as e:
                    print(f"DEBUG: Error reading testcase name from 1.json: {e}")
            
            # Clean the project name for use as directory name
            import re
            # First replace forward slashes with underscores to prevent path splitting
            clean_project_name = project_name.replace('/', '_')
            # Then remove other invalid characters
            clean_project_name = re.sub(r'[^\w\s\.\-]', '', clean_project_name)
            clean_project_name = clean_project_name.replace(' ', '_')
            
            # Check if the project folder already exists in tmp
            app_root = self.get_app_root_dir()
            tmp_dir = os.path.join(app_root, "tmp")
            existing_folders = []
            
            if os.path.exists(tmp_dir):
                existing_folders = [d for d in os.listdir(tmp_dir) 
                                  if os.path.isdir(os.path.join(tmp_dir, d))]
            
            # First, check if the exact cleaned project name already exists
            if clean_project_name in existing_folders:
                project_name = clean_project_name
            else:
                # Check if there's a similar folder (for backward compatibility)
                matching_folder = None
                
                # Look for patterns like "X.X.X_VULNERABILITY_SCANNING"
                pattern = r'(\d+\.\d+\.\d+_VULNERABILITY_SCANNING)'
                match = re.search(pattern, clean_project_name)
                if match:
                    main_project_name = match.group(1)
                    
                    # Check if this exact pattern exists
                    for folder in existing_folders:
                        if folder == main_project_name:
                            matching_folder = folder
                            break
                
                # If no exact match, try partial matching
                if not matching_folder:
                    for folder in existing_folders:
                        # Check if the folder name contains the project name (case insensitive)
                        if clean_project_name.lower() in folder.lower() or folder.lower() in clean_project_name.lower():
                            # Prefer exact matches or clean pattern matches
                            if folder == clean_project_name or re.match(r'^\d+\.\d+\.\d+_VULNERABILITY_SCANNING$', folder):
                                matching_folder = folder
                                break
                            elif not matching_folder:  # Use first match as fallback
                                matching_folder = folder
                
                if matching_folder:
                    project_name = matching_folder
                else:
                    # Create new folder with cleaned name
                    project_name = clean_project_name
            
            # Create the full path: tmp/<project_name>/code/
            project_dir = os.path.join(tmp_dir, project_name)
            code_dir = os.path.join(project_dir, "code")
            
            # Create directories if they don't exist
            os.makedirs(code_dir, exist_ok=True)

            # Create Input folder in home directory
            input_folder_path = os.path.expanduser("~/Input")
            try:
                os.makedirs(input_folder_path, exist_ok=True)
                print(f"DEBUG: Created/verified Input folder: {input_folder_path}")
            except Exception as e:
                print(f"ERROR: Could not create Input folder: {e}")
            
            
            print(f"DEBUG: Created code folder: {code_dir}")
            print(f"DEBUG: Project directory: {project_dir}")
            print(f"DEBUG: Using testcase name: {project_name}")
            
            return code_dir
            
        except Exception as e:
            print(f"Error creating code folder: {e}")
            return None
    
    def copy_scripts_from_step_widgets(self, code_folder_path):
        """Copy scripts directly from step widgets (fallback method)"""
        try:
            print("DEBUG: ===== COPY SCRIPTS FROM STEP WIDGETS START =====")
            print(f"DEBUG: Export folder path: {code_folder_path}")
            
            if not hasattr(self.parent, 'step_widgets'):
                print("DEBUG: No step_widgets found")
                return
            
            scripts_copied = 0
            
            for step_key, step_widget in self.parent.step_widgets.items():
                print(f"DEBUG: Checking step widget: {step_key}")
                
                if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                    print(f"DEBUG: Found {len(step_widget['upload_scripts_list'])} scripts in step {step_key}")
                    
                    for script_info in step_widget['upload_scripts_list']:
                        print(f"DEBUG: Processing script: {script_info}")
                        
                        # Get the original path from the script info (do not persist this later)
                        original_path = script_info.get('path', '') or script_info.get('original_path', '')
                        filename = script_info.get('filename', '')
                        
                        print(f"DEBUG: Original path: {original_path}")
                        print(f"DEBUG: Filename: {filename}")
                        
                        if original_path and filename:
                            # Normalize the path
                            original_path = os.path.normpath(os.path.expanduser(original_path))
                            
                            # Check if file exists
                            if os.path.isfile(original_path):
                                # Generate unique filename
                                import uuid
                                unique_id = str(uuid.uuid4())[:8]
                                new_filename = f"uploaded_{unique_id}_{filename}"
                                dst_path = os.path.join(code_folder_path, new_filename)
                                
                                # Copy the file
                                shutil.copy2(original_path, dst_path)
                                print(f"✅ Copied script from step widget: {filename} -> {new_filename}")
                                scripts_copied += 1
                                # Update fields and remove original_path from persisted data
                                script_info['path'] = dst_path
                                script_info['filename'] = new_filename
                                if 'original_path' in script_info:
                                    del script_info['original_path']
                            else:
                                print(f"⚠️ Script file not found: {original_path}")
                        else:
                            print(f"⚠️ Script missing path or filename: {script_info}")
                else:
                    print(f"DEBUG: No scripts found in step {step_key}")
            
            print(f"DEBUG: Total scripts copied from step widgets: {scripts_copied}")
            print("DEBUG: ===== COPY SCRIPTS FROM STEP WIDGETS COMPLETED =====")
            
        except Exception as e:
            print(f"⚠️ Error copying scripts from step widgets: {e}")
            import traceback
            traceback.print_exc()

    def copy_images_from_step_widgets(self, images_folder_path):
        """Copy images directly from step widgets (fallback method)"""
        try:
            print("DEBUG: ===== COPY IMAGES FROM STEP WIDGETS START =====")
            print(f"DEBUG: Export images folder path: {images_folder_path}")
            
            if not hasattr(self.parent, 'step_widgets'):
                print("DEBUG: No step_widgets found")
                return
            
            images_copied = 0
            
            for step_key, step_widget in self.parent.step_widgets.items():
                print(f"DEBUG: Checking step widget: {step_key}")
                
                if 'upload_images_list' in step_widget and step_widget['upload_images_list']:
                    print(f"DEBUG: Found {len(step_widget['upload_images_list'])} images in step {step_key}")
                    
                    for image_info in step_widget['upload_images_list']:
                        print(f"DEBUG: Processing image: {image_info}")
                        
                        # Get the original path from the image info (do not persist this later)
                        original_path = image_info.get('path', '') or image_info.get('original_path', '')
                        filename = image_info.get('filename', '')
                        
                        print(f"DEBUG: Original path: {original_path}")
                        print(f"DEBUG: Filename: {filename}")
                        
                        if original_path and filename:
                            # Normalize the path
                            original_path = os.path.normpath(os.path.expanduser(original_path))
                            
                            # Check if file exists
                            if os.path.isfile(original_path):
                                # Check if it's a valid image file
                                valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg']
                                if any(original_path.lower().endswith(ext) for ext in valid_image_extensions):
                                    # Generate unique filename
                                    import uuid
                                    unique_id = str(uuid.uuid4())[:8]
                                    file_extension = os.path.splitext(filename)[1]
                                    base_filename = os.path.splitext(filename)[0]
                                    new_filename = f"uploaded_{unique_id}_{base_filename}{file_extension}"
                                    dst_path = os.path.join(images_folder_path, new_filename)
                                    
                                    # Copy the file
                                    import shutil
                                    shutil.copy2(original_path, dst_path)
                                    print(f"✅ Copied image from step widget: {filename} -> {new_filename}")
                                    images_copied += 1
                                    
                                    # Update the image info with the new path and remove original_path from persisted data
                                    image_info['path'] = dst_path
                                    image_info['filename'] = new_filename
                                    if 'original_path' in image_info:
                                        del image_info['original_path']
                                else:
                                    print(f"⚠️ Not a valid image file: {original_path}")
                            else:
                                print(f"⚠️ Image file not found: {original_path}")
                        else:
                            print(f"⚠️ Missing original_path or filename for image")
            
            print(f"DEBUG: Total images copied from step widgets: {images_copied}")
            print("DEBUG: ===== COPY IMAGES FROM STEP WIDGETS COMPLETED =====")
            
        except Exception as e:
            print(f"⚠️ Error copying images from step widgets: {e}")
            import traceback
            traceback.print_exc()

    def copy_pending_scripts_to_export_folder(self, code_folder_path):
        """Copy pending scripts from import to export folder (same logic as upload_section_11_script_from_path)"""
        try:
            print("DEBUG: ===== COPY PENDING SCRIPTS TO EXPORT FOLDER START =====")
            print(f"DEBUG: Export folder path: {code_folder_path}")
            
            # Debug script storage first
            self.debug_script_storage()
            
            # Debug import project directory
            if hasattr(self.parent, 'import_project_dir'):
                print(f"DEBUG: Import project directory: {self.parent.import_project_dir}")
            else:
                print("DEBUG: No import_project_dir found")
            
            # First try to get scripts from pending_scripts_for_export
            scripts_to_copy = []
            
            if hasattr(self.parent, 'pending_scripts_for_export') and self.parent.pending_scripts_for_export:
                print(f"DEBUG: Found {len(self.parent.pending_scripts_for_export)} scripts in pending_scripts_for_export")
                scripts_to_copy.extend(self.parent.pending_scripts_for_export)
            
            # Also check step_widgets for scripts (same as the original hardcoded approach)
            if hasattr(self.parent, 'step_widgets'):
                print(f"DEBUG: Checking step_widgets for scripts")
                for step_key, step_widget in self.parent.step_widgets.items():
                    if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                        print(f"DEBUG: Found {len(step_widget['upload_scripts_list'])} scripts in step_widget {step_key}")
                        for script_info in step_widget['upload_scripts_list']:
                            # Use 'path' field instead of 'original_path'
                            relative_path = script_info.get('path', '')
                            if relative_path and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                # Combine import directory with relative path to get absolute path
                                absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                                print(f"DEBUG: Combined absolute path for script: {absolute_path}")
                                
                                # Create the same structure as pending_scripts_for_export (do not persist original_path later)
                                script_data = {
                                    'original_path': absolute_path,  # temp for copying only
                                    'original_filename': script_info.get('original_filename', ''),
                                    'description': script_info.get('description', ''),
                                    'script_info': script_info,
                                    'step_data': step_widget
                                }
                                scripts_to_copy.append(script_data)
                            else:
                                print(f"DEBUG: Skipping script - missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
            
            # Also check global step scripts (same as the original hardcoded approach)
            if hasattr(self.parent, '_global_step_scripts'):
                print(f"DEBUG: Checking _global_step_scripts for scripts")
                for step_key, step_scripts in self.parent._global_step_scripts.items():
                    print(f"DEBUG: Found {len(step_scripts)} scripts in global storage for step {step_key}")
                    for script_info in step_scripts:
                        # Use 'path' field instead of 'original_path'
                        relative_path = script_info.get('path', '')
                        if relative_path and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                            # Combine import directory with relative path to get absolute path
                            absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                            print(f"DEBUG: Combined absolute path for global script: {absolute_path}")
                            
                            # Create the same structure as pending_scripts_for_export (do not persist original_path later)
                            script_data = {
                                'original_path': absolute_path,  # temp for copying only
                                'original_filename': script_info.get('original_filename', ''),
                                'description': script_info.get('description', ''),
                                'script_info': script_info,
                                'step_data': {'step_key': step_key}
                            }
                            scripts_to_copy.append(script_data)
                        else:
                            print(f"DEBUG: Skipping global script - missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
            
            if not scripts_to_copy:
                print("DEBUG: No scripts found to copy")
                return
            
            print(f"DEBUG: Total scripts to copy: {len(scripts_to_copy)}")
            
            for i, script_data in enumerate(scripts_to_copy):
                print(f"DEBUG: Processing script {i+1}/{len(scripts_to_copy)}")
                print(f"DEBUG: Script data: {script_data}")
                
                original_path = script_data.get('original_path', '')
                original_filename = script_data.get('original_filename', '')
                description = script_data.get('description', '')
                
                print(f"DEBUG: Original path: {original_path}")
                print(f"DEBUG: Original filename: {original_filename}")
                print(f"DEBUG: Description: {description}")
                
                # Validate path (same as upload_section_11_script_from_path)
                if not original_path:
                    print("⚠️ Script has no original path")
                    continue
                
                original_path = os.path.normpath(os.path.expanduser(original_path))
                
                # If the original path doesn't exist, try to find it in the old testcase directory
                if not os.path.isfile(original_path):
                    print(f"⚠️ Script file not found at: {original_path}")
                    
                    # Try to find the file in the old testcase directory
                    if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                        found_path = self._find_script_file_in_directory(self.parent.import_project_dir, original_filename)
                        if found_path:
                            original_path = found_path
                            print(f"✅ Found script file in old testcase directory: {original_path}")
                        else:
                            print(f"⚠️ Could not find script file {original_filename} in old testcase directory")
                            continue
                    else:
                        print(f"⚠️ No import_project_dir available to search for script")
                        continue
                
                if not original_path.lower().endswith(".py"):
                    print(f"⚠️ Not a Python file: {original_path}")
                    continue
                
                print(f"✅ Script file validated: {original_path}")
                
                # Generate unique filename for export (same as upload_section_11_script_from_path)
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                export_filename = f"uploaded_{unique_id}_{original_filename}"
                export_path = os.path.join(code_folder_path, export_filename)
                
                print(f"DEBUG: Export filename: {export_filename}")
                print(f"DEBUG: Export path: {export_path}")
                
                try:
                    # Copy the script file to export folder (same as upload_section_11_script_from_path)
                    import shutil
                    shutil.copy2(original_path, export_path)
                    print(f"✅ Successfully copied script: {original_filename} -> {export_filename}")
                    
                    # Update the script info in the parent with the new export path
                    script_info = script_data.get('script_info', {})
                    if script_info:
                        script_info['path'] = export_path
                        script_info['filename'] = export_filename
                        if 'original_path' in script_info:
                            del script_info['original_path']
                        print(f"✅ Updated script info with export path: {export_filename}")
                    
                    # Also update the step widget if available
                    step_data = script_data.get('step_data', {})
                    print(f"DEBUG: Step data structure: {step_data}")
                    if step_data and 'upload_scripts_list' in step_data:
                        for step_script in step_data['upload_scripts_list']:
                            if (step_script.get('original_filename') == original_filename and 
                                step_script.get('description') == description):
                                step_script['path'] = export_path
                                step_script['filename'] = export_filename
                                print(f"✅ Updated step widget script info: {export_filename}")
                                break
                    else:
                        print(f"DEBUG: Step data structure doesn't have upload_scripts_list or is empty")
                        
                except Exception as e:
                    print(f"⚠️ Error copying script {original_filename}: {e}")
                    continue
            
            print("DEBUG: ===== COPY PENDING SCRIPTS TO EXPORT FOLDER COMPLETED =====")
            
            # Verify that scripts were copied successfully
            self.verify_scripts_copied(code_folder_path)
            
        except Exception as e:
            print(f"⚠️ Error in copy_pending_scripts_to_export_folder: {e}")
            import traceback
            traceback.print_exc()
    
    def verify_scripts_copied(self, code_folder_path):
        """Verify that scripts were copied successfully to the export folder"""
        try:
            print(f"DEBUG: Verifying scripts in export folder: {code_folder_path}")
            
            if not os.path.exists(code_folder_path):
                print(f"⚠️ Export folder does not exist: {code_folder_path}")
                return
            
            # List all files in the export folder
            files = os.listdir(code_folder_path)
            print(f"DEBUG: Files in export folder: {files}")
            
            # Check for script files (now using original filenames)
            script_files = [f for f in files if f.endswith('.py')]
            print(f"DEBUG: Found {len(script_files)} script files: {script_files}")
            
            if script_files:
                print(f"✅ Successfully copied {len(script_files)} scripts to export folder")
                for script in script_files:
                    script_path = os.path.join(code_folder_path, script)
                    if os.path.exists(script_path):
                        file_size = os.path.getsize(script_path)
                        print(f"✅ Script {script} exists with size {file_size} bytes")
                    else:
                        print(f"⚠️ Script {script} not found in export folder")
            else:
                print("⚠️ No uploaded script files found in export folder")
                
        except Exception as e:
            print(f"⚠️ Error verifying scripts: {e}")
    
    def copy_pending_images_to_export_folder(self, images_folder_path):
        """Copy pending images from import to export folder (same logic as upload_section_11_script_from_path)"""
        try:
            print("DEBUG: ===== COPY PENDING IMAGES TO EXPORT FOLDER START =====")
            print(f"DEBUG: Export images folder path: {images_folder_path}")
            
            # Debug image storage first
            self.debug_image_storage()
            
            # Debug import project directory
            if hasattr(self.parent, 'import_project_dir'):
                print(f"DEBUG: Import project directory: {self.parent.import_project_dir}")
            else:
                print("DEBUG: No import_project_dir found")
            
            # First try to get images from pending_images_for_export
            images_to_copy = []
            
            if hasattr(self.parent, 'pending_images_for_export') and self.parent.pending_images_for_export:
                print(f"DEBUG: Found {len(self.parent.pending_images_for_export)} images in pending_images_for_export")
                images_to_copy.extend(self.parent.pending_images_for_export)
            
            # Also check step_widgets for images (same as the original hardcoded approach)
            if hasattr(self.parent, 'step_widgets'):
                print(f"DEBUG: Checking step_widgets for images")
                for step_key, step_widget in self.parent.step_widgets.items():
                    if 'upload_images_list' in step_widget and step_widget['upload_images_list']:
                        print(f"DEBUG: Found {len(step_widget['upload_images_list'])} images in step_widget {step_key}")
                        for image_info in step_widget['upload_images_list']:
                            # Use 'path' field instead of 'original_path'
                            relative_path = image_info.get('path', '')
                            if relative_path and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                # Combine import directory with relative path to get absolute path
                                absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                                print(f"DEBUG: Combined absolute path for image: {absolute_path}")
                                
                                # Create the same structure as pending_images_for_export (do not persist original_path later)
                                image_data = {
                                    'original_path': absolute_path,  # temp for copying only
                                    'original_filename': image_info.get('original_filename', ''),
                                    'description': image_info.get('description', ''),
                                    'image_info': image_info,
                                    'step_data': step_widget
                                }
                                images_to_copy.append(image_data)
                            else:
                                print(f"DEBUG: Skipping image - missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
            
            # Also check global step images (same as the original hardcoded approach)
            if hasattr(self.parent, '_global_step_images'):
                print(f"DEBUG: Checking _global_step_images for images")
                for step_key, step_images in self.parent._global_step_images.items():
                    print(f"DEBUG: Found {len(step_images)} images in global storage for step {step_key}")
                    for image_info in step_images:
                        # Use 'path' field instead of 'original_path'
                        relative_path = image_info.get('path', '')
                        if relative_path and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                            # Combine import directory with relative path to get absolute path
                            absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                            print(f"DEBUG: Combined absolute path for global image: {absolute_path}")
                            
                            # Create the same structure as pending_images_for_export (do not persist original_path later)
                            image_data = {
                                'original_path': absolute_path,  # temp for copying only
                                'original_filename': image_info.get('original_filename', ''),
                                'description': image_info.get('description', ''),
                                'image_info': image_info,
                                'step_data': {'step_key': step_key}
                            }
                            images_to_copy.append(image_data)
                        else:
                            print(f"DEBUG: Skipping global image - missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
            
            if not images_to_copy:
                print("DEBUG: No images found to copy")
                return
            
            print(f"DEBUG: Total images to copy: {len(images_to_copy)}")
            
            for i, image_data in enumerate(images_to_copy):
                print(f"DEBUG: Processing image {i+1}/{len(images_to_copy)}")
                print(f"DEBUG: Image data: {image_data}")
                
                original_path = image_data.get('original_path', '')
                original_filename = image_data.get('original_filename', '')
                description = image_data.get('description', '')
                
                print(f"DEBUG: Original path: {original_path}")
                print(f"DEBUG: Original filename: {original_filename}")
                print(f"DEBUG: Description: {description}")
                
                # Validate path (same as upload_section_11_script_from_path)
                if not original_path:
                    print("⚠️ Image has no original path")
                    continue
                
                original_path = os.path.normpath(os.path.expanduser(original_path))
                
                # If the original path doesn't exist, try to find it in the old testcase directory
                if not os.path.isfile(original_path):
                    print(f"⚠️ Image file not found at: {original_path}")
                    
                    # Try to find the file in the old testcase directory
                    if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                        found_path = self._find_image_file_in_directory(self.parent.import_project_dir, original_filename)
                        if found_path:
                            original_path = found_path
                            print(f"✅ Found image file in old testcase directory: {original_path}")
                        else:
                            print(f"⚠️ Could not find image file {original_filename} in old testcase directory")
                            continue
                    else:
                        print(f"⚠️ No import_project_dir available to search for image")
                        continue
                
                # Check if it's a valid image file
                valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg']
                if not any(original_path.lower().endswith(ext) for ext in valid_image_extensions):
                    print(f"⚠️ Not a valid image file: {original_path}")
                    continue
                
                print(f"✅ Image file validated: {original_path}")
                
                # Generate unique filename for export (same as upload_section_11_script_from_path)
                import uuid
                unique_id = str(uuid.uuid4())[:8]
                file_extension = os.path.splitext(original_filename)[1]
                base_filename = os.path.splitext(original_filename)[0]
                export_filename = f"uploaded_{unique_id}_{base_filename}{file_extension}"
                export_path = os.path.join(images_folder_path, export_filename)
                
                print(f"DEBUG: Export filename: {export_filename}")
                print(f"DEBUG: Export path: {export_path}")
                
                try:
                    # Copy the image file to export folder (same as upload_section_11_script_from_path)
                    import shutil
                    shutil.copy2(original_path, export_path)
                    print(f"✅ Successfully copied image: {original_filename} -> {export_filename}")
                    
                    # Update the image info in the parent with the new export path
                    image_info = image_data.get('image_info', {})
                    if image_info:
                        image_info['path'] = export_path
                        image_info['filename'] = export_filename
                        if 'original_path' in image_info:
                            del image_info['original_path']
                        print(f"✅ Updated image info with export path: {export_filename}")
                    
                    # Also update the step widget if available
                    step_data = image_data.get('step_data', {})
                    print(f"DEBUG: Step data structure: {step_data}")
                    if step_data and 'upload_images_list' in step_data:
                        for step_image in step_data['upload_images_list']:
                            if (step_image.get('original_filename') == original_filename and 
                                step_image.get('description') == description):
                                step_image['path'] = export_path
                                step_image['filename'] = export_filename
                                print(f"✅ Updated step widget image info: {export_filename}")
                                break
                    else:
                        print(f"DEBUG: Step data structure doesn't have upload_images_list or is empty")
                        
                except Exception as e:
                    print(f"⚠️ Error copying image {original_filename}: {e}")
                    continue
            
            print("DEBUG: ===== COPY PENDING IMAGES TO EXPORT FOLDER COMPLETED =====")
            
            # Verify that images were copied successfully
            self.verify_images_copied(images_folder_path)
            
        except Exception as e:
            print(f"⚠️ Error in copy_pending_images_to_export_folder: {e}")
            import traceback
            traceback.print_exc()
    
    def verify_images_copied(self, images_folder_path):
        """Verify that images were copied successfully to the export folder"""
        try:
            print(f"DEBUG: Verifying images in export folder: {images_folder_path}")
            
            if not os.path.exists(images_folder_path):
                print(f"⚠️ Export images folder does not exist: {images_folder_path}")
                return
            
            # List all files in the export folder
            files = os.listdir(images_folder_path)
            print(f"DEBUG: Files in export images folder: {files}")
            
            # Check for uploaded image files
            valid_image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg']
            uploaded_images = [f for f in files if f.startswith('uploaded_') and 
                             any(f.lower().endswith(ext) for ext in valid_image_extensions)]
            print(f"DEBUG: Found {len(uploaded_images)} uploaded image files: {uploaded_images}")
            
            if uploaded_images:
                print(f"✅ Successfully copied {len(uploaded_images)} images to export folder")
                for image in uploaded_images:
                    image_path = os.path.join(images_folder_path, image)
                    if os.path.exists(image_path):
                        file_size = os.path.getsize(image_path)
                        print(f"✅ Image {image} exists with size {file_size} bytes")
                    else:
                        print(f"⚠️ Image {image} not found in export folder")
            else:
                print("⚠️ No uploaded image files found in export folder")
                
        except Exception as e:
            print(f"⚠️ Error verifying images: {e}")
    
    def debug_image_storage(self):
        """Debug function to check what images are available in storage"""
        try:
            print("DEBUG: ===== IMAGE STORAGE DEBUG =====")
            
            # Check pending_images_for_export
            if hasattr(self.parent, 'pending_images_for_export'):
                print(f"DEBUG: pending_images_for_export has {len(self.parent.pending_images_for_export)} items")
                for i, image in enumerate(self.parent.pending_images_for_export):
                    print(f"DEBUG: pending_images_for_export[{i}]: {image}")
            else:
                print("DEBUG: No pending_images_for_export attribute found")
            
            # Check step_widgets
            if hasattr(self.parent, 'step_widgets'):
                print(f"DEBUG: step_widgets has {len(self.parent.step_widgets)} items")
                for step_key, step_widget in self.parent.step_widgets.items():
                    if 'upload_images_list' in step_widget:
                        print(f"DEBUG: step_widget {step_key} has {len(step_widget['upload_images_list'])} images")
                        for image in step_widget['upload_images_list']:
                            print(f"DEBUG: Image in {step_key}: {image}")
            else:
                print("DEBUG: No step_widgets attribute found")
            
            # Check global step images
            if hasattr(self.parent, '_global_step_images'):
                print(f"DEBUG: _global_step_images has {len(self.parent._global_step_images)} items")
                for step_key, images in self.parent._global_step_images.items():
                    print(f"DEBUG: Global step {step_key} has {len(images)} images")
                    for image in images:
                        print(f"DEBUG: Global image in {step_key}: {image}")
            else:
                print("DEBUG: No _global_step_images attribute found")
            
            print("DEBUG: ===== END IMAGE STORAGE DEBUG =====")
            
        except Exception as e:
            print(f"⚠️ Error in debug_image_storage: {e}")
    
    def _find_image_file_in_directory(self, directory, filename):
        """
        Recursively search for an image file in a directory
        
        Args:
            directory: Directory to search in
            filename: Filename to search for
            
        Returns:
            str: Full path to the file if found, None otherwise
        """
        try:
            if not os.path.exists(directory):
                return None
            
            for root, dirs, files in os.walk(directory):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    print(f"DEBUG: Found image file by searching: {file_path}")
                    return file_path
            
            print(f"DEBUG: Image file {filename} not found in directory {directory}")
            return None
            
        except Exception as e:
            print(f"⚠️ Error searching for image file: {e}")
            return None

    def debug_script_storage(self):
        """Debug function to check what scripts are available in storage"""
        try:
            print("DEBUG: ===== SCRIPT STORAGE DEBUG =====")
            
            # Check pending_scripts_for_export
            if hasattr(self.parent, 'pending_scripts_for_export'):
                print(f"DEBUG: pending_scripts_for_export has {len(self.parent.pending_scripts_for_export)} items")
                for i, script in enumerate(self.parent.pending_scripts_for_export):
                    print(f"DEBUG: pending_scripts_for_export[{i}]: {script}")
            else:
                print("DEBUG: No pending_scripts_for_export attribute found")
            
            # Check step_widgets
            if hasattr(self.parent, 'step_widgets'):
                print(f"DEBUG: step_widgets has {len(self.parent.step_widgets)} items")
                for step_key, step_widget in self.parent.step_widgets.items():
                    if 'upload_scripts_list' in step_widget:
                        print(f"DEBUG: step_widget {step_key} has {len(step_widget['upload_scripts_list'])} scripts")
                        for script in step_widget['upload_scripts_list']:
                            print(f"DEBUG: Script in {step_key}: {script}")
            else:
                print("DEBUG: No step_widgets attribute found")
            
            # Check global step scripts
            if hasattr(self.parent, '_global_step_scripts'):
                print(f"DEBUG: _global_step_scripts has {len(self.parent._global_step_scripts)} items")
                for step_key, scripts in self.parent._global_step_scripts.items():
                    print(f"DEBUG: Global step {step_key} has {len(scripts)} scripts")
                    for script in scripts:
                        print(f"DEBUG: Global script in {step_key}: {script}")
            else:
                print("DEBUG: No _global_step_scripts attribute found")
            
            print("DEBUG: ===== END SCRIPT STORAGE DEBUG =====")
            
        except Exception as e:
            print(f"⚠️ Error in debug_script_storage: {e}")
    
    def _find_script_file_in_directory(self, directory, filename):
        """
        Recursively search for a script file in a directory
        
        Args:
            directory: Directory to search in
            filename: Filename to search for
            
        Returns:
            str: Full path to the file if found, None otherwise
        """
        try:
            if not os.path.exists(directory):
                return None
            
            for root, dirs, files in os.walk(directory):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    print(f"DEBUG: Found script file by searching: {file_path}")
                    return file_path
            
            print(f"DEBUG: Script file {filename} not found in directory {directory}")
            return None
            
        except Exception as e:
            print(f"⚠️ Error searching for script file: {e}")
            return None
    
    def generate_script_py_content(self):
        """Generate content for script.py file"""
        script_content = '''#!/usr/bin/env python3
"""
Automated Test Script
Generated by Security Report Generator
"""

import os
import sys
import json
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_execution.log'),
        logging.StreamHandler()
    ]
)

class TestExecutor:
    """Test execution class for automated testing"""
    
    def __init__(self, config_file="questions_config.json"):
        """Initialize test executor with configuration"""
        self.config_file = config_file
        self.config = self.load_config()
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def execute_test_steps(self):
        """Execute all test steps from configuration"""
        self.logger.info("Starting test execution...")
        
        # Get execution steps from config
        execution_steps = self.config.get('execution_steps', [])
        
        for step in execution_steps:
            step_id = step.get('id', 'Unknown')
            step_name = step.get('name', 'Unknown Step')
            step_description = step.get('description', 'No description')
            
            self.logger.info(f"Executing step {step_id}: {step_name}")
            self.logger.info(f"Description: {step_description}")
            
            # Here you would implement the actual step execution logic
            # For now, we'll just log the step
            self.logger.info(f"Step {step_id} completed successfully")
            
        self.logger.info("Test execution completed")
    
    def run_questions_check(self):
        """Run through essential questions check"""
        self.logger.info("Running essential questions check...")
        
        questions = self.config.get('questions', [])
        
        for question in questions:
            question_id = question.get('id', 'Unknown')
            question_text = question.get('question', 'No question text')
            question_type = question.get('question_type', 'yes_no')
            is_critical = question.get('critical', False)
            
            self.logger.info(f"Question {question_id}: {question_text}")
            self.logger.info(f"Type: {question_type}, Critical: {is_critical}")
            
            # Here you would implement the actual question checking logic
            # For now, we'll just log the question
            
        self.logger.info("Essential questions check completed")

def main():
    """Main function"""
    print("Security Test Script")
    print("=" * 50)
    
    # Initialize test executor
    executor = TestExecutor()
    
    # Run essential questions check
    executor.run_questions_check()
    
    # Execute test steps
    executor.execute_test_steps()
    
    print("\\nTest execution completed successfully!")

if __name__ == "__main__":
    main()
'''
        return script_content
    
    def show_push_options_dialog(self):
        """Directly proceed with push without dialog"""
        try:
            # No dialog needed, directly proceed with push
            self.push_files()
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to push files: {str(e)}")

    def push_files(self):
        """Push files to backend via API - automatically detect and push existing folders"""
        try:
            # Get selected files or all files in current directory
            selected_items = self.files_table.selectedItems()
            print(f"DEBUG: push_files called, selected_items count: {len(selected_items)}")
            
            if not selected_items:
                QMessageBox.warning(self.parent, "Error", "Please select a folder to push.")
                return
            
            # Get testcase_id from parent application
            testcase_id = self.get_testcase_id()
            if not testcase_id:
                QMessageBox.warning(self.parent, "Error", "No testcase ID found. Please select a testcase from the Full Tree page first.")
                return
            
            # Find the selected folder
            selected_folder_path = None
            selected_folder_name = None
            
            for item in selected_items:
                file_data = item.data(Qt.ItemDataRole.UserRole)
                if file_data and file_data.get('isDir'):
                    folder_name = file_data.get('name', '')
                    # Use the correct tmp directory path relative to app root
                    app_root = self.get_app_root_dir()
                    tmp_dir = os.path.join(app_root, "tmp")
                    folder_path = os.path.join(tmp_dir, folder_name)
                    
                    if os.path.exists(folder_path):
                        selected_folder_path = folder_path
                        selected_folder_name = folder_name
                        break
            
            if not selected_folder_path:
                QMessageBox.warning(self.parent, "Error", "No valid folder selected.")
                return
            
            print(f"DEBUG: Selected folder: {selected_folder_path}")
            
            # Check which subfolders exist and push them
            success_count = 0
            error_messages = []
            pushed_folders = []
            
            # Check for report folder
            report_folder = os.path.join(selected_folder_path, 'report')
            if os.path.exists(report_folder):
                print(f"DEBUG: Found report folder, pushing doc files...")
                success = self.push_doc_files(selected_items, testcase_id)
                if success:
                    success_count += 1
                    pushed_folders.append("report")
                else:
                    error_messages.append("Failed to push Doc files")
            else:
                print(f"DEBUG: No report folder found")
            
            # Check for code folder
            code_folder = os.path.join(selected_folder_path, 'code')
            if os.path.exists(code_folder):
                print(f"DEBUG: Found code folder, pushing script files...")
                success = self.push_script_files(selected_items, testcase_id)
                if success:
                    success_count += 1
                    pushed_folders.append("code")
                else:
                    error_messages.append("Failed to push Script files")
            else:
                print(f"DEBUG: No code folder found")
            
            # Always push the entire selected folder as data
            print(f"DEBUG: Pushing entire folder as data...")
            success = self.push_data_files(selected_items, testcase_id)
            if success:
                success_count += 1
                pushed_folders.append("entire folder")
            else:
                error_messages.append("Failed to push Data files")
            
            # Show results
            if success_count > 0:
                # Move the pushed folder to tmp/file/pushed files
                self.move_folder_to_pushed_files(selected_folder_path, selected_folder_name)
                
                if len(error_messages) == 0:
                    QMessageBox.information(self.parent, "Success", 
                                          f"Successfully pushed {success_count} items to the backend!\n\nPushed: {', '.join(pushed_folders)}")
                else:
                    QMessageBox.warning(self.parent, "Partial Success", 
                                      f"Successfully pushed {success_count} items.\n\nPushed: {', '.join(pushed_folders)}\n\nErrors:\n" + "\n".join(error_messages))
            else:
                QMessageBox.critical(self.parent, "Error", 
                                   f"Failed to push any files.\n\nErrors:\n" + "\n".join(error_messages))
                    
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to push files: {str(e)}")
    
    def get_app_root_dir(self):
        """Get the application root directory dynamically"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # The app root is the parent directory of Report_Generator_Automation-main
            script_dir = os.path.expanduser("~/Report_Generator_Automation-main")
            if script_dir.endswith('Report_Generator_Automation-main'):
                app_root = os.path.dirname(script_dir)
            else:
                # Fallback: assume we're in the app root
                app_root = script_dir
            
            print(f"DEBUG: App root directory: {app_root}")
            return app_root
        except Exception as e:
            print(f"Error getting app root directory: {e}")
            # Fallback to current working directory
            return os.getcwd()
    
    def get_testcase_id(self):
        """Get the current testcase_id from 1.json or parent application"""
        try:
            print("DEBUG: get_testcase_id called")
            
            # Try to get testcase_id from parent application first
            if hasattr(self.parent, 'testcase_id') and self.parent.testcase_id:
                print(f"DEBUG: Using parent.testcase_id: {self.parent.testcase_id}")
                return self.parent.testcase_id
            elif hasattr(self.parent, 'current_testcase_id') and self.parent.current_testcase_id:
                print(f"DEBUG: Using parent.current_testcase_id: {self.parent.current_testcase_id}")
                return self.parent.current_testcase_id
            elif hasattr(self.parent, 'subtype_id_map') and self.parent.subtype_id_map:
                # Get the first testcase_id from the map
                testcase_id = next(iter(self.parent.subtype_id_map.values()), None)
                print(f"DEBUG: Using subtype_id_map testcase_id: {testcase_id}")
                if testcase_id:
                    return testcase_id
            
            print("DEBUG: No testcase_id found in parent, trying 1.json...")
            
            # Try to read from 1.json (primary source for testcase data)
            import json
            import os
            try:
                # Try multiple possible locations for 1.json
                possible_paths = [
                    os.path.expanduser('~/1.json'),  # Home directory (primary for .deb installation)
                    os.path.join(os.getcwd(), '1.json'),  # Explicit current directory
                    '1.json',  # Current directory (fallback)
                    os.path.join(os.path.dirname(__file__), '1.json'),  # Same directory as this script
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), '1.json'),  # Parent directory
                ]
                
                config_path = None
                for path in possible_paths:
                    print(f"DEBUG: Checking 1.json at: {os.path.abspath(path)}")
                    if os.path.exists(path):
                        config_path = path
                        print(f"DEBUG: Found 1.json at: {os.path.abspath(path)}")
                        break
                
                if not config_path:
                    print("DEBUG: 1.json not found in any expected location")
                    return None
                
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    print(f"DEBUG: 1.json content: {config}")
                    testcase_id = config.get('testcase_id')
                    print(f"DEBUG: Found testcase_id in 1.json: {testcase_id}")
                    if testcase_id:
                        print(f"DEBUG: Using 1.json testcase_id: {testcase_id}")
                        return testcase_id
                    else:
                        print("DEBUG: testcase_id is None or empty in 1.json")
            except Exception as json1_error:
                print(f"DEBUG: Error reading testcase_id from 1.json: {json1_error}")
                print(f"DEBUG: Error type: {type(json1_error)}")
            
            print("DEBUG: No testcase_id found anywhere")
            return None
        except Exception as e:
            print(f"Error getting testcase_id: {e}")
            return None
    
    def push_doc_files(self, selected_items, testcase_id):
        """Push document files to api/report/update/file"""
        try:
            print(f"DEBUG: push_doc_files called with {len(selected_items)} selected items")
            
            # Find doc files in the selected folder
            doc_files = []
            for item in selected_items:
                file_data = item.data(Qt.ItemDataRole.UserRole)
                log_debug(f"Processing item with data: {file_data}")
                
                if file_data and file_data.get('isDir'):  # Check for directory
                    folder_name = file_data.get('name', '')
                    log_debug(f"Found directory name: {folder_name}")
                    
                    # Construct full path relative to tmp directory
                    app_root = self.get_app_root_dir()
                    tmp_dir = os.path.join(app_root, "tmp")
                    folder_path = os.path.join(tmp_dir, folder_name)
                    log_debug(f"Full folder path: {folder_path}")
                    
                    # Look for doc files in the report folder
                    report_folder = os.path.join(folder_path, 'report')
                    log_debug(f"Looking for report folder: {report_folder}")
                    log_debug(f"Report folder exists: {os.path.exists(report_folder)}")
                    
                    if os.path.exists(report_folder):
                        report_files = os.listdir(report_folder)
                        log_debug(f"Files in report folder: {report_files}")
                        
                        for file_name in report_files:
                            if file_name.lower().endswith(('.doc', '.docx', '.pdf')):
                                doc_file_path = os.path.join(report_folder, file_name)
                                doc_files.append(doc_file_path)
                                log_debug(f"Found doc file: {doc_file_path}")
            
            log_debug(f"Total doc files found: {len(doc_files)}")
            if not doc_files:
                log_warning("No document files found in report folder")
                return False
            
            # Make API call for each doc file
            success_count = 0
            for doc_file in doc_files:
                log_debug(f"Attempting to push document file: {doc_file}")
                success = self.make_api_call(
                    endpoint="api/report/update/file",
                    testcase_id=testcase_id,
                    file_path=doc_file,
                    file_type="doc"
                )
                if success:
                    success_count += 1
                    log_info(f"Successfully pushed document file: {os.path.basename(doc_file)}")
                else:
                    log_error(f"Failed to push document file: {os.path.basename(doc_file)}")
            
            if success_count == len(doc_files):
                log_info(f"All {len(doc_files)} document files pushed successfully")
                return True
            elif success_count > 0:
                log_warning(f"Only {success_count} out of {len(doc_files)} document files pushed successfully")
                return False
            else:
                log_error("No document files were pushed successfully")
                return False
            
        except Exception as e:
            log_error(f"Error pushing doc files: {e}")
            return False
    
    def copy_question_config_to_code_folder(self, testcase_folder_path):
        """Copy question_config.json from configuration folder to code folder"""
        try:
            # Source: configuration/question_config.json
            config_folder = os.path.join(testcase_folder_path, 'configuration')
            source_file = os.path.join(config_folder, 'question_config.json')
            
            # Destination: code/question_config.json
            code_folder = os.path.join(testcase_folder_path, 'code')
            dest_file = os.path.join(code_folder, 'question_config.json')
            
            # Copy if source exists
            if os.path.exists(source_file):
                if not os.path.exists(code_folder):
                    os.makedirs(code_folder)
                shutil.copy2(source_file, dest_file)
                log_debug(f"Copied question_config.json to code folder")
                return True
            else:
                log_debug(f"question_config.json not found in configuration folder")
                return False
                
        except Exception as e:
            log_error(f"Error copying question_config.json: {e}")
            return False

    def push_script_files(self, selected_items, testcase_id):
        """Push script files to api/release/update/file as zip from tmp/{folder}/code/ and tmp/{folder}/raw_logs/"""
        try:
            log_debug(f"push_script_files called with {len(selected_items)} selected items")
            
            # Find the selected folder
            selected_folder = None
            for item in selected_items:
                file_data = item.data(Qt.ItemDataRole.UserRole)
                log_debug(f"Processing item with data: {file_data}")
                
                if file_data and file_data.get('isDir'):  # Check for directory
                    folder_name = file_data.get('name', '')
                    log_debug(f"Found directory name: {folder_name}")
                    
                    # Construct full path relative to tmp directory
                    app_root = self.get_app_root_dir()
                    tmp_dir = os.path.join(app_root, "tmp")
                    folder_path = os.path.join(tmp_dir, folder_name)
                    log_debug(f"Full folder path: {folder_path}")
                    log_debug(f"Folder exists: {os.path.exists(folder_path)}")
                    
                    if os.path.exists(folder_path):
                        selected_folder = folder_path
                        log_debug(f"Selected folder for script files: {selected_folder}")
                        break
            
            if not selected_folder:
                log_warning("No folder selected for script files")
                return False
            
            # Get files from tmp/{folder}/code/, tmp/{folder}/raw_logs/, and GENERAL/comman_files/ directories
            code_folder = os.path.join(selected_folder, "code")
            raw_logs_folder = os.path.join(selected_folder, "raw_logs")
            
            # Get GENERAL/comman_files directory
            script_dir = os.path.expanduser("~/GENERAL")
            general_common_files_dir = os.path.join(script_dir, "common_files")
            
            log_debug(f"Looking for code folder: {code_folder}")
            log_debug(f"Code folder exists: {os.path.exists(code_folder)}")
            log_debug(f"Looking for raw_logs folder: {raw_logs_folder}")
            log_debug(f"Raw logs folder exists: {os.path.exists(raw_logs_folder)}")
            log_debug(f"Looking for GENERAL/common_files: {general_common_files_dir}")
            log_debug(f"GENERAL/common_files exists: {os.path.exists(general_common_files_dir)}")
            
            # Create zip file with proper structure
            import tempfile
            import zipfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                zip_path = temp_zip.name
            
            log_debug(f"Creating zip file: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Only add files from the code folder (not the entire folder structure)
                if os.path.exists(code_folder):
                    log_debug(f"Adding files from code folder: {code_folder}")
                    for root, dirs, files in os.walk(code_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Use relative path from the code folder root
                            arcname = os.path.relpath(file_path, code_folder)
                            zipf.write(file_path, arcname)
                            log_debug(f"Added code file to zip: {arcname}")
                
                # Add common files from ~/GENERAL/common_files/ to the zip root
                if os.path.exists(general_common_files_dir):
                    log_debug(f"Adding common files from: {general_common_files_dir}")
                    for root, dirs, files in os.walk(general_common_files_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Add to zip root (same level as code files)
                            arcname = file
                            zipf.write(file_path, arcname)
                            log_debug(f"Added common file to zip: {arcname}")
                
                # Also copy question_config.json to zip root if it exists
                question_config_source = os.path.join(selected_folder, "configuration", "question_config.json")
                if os.path.exists(question_config_source):
                    arcname = "question_config.json"
                    zipf.write(question_config_source, arcname)
                    log_debug(f"Added question_config.json to zip: {arcname}")
            
            log_debug(f"Zip file created successfully")
            
            # Make API call with zip file
            success = self.make_api_call(
                endpoint="api/release/update/file",
                testcase_id=testcase_id,
                file_path=zip_path,
                file_type="zip"
            )
            
            # Clean up temporary zip file
            try:
                os.unlink(zip_path)
                log_debug(f"Temporary zip file cleaned up")
            except:
                pass
            
            return success
            
        except Exception as e:
            log_error(f"Error pushing script files: {e}")
            return False

    
    def push_data_files(self, selected_items, testcase_id):
        """Push selected folder as zip to /configuration/update"""
        try:
            log_debug(f"push_data_files called with {len(selected_items)} selected items")
            
            # Find the selected folder
            selected_folder = None
            for item in selected_items:
                file_data = item.data(Qt.ItemDataRole.UserRole)
                log_debug(f"Processing item with data: {file_data}")
                
                if file_data and file_data.get('isDir'):  # Check for directory
                    folder_name = file_data.get('name', '')
                    print(f"DEBUG: Found directory name: {folder_name}")
                    
                    # Construct full path relative to tmp directory
                    app_root = self.get_app_root_dir()
                    tmp_dir = os.path.join(app_root, "tmp")
                    folder_path = os.path.join(tmp_dir, folder_name)
                    log_debug(f"Full folder path: {folder_path}")
                    log_debug(f"Folder exists: {os.path.exists(folder_path)}")
                    
                    if os.path.exists(folder_path):
                        selected_folder = folder_path
                        log_debug(f"Selected folder for zipping: {selected_folder}")
                        break
            
            if not selected_folder:
                log_warning("No folder selected for zipping")
                return False
            
            # Create zip file from the selected folder (everything inside tmp/{folder})
            import tempfile
            import zipfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                zip_path = temp_zip.name
            
            log_debug(f"Zip file created successfully")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(selected_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Use relative path from the selected folder root
                        arcname = os.path.relpath(file_path, selected_folder)
                        zipf.write(file_path, arcname)
                        print(f"DEBUG: Added to zip: {arcname}")
            
            print(f"DEBUG: Zip file created successfully")
            
            # Make API call with zip file
            success = self.make_api_call(
                endpoint="api/configuration/update",
                testcase_id=testcase_id,
                file_path=zip_path,
                file_type="config_file"
            )
            
            # Clean up temporary zip file
            try:
                os.unlink(zip_path)
                log_debug(f"Temporary zip file cleaned up")
            except:
                pass
            
            return success
            
        except Exception as e:
            log_error(f"Error pushing data files: {e}")
            return False
    
    def make_api_call(self, endpoint, testcase_id, file_path, file_type):
        """Make API call to the specified endpoint"""
        try:
            import requests
            
            # Get authorization token
            token = self.get_auth_token()
            if not token:
                log_error("No authorization token found")
                return False
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Prepare data
            data = {
                "testcase_id": testcase_id
            }
            
            # Prepare files
            files = {}
            if file_type == "doc":
                files["file"] = open(file_path, 'rb')
            elif file_type == "zip":
                files["file"] = open(file_path, 'rb')
            elif file_type == "config_file":
                files["config_file"] = open(file_path, 'rb')
            
            # Make the API call
            base_url = self.get_base_url()
            # Remove trailing slash from base_url if it exists
            if base_url.endswith('/'):
                base_url = base_url.rstrip('/')
            url = f"{base_url}/{endpoint}"
            
            log_debug(f"Base URL from config: {base_url}")
            log_debug(f"Making API call to: {url}")
            log_debug(f"Testcase ID: {testcase_id}")
            log_debug(f"File: {file_path}")
            log_debug(f"File type: {file_type}")
            
            # Check if file exists before making API call
            if not os.path.exists(file_path):
                log_error(f"File does not exist: {file_path}")
                return False
            
            # Get file size for logging
            file_size = os.path.getsize(file_path)
            log_debug(f"File size: {file_size} bytes")
            
            response = requests.put(url, headers=headers, data=data, files=files)
            
            # Close file handles
            for file_handle in files.values():
                file_handle.close()
            
            log_debug(f"API response status: {response.status_code}")
            log_debug(f"API response text: {response.text}")
            
            
            if response.status_code in [200, 201]:  # Accept both 200 OK and 201 Created
                log_info(f"Successfully pushed {file_type} file (status: {response.status_code})")
                return True
            elif response.status_code in [405, 501]:  # Method not allowed or not implemented
                log_warning(f"PUT method not supported (status: {response.status_code}), trying POST...")
                
                # Reopen files for POST request
                files = {}
                if file_type == "doc":
                    files["file"] = open(file_path, 'rb')
                elif file_type == "zip":
                    files["file"] = open(file_path, 'rb')
                elif file_type == "config_file":
                    files["config_file"] = open(file_path, 'rb')
                
                # Try POST method
                response = requests.post(url, headers=headers, data=data, files=files)
                
                # Close file handles again
                for file_handle in files.values():
                    file_handle.close()
                
                log_debug(f"POST API response status: {response.status_code}")
                log_debug(f"POST API response text: {response.text}")
                
                if response.status_code in [200, 201]:
                    log_info(f"Successfully pushed {file_type} file with POST (status: {response.status_code})")
                    return True
                else:
                    log_error(f"POST API call also failed with status {response.status_code}: {response.text}")
                    return False
            else:
                log_error(f"API call failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            log_error(f"Error making API call: {e}")
            return False
    
    def get_auth_token(self):
        """Get authorization token from 1.json or parent application"""
        try:
            log_debug("get_auth_token called")
            
            # Try to get token from parent application first
            if hasattr(self.parent, 'token') and self.parent.token:
                log_debug(f"Using parent token: {self.parent.token[:20]}...")
                return self.parent.token
            else:
                log_debug("No parent token")
            
            log_debug("No token found in parent, trying 1.json...")
            
            # Try to read from 1.json (primary source for testcase data)
            import json
            import os
            try:
                # Try multiple possible locations for 1.json
                possible_paths = [
                    os.path.expanduser('~/1.json'),  # Home directory (primary for .deb installation)
                    os.path.join(os.getcwd(), '1.json'),  # Explicit current directory
                    '1.json',  # Current directory (fallback)
                    os.path.join(os.path.dirname(__file__), '1.json'),  # Same directory as this script
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), '1.json'),  # Parent directory
                ]
                
                config_path = None
                for path in possible_paths:
                    log_debug(f"Checking 1.json for token at: {os.path.abspath(path)}")
                    if os.path.exists(path):
                        config_path = path
                        log_debug(f"Found 1.json at: {os.path.abspath(path)}")
                        break
                
                if not config_path:
                    log_warning("1.json not found in any expected location for token")
                    return None
                
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    log_debug(f"1.json content: {config}")
                    token = config.get('token')
                    log_debug(f"Found token in 1.json: {token[:20] if token else 'None'}...")
                    if token:
                        log_debug(f"Using 1.json token: {token[:20]}...")
                        return token
                    else:
                        log_warning("token is None or empty in 1.json")
            except Exception as json1_error:
                log_error(f"Error reading token from 1.json: {json1_error}")
                log_error(f"Error type: {type(json1_error)}")
            
            # Try to read from client.conf.json as fallback (for basic server info)
            try:
                with open('client.conf.json', 'r') as f:
                    config = json.load(f)
                    token = config.get('token')
                    if token:
                        log_debug(f"Using client.conf.json token: {token[:20]}...")
                        return token
            except Exception as config_error:
                log_error(f"Error reading token from client.conf.json: {config_error}")
            
            log_warning("No token found anywhere")
            return None
        except Exception as e:
            log_error(f"Error getting auth token: {e}")
            return None
    
    def get_base_url(self):
        """Get base URL from 1.json or configuration"""
        try:
            print("DEBUG: get_base_url called")
            
            # Try to read from 1.json first (primary source for testcase data)
            import json
            import os
            try:
                # Try multiple possible locations for 1.json
                possible_paths = [
                    os.path.expanduser('~/1.json'),  # Home directory (primary for .deb installation)
                    os.path.join(os.getcwd(), '1.json'),  # Explicit current directory
                    '1.json',  # Current directory (fallback)
                    os.path.join(os.path.dirname(__file__), '1.json'),  # Same directory as this script
                    os.path.join(os.path.dirname(os.path.dirname(__file__)), '1.json'),  # Parent directory
                ]
                
                config_path = None
                for path in possible_paths:
                    print(f"DEBUG: Checking 1.json for base_url at: {os.path.abspath(path)}")
                    if os.path.exists(path):
                        config_path = path
                        print(f"DEBUG: Found 1.json at: {os.path.abspath(path)}")
                        break
                
                if config_path:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        base_url = config.get('base_url')
                        if base_url:
                            print(f"DEBUG: Using 1.json base_url: {base_url}")
                            return base_url
                        else:
                            print("DEBUG: No base_url found in 1.json")
                else:
                    print("DEBUG: 1.json not found in any expected location for base_url")
            except Exception as json1_error:
                print(f"DEBUG: Error reading 1.json: {json1_error}")
            
            # Try to read from client.conf.json as fallback
            try:
                with open('client.conf.json', 'r') as f:
                    config = json.load(f)
                    base_url = config.get('server_url')
                    if base_url:
                        print(f"DEBUG: Using client.conf.json server_url: {base_url}")
                        return base_url
                    else:
                        print("DEBUG: No server_url found in client.conf.json")
            except Exception as config_error:
                print(f"DEBUG: Error reading client.conf.json: {config_error}")
            
            # Try to get base URL from parent application as fallback
            if hasattr(self.parent, 'base_url') and self.parent.base_url:
                print(f"DEBUG: Using parent base_url: {self.parent.base_url}")
                return self.parent.base_url
            
            print("DEBUG: No base_url found in any source")
            return None
        except Exception as e:
            print(f"Error getting base URL: {e}")
            return None
    
    def move_folder_to_pushed_files(self, source_folder_path, folder_name):
        """Move the pushed folder to tmp/file/pushed files directory"""
        try:
            # Create the pushed files directory structure
            app_root = self.get_app_root_dir()
            pushed_files_dir = os.path.join(app_root, "tmp", "file", "pushed files")
            os.makedirs(pushed_files_dir, exist_ok=True)
            
            # Create destination path with timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_folder_name = f"{folder_name}_{timestamp}"
            dest_folder_path = os.path.join(pushed_files_dir, dest_folder_name)
            
            # Move the folder
            shutil.move(source_folder_path, dest_folder_path)
            
            print(f"DEBUG: Moved folder from {source_folder_path} to {dest_folder_path}")
            
            # Refresh the file list to show the folder is gone
            self.refresh_files()
            
        except Exception as e:
            print(f"Error moving folder to pushed files: {e}")
    
    def pull_files(self):
        """Pull files from backend via API"""
        try:
            # TODO: Implement API call to backend
            # For now, just show success message
            QMessageBox.information(self.parent, "Success", 
                                  "Files pulled successfully!\n\nNote: Backend API integration will be implemented later.")
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Error", f"Failed to pull files: {str(e)}")


class ScriptAutomationUploadDialog(QDialog):
    """Dialog for uploading script automation files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.uploaded_zip_path = None
        self.last_uploaded_zip = self.get_last_uploaded_zip()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Script Automation Files Upload")
        self.setModal(True)
        self.resize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton#browse_btn {
                background-color: #2196F3;
            }
            QPushButton#browse_btn:hover {
                background-color: #1976D2;
            }
            QPushButton#cancel_btn {
                background-color: #f44336;
            }
            QPushButton#cancel_btn:hover {
                background-color: #da190b;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                color: #ffffff;
                font-size: 12px;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 14px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 2px solid #4CAF50;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3c3c3c;
                border: 2px solid #555;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("📁 Script Automation Files Upload")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Upload a ZIP file containing your script automation files. The files will be automatically organized into the code folder.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(desc_label)
        
        # Last uploaded file checkbox (if exists)
        if self.last_uploaded_zip:
            last_upload_layout = QHBoxLayout()
            
            self.use_last_zip_checkbox = QCheckBox(f"📎 Use last uploaded file: {os.path.basename(self.last_uploaded_zip)}")
            self.use_last_zip_checkbox.setChecked(True)
            self.use_last_zip_checkbox.stateChanged.connect(self.on_use_last_zip_changed)
            last_upload_layout.addWidget(self.use_last_zip_checkbox)
            
            # Remove button for last uploaded file
            self.remove_last_zip_btn = QPushButton("Remove")
            self.remove_last_zip_btn.setObjectName("remove_btn")
            self.remove_last_zip_btn.setFixedSize(60, 25)
            self.remove_last_zip_btn.setStyleSheet("""
                QPushButton#remove_btn {
                    background-color: #ff6b6b;
                    color: #ffffff;
                    border: none;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton#remove_btn:hover {
                    background-color: #ff5252;
                }
                QPushButton#remove_btn:pressed {
                    background-color: #e53935;
                }
            """)
            self.remove_last_zip_btn.clicked.connect(self.remove_last_uploaded_zip)
            last_upload_layout.addWidget(self.remove_last_zip_btn)
            
            last_upload_layout.addStretch()
            layout.addLayout(last_upload_layout)
        
        # File selection section
        file_section_label = QLabel("Select ZIP File:")
        file_section_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(file_section_label)
        
        # File path input and browse button
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("No file selected...")
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setObjectName("browse_btn")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)
        
        layout.addLayout(file_layout)
        
        # File info
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.file_info_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.confirm_btn = QPushButton("Confirm Push")
        self.confirm_btn.clicked.connect(self.confirm_upload)
        self.confirm_btn.setEnabled(False)
        button_layout.addWidget(self.confirm_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initialize with last uploaded file if available
        if self.last_uploaded_zip and hasattr(self, 'use_last_zip_checkbox') and self.use_last_zip_checkbox.isChecked():
            self.file_path_edit.setText(self.last_uploaded_zip)
            self.update_file_info(self.last_uploaded_zip)
            self.confirm_btn.setEnabled(True)
    
    def get_last_uploaded_zip(self):
        """Get the path of the last uploaded ZIP file"""
        try:
            # Check for a config file that stores the last uploaded ZIP path
            config_file = os.path.join(os.getcwd(), "last_uploaded_zip.json")
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    zip_path = config.get('last_zip_path')
                    if zip_path and os.path.exists(zip_path):
                        return zip_path
        except Exception as e:
            print(f"Error reading last uploaded ZIP: {e}")
        return None
    
    def save_last_uploaded_zip(self, zip_path):
        """Save the path of the uploaded ZIP file"""
        try:
            config_file = os.path.join(os.getcwd(), "last_uploaded_zip.json")
            import json
            config = {'last_zip_path': zip_path}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving last uploaded ZIP: {e}")
    
    def remove_last_uploaded_zip(self):
        """Remove the last uploaded ZIP file from memory"""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Confirm Removal", 
                f"Are you sure you want to remove the last uploaded ZIP file from memory?\n\nFile: {os.path.basename(self.last_uploaded_zip)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Remove the config file
            config_file = os.path.join(os.getcwd(), "last_uploaded_zip.json")
            if os.path.exists(config_file):
                os.remove(config_file)
            
            # Clear the current state
            self.last_uploaded_zip = None
            
            # Hide the checkbox and remove button instead of deleting them
            if hasattr(self, 'use_last_zip_checkbox') and self.use_last_zip_checkbox is not None:
                self.use_last_zip_checkbox.setVisible(False)
                self.use_last_zip_checkbox = None
            
            if hasattr(self, 'remove_last_zip_btn') and self.remove_last_zip_btn is not None:
                self.remove_last_zip_btn.setVisible(False)
                self.remove_last_zip_btn = None
            
            # Clear the file path and info
            self.file_path_edit.clear()
            self.file_info_label.clear()
            self.confirm_btn.setEnabled(False)
            
            # Show success message
            QMessageBox.information(self, "Success", "Last uploaded ZIP file has been removed from memory.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove last uploaded ZIP: {str(e)}")
    
    
    def on_use_last_zip_changed(self, state):
        """Handle checkbox state change for using last uploaded ZIP"""
        if state == Qt.CheckState.Checked.value and self.last_uploaded_zip:
            self.file_path_edit.setText(self.last_uploaded_zip)
            self.update_file_info(self.last_uploaded_zip)
            self.confirm_btn.setEnabled(True)
        else:
            self.file_path_edit.clear()
            self.file_info_label.clear()
            self.confirm_btn.setEnabled(False)
    
    def browse_file(self):
        """Browse for ZIP file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Script Automation ZIP File",
            "",
            "ZIP Files (*.zip);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.update_file_info(file_path)
            self.confirm_btn.setEnabled(True)
            
            # Uncheck the last uploaded checkbox if user browses for a new file
            if hasattr(self, 'use_last_zip_checkbox') and self.use_last_zip_checkbox is not None:
                self.use_last_zip_checkbox.setChecked(False)
    
    def update_file_info(self, file_path):
        """Update file information display"""
        try:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                self.file_info_label.setText(f"File: {os.path.basename(file_path)} | Size: {size_mb:.2f} MB")
            else:
                self.file_info_label.setText("File not found")
        except Exception as e:
            self.file_info_label.setText(f"Error reading file: {e}")
    
    def confirm_upload(self):
        """Confirm and process the ZIP upload"""
        try:
            zip_path = self.file_path_edit.text().strip()
            if not zip_path or not os.path.exists(zip_path):
                QMessageBox.warning(self, "Error", "Please select a valid ZIP file.")
                return
            
            # Validate ZIP file
            if not zip_path.lower().endswith('.zip'):
                QMessageBox.warning(self, "Error", "Please select a ZIP file (.zip extension).")
                return
            
            # Show processing message
            processing_msg = QMessageBox(self)
            processing_msg.setWindowTitle("Processing ZIP File")
            processing_msg.setText("Extracting and organizing files...")
            processing_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
            processing_msg.show()
            processing_msg.repaint()
            
            # Process the ZIP file
            success = self.process_zip_upload(zip_path)
            processing_msg.close()
            
            if success:
                # Save as last uploaded ZIP
                self.save_last_uploaded_zip(zip_path)
                
                # Get extraction summary if available
                summary = getattr(self, 'extraction_summary', {})
                total_files = summary.get('total_files', 0)
                copied_files = summary.get('copied_files', 0)
                skipped_files = summary.get('skipped_files', 0)
                
                success_msg = f"Script automation files uploaded and organized successfully!\n\n"
                success_msg += f"Files extracted to: tmp/sdfcvokjn/code/\n"
                success_msg += f"ZIP file: {os.path.basename(zip_path)}\n"
                success_msg += f"Files processed: {copied_files} copied"
                if skipped_files > 0:
                    success_msg += f", {skipped_files} skipped (hidden/system files)"
                
                QMessageBox.information(self, "Success", success_msg)
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    "Failed to process the ZIP file. Please check:\n"
                    "• File is a valid ZIP archive\n"
                    "• ZIP file is not corrupted\n"
                    "• You have write permissions to the tmp folder"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload files: {str(e)}")
    
    def process_zip_upload(self, zip_path):
        """Process the uploaded ZIP file and organize files into tmp/sdfcvokjn/code/ structure"""
        try:
            import zipfile
            import tempfile
            import shutil
            
            print(f"Processing ZIP file: {zip_path}")
            
            # Validate ZIP file first
            try:
                with zipfile.ZipFile(zip_path, 'r') as test_zip:
                    # Test if ZIP is readable
                    test_zip.testzip()
                    file_count = len(test_zip.namelist())
                    print(f"ZIP file contains {file_count} files/entries")
            except zipfile.BadZipFile:
                print("Error: Invalid or corrupted ZIP file")
                return False
            except Exception as e:
                print(f"Error validating ZIP file: {e}")
                return False
            
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    print(f"Extracted ZIP contents to temporary directory: {temp_dir}")
                
                # Create the target folder structure: tmp/sdfcvokjn/code/
                app_root = self.get_app_root_dir()
                tmp_dir = os.path.join(app_root, "tmp")
                os.makedirs(tmp_dir, exist_ok=True)
                
                # Use consistent folder name 'sdfcvokjn' as shown in the image
                target_folder = os.path.join(tmp_dir, "sdfcvokjn")
                os.makedirs(target_folder, exist_ok=True)
                
                # Create the code folder
                code_folder = os.path.join(target_folder, "code")
                os.makedirs(code_folder, exist_ok=True)
                
                # Create Input folder in home directory
                input_folder_path = os.path.expanduser("~/Input")
                try:
                    os.makedirs(input_folder_path, exist_ok=True)
                    print(f"DEBUG: Created/verified Input folder: {input_folder_path}")
                except Exception as e:
                    print(f"ERROR: Could not create Input folder: {e}")
                
                print(f"Target code folder: {code_folder}")
                
                # Get all files from the extracted ZIP
                extracted_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # Calculate relative path from temp_dir
                        rel_path = os.path.relpath(src_path, temp_dir)
                        extracted_files.append((src_path, rel_path))
                
                print(f"Found {len(extracted_files)} files in ZIP")
                
                # Check if all files are in a single top-level folder
                top_level_folders = set()
                for src_path, rel_path in extracted_files:
                    if '/' in rel_path or '\\' in rel_path:
                        # Get the first part of the path (top-level folder)
                        first_part = rel_path.split('/')[0] if '/' in rel_path else rel_path.split('\\')[0]
                        top_level_folders.add(first_part)
                
                # If there's only one top-level folder, we'll skip it and extract files directly
                skip_top_folder = len(top_level_folders) == 1 and len(extracted_files) > 0
                if skip_top_folder:
                    top_folder_name = list(top_level_folders)[0]
                    print(f"Detected single top-level folder '{top_folder_name}', extracting files directly to code folder")
                
                # Copy all extracted files to the code folder
                copied_count = 0
                skipped_count = 0
                for src_path, rel_path in extracted_files:
                    # Skip hidden files and system files
                    if rel_path.startswith('.') or rel_path.startswith('__pycache__'):
                        print(f"Skipped hidden/system file: {rel_path}")
                        skipped_count += 1
                        continue
                    
                    # If we detected a single top-level folder, skip it in the destination path
                    if skip_top_folder:
                        # Remove the top-level folder from the path
                        if '/' in rel_path:
                            path_parts = rel_path.split('/')
                            if path_parts[0] == top_folder_name:
                                rel_path = '/'.join(path_parts[1:])
                        elif '\\' in rel_path:
                            path_parts = rel_path.split('\\')
                            if path_parts[0] == top_folder_name:
                                rel_path = '\\'.join(path_parts[1:])
                    
                    # If rel_path is empty after removing top folder, use just the filename
                    if not rel_path:
                        rel_path = os.path.basename(src_path)
                    
                    dst_path = os.path.join(code_folder, rel_path)
                    
                    # Create directory if it doesn't exist
                    dst_dir = os.path.dirname(dst_path)
                    os.makedirs(dst_dir, exist_ok=True)
                    
                    try:
                        # Copy file
                        shutil.copy2(src_path, dst_path)
                        print(f"Copied: {rel_path} -> {dst_path}")
                        copied_count += 1
                    except Exception as e:
                        print(f"Error copying {rel_path}: {e}")
                        skipped_count += 1
                
                print(f"Successfully copied {copied_count} files to: {code_folder}")
                if skipped_count > 0:
                    print(f"Skipped {skipped_count} files (hidden/system files)")
                
                # Also create configuration folder if it doesn't exist
                config_folder = os.path.join(target_folder, "configuration")
                os.makedirs(config_folder, exist_ok=True)
                print(f"Created configuration folder: {config_folder}")
                
                # Create raw_logs folder if it doesn't exist
                raw_logs_folder = os.path.join(target_folder, "raw_logs")
                os.makedirs(raw_logs_folder, exist_ok=True)
                print(f"Created raw_logs folder: {raw_logs_folder}")
                
                # Create report folder if it doesn't exist
                report_folder = os.path.join(target_folder, "report")
                os.makedirs(report_folder, exist_ok=True)
                print(f"Created report folder: {report_folder}")
                
                # Store extraction summary for user feedback
                self.extraction_summary = {
                    'total_files': len(extracted_files),
                    'copied_files': copied_count,
                    'skipped_files': skipped_count,
                    'code_folder': code_folder
                }
                
                # Refresh the file list in the parent if it has the method
                if hasattr(self.parent, 'refresh_files'):
                    self.parent.refresh_files()
                
                return True
                
        except Exception as e:
            print(f"Error processing ZIP upload: {e}")
            import traceback
            traceback.print_exc()
            return False


class PushOptionsDialog(QDialog):
    """Dialog for selecting push options"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_options = []
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Select Push Options")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Select which files to push:")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Checkboxes
        self.doc_checkbox = QCheckBox("Doc - Push document files from report folder")
        self.doc_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                padding: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        layout.addWidget(self.doc_checkbox)
        
        self.script_checkbox = QCheckBox("📜 Script - Push code folder as zip file")
        self.script_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                padding: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        layout.addWidget(self.script_checkbox)
        
        self.data_checkbox = QCheckBox("📊 Data Upload - Push selected folder as zip")
        self.data_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                padding: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        layout.addWidget(self.data_checkbox)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        push_btn = QPushButton("Push Files")
        push_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        push_btn.clicked.connect(self.accept)
        button_layout.addWidget(push_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def get_sections_1_7_data(self):
        """Get sections 1-7 data from parent application"""
        try:
            print(f"DEBUG: get_sections_1_7_data called")
            
            # Use the proper sections_1_7_manager to get data
            if hasattr(self.parent, 'sections_1_7_manager'):
                print(f"DEBUG: Using sections_1_7_manager to get data")
                return self.parent.sections_1_7_manager.get_sections_1_7_data()
            else:
                print(f"DEBUG: sections_1_7_manager not found, falling back to manual collection")
                sections_data = {}
                
                # Get Section 1 data (ITSAR Section No & Name)
                if hasattr(self.parent, 'section_1_heading_edit') and hasattr(self.parent, 'section_1_edit'):
                    section_1_data = {
                        'heading': self.parent.section_1_heading_edit.text().strip() if self.parent.section_1_heading_edit else "ITSAR Section No & Name",
                        'text': self.parent.section_1_edit.text().strip() if self.parent.section_1_edit else "",
                        'images': [],
                        'scripts': []
                    }
                
                    # Get images from Section 1
                    if hasattr(self.parent, 'section_1_images_list'):
                        for image_info in self.parent.section_1_images_list:
                            if image_info['path'] and os.path.exists(image_info['path']):
                                # Get relative path from project root for original_path
                                project_root = os.getcwd()
                                try:
                                    original_path = os.path.relpath(image_info['path'], project_root)
                                except ValueError:
                                    # If paths are on different drives, use the full path
                                    original_path = image_info['path']
                                
                                section_1_data['images'].append({
                                    'path': image_info['path'],
                                    'filename': image_info['filename'],
                                    'original_filename': image_info.get('original_filename', image_info['filename']),
                                    'description': image_info.get('description', ''),
                                    'original_path': original_path
                                })
                    
                    # Get scripts from Section 1
                    if hasattr(self.parent, 'section_1_scripts_list'):
                        for script_info in self.parent.section_1_scripts_list:
                            if script_info['path'] and os.path.exists(script_info['path']):
                                # Ensure we have the full absolute path
                                full_path = os.path.abspath(script_info['path'])
                                print(f"DEBUG: Section 1 script path: {script_info['path']} -> {full_path}")
                                
                                # Get relative path from project root for original_path
                                project_root = os.getcwd()
                                try:
                                    original_path = os.path.relpath(script_info['path'], project_root)
                                except ValueError:
                                    # If paths are on different drives, use the full path
                                    original_path = script_info['path']
                                
                                section_1_data['scripts'].append({
                                    'path': full_path,  # Use full absolute path
                                    'filename': script_info['filename'],
                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                    'description': script_info.get('description', ''),
                                    'is_pasted': script_info.get('is_pasted', False),
                                    'original_path': original_path,
                                    'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                                })
                    
                    sections_data['section_1'] = section_1_data
            
            # Get Section 2 data (Security Requirement No & Name)
            if hasattr(self.parent, 'section_2_heading_edit') and hasattr(self.parent, 'section_2_edit'):
                section_2_data = {
                    'heading': self.parent.section_2_heading_edit.text().strip() if self.parent.section_2_heading_edit else "Security Requirement No & Name",
                    'text': self.parent.section_2_edit.text().strip() if self.parent.section_2_edit else "",
                    'images': [],
                    'scripts': []
                }
                
                # Get images from Section 2
                if hasattr(self.parent, 'section_2_images_list'):
                    for image_info in self.parent.section_2_images_list:
                        if image_info['path'] and os.path.exists(image_info['path']):
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(image_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = image_info['path']
                            
                            section_2_data['images'].append({
                                'path': image_info['path'],
                                'filename': image_info['filename'],
                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                'description': image_info.get('description', ''),
                                'original_path': original_path
                            })
                
                # Get scripts from Section 2
                if hasattr(self.parent, 'section_2_scripts_list'):
                    for script_info in self.parent.section_2_scripts_list:
                        if script_info['path'] and os.path.exists(script_info['path']):
                            # Ensure we have the full absolute path
                            full_path = os.path.abspath(script_info['path'])
                            print(f"DEBUG: Section 2 script path: {script_info['path']} -> {full_path}")
                            
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(script_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = script_info['path']
                            
                            section_2_data['scripts'].append({
                                'path': full_path,  # Use full absolute path
                                'filename': script_info['filename'],
                                'original_filename': script_info.get('original_filename', script_info['filename']),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False),
                                'original_path': original_path,
                                'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                            })
                
                sections_data['section_2'] = section_2_data
            
            # Get Section 3 data (Requirement Description)
            if hasattr(self.parent, 'section_3_heading_edit') and hasattr(self.parent, 'section_3_edit'):
                section_3_data = {
                    'heading': self.parent.section_3_heading_edit.text().strip() if self.parent.section_3_heading_edit else "Requirement Description",
                    'text': self.parent.section_3_edit.toPlainText().strip() if self.parent.section_3_edit else "",
                    'images': [],
                    'scripts': []
                }
                
                # Get images from Section 3
                if hasattr(self.parent, 'section_3_images_list'):
                    for image_info in self.parent.section_3_images_list:
                        if image_info['path'] and os.path.exists(image_info['path']):
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(image_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = image_info['path']
                            
                            section_3_data['images'].append({
                                'path': image_info['path'],
                                'filename': image_info['filename'],
                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                'description': image_info.get('description', ''),
                                'original_path': original_path
                            })
                
                # Get scripts from Section 3
                if hasattr(self.parent, 'section_3_scripts_list'):
                    for script_info in self.parent.section_3_scripts_list:
                        if script_info['path'] and os.path.exists(script_info['path']):
                            # Ensure we have the full absolute path
                            full_path = os.path.abspath(script_info['path'])
                            print(f"DEBUG: Section 3 script path: {script_info['path']} -> {full_path}")
                            
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(script_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = script_info['path']
                            
                            section_3_data['scripts'].append({
                                'path': full_path,  # Use full absolute path
                                'filename': script_info['filename'],
                                'original_filename': script_info.get('original_filename', script_info['filename']),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False),
                                'original_path': original_path,
                                'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                            })
                
                sections_data['section_3'] = section_3_data
            
            # Get Section 6 data (Preconditions)
            if hasattr(self.parent, 'section_6_heading_edit') and hasattr(self.parent, 'section_6_edit'):
                section_6_data = {
                    'heading': self.parent.section_6_heading_edit.text().strip() if self.parent.section_6_heading_edit else "Preconditions",
                    'text': self.parent.section_6_edit.toPlainText().strip() if self.parent.section_6_edit else "",
                    'images': [],
                    'scripts': []
                }
                
                # Get images from Section 6
                if hasattr(self.parent, 'section_6_images_list'):
                    for image_info in self.parent.section_6_images_list:
                        if image_info['path'] and os.path.exists(image_info['path']):
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(image_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = image_info['path']
                            
                            section_6_data['images'].append({
                                'path': image_info['path'],
                                'filename': image_info['filename'],
                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                'description': image_info.get('description', ''),
                                'original_path': original_path
                            })
                
                # Get scripts from Section 6
                if hasattr(self.parent, 'section_6_scripts_list'):
                    for script_info in self.parent.section_6_scripts_list:
                        if script_info['path'] and os.path.exists(script_info['path']):
                            # Ensure we have the full absolute path
                            full_path = os.path.abspath(script_info['path'])
                            print(f"DEBUG: Section 6 script path: {script_info['path']} -> {full_path}")
                            
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(script_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = script_info['path']
                            
                            section_6_data['scripts'].append({
                                'path': full_path,  # Use full absolute path
                                'filename': script_info['filename'],
                                'original_filename': script_info.get('original_filename', script_info['filename']),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False),
                                'original_path': original_path,
                                'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                            })
                
                sections_data['section_6'] = section_6_data
            
            # Get Section 7 data (Test Objective)
            if hasattr(self.parent, 'section_7_heading_edit') and hasattr(self.parent, 'section_7_edit'):
                section_7_data = {
                    'heading': self.parent.section_7_heading_edit.text().strip() if self.parent.section_7_heading_edit else "Test Objective",
                    'text': self.parent.section_7_edit.toPlainText().strip() if self.parent.section_7_edit else "",
                    'images': [],
                    'scripts': []
                }
                
                # Get images from Section 7
                if hasattr(self.parent, 'section_7_images_list'):
                    for image_info in self.parent.section_7_images_list:
                        if image_info['path'] and os.path.exists(image_info['path']):
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(image_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = image_info['path']
                            
                            section_7_data['images'].append({
                                'path': image_info['path'],
                                'filename': image_info['filename'],
                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                'description': image_info.get('description', ''),
                                'original_path': original_path
                            })
                
                # Get scripts from Section 7
                if hasattr(self.parent, 'section_7_scripts_list'):
                    for script_info in self.parent.section_7_scripts_list:
                        if script_info['path'] and os.path.exists(script_info['path']):
                            # Ensure we have the full absolute path
                            full_path = os.path.abspath(script_info['path'])
                            print(f"DEBUG: Section 7 script path: {script_info['path']} -> {full_path}")
                            
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(script_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = script_info['path']
                            
                            section_7_data['scripts'].append({
                                'path': full_path,  # Use full absolute path
                                'filename': script_info['filename'],
                                'original_filename': script_info.get('original_filename', script_info['filename']),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False),
                                'original_path': original_path,
                                'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                            })
                
                sections_data['section_7'] = section_7_data
            
            # Get Section 4 data (DUT Confirmation Details)
            if hasattr(self.parent, 'section_4_pairs'):
                section_4_data = {
                    'heading': self.parent.section_4_heading_edit.text().strip() if hasattr(self.parent, 'section_4_heading_edit') else "DUT Confirmation Details",
                    'pairs': []
                }
                
                for pair_info in self.parent.section_4_pairs:
                    pair_data = {
                        'text': pair_info['text_edit'].toPlainText().strip() if hasattr(pair_info.get('text_edit', ''), 'toPlainText') else '',
                        'images': [],
                        'scripts': []
                    }
                    
                    # Get images from this pair
                    if 'images_list' in pair_info:
                        for image_info in pair_info['images_list']:
                            if image_info['path'] and os.path.exists(image_info['path']):
                                pair_data['images'].append({
                                    'path': image_info['path'],
                                    'filename': image_info['filename'],
                                    'original_filename': image_info.get('original_filename', image_info['filename']),
                                    'description': image_info.get('description', '')
                                })
                    
                    # Get scripts from this pair
                    if 'upload_scripts_list' in pair_info:
                        for script_info in pair_info['upload_scripts_list']:
                            if script_info['path'] and os.path.exists(script_info['path']):
                                # Ensure we have the full absolute path
                                full_path = os.path.abspath(script_info['path'])
                                print(f"DEBUG: Section 4 script path: {script_info['path']} -> {full_path}")
                                pair_data['scripts'].append({
                                    'path': full_path,  # Use full absolute path
                                    'filename': script_info['filename'],
                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                    'description': script_info.get('description', ''),
                                    'is_pasted': script_info.get('is_pasted', False),
                                    'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                                })
                    
                    section_4_data['pairs'].append(pair_data)
                
                sections_data['section_4'] = section_4_data
            
            # Get Section 5 data (DUT Configuration)
            if hasattr(self.parent, 'section_5_pairs'):
                section_5_data = {
                    'heading': self.parent.section_5_heading_edit.text().strip() if hasattr(self.parent, 'section_5_heading_edit') else "DUT Configuration",
                    'pairs': []
                }
                
                for pair_info in self.parent.section_5_pairs:
                    pair_data = {
                        'text': pair_info['text_edit'].toPlainText().strip() if hasattr(pair_info.get('text_edit', ''), 'toPlainText') else '',
                        'images': [],
                        'scripts': []
                    }
                    
                    # Get images from this pair
                    if 'images_list' in pair_info:
                        for image_info in pair_info['images_list']:
                            if image_info['path'] and os.path.exists(image_info['path']):
                                pair_data['images'].append({
                                    'path': image_info['path'],
                                    'filename': image_info['filename'],
                                    'original_filename': image_info.get('original_filename', image_info['filename']),
                                    'description': image_info.get('description', '')
                                })
                    
                    # Get scripts from this pair
                    if 'upload_scripts_list' in pair_info:
                        for script_info in pair_info['upload_scripts_list']:
                            if script_info['path'] and os.path.exists(script_info['path']):
                                # Ensure we have the full absolute path
                                full_path = os.path.abspath(script_info['path'])
                                print(f"DEBUG: Section 5 script path: {script_info['path']} -> {full_path}")
                                pair_data['scripts'].append({
                                    'path': full_path,  # Use full absolute path
                                    'filename': script_info['filename'],
                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                    'description': script_info.get('description', ''),
                                    'is_pasted': script_info.get('is_pasted', False),
                                    'placeholder': script_info.get('placeholder', script_info.get('description', ''))
                                })
                    
                    section_5_data['pairs'].append(pair_data)
                
                sections_data['section_5'] = section_5_data
            
            print(f"DEBUG: sections_1_7_data: {sections_data}")
            return sections_data
            
        except Exception as e:
            print(f"Error getting sections 1-7 data: {e}")
            return {}
    
    def get_hash_sections_data(self):
        """Get hash sections data for export"""
        hash_sections_data = []
        
        if hasattr(self.parent, 'hash_sections') and self.parent.hash_sections:
            for section_info in self.parent.hash_sections:
                section_data = {
                    'heading': section_info['heading_edit'].text().strip() if section_info['heading_edit'] else "",
                    'direct_hash_value': section_info['direct_hash_edit'].text().strip() if section_info['direct_hash_edit'] else "",
                    'hash_count': section_info['hash_count_spinbox'].value() if section_info['hash_count_spinbox'] else 0,
                    'hash_fields': [],
                    'direct_hash_images': [],
                    'direct_hash_scripts': []
                }
                
                # Get direct hash images
                if 'direct_hash_field_info' in section_info and 'images_list' in section_info['direct_hash_field_info']:
                    for image_info in section_info['direct_hash_field_info']['images_list']:
                        if image_info['path'] and os.path.exists(image_info['path']):
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(image_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = image_info['path']
                            
                            section_data['direct_hash_images'].append({
                                'path': image_info['path'],
                                'filename': image_info['filename'],
                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                'description': image_info.get('description', ''),
                                'original_path': original_path
                            })
                
                # Get direct hash scripts
                if 'direct_hash_field_info' in section_info and 'scripts_list' in section_info['direct_hash_field_info']:
                    for script_info in section_info['direct_hash_field_info']['scripts_list']:
                        if script_info['path'] and os.path.exists(script_info['path']):
                            # Ensure we have the full absolute path
                            full_path = os.path.abspath(script_info['path'])
                            print(f"DEBUG: Hash section direct hash script path: {script_info['path']} -> {full_path}")
                            
                            # Get relative path from project root for original_path
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(script_info['path'], project_root)
                            except ValueError:
                                # If paths are on different drives, use the full path
                                original_path = script_info['path']
                            
                            section_data['direct_hash_scripts'].append({
                                'path': full_path,  # Use full absolute path
                                'filename': script_info['filename'],
                                'original_filename': script_info.get('original_filename', script_info['filename']),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False),
                                'original_path': original_path
                            })
                
                # Get hash fields
                if 'hash_fields' in section_info:
                    for field_info in section_info['hash_fields']:
                        field_data = {
                            'label': field_info['name_edit'].text().strip() if field_info['name_edit'] else "",
                            'value': field_info['value_edit'].text().strip() if field_info['value_edit'] else "",
                            'images': [],
                            'scripts': []
                        }
                        
                        # Get images for this hash field
                        if 'images_list' in field_info:
                            for image_info in field_info['images_list']:
                                if image_info['path'] and os.path.exists(image_info['path']):
                                    # Get relative path from project root for original_path
                                    project_root = os.getcwd()
                                    try:
                                        original_path = os.path.relpath(image_info['path'], project_root)
                                    except ValueError:
                                        # If paths are on different drives, use the full path
                                        original_path = image_info['path']
                                    
                                    field_data['images'].append({
                                        'path': image_info['path'],
                                        'filename': image_info['filename'],
                                        'original_filename': image_info.get('original_filename', image_info['filename']),
                                        'description': image_info.get('description', ''),
                                        'original_path': original_path
                                    })
                        
                        # Get scripts for this hash field
                        if 'scripts_list' in field_info:
                            for script_info in field_info['scripts_list']:
                                if script_info['path'] and os.path.exists(script_info['path']):
                                    # Ensure we have the full absolute path
                                    full_path = os.path.abspath(script_info['path'])
                                    print(f"DEBUG: Hash section field script path: {script_info['path']} -> {full_path}")
                                    
                                    # Get relative path from project root for original_path
                                    project_root = os.getcwd()
                                    try:
                                        original_path = os.path.relpath(script_info['path'], project_root)
                                    except ValueError:
                                        # If paths are on different drives, use the full path
                                        original_path = script_info['path']
                                    
                                    field_data['scripts'].append({
                                        'path': full_path,  # Use full absolute path
                                        'filename': script_info['filename'],
                                        'original_filename': script_info.get('original_filename', script_info['filename']),
                                        'description': script_info.get('description', ''),
                                        'is_pasted': script_info.get('is_pasted', False),
                                        'original_path': original_path
                                    })
                        
                        section_data['hash_fields'].append(field_data)
                
                hash_sections_data.append(section_data)
        
        return hash_sections_data
    
    def get_test_bed_diagram_data(self):
        """Get test bed diagram data for Section 8"""
        print(f"DEBUG: get_test_bed_diagram_data called")
        print(f"DEBUG: self.parent type: {type(self.parent)}")
        print(f"DEBUG: self.parent has test_bed_diagram_data: {hasattr(self.parent, 'test_bed_diagram_data')}")
        try:
            test_bed_data = {
                'heading': '',
                'images': [],
                'scripts': []
            }
            
            # Get the heading
            if hasattr(self.parent, 'test_bed_diagram_heading_edit'):
                try:
                    test_bed_data['heading'] = self.parent.test_bed_diagram_heading_edit.text().strip()
                except Exception as e:
                    print(f"Warning: Could not extract test bed diagram heading: {e}")
                    test_bed_data['heading'] = ""
            
            # Get the notes
            if hasattr(self.parent, 'test_bed_diagram_notes_edit'):
                try:
                    test_bed_data['notes'] = self.parent.test_bed_diagram_notes_edit.toPlainText().strip()
                except Exception as e:
                    print(f"Warning: Could not extract test bed diagram notes: {e}")
                    test_bed_data['notes'] = ""
            
            # Get images from new structure first, fallback to old structure
            print(f"DEBUG: Checking for test_bed_diagram_data: {hasattr(self.parent, 'test_bed_diagram_data')}")
            if hasattr(self.parent, 'test_bed_diagram_data'):
                print(f"DEBUG: test_bed_diagram_data exists: {self.parent.test_bed_diagram_data}")
                print(f"DEBUG: test_bed_diagram_data images: {self.parent.test_bed_diagram_data.get('images', [])}")
                print(f"DEBUG: test_bed_diagram_data scripts: {self.parent.test_bed_diagram_data.get('scripts', [])}")
                print(f"DEBUG: test_bed_diagram_data scripts length: {len(self.parent.test_bed_diagram_data.get('scripts', []))}")
            
            if hasattr(self.parent, 'test_bed_diagram_data') and self.parent.test_bed_diagram_data:
                print(f"DEBUG: Found {len(self.parent.test_bed_diagram_data['images'])} test bed diagram images in new structure")
                for image_info in self.parent.test_bed_diagram_data['images']:
                    if image_info['path'] and os.path.exists(image_info['path']):
                        test_bed_data['images'].append({
                            'path': image_info['path'],
                            'filename': image_info['filename'],
                            'original_filename': image_info.get('original_filename', image_info['filename']),
                            'description': image_info.get('description', '')
                        })
                        print(f"DEBUG: Added test bed image from new structure: {image_info['filename']}")
            elif hasattr(self.parent, 'test_bed_images') and self.parent.test_bed_images:
                print(f"DEBUG: Found {len(self.parent.test_bed_images)} test bed images in old structure")
                for image_info in self.parent.test_bed_images:
                    if image_info['path'] and os.path.exists(image_info['path']):
                        test_bed_data['images'].append({
                            'path': image_info['path'],
                            'filename': image_info['filename'],
                            'original_filename': image_info.get('original_filename', image_info['filename']),
                            'description': image_info.get('description', '')
                        })
                        print(f"DEBUG: Added test bed image from old structure: {image_info['filename']}")
            
            # Get scripts from new structure first, fallback to old structure
            print(f"DEBUG: Checking for test_bed_diagram_data scripts: {hasattr(self.parent, 'test_bed_diagram_data')}")
            if hasattr(self.parent, 'test_bed_diagram_data') and self.parent.test_bed_diagram_data:
                print(f"DEBUG: Found {len(self.parent.test_bed_diagram_data['scripts'])} test bed diagram scripts in new structure")
                for script_info in self.parent.test_bed_diagram_data['scripts']:
                    print(f"DEBUG: Processing script: {script_info}")
                    print(f"DEBUG: Script path: {script_info.get('path', 'NO PATH')}")
                    print(f"DEBUG: Script path exists: {os.path.exists(script_info.get('path', ''))}")
                    if script_info['path'] and os.path.exists(script_info['path']):
                        test_bed_data['scripts'].append({
                            'path': script_info['path'],
                            'filename': script_info['filename'],
                            'original_filename': script_info.get('original_filename', script_info['filename']),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        })
                        print(f"DEBUG: Added test bed script from new structure: {script_info['filename']} with description: '{script_info.get('description', '')}'")
            elif hasattr(self.parent, 'test_bed_scripts') and self.parent.test_bed_scripts:
                print(f"DEBUG: Found {len(self.parent.test_bed_scripts)} test bed scripts in old structure")
                for script_info in self.parent.test_bed_scripts:
                    if script_info['path'] and os.path.exists(script_info['path']):
                        test_bed_data['scripts'].append({
                            'path': script_info['path'],
                            'filename': script_info['filename'],
                            'original_filename': script_info.get('original_filename', script_info['filename']),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        })
                        print(f"DEBUG: Added test bed script from old structure: {script_info['filename']} with description: '{script_info.get('description', '')}'")
            
            print(f"DEBUG: Test bed diagram data: {test_bed_data}")
            print(f"DEBUG: Test bed diagram images count: {len(test_bed_data['images'])}")
            print(f"DEBUG: Test bed diagram scripts count: {len(test_bed_data['scripts'])}")
            return test_bed_data
            
        except Exception as e:
            print(f"Error getting test bed diagram data: {e}")
            return {'heading': '', 'images': [], 'scripts': []}

    def get_dut_fields_data(self):
        """Get DUT fields data from parent application"""
        try:
            print(f"DEBUG: get_dut_fields_data called")
            if hasattr(self.parent, 'dut_fields'):
                dut_fields = []
                for field in self.parent.dut_fields:
                    if isinstance(field, dict):
                        dut_fields.append(field)
                print(f"DEBUG: Found {len(dut_fields)} DUT fields")
                return dut_fields
            else:
                print(f"DEBUG: No dut_fields attribute found in parent")
                return []
        except Exception as e:
            print(f"Error getting DUT fields data: {e}")
            return []

    def get_hash_sections_data(self):
        """Get hash sections data from parent application"""
        try:
            print(f"DEBUG: get_hash_sections_data called")
            if hasattr(self.parent, 'hash_sections'):
                hash_sections = []
                for section in self.parent.hash_sections:
                    if isinstance(section, dict):
                        hash_sections.append(section)
                print(f"DEBUG: Found {len(hash_sections)} hash sections")
                return hash_sections
            else:
                print(f"DEBUG: No hash_sections attribute found in parent")
                return []
        except Exception as e:
            print(f"Error getting hash sections data: {e}")
            return []

    def get_itsar_fields_data(self):
        """Get ITSAR fields data from parent application"""
        try:
            print(f"DEBUG: get_itsar_fields_data called")
            if hasattr(self.parent, 'itsar_fields'):
                itsar_fields = []
                for field in self.parent.itsar_fields:
                    if isinstance(field, dict):
                        itsar_fields.append(field)
                print(f"DEBUG: Found {len(itsar_fields)} ITSAR fields")
                return itsar_fields
            else:
                print(f"DEBUG: No itsar_fields attribute found in parent")
                return []
        except Exception as e:
            print(f"Error getting ITSAR fields data: {e}")
            return []

    def get_test_scenarios_data(self):
        """Get test scenarios data from parent application"""
        try:
            if hasattr(self.parent, 'test_scenarios'):
                processed_scenarios = []
                for scenario in self.parent.test_scenarios:
                    scenario_data = {
                        'key': self._safe_extract_text(scenario.get('key_edit')),
                        'description': self._safe_extract_plain_text(scenario.get('value_edit')),
                        'images': [],
                        'scripts': [],
                        'placeholders': []
                    }
                    
                    # Collect images from scenario
                    if 'images' in scenario:
                        for image_info in scenario['images']:
                            processed_image = {
                                'path': image_info.get('path', ''),
                                'filename': image_info.get('filename', ''),
                                'original_filename': image_info.get('original_filename', ''),
                                'description': image_info.get('description', ''),
                                'is_placeholder': image_info.get('is_placeholder', False)
                            }
                            scenario_data['images'].append(processed_image)
                    
                    # Collect scripts from scenario
                    if 'scripts' in scenario:
                        for script_info in scenario['scripts']:
                            processed_script = {
                                'path': script_info.get('path', ''),
                                'filename': script_info.get('filename', ''),
                                'original_filename': script_info.get('original_filename', ''),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False)
                            }
                            scenario_data['scripts'].append(processed_script)
                    
                    processed_scenarios.append(scenario_data)
                
                return processed_scenarios
            return []
        except Exception as e:
            print(f"Error getting test scenarios data: {e}")
            return []

    def get_tools_required_data(self):
        """Get tools required data from parent application"""
        try:
            if hasattr(self.parent, 'tools_required'):
                processed_tools = []
                for tool in self.parent.tools_required:
                    tool_data = {
                        'name': self._safe_extract_text(tool.get('tool_edit')),
                        'description': self._safe_extract_plain_text(tool.get('tool_edit')),
                        'images': [],
                        'scripts': [],
                        'placeholders': []
                    }
                    
                    # Collect images from tool
                    if 'images' in tool:
                        for image_info in tool['images']:
                            processed_image = {
                                'path': image_info.get('path', ''),
                                'filename': image_info.get('filename', ''),
                                'original_filename': image_info.get('original_filename', ''),
                                'description': image_info.get('description', ''),
                                'is_placeholder': image_info.get('is_placeholder', False)
                            }
                            tool_data['images'].append(processed_image)
                    
                    # Collect scripts from tool
                    if 'scripts' in tool:
                        for script_info in tool['scripts']:
                            processed_script = {
                                'path': script_info.get('path', ''),
                                'filename': script_info.get('filename', ''),
                                'original_filename': script_info.get('original_filename', ''),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False)
                            }
                            tool_data['scripts'].append(processed_script)
                    
                    processed_tools.append(tool_data)
                
                return processed_tools
            return []
        except Exception as e:
            print(f"Error getting tools required data: {e}")
            return []

    def get_expected_results_data(self):
        """Get expected results data from parent application"""
        try:
            if hasattr(self.parent, 'expected_results'):
                return self.parent.expected_results
            return []
        except Exception as e:
            print(f"Error getting expected results data: {e}")
            return []

    def get_step_images_data(self):
        """Get step images data from parent application"""
        try:
            if hasattr(self.parent, 'step_images'):
                return self.parent.step_images
            return []
        except Exception as e:
            print(f"Error getting step images data: {e}")
            return []

    def get_manual_execution_steps_data(self):
        """Get manual execution steps data from parent application"""
        try:
            if hasattr(self.parent, 'manual_steps'):
                return self.parent.manual_steps
            return []
        except Exception as e:
            print(f"Error getting manual execution steps data: {e}")
            return []

    
    def get_test_execution_cases_data(self):
        """Get test execution cases data from parent application"""
        try:
            print(f"DEBUG: get_test_execution_cases_data called")
            print(f"DEBUG: parent has test_execution_cases: {hasattr(self.parent, 'test_execution_cases')}")
            if hasattr(self.parent, 'test_execution_cases'):
                test_execution_cases = []
                print(f"DEBUG: Found {len(self.parent.test_execution_cases)} test execution cases")
                print(f"DEBUG: test_execution_cases content: {self.parent.test_execution_cases}")
                for case_data in self.parent.test_execution_cases:
                    print(f"DEBUG: Processing case_data: {case_data}")
                    case_info = {
                        'case_number': case_data.get('case_number', ''),
                        'scenario_key': case_data.get('scenario_key', ''),
                        'itsar_description': self._safe_extract_text(case_data.get('itsar_edit')),
                        'test_case_description': self._safe_extract_plain_text(case_data.get('case_desc_edit')),
                        'test_objective': self._safe_extract_plain_text(case_data.get('test_objective_edit')),
                        'test_observations': self._safe_extract_plain_text(case_data.get('observations_edit')),
                        'evidence_provided': self._safe_extract_plain_text(case_data.get('evidence_edit')),
                        'images': [],
                        'scripts': [],
                        'placeholders': [],
                        'steps_data': []
                    }
                    
                    # Collect images and scripts from steps
                    print(f"DEBUG: case_data has 'steps': {'steps' in case_data}")
                    if 'steps' in case_data:
                        print(f"DEBUG: case_data['steps']: {case_data['steps']}")
                        for step_index, step in enumerate(case_data['steps'], 1):
                            print(f"DEBUG: Processing step {step_index}: {step}")
                            print(f"DEBUG: case_info['case_number']: {case_info['case_number']}")
                            print(f"DEBUG: step_index: {step_index}")
                            print(f"DEBUG: Will look for step_key: {case_info['case_number']}_{step_index}")
                            
                            step_data = {
                                'step_text': self._safe_extract_text(step.get('step_edit')),
                                'images': [],
                                'scripts': [],
                                'placeholders': []
                            }
                            
                            # Get step key to find corresponding step widget
                            step_key = f"{case_info['case_number']}_{step_index}"
                            print(f"DEBUG: Looking for step_key: {step_key}")
                            print(f"DEBUG: case_info['case_number']: {case_info['case_number']}")
                            print(f"DEBUG: step_index: {step_index}")
                            print(f"DEBUG: case_info keys: {list(case_info.keys())}")
                            print(f"DEBUG: case_info type: {type(case_info)}")
                            
                            # Debug: Check all available step keys and their content
                            if hasattr(self.parent, 'step_widgets'):
                                print(f"DEBUG: All available step_widgets keys: {list(self.parent.step_widgets.keys())}")
                                for key, widget_data in self.parent.step_widgets.items():
                                    print(f"DEBUG: step_widgets[{key}] keys: {list(widget_data.keys())}")
                                    if 'placeholders_list' in widget_data:
                                        print(f"DEBUG: step_widgets[{key}]['placeholders_list'] has {len(widget_data['placeholders_list'])} items: {widget_data['placeholders_list']}")
                                    else:
                                        print(f"DEBUG: step_widgets[{key}] has no placeholders_list")
                                
                                # Also check global storage
                                if hasattr(self.parent, '_global_step_placeholders'):
                                    print(f"DEBUG: Global step placeholders keys: {list(self.parent._global_step_placeholders.keys())}")
                                    for key, placeholders in self.parent._global_step_placeholders.items():
                                        print(f"DEBUG: _global_step_placeholders[{key}] has {len(placeholders)} items: {placeholders}")
                                else:
                                    print(f"DEBUG: No _global_step_placeholders attribute found")
                            else:
                                print(f"DEBUG: No step_widgets attribute found in parent")
                            
                            # Get images and scripts from step widgets
                            print(f"DEBUG: parent has step_widgets: {hasattr(self.parent, 'step_widgets')}")
                            if hasattr(self.parent, 'step_widgets'):
                                print(f"DEBUG: step_widgets keys: {list(self.parent.step_widgets.keys())}")
                                print(f"DEBUG: step_key in step_widgets: {step_key in self.parent.step_widgets}")
                                print(f"DEBUG: step_widgets type: {type(self.parent.step_widgets)}")
                                print(f"DEBUG: step_widgets content: {self.parent.step_widgets}")
                            else:
                                print(f"DEBUG: No step_widgets found in parent")
                            if hasattr(self.parent, 'step_widgets') and step_key in self.parent.step_widgets:
                                step_widget = self.parent.step_widgets[step_key]
                                print(f"DEBUG: Found step widget for key: {step_key}")
                                print(f"DEBUG: step_widget keys: {list(step_widget.keys())}")
                                print(f"DEBUG: step_widget content: {step_widget}")
                                
                                # Debug: Check if placeholders_list exists and has content
                                if 'placeholders_list' in step_widget:
                                    print(f"DEBUG: placeholders_list exists in step_widget with {len(step_widget['placeholders_list'])} items")
                                    print(f"DEBUG: placeholders_list content: {step_widget['placeholders_list']}")
                                else:
                                    print(f"DEBUG: placeholders_list NOT found in step_widget")
                                    print(f"DEBUG: Available keys in step_widget: {list(step_widget.keys())}")
                                
                                # Collect images
                                if 'upload_images_list' in step_widget:
                                    print(f"DEBUG: Found {len(step_widget['upload_images_list'])} images in step {step_key}")
                                    for image_info in step_widget['upload_images_list']:
                                        if image_info['path'] and os.path.exists(image_info['path']):
                                            step_data['images'].append({
                                                'path': image_info['path'],
                                                'filename': image_info['filename'],
                                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                                'description': image_info.get('description', '')
                                            })
                                            print(f"DEBUG: Added image: {image_info['filename']}")
                                        else:
                                            print(f"DEBUG: Image path not found or doesn't exist: {image_info.get('path', 'No path')}")
                                else:
                                    print(f"DEBUG: No upload_images_list found in step {step_key}")
                                
                                # Collect scripts
                                if 'upload_scripts_list' in step_widget:
                                    print(f"DEBUG: Found {len(step_widget['upload_scripts_list'])} scripts in step {step_key}")
                                    for script_info in step_widget['upload_scripts_list']:
                                        print(f"DEBUG: Processing script_info: {script_info}")
                                        
                                        # Use 'path' field from JSON, fallback to 'original_path' if needed
                                        script_path = script_info.get('path', script_info.get('original_path', ''))
                                        print(f"DEBUG: Using script_path (from 'path' field): {script_path}")
                                        
                                        # Handle relative paths by combining with import_project_dir
                                        if script_path:
                                            if not os.path.isabs(script_path) and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                                # Convert relative path to absolute path
                                                absolute_path = os.path.join(self.parent.import_project_dir, script_path)
                                                print(f"DEBUG: Converted relative path to absolute: {script_path} -> {absolute_path}")
                                                script_path = absolute_path
                                            
                                            if os.path.exists(script_path):
                                                script_data = {
                                                    'path': script_path,  # Use the actual file path
                                                    'filename': script_info['filename'],
                                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                                    'description': script_info.get('description', ''),
                                                    'is_pasted': script_info.get('is_pasted', False),
                                                    # 'original_path': script_path  # Preserve original path for export
                                                }
                                                print(f"DEBUG: Export - Adding script from step widget: '{script_info['filename']}' with description: '{script_data['description']}'")
                                                step_data['scripts'].append(script_data)
                                                # Also add to upload_scripts_list for document generation compatibility
                                                step_data['upload_scripts_list'] = step_data.get('upload_scripts_list', [])
                                                step_data['upload_scripts_list'].append(script_data)
                                            else:
                                                print(f"DEBUG: Script path not found or doesn't exist: {script_path}")
                                                # Still add the script data even if file doesn't exist (for import/export workflow)
                                                script_data = {
                                                    'path': script_path,
                                                    'filename': script_info['filename'],
                                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                                    'description': script_info.get('description', ''),
                                                    'is_pasted': script_info.get('is_pasted', False),
                                                    # 'original_path': script_path
                                                }
                                                print(f"DEBUG: Export - Adding script data even though file doesn't exist: '{script_info['filename']}'")
                                                step_data['scripts'].append(script_data)
                                                # Also add to upload_scripts_list for document generation compatibility
                                                step_data['upload_scripts_list'] = step_data.get('upload_scripts_list', [])
                                                step_data['upload_scripts_list'].append(script_data)
                                        else:
                                            print(f"DEBUG: No script path found in script_info")
                                else:
                                    print(f"DEBUG: No upload_scripts_list found in step {step_key}")
                                
                                # Collect placeholders
                                if 'placeholders_list' in step_widget:
                                    print(f"DEBUG: Found {len(step_widget['placeholders_list'])} placeholders in step {step_key}")
                                    print(f"DEBUG: placeholders_list content: {step_widget['placeholders_list']}")
                                    for placeholder_info in step_widget['placeholders_list']:
                                        print(f"DEBUG: Processing placeholder_info: {placeholder_info}")
                                        if placeholder_info.get('name'):
                                            placeholder_data = {
                                                'name': placeholder_info['name'],
                                                'type': 'placeholder',
                                                'is_placeholder': True
                                            }
                                            step_data['placeholders'].append(placeholder_data)
                                            print(f"DEBUG: Added placeholder: {placeholder_info['name']} to step_data['placeholders']")
                                        else:
                                            print(f"DEBUG: Placeholder info missing name: {placeholder_info}")
                                else:
                                    print(f"DEBUG: No placeholders_list found in step {step_key}")
                                    print(f"DEBUG: Available keys in step_widget: {list(step_widget.keys())}")
                                    print(f"DEBUG: step_widget full content: {step_widget}")
                                    
                                    # FALLBACK: Check global storage for placeholders
                                    if hasattr(self.parent, '_global_step_placeholders') and step_key in self.parent._global_step_placeholders:
                                        global_placeholders = self.parent._global_step_placeholders[step_key]
                                        print(f"DEBUG: Found {len(global_placeholders)} placeholders in global storage for step {step_key}")
                                        print(f"DEBUG: Global placeholders content: {global_placeholders}")
                                        for placeholder_info in global_placeholders:
                                            if placeholder_info.get('name'):
                                                placeholder_data = {
                                                    'name': placeholder_info['name'],
                                                    'type': 'placeholder',
                                                    'is_placeholder': True
                                                }
                                                step_data['placeholders'].append(placeholder_data)
                                                print(f"DEBUG: Added placeholder from global storage: {placeholder_info['name']} to step_data['placeholders']")
                                    else:
                                        print(f"DEBUG: No placeholders found in global storage for step {step_key}")
                                        print(f"DEBUG: _global_step_placeholders exists: {hasattr(self.parent, '_global_step_placeholders')}")
                                        if hasattr(self.parent, '_global_step_placeholders'):
                                            print(f"DEBUG: _global_step_placeholders keys: {list(self.parent._global_step_placeholders.keys())}")
                                            print(f"DEBUG: _global_step_placeholders content: {self.parent._global_step_placeholders}")
                            else:
                                print(f"DEBUG: Step widget not found for key: {step_key}")
                                if hasattr(self.parent, 'step_widgets'):
                                    print(f"DEBUG: Available step keys: {list(self.parent.step_widgets.keys())}")
                                else:
                                    print(f"DEBUG: No step_widgets attribute found")
                            
                            # Also check global storage for images and scripts
                            if hasattr(self.parent, '_global_step_images') and step_key in self.parent._global_step_images:
                                print(f"DEBUG: Found {len(self.parent._global_step_images[step_key])} images in global storage for step {step_key}")
                                for image_info in self.parent._global_step_images[step_key]:
                                    if image_info['path'] and os.path.exists(image_info['path']):
                                        # Check if image is already added to avoid duplicates
                                        image_already_added = any(img.get('filename') == image_info['filename'] for img in step_data['images'])
                                        if not image_already_added:
                                            step_data['images'].append({
                                                'path': image_info['path'],
                                                'filename': image_info['filename'],
                                                'original_filename': image_info.get('original_filename', image_info['filename']),
                                                'description': image_info.get('description', '')
                                            })
                                            print(f"DEBUG: Added image from global storage: {image_info['filename']}")
                                        else:
                                            print(f"DEBUG: Image {image_info['filename']} already added from step widget")
                                    else:
                                        print(f"DEBUG: Image path not found or doesn't exist in global storage: {image_info.get('path', 'No path')}")
                            
                            if hasattr(self.parent, '_global_step_scripts') and step_key in self.parent._global_step_scripts:
                                print(f"DEBUG: Found {len(self.parent._global_step_scripts[step_key])} scripts in global storage for step {step_key}")
                                for script_info in self.parent._global_step_scripts[step_key]:
                                    print(f"DEBUG: Processing global script_info: {script_info}")
                                    
                                    # Use 'path' field from JSON, fallback to 'original_path' if needed
                                    script_path = script_info.get('path', script_info.get('original_path', ''))
                                    print(f"DEBUG: Using global script_path (from 'path' field): {script_path}")
                                    
                                    # Handle relative paths by combining with import_project_dir
                                    if script_path:
                                        if not os.path.isabs(script_path) and hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                            # Convert relative path to absolute path
                                            absolute_path = os.path.join(self.parent.import_project_dir, script_path)
                                            print(f"DEBUG: Converted global relative path to absolute: {script_path} -> {absolute_path}")
                                            script_path = absolute_path
                                        
                                        if os.path.exists(script_path):
                                            # Check if script is already added to avoid duplicates
                                            script_already_added = any(scr.get('filename') == script_info['filename'] for scr in step_data['scripts'])
                                            if not script_already_added:
                                                script_data = {
                                                    'path': script_path,  # Use the actual file path
                                                    'filename': script_info['filename'],
                                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                                    'description': script_info.get('description', ''),
                                                    'is_pasted': script_info.get('is_pasted', False),
                                                    # 'original_path': script_path  # Preserve original path for export
                                                }
                                                print(f"DEBUG: Export - Adding script from global storage: '{script_info['filename']}' with description: '{script_data['description']}'")
                                                step_data['scripts'].append(script_data)
                                            else:
                                                print(f"DEBUG: Script {script_info['filename']} already added from step widget")
                                        else:
                                            print(f"DEBUG: Script path not found or doesn't exist in global storage: {script_path}")
                                            # Still add the script data even if file doesn't exist (for import/export workflow)
                                            script_already_added = any(scr.get('filename') == script_info['filename'] for scr in step_data['scripts'])
                                            if not script_already_added:
                                                script_data = {
                                                    'path': script_path,
                                                    'filename': script_info['filename'],
                                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                                    'description': script_info.get('description', ''),
                                                    'is_pasted': script_info.get('is_pasted', False),
                                                    # 'original_path': script_path
                                                }
                                                print(f"DEBUG: Export - Adding script data from global storage even though file doesn't exist: '{script_info['filename']}'")
                                                step_data['scripts'].append(script_data)
                                    else:
                                        print(f"DEBUG: No script path found in global script_info")
                            
                            # Also check global storage for placeholders
                            if hasattr(self.parent, '_global_step_placeholders') and step_key in self.parent._global_step_placeholders:
                                print(f"DEBUG: Found {len(self.parent._global_step_placeholders[step_key])} placeholders in global storage for step {step_key}")
                                for placeholder_info in self.parent._global_step_placeholders[step_key]:
                                    if placeholder_info.get('name'):
                                        # Check if placeholder is already added to avoid duplicates
                                        placeholder_already_added = any(ph.get('name') == placeholder_info['name'] for ph in step_data['placeholders'])
                                        if not placeholder_already_added:
                                            step_data['placeholders'].append({
                                                'name': placeholder_info['name'],
                                                'type': 'placeholder',
                                                'is_placeholder': True
                                            })
                                            print(f"DEBUG: Added placeholder from global storage: {placeholder_info['name']}")
                                        else:
                                            print(f"DEBUG: Placeholder {placeholder_info['name']} already added from step widget")
                            
                            print(f"DEBUG: Final step_data before append: {step_data}")
                            print(f"DEBUG: step_data['placeholders'] length: {len(step_data['placeholders'])}")
                            case_info['steps_data'].append(step_data)
                    
                    # Collect case-level placeholders from step widgets
                    print(f"DEBUG: Collecting case-level placeholders for case {case_info['case_number']}")
                    case_placeholders = set()  # Use set to avoid duplicates
                    
                    if 'steps' in case_data:
                        for step_index, step in enumerate(case_data['steps'], 1):
                            step_key = f"{case_info['case_number']}_{step_index}"
                            if hasattr(self.parent, 'step_widgets') and step_key in self.parent.step_widgets:
                                step_widget = self.parent.step_widgets[step_key]
                                if 'placeholders_list' in step_widget:
                                    for placeholder_info in step_widget['placeholders_list']:
                                        if placeholder_info.get('name'):
                                            case_placeholders.add(placeholder_info['name'])
                                            print(f"DEBUG: Added case-level placeholder: {placeholder_info['name']}")
                    
                    # Add case-level placeholders to case_info
                    for placeholder_name in case_placeholders:
                        case_info['placeholders'].append({
                            'name': placeholder_name,
                            'type': 'placeholder',
                            'is_placeholder': True
                        })
                        print(f"DEBUG: Added to case-level placeholders: {placeholder_name}")
                    
                    print(f"DEBUG: Case {case_info['case_number']} has {len(case_info['placeholders'])} case-level placeholders")
                    
                    # Also check global storage for case-level placeholders
                    if hasattr(self.parent, 'automatic_images') and self.parent.automatic_images:
                        for placeholder_info in self.parent.automatic_images:
                            if isinstance(placeholder_info, dict) and 'placeholder' in placeholder_info:
                                # Check if this placeholder belongs to this case
                                if placeholder_info.get('source') == 'section_11':
                                    case_info['placeholders'].append(placeholder_info['placeholder'])
                    
                    test_execution_cases.append(case_info)
                
                # Debug: Show final test execution cases data
                print(f"DEBUG: Final test execution cases data:")
                for i, case in enumerate(test_execution_cases):
                    print(f"DEBUG: Case {i+1}: {case.get('case_number', 'unknown')}")
                    steps_data = case.get('steps_data', [])
                    print(f"DEBUG: Case {i+1} has {len(steps_data)} steps_data")
                    for j, step_data in enumerate(steps_data):
                        scripts = step_data.get('scripts', [])
                        print(f"DEBUG: Step {j+1} has {len(scripts)} scripts")
                        for script in scripts:
                            print(f"DEBUG: Script in step {j+1}: {script}")
                
                return test_execution_cases
            return []
        except Exception as e:
            print(f"Error getting test execution cases data: {e}")
            return []
            
    def get_expected_results_data(self):
        """Get expected results data for Section 9"""
        print(f"DEBUG: get_expected_results_data called")
        expected_results_data = []
        
        try:
            # First, try to get data from the expected_results list structure (used by import)
            if hasattr(self.parent, 'expected_results') and self.parent.expected_results:
                print(f"DEBUG: Found expected_results list with {len(self.parent.expected_results)} entries")
                for i, result_data in enumerate(self.parent.expected_results):
                    if isinstance(result_data, dict):
                        processed_result = {
                            'scenario_key': result_data.get('scenario_key', ''),
                            'expected_result': result_data.get('expected_result', ''),
                            'images': [],
                            'scripts': []
                        }
                        
                        # Process images from the result data
                        for image_info in result_data.get('images', []):
                            if image_info.get('path') and os.path.exists(image_info['path']):
                                # Get relative path from project root for original_path
                                project_root = os.getcwd()
                                try:
                                    original_path = os.path.relpath(image_info['path'], project_root)
                                except ValueError:
                                    # If paths are on different drives, use the full path
                                    original_path = image_info['path']
                                
                                processed_result['images'].append({
                                    'path': image_info['path'],
                                    'filename': image_info['filename'],
                                    'original_filename': image_info.get('original_filename', image_info['filename']),
                                    'description': image_info.get('description', ''),
                                    'original_path': original_path
                                })
                                print(f"DEBUG: Added expected result image from list: {image_info['filename']}")
                        
                        # Process scripts from the result data
                        for script_info in result_data.get('scripts', []):
                            if script_info.get('path') and os.path.exists(script_info['path']):
                                # Ensure we have the full absolute path
                                full_path = os.path.abspath(script_info['path'])
                                
                                # Get relative path from project root for original_path
                                project_root = os.getcwd()
                                try:
                                    original_path = os.path.relpath(script_info['path'], project_root)
                                except ValueError:
                                    # If paths are on different drives, use the full path
                                    original_path = script_info['path']
                                
                                processed_result['scripts'].append({
                                    'path': full_path,  # Use full absolute path
                                    'filename': script_info['filename'],
                                    'original_filename': script_info.get('original_filename', script_info['filename']),
                                    'description': script_info.get('description', ''),
                                    'is_pasted': script_info.get('is_pasted', False),
                                    'original_path': original_path
                                })
                                print(f"DEBUG: Added expected result script from list: {script_info['filename']}")
                        
                        expected_results_data.append(processed_result)
            
            # Fallback: Get expected results from test scenarios (legacy method)
            elif hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                print(f"DEBUG: Using fallback method - getting data from test scenarios")
                for scenario in self.parent.test_scenarios:
                    scenario_key = scenario['key_edit'].text().strip()
                    expected_result = ""
                    
                    if 'expected_result_edit' in scenario:
                        QApplication.processEvents()
                        expected_result = scenario['expected_result_edit'].toPlainText().strip()
                        print(f"DEBUG: Export - Reading expected result from UI for scenario '{scenario_key}': '{expected_result}'")

                    
                    if scenario_key or expected_result:
                        result_data = {
                            'scenario_key': scenario_key,
                            'expected_result': expected_result,
                            'images': [],
                            'scripts': []
                        }
                        
                        # Get images for this expected result (global storage)
                        if hasattr(self.parent, 'expected_results_images') and self.parent.expected_results_images:
                            print(f"DEBUG: Found {len(self.parent.expected_results_images)} expected results images")
                            for image_info in self.parent.expected_results_images:
                                if image_info['path'] and os.path.exists(image_info['path']):
                                    # Get relative path from project root for original_path
                                    project_root = os.getcwd()
                                    try:
                                        original_path = os.path.relpath(image_info['path'], project_root)
                                    except ValueError:
                                        # If paths are on different drives, use the full path
                                        original_path = image_info['path']
                                    
                                    result_data['images'].append({
                                        'path': image_info['path'],
                                        'filename': image_info['filename'],
                                        'original_filename': image_info.get('original_filename', image_info['filename']),
                                        'description': image_info.get('description', ''),
                                        'original_path': original_path
                                    })
                                    print(f"DEBUG: Added expected result image: {image_info['filename']}")
                        
                        # Get scripts for this expected result (global storage)
                        if hasattr(self.parent, 'expected_results_scripts') and self.parent.expected_results_scripts:
                            print(f"DEBUG: Found {len(self.parent.expected_results_scripts)} expected results scripts")
                            for script_info in self.parent.expected_results_scripts:
                                if script_info['path'] and os.path.exists(script_info['path']):
                                    # Ensure we have the full absolute path
                                    full_path = os.path.abspath(script_info['path'])
                                    
                                    # Get relative path from project root for original_path
                                    project_root = os.getcwd()
                                    try:
                                        original_path = os.path.relpath(script_info['path'], project_root)
                                    except ValueError:
                                        # If paths are on different drives, use the full path
                                        original_path = script_info['path']
                                    
                                    result_data['scripts'].append({
                                        'path': full_path,  # Use full absolute path
                                        'filename': script_info['filename'],
                                        'original_filename': script_info.get('original_filename', script_info['filename']),
                                        'description': script_info.get('description', ''),
                                        'is_pasted': script_info.get('is_pasted', False),
                                        'original_path': original_path
                                    })
                                    print(f"DEBUG: Added expected result script: {script_info['filename']}")
                        
                        expected_results_data.append(result_data)
            
            print(f"DEBUG: get_expected_results_data returning {len(expected_results_data)} expected results")
            for result in expected_results_data:
                print(f"DEBUG: Expected result '{result.get('scenario_key', 'N/A')}' has {len(result.get('images', []))} images and {len(result.get('scripts', []))} scripts")
            return expected_results_data
            
        except Exception as e:
            print(f"Error getting expected results data: {e}")
            return []
    
    def get_selected_options(self):
        """Get the selected options"""
        options = []
        if self.doc_checkbox.isChecked():
            options.append("Doc")
        if self.script_checkbox.isChecked():
            options.append("Script")
        if self.data_checkbox.isChecked():
            options.append("Data Upload")
        return options



# Example usage and integration
class ExampleIntegration:
    """Example of how to integrate these pages into your application"""
    
    def __init__(self):
        from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
        
        self.app = QApplication(sys.argv)
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("Export Code and Files Pages Demo")
        self.main_window.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Initialize the pages
        self.pages = ExportCodeAndFilesPages(self.main_window)
        
        # Create pages
        export_code_page = self.pages.create_export_code_page()
        files_page = self.pages.create_files_page()
        
        # Add pages to layout (you can use QStackedWidget for switching)
        layout.addWidget(export_code_page)
        layout.addWidget(files_page)
    
    def run(self):
        """Run the example application"""
        self.main_window.show()
        return self.app.exec()


if __name__ == "__main__":
    # Run the example
    example = ExampleIntegration()
    example.run()
