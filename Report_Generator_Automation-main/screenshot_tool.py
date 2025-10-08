#!/usr/bin/env python3
"""
Security Assessment Report Generator - Complete PyQt6 Application
Generates structured .docx reports with embedded terminal and screenshot annotation
"""

import os
import sys
import json
import subprocess
import time
import logging
import socket
import re
import shutil
import tempfile
from datetime import datetime
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QSplitter, QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QGroupBox, QCheckBox, QComboBox, QSpinBox, QProgressBar, QTextBrowser,
    QTabWidget, QFormLayout, QSizePolicy, QSpacerItem, QDialog, QDialogButtonBox,
    QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QSettings, QProcess
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QAction, QPainter, QPen

from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION

from terminal_widget import TerminalWidget
from screenshot_tool import ScreenshotTool
from document_generator import DocumentGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StyleSheet:
    """Application-wide stylesheet definitions"""
    
    DARK_THEME = """
    QMainWindow {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    QSplitter::handle {
        background-color: #444444;
        width: 2px;
    }
    
    QSplitter::handle:hover {
        background-color: #666666;
    }
    
    /* Sidebar Styling */
    #sidebar {
        background-color: #080808;
        border-right: 1px solid #444444;
    }
    
    QListWidget {
        background-color: #080808;
        border: none;
        outline: none;
        color: #ffffff;
        font-size: 14px;
        padding: 5px;
    }
    
    QListWidget::item {
        padding: 12px 16px;
        border-bottom: 1px solid #333333;
        background-color: transparent;
    }
    
    QListWidget::item:hover {
        background-color: #3c3c3e;
    }
    
    QListWidget::item:selected {
        background-color: #b95a30;
        color: #ffffff;
    }
    
    /* Content Area Styling */
    #contentArea {
        background-color: #1a1a1a;
        padding: 20px;
    }
    
    QGroupBox {
        font-size: 14px;
        font-weight: bold;
        color: #ffffff;
        background-color: #2c2c2e;
        border: 1px solid #444444;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 15px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
        color: #ff9800;
    }
    
    QLabel {
        color: #ffffff;
        font-size: 12px;
    }
    
    QLineEdit, QTextEdit, QComboBox {
        background-color: #232b3b;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 8px;
        color: #ffffff;
        font-size: 12px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border: 2px solid #2196f3;
    }
    
    QPushButton {
        background-color: #b95a30;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        font-size: 12px;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #d46a40;
    }
    
    QPushButton:pressed {
        background-color: #a54a20;
    }
    
    QPushButton:disabled {
        background-color: #555555;
        color: #999999;
    }
    
    /* Table Styling */
    QTableWidget {
        background-color: #232b3b;
        alternate-background-color: #2a3441;
        border: 1px solid #444444;
        gridline-color: #444444;
        color: #ffffff;
    }
    
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #444444;
    }
    
    QTableWidget::item:selected {
        background-color: #b95a30;
    }
    
    QHeaderView::section {
        background-color: #353537;
        color: #e5e7eb;
        padding: 8px;
        border: 1px solid #444444;
        font-weight: bold;
    }
    
    /* Preview Panel Styling */
    #previewPanel {
        background-color: #1a1a1a;
        border-left: 1px solid #444444;
    }
    
    QTextBrowser {
        background-color: #232b3b;
        border: 1px solid #444444;
        border-radius: 4px;
        color: #ffffff;
        font-family: 'Calibri', Arial, sans-serif;
        font-size: 11px;
        padding: 15px;
    }
    
    /* Scrollbar Styling */
    QScrollBar:vertical {
        background-color: #2c2c2e;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #555555;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #666666;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
        border: none;
    }
    
    QProgressBar {
        background-color: #4b5563;
        border: 1px solid #444444;
        border-radius: 4px;
        text-align: center;
        color: #ffffff;
    }
    
    QProgressBar::chunk {
        background-color: #3b82f6;
        border-radius: 3px;
    }
    """

class SecurityReportGenerator(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings('SecurityReportGenerator', 'MainApp')
        self.current_data = {}
        self.screenshots = []
        self.test_scenarios = []
        self.execution_blocks = []
        self.document_generator = DocumentGenerator()
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Security Assessment Report Generator")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Apply dark theme
        self.setStyleSheet(StyleSheet.DARK_THEME)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        central_widget_layout = QHBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        central_widget_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create sidebar
        self.create_sidebar(main_splitter)
        
        # Create content area
        self.create_content_area(main_splitter)
        
        # Create preview panel
        self.create_preview_panel(main_splitter)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 800, 500])
        main_splitter.setStretchFactor(0, 0)  # Sidebar fixed
        main_splitter.setStretchFactor(1, 1)  # Content area stretches
        main_splitter.setStretchFactor(2, 0)  # Preview panel semi-fixed
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage("Ready")
            
        # Select first item after everything is initialized
        self.nav_list.setCurrentRow(0)
        
    def create_sidebar(self, parent):
        """Create the navigation sidebar"""
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("sidebar")
        sidebar_widget.setFixedWidth(300)
        
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("Security Report Generator")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 20px;
                color: #ff9800;
                background-color: #080808;
                border-bottom: 1px solid #444444;
            }
        """)
        sidebar_layout.addWidget(title_label)
        
        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        
        nav_items = [
            ("📋 Report Information", "report_info"),
            ("🖥️ DUT Configuration", "dut_config"),
            ("🔌 Interface Status", "interface_status"),
            ("📷 Screenshots & Evidence", "screenshots"),
            ("🔧 Embedded Terminal", "terminal"),
            ("📝 Test Scenarios", "test_scenarios"),
            ("🎯 Test Execution", "test_execution"),
            ("📄 Preview Document", "preview"),
            ("📤 Export Report", "export")
        ]
        
        for text, data in nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.nav_list.addItem(item)
        
        self.nav_list.currentItemChanged.connect(self.on_nav_changed)
        sidebar_layout.addWidget(self.nav_list)
        
        parent.addWidget(sidebar_widget)
        
    def create_content_area(self, parent):
        """Create the main content area"""
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        
        content_layout = QVBoxLayout(content_widget)
        
        # Create stacked widget for different forms
        self.content_stack = QStackedWidget()
        
        # Add different content pages
        self.create_report_info_page()
        self.create_dut_config_page()
        self.create_interface_status_page()
        self.create_screenshots_page()
        self.create_terminal_page()
        self.create_test_scenarios_page()
        self.create_test_execution_page()
        self.create_preview_page()
        self.create_export_page()
        
        content_layout.addWidget(self.content_stack)
        parent.addWidget(content_widget)
        
    def create_preview_panel(self, parent):
        """Create the live preview panel"""
        preview_widget = QWidget()
        preview_widget.setObjectName("previewPanel")
        preview_widget.setFixedWidth(500)
        
        preview_layout = QVBoxLayout(preview_widget)
        
        # Title
        preview_title = QLabel("Live Document Preview")
        preview_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ff9800;
                padding: 10px;
                border-bottom: 1px solid #444444;
            }
        """)
        preview_layout.addWidget(preview_title)
        
        # Preview browser
        self.preview_browser = QTextBrowser()
        self.preview_browser.setObjectName("previewBrowser")
        preview_layout.addWidget(self.preview_browser)
        
        # Update button
        update_btn = QPushButton("🔄 Update Preview")
        update_btn.clicked.connect(self.update_preview)
        preview_layout.addWidget(update_btn)
        
        parent.addWidget(preview_widget)
        
    def create_report_info_page(self):
        """Create report information form"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Report Information")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Basic Information Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.test_report_field = QLineEdit()
        self.test_report_field.setPlaceholderText("e.g., 1.9.4 VULNERABILITY SCANNING")
        basic_layout.addRow("Test Report For:", self.test_report_field)
        
        self.itsar_section_field = QLineEdit()
        self.itsar_section_field.setPlaceholderText("e.g., Section 1.9 Vulnerability Testing Requirements")
        basic_layout.addRow("ITSAR Section No & Name:", self.itsar_section_field)
        
        self.security_req_field = QLineEdit()
        self.security_req_field.setPlaceholderText("e.g., 1.9.4: Vulnerability Scanning")
        basic_layout.addRow("Security Requirement No & Name:", self.security_req_field)
        
        self.req_description_field = QTextEdit()
        self.req_description_field.setPlaceholderText("Enter requirement description...")
        self.req_description_field.setMaximumHeight(100)
        basic_layout.addRow("Requirement Description:", self.req_description_field)
        
        layout.addWidget(basic_group)
        
        # DUT Details Group
        dut_group = QGroupBox("DUT Details")
        dut_layout = QFormLayout(dut_group)
        
        self.dut_details_field = QLineEdit()
        self.dut_details_field.setPlaceholderText("Enter DUT details...")
        dut_layout.addRow("DUT Details:", self.dut_details_field)
        
        self.dut_software_version_field = QLineEdit()
        self.dut_software_version_field.setPlaceholderText("Enter software version...")
        dut_layout.addRow("DUT Software Version:", self.dut_software_version_field)
        
        self.fortiap_hash_os_field = QLineEdit()
        self.fortiap_hash_os_field.setPlaceholderText("Enter FortiAP OS hash...")
        dut_layout.addRow("FortiAP Hash (OS):", self.fortiap_hash_os_field)
        
        self.fortigate_hash_os_field = QLineEdit()
        self.fortigate_hash_os_field.setPlaceholderText("Enter FortiGate OS hash...")
        dut_layout.addRow("FortiGate Hash (OS):", self.fortigate_hash_os_field)
        
        self.fortiap_hash_config_field = QLineEdit()
        self.fortiap_hash_config_field.setPlaceholderText("Enter FortiAP config hash...")
        dut_layout.addRow("FortiAP Hash (Config):", self.fortiap_hash_config_field)
        
        layout.addWidget(dut_group)
        
        # ITSAR Information Group
        itsar_group = QGroupBox("ITSAR Information")
        itsar_layout = QFormLayout(itsar_group)
        
        self.applicable_itsar_field = QLineEdit()
        self.applicable_itsar_field.setPlaceholderText("Enter applicable ITSAR...")
        itsar_layout.addRow("Applicable ITSAR:", self.applicable_itsar_field)
        
        self.itsar_version_field = QLineEdit()
        self.itsar_version_field.setPlaceholderText("Enter ITSAR version...")
        itsar_layout.addRow("ITSAR Version No:", self.itsar_version_field)
        
        layout.addWidget(itsar_group)
        
        # OEM Documents Group
        oem_group = QGroupBox("OEM Supplied Documents")
        oem_layout = QFormLayout(oem_group)
        
        self.guidance_doc_field = QLineEdit()
        self.guidance_doc_field.setPlaceholderText("Enter guidance document...")
        oem_layout.addRow("Guidance Document:", self.guidance_doc_field)
        
        self.fips_doc_field = QLineEdit()
        self.fips_doc_field.setPlaceholderText("Enter FIPS document...")
        oem_layout.addRow("FIPS Document:", self.fips_doc_field)
        
        self.admin_guide_field = QLineEdit()
        self.admin_guide_field.setPlaceholderText("Enter administrative guide...")
        oem_layout.addRow("Administrative Guide:", self.admin_guide_field)
        
        layout.addWidget(oem_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_dut_config_page(self):
        """Create DUT configuration form"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("DUT Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Connection Details Group
        connection_group = QGroupBox("Connection Details")
        connection_layout = QFormLayout(connection_group)
        
        self.machine_ip_field = QLineEdit()
        self.machine_ip_field.setPlaceholderText("e.g., 192.168.1.100")
        connection_layout.addRow("Testing Machine IP:", self.machine_ip_field)
        
        self.target_ip_field = QLineEdit()
        self.target_ip_field.setPlaceholderText("e.g., 192.168.1.1")
        connection_layout.addRow("Target DUT IP:", self.target_ip_field)
        
        self.ssh_username_field = QLineEdit()
        self.ssh_username_field.setPlaceholderText("e.g., admin")
        connection_layout.addRow("SSH Username:", self.ssh_username_field)
        
        self.ssh_password_field = QLineEdit()
        self.ssh_password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.ssh_password_field.setPlaceholderText("Enter SSH password...")
        connection_layout.addRow("SSH Password:", self.ssh_password_field)
        
        layout.addWidget(connection_group)
        
        # Configuration Text Group
        config_group = QGroupBox("Configuration Details")
        config_layout = QVBoxLayout(config_group)
        
        self.dut_configuration_field = QTextEdit()
        self.dut_configuration_field.setPlaceholderText("Enter DUT configuration details...")
        config_layout.addWidget(self.dut_configuration_field)
        
        layout.addWidget(config_group)
        
        # Preconditions Group
        preconditions_group = QGroupBox("Preconditions")
        preconditions_layout = QVBoxLayout(preconditions_group)
        
        self.preconditions_field = QTextEdit()
        self.preconditions_field.setPlaceholderText("Enter test preconditions...")
        preconditions_layout.addWidget(self.preconditions_field)
        
        layout.addWidget(preconditions_group)
        
        # Test Objective Group
        objective_group = QGroupBox("Test Objective")
        objective_layout = QVBoxLayout(objective_group)
        
        self.test_objective_field = QTextEdit()
        self.test_objective_field.setPlaceholderText("Enter test objective...")
        objective_layout.addWidget(self.test_objective_field)
        
        layout.addWidget(objective_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_interface_status_page(self):
        """Create interface status configuration"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Interface Status Details")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Interface Table
        interface_group = QGroupBox("Interface Configuration")
        interface_layout = QVBoxLayout(interface_group)
        
        self.interface_table = QTableWidget(0, 4)
        self.interface_table.setHorizontalHeaderLabels(["Interfaces", "No. of Ports", "Interface Type", "Interface Name"])
        
        # Start with empty table - no hardcoded data
        
        header = self.interface_table.horizontalHeader()
        if header:
            header.setStretchLastSection(True)
        interface_layout.addWidget(self.interface_table)
        
        # Add/Remove buttons
        button_layout = QHBoxLayout()
        add_interface_btn = QPushButton("+ Add Interface")
        add_interface_btn.clicked.connect(self.add_interface_row)
        remove_interface_btn = QPushButton("- Remove Interface")
        remove_interface_btn.clicked.connect(self.remove_interface_row)
        
        button_layout.addWidget(add_interface_btn)
        button_layout.addWidget(remove_interface_btn)
        button_layout.addStretch()
        
        interface_layout.addLayout(button_layout)
        layout.addWidget(interface_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_screenshots_page(self):
        """Create screenshots and evidence management page"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Screenshots & Evidence")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Screenshots Group
        screenshots_group = QGroupBox("Manage Screenshots")
        screenshots_layout = QVBoxLayout(screenshots_group)
        
        # Screenshot list
        self.screenshot_list = QListWidget()
        self.screenshot_list.setMaximumHeight(200)
        screenshots_layout.addWidget(self.screenshot_list)
        
        # Screenshot buttons
        screenshot_buttons = QHBoxLayout()
        
        add_screenshot_btn = QPushButton("📷 Add Screenshot")
        add_screenshot_btn.clicked.connect(self.add_screenshot)
        
        remove_screenshot_btn = QPushButton("🗑️ Remove Screenshot")
        remove_screenshot_btn.clicked.connect(self.remove_screenshot)
        
        annotate_screenshot_btn = QPushButton("✏️ Annotate Screenshot")
        annotate_screenshot_btn.clicked.connect(self.annotate_screenshot)
        
        screenshot_buttons.addWidget(add_screenshot_btn)
        screenshot_buttons.addWidget(remove_screenshot_btn)
        screenshot_buttons.addWidget(annotate_screenshot_btn)
        screenshot_buttons.addStretch()
        
        screenshots_layout.addLayout(screenshot_buttons)
        layout.addWidget(screenshots_group)
        
        # Evidence Format Group
        evidence_group = QGroupBox("Expected Format of Evidence")
        evidence_layout = QVBoxLayout(evidence_group)
        
        self.evidence_format_field = QTextEdit()
        self.evidence_format_field.setPlaceholderText("Enter expected evidence format (e.g., Screenshot of Burp Suite, Nessus, Nmap and Firefox)...")
        evidence_layout.addWidget(self.evidence_format_field)
        
        layout.addWidget(evidence_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_terminal_page(self):
        """Create embedded terminal page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Embedded Terminal")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Terminal controls
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Clear Terminal")
        screenshot_btn = QPushButton("📷 Screenshot Terminal")
        fullscreen_btn = QPushButton("🔍 Toggle Fullscreen")
        
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(screenshot_btn)
        controls_layout.addWidget(fullscreen_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Terminal widget
        self.terminal_widget = TerminalWidget()
        layout.addWidget(self.terminal_widget)
        
        # Connect buttons
        clear_btn.clicked.connect(self.terminal_widget.clear_terminal)
        screenshot_btn.clicked.connect(self.screenshot_terminal)
        fullscreen_btn.clicked.connect(self.toggle_terminal_fullscreen)
        
        self.content_stack.addWidget(page)
        
    def create_test_scenarios_page(self):
        """Create test scenarios management page"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Test Scenarios")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Test Plan Group
        test_plan_group = QGroupBox("Test Plan Overview")
        test_plan_layout = QVBoxLayout(test_plan_group)
        
        self.test_plan_field = QTextEdit()
        self.test_plan_field.setPlaceholderText("Enter overall test plan description...")
        self.test_plan_field.setMaximumHeight(100)
        test_plan_layout.addWidget(self.test_plan_field)
        
        layout.addWidget(test_plan_group)
        
        # Scenarios Group
        scenarios_group = QGroupBox("Test Scenarios")
        scenarios_layout = QVBoxLayout(scenarios_group)
        
        # Scenarios list
        self.scenarios_list = QListWidget()
        self.scenarios_list.setMaximumHeight(200)
        scenarios_layout.addWidget(self.scenarios_list)
        
        # Scenario buttons
        scenario_buttons = QHBoxLayout()
        
        add_scenario_btn = QPushButton("+ Add Scenario")
        add_scenario_btn.clicked.connect(self.add_test_scenario)
        
        edit_scenario_btn = QPushButton("✏️ Edit Scenario")
        edit_scenario_btn.clicked.connect(self.edit_test_scenario)
        
        remove_scenario_btn = QPushButton("- Remove Scenario")
        remove_scenario_btn.clicked.connect(self.remove_test_scenario)
        
        scenario_buttons.addWidget(add_scenario_btn)
        scenario_buttons.addWidget(edit_scenario_btn)
        scenario_buttons.addWidget(remove_scenario_btn)
        scenario_buttons.addStretch()
        
        scenarios_layout.addLayout(scenario_buttons)
        layout.addWidget(scenarios_group)
        
        # Expected Results Group
        results_group = QGroupBox("Expected Results for Pass")
        results_layout = QVBoxLayout(results_group)
        
        self.expected_results_field = QTextEdit()
        self.expected_results_field.setPlaceholderText("Enter expected results for test to pass...")
        results_layout.addWidget(self.expected_results_field)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_test_execution_page(self):
        """Create test execution page"""
        page = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(page)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Test Execution")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Auto-generate info
        info_label = QLabel("Test execution sections are auto-generated from test scenarios. You can also manually add execution blocks.")
        info_label.setStyleSheet("color: #ffcc00; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Generate button
        generate_btn = QPushButton("🔄 Generate from Scenarios")
        generate_btn.clicked.connect(self.generate_execution_from_scenarios)
        layout.addWidget(generate_btn)
        
        # Execution list
        execution_group = QGroupBox("Test Execution Blocks")
        execution_layout = QVBoxLayout(execution_group)
        
        self.execution_list = QListWidget()
        execution_layout.addWidget(self.execution_list)
        
        # Execution buttons
        execution_buttons = QHBoxLayout()
        
        add_execution_btn = QPushButton("+ Add Execution Block")
        add_execution_btn.clicked.connect(self.add_execution_block)
        
        edit_execution_btn = QPushButton("✏️ Edit Block")
        edit_execution_btn.clicked.connect(self.edit_execution_block)
        
        remove_execution_btn = QPushButton("- Remove Block")
        remove_execution_btn.clicked.connect(self.remove_execution_block)
        
        execution_buttons.addWidget(add_execution_btn)
        execution_buttons.addWidget(edit_execution_btn)
        execution_buttons.addWidget(remove_execution_btn)
        execution_buttons.addStretch()
        
        execution_layout.addLayout(execution_buttons)
        layout.addWidget(execution_group)
        
        layout.addStretch()
        self.content_stack.addWidget(scroll_area)
        
    def create_preview_page(self):
        """Create document preview page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Document Preview")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Preview browser (same as sidebar but larger)
        self.main_preview_browser = QTextBrowser()
        layout.addWidget(self.main_preview_browser)
        
        # Update button
        update_preview_btn = QPushButton("🔄 Update Preview")
        update_preview_btn.clicked.connect(self.update_main_preview)
        layout.addWidget(update_preview_btn)
        
        self.content_stack.addWidget(page)
        
    def create_export_page(self):
        """Create export page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title = QLabel("Export Report")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Export options group
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        # File name
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("File Name:"))
        self.filename_field = QLineEdit()
        self.filename_field.setText(f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        filename_layout.addWidget(self.filename_field)
        export_layout.addLayout(filename_layout)
        
        # Export buttons
        export_buttons_layout = QVBoxLayout()
        
        export_docx_btn = QPushButton("📄 Export as DOCX")
        export_docx_btn.clicked.connect(self.export_docx)
        export_docx_btn.setStyleSheet("QPushButton { background-color: #2196f3; }")
        
        export_pdf_btn = QPushButton("📑 Export as PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_pdf_btn.setStyleSheet("QPushButton { background-color: #4caf50; }")
        
        export_buttons_layout.addWidget(export_docx_btn)
        export_buttons_layout.addWidget(export_pdf_btn)
        
        export_layout.addLayout(export_buttons_layout)
        layout.addWidget(export_group)
        
        # Export log
        log_group = QGroupBox("Export Log")
        log_layout = QVBoxLayout(log_group)
        
        self.export_log = QTextEdit()
        self.export_log.setReadOnly(True)
        self.export_log.setMaximumHeight(200)
        log_layout.addWidget(self.export_log)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        self.content_stack.addWidget(page)
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Report', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_report)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open Report', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_report)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save Report', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_report)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        terminal_action = QAction('Open Terminal', self)
        terminal_action.triggered.connect(lambda: self.nav_list.setCurrentRow(4))
        tools_menu.addAction(terminal_action)
        
        screenshot_action = QAction('Take Screenshot', self)
        screenshot_action.triggered.connect(self.add_screenshot)
        tools_menu.addAction(screenshot_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def on_nav_changed(self, current, previous):
        """Handle navigation changes"""
        if current:
            page_name = current.data(Qt.ItemDataRole.UserRole)
            page_index = {
                "report_info": 0,
                "dut_config": 1,
                "interface_status": 2,
                "screenshots": 3,
                "terminal": 4,
                "test_scenarios": 5,
                "test_execution": 6,
                "preview": 7,
                "export": 8
            }.get(page_name, 0)
            
            self.content_stack.setCurrentIndex(page_index)
            self.update_preview()
            
    def add_interface_row(self):
        """Add new interface row"""
        row_count = self.interface_table.rowCount()
        self.interface_table.insertRow(row_count)
        
    def remove_interface_row(self):
        """Remove selected interface row"""
        current_row = self.interface_table.currentRow()
        if current_row >= 0:
            self.interface_table.removeRow(current_row)
            
    def add_screenshot(self):
        """Add screenshot from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Add Screenshot", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            self.screenshots.append(file_path)
            filename = os.path.basename(file_path)
            self.screenshot_list.addItem(filename)
            self.update_preview()
            
    def remove_screenshot(self):
        """Remove selected screenshot"""
        current_row = self.screenshot_list.currentRow()
        if current_row >= 0:
            del self.screenshots[current_row]
            self.screenshot_list.takeItem(current_row)
            self.update_preview()
            
    def annotate_screenshot(self):
        """Open screenshot annotation tool"""
        current_row = self.screenshot_list.currentRow()
        if current_row >= 0:
            screenshot_path = self.screenshots[current_row]
            annotation_tool = ScreenshotTool(screenshot_path, self)
            if annotation_tool.exec() == QDialog.DialogCode.Accepted:
                # Update screenshot with annotated version
                self.screenshots[current_row] = annotation_tool.get_annotated_path()
                self.update_preview()
                
    def screenshot_terminal(self):
        """Take screenshot of terminal"""
        pixmap = self.terminal_widget.grab()
        temp_path = tempfile.mktemp(suffix='.png')
        pixmap.save(temp_path)
        
        # Open annotation tool
        annotation_tool = ScreenshotTool(temp_path, self)
        if annotation_tool.exec() == QDialog.DialogCode.Accepted:
            final_path = annotation_tool.get_annotated_path()
            self.screenshots.append(final_path)
            filename = f"terminal_screenshot_{len(self.screenshots)}.png"
            self.screenshot_list.addItem(filename)
            self.update_preview()
            
    def toggle_terminal_fullscreen(self):
        """Toggle terminal fullscreen mode"""
        # This would need to be implemented based on specific requirements
        pass
        
    def add_test_scenario(self):
        """Add new test scenario"""
        dialog = TestScenarioDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            scenario_data = dialog.get_scenario_data()
            self.test_scenarios.append(scenario_data)
            self.scenarios_list.addItem(scenario_data['title'])
            self.update_preview()
            
    def edit_test_scenario(self):
        """Edit selected test scenario"""
        current_row = self.scenarios_list.currentRow()
        if current_row >= 0:
            scenario_data = self.test_scenarios[current_row]
            dialog = TestScenarioDialog(self, scenario_data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                updated_data = dialog.get_scenario_data()
                self.test_scenarios[current_row] = updated_data
                item = self.scenarios_list.item(current_row)
                if item:
                    item.setText(updated_data['title'])
                self.update_preview()
                
    def remove_test_scenario(self):
        """Remove selected test scenario"""
        current_row = self.scenarios_list.currentRow()
        if current_row >= 0:
            del self.test_scenarios[current_row]
            self.scenarios_list.takeItem(current_row)
            self.update_preview()
            
    def generate_execution_from_scenarios(self):
        """Generate test execution blocks from scenarios"""
        self.execution_list.clear()
        self.execution_blocks = []
        print(f"🔧 DEBUG: Generating execution blocks from {len(self.test_scenarios)} scenarios")
        for i, scenario in enumerate(self.test_scenarios):
            execution_block = {
                'number': f"11.1.{i+1}",
                'name': scenario['title'],
                'description': scenario.get('description', ''),
                'steps': scenario.get('steps', []),
                'observations': '',
                'evidence': ''
            }
            self.execution_blocks.append(execution_block)
            item_text = f"{execution_block['number']} - {execution_block['name']}"
            self.execution_list.addItem(item_text)
        print(f"🔧 DEBUG: Generated {len(self.execution_blocks)} execution blocks")
        self.update_preview()
            
    def add_execution_block(self):
        """Add manual execution block"""
        dialog = ExecutionBlockDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            block_data = dialog.get_block_data()
            self.execution_blocks.append(block_data)
            item_text = f"{block_data['number']} - {block_data['name']}"
            self.execution_list.addItem(item_text)
            
    def edit_execution_block(self):
        """Edit selected execution block"""
        # Implementation would be similar to edit_test_scenario
        pass
        
    def remove_execution_block(self):
        """Remove selected execution block"""
        current_row = self.execution_list.currentRow()
        if current_row >= 0:
            self.execution_list.takeItem(current_row)
            if current_row < len(self.execution_blocks):
                del self.execution_blocks[current_row]
            
    def update_preview(self):
        """Update the preview panel"""
        preview_text = self.document_generator.generate_preview(self.get_all_data())
        self.preview_browser.setHtml(preview_text)
        
    def update_main_preview(self):
        """Update the main preview page"""
        preview_text = self.document_generator.generate_preview(self.get_all_data())
        self.main_preview_browser.setHtml(preview_text)
        
    def get_all_data(self):
        """Collect all form data"""
        data = {
            'test_report': self.test_report_field.text(),
            'itsar_section': self.itsar_section_field.text(),
            'security_req': self.security_req_field.text(),
            'req_description': self.req_description_field.toPlainText(),
            'dut_details': self.dut_details_field.text(),
            'dut_software_version': self.dut_software_version_field.text(),
            'fortiap_hash_os': self.fortiap_hash_os_field.text(),
            'fortigate_hash_os': self.fortigate_hash_os_field.text(),
            'fortiap_hash_config': self.fortiap_hash_config_field.text(),
            'applicable_itsar': self.applicable_itsar_field.text(),
            'itsar_version': self.itsar_version_field.text(),
            'guidance_doc': self.guidance_doc_field.text(),
            'fips_doc': self.fips_doc_field.text(),
            'admin_guide': self.admin_guide_field.text(),
            'machine_ip': self.machine_ip_field.text(),
            'target_ip': self.target_ip_field.text(),
            'ssh_username': self.ssh_username_field.text(),
            'ssh_password': self.ssh_password_field.text(),
            'dut_configuration': self.dut_configuration_field.toPlainText(),
            'preconditions': self.preconditions_field.toPlainText(),
            'test_objective': self.test_objective_field.toPlainText(),
            'interfaces': self.get_interface_data(),
            'screenshots': self.screenshots,
            'evidence_format': self.evidence_format_field.toPlainText(),
            'test_plan': self.test_plan_field.toPlainText(),
            'test_scenarios': self.test_scenarios,
            'expected_results': self.expected_results_field.toPlainText(),
            'execution_blocks': self.execution_blocks
        }
        print(f"🔧 DEBUG: get_all_data() - execution_blocks count: {len(self.execution_blocks)}")
        print(f"🔧 DEBUG: get_all_data() - execution_blocks: {self.execution_blocks}")
        return data
        
    def get_interface_data(self):
        """Get interface table data"""
        interfaces = []
        for row in range(self.interface_table.rowCount()):
            interface = []
            for col in range(self.interface_table.columnCount()):
                item = self.interface_table.item(row, col)
                interface.append(item.text() if item else "")
            interfaces.append(interface)
        return interfaces
        
    def export_docx(self):
        """Export document as DOCX"""
        filename = self.filename_field.text()
        if not filename.endswith('.docx'):
            filename += '.docx'
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DOCX Report",
            filename,
            "Word Documents (*.docx)"
        )
        
        if file_path:
            try:
                data = self.get_all_data()
                self.document_generator.generate_docx(data, file_path)
                self.export_log.append(f"Successfully exported DOCX to: {file_path}")
                QMessageBox.information(self, "Export Complete", f"Document exported successfully to:\n{file_path}")
            except Exception as e:
                self.export_log.append(f"Error exporting DOCX: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"Failed to export document:\n{str(e)}")
                
    def export_pdf(self):
        """Export document as PDF"""
        filename = self.filename_field.text()
        if not filename.endswith('.pdf'):
            filename += '.pdf'
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            filename,
            "PDF Documents (*.pdf)"
        )
        
        if file_path:
            try:
                data = self.get_all_data()
                # First create DOCX, then convert to PDF
                temp_docx = tempfile.mktemp(suffix='.docx')
                self.document_generator.generate_docx(data, temp_docx)
                
                # Convert to PDF using LibreOffice
                subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', os.path.dirname(file_path), temp_docx
                ], check=True)
                
                # Move PDF to final location
                temp_pdf = temp_docx.replace('.docx', '.pdf')
                if os.path.exists(temp_pdf):
                    shutil.move(temp_pdf, file_path)
                    
                # Clean up
                if os.path.exists(temp_docx):
                    os.remove(temp_docx)
                    
                self.export_log.append(f"Successfully exported PDF to: {file_path}")
                QMessageBox.information(self, "Export Complete", f"PDF exported successfully to:\n{file_path}")
            except Exception as e:
                self.export_log.append(f"Error exporting PDF: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")
                
    def new_report(self):
        """Create new report"""
        reply = QMessageBox.question(self, "New Report", "Create a new report? All unsaved changes will be lost.")
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_all_fields()
            
    def open_report(self):
        """Open existing report"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Report",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.load_data(data)
                QMessageBox.information(self, "Open Complete", "Report loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Open Error", f"Failed to open report:\n{str(e)}")
                
    def save_report(self):
        """Save current report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                data = self.get_all_data()
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Save Complete", "Report saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save report:\n{str(e)}")
                
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Security Assessment Report Generator\n\n"
                         "A comprehensive tool for generating security assessment reports\n"
                         "with embedded terminal and screenshot annotation capabilities.\n\n"
                         "Built with PyQt6 and python-docx")
        
    def clear_all_fields(self):
        """Clear all form fields"""
        # Implementation to clear all fields
        pass
        
    def load_data(self, data):
        """Load data into form fields"""
        # Implementation to load data into fields
        pass
        
    def load_config(self):
        """Load application configuration"""
        # Load any saved settings
        pass
        
    def save_config(self):
        """Save application configuration"""
        # Save settings
        pass
        
    def closeEvent(self, a0):
        """Handle application close"""
        self.save_config()
        a0.accept()

class TestScenarioDialog(QDialog):
    """Dialog for creating/editing test scenarios"""
    
    def __init__(self, parent=None, scenario_data=None):
        super().__init__(parent)
        self.scenario_data = scenario_data or {}
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Test Scenario")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Scenario Title:"))
        self.title_field = QLineEdit()
        title_layout.addWidget(self.title_field)
        layout.addLayout(title_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_field = QTextEdit()
        self.description_field.setMaximumHeight(100)
        layout.addWidget(self.description_field)
        
        # Steps
        layout.addWidget(QLabel("Execution Steps:"))
        self.steps_list = QListWidget()
        layout.addWidget(self.steps_list)
        
        # Step buttons
        step_buttons = QHBoxLayout()
        add_step_btn = QPushButton("+ Add Step")
        add_step_btn.clicked.connect(self.add_step)
        remove_step_btn = QPushButton("- Remove Step")
        remove_step_btn.clicked.connect(self.remove_step)
        
        step_buttons.addWidget(add_step_btn)
        step_buttons.addWidget(remove_step_btn)
        step_buttons.addStretch()
        layout.addLayout(step_buttons)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """Load existing scenario data"""
        if self.scenario_data:
            self.title_field.setText(self.scenario_data.get('title', ''))
            self.description_field.setPlainText(self.scenario_data.get('description', ''))
            for step in self.scenario_data.get('steps', []):
                self.steps_list.addItem(step)
                
    def add_step(self):
        """Add new step"""
        text, ok = QInputDialog.getText(self, "Add Step", "Enter step description:")
        if ok and text:
            self.steps_list.addItem(text)
            
    def remove_step(self):
        """Remove selected step"""
        current_row = self.steps_list.currentRow()
        if current_row >= 0:
            self.steps_list.takeItem(current_row)
            
    def get_scenario_data(self):
        """Get scenario data from dialog"""
        steps = []
        for i in range(self.steps_list.count()):
            item = self.steps_list.item(i)
            if item:
                steps.append(item.text())
            
        return {
            'title': self.title_field.text(),
            'description': self.description_field.toPlainText(),
            'steps': steps
        }

class ExecutionBlockDialog(QDialog):
    """Dialog for creating/editing execution blocks"""
    
    def __init__(self, parent=None, block_data=None):
        super().__init__(parent)
        self.block_data = block_data or {}
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Test Execution Block")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Number and Name
        form_layout = QFormLayout()
        
        self.number_field = QLineEdit()
        form_layout.addRow("Test Case Number:", self.number_field)
        
        self.name_field = QLineEdit()
        form_layout.addRow("Test Case Name:", self.name_field)
        
        layout.addLayout(form_layout)
        
        # Description
        layout.addWidget(QLabel("Test Case Description:"))
        self.description_field = QTextEdit()
        self.description_field.setMaximumHeight(100)
        layout.addWidget(self.description_field)
        
        # Observations
        layout.addWidget(QLabel("Test Observations:"))
        self.observations_field = QTextEdit()
        self.observations_field.setMaximumHeight(100)
        layout.addWidget(self.observations_field)
        
        # Evidence
        layout.addWidget(QLabel("Evidence Provided:"))
        self.evidence_field = QTextEdit()
        self.evidence_field.setMaximumHeight(100)
        layout.addWidget(self.evidence_field)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_data(self):
        """Load existing block data"""
        if self.block_data:
            self.number_field.setText(self.block_data.get('number', ''))
            self.name_field.setText(self.block_data.get('name', ''))
            self.description_field.setPlainText(self.block_data.get('description', ''))
            self.observations_field.setPlainText(self.block_data.get('observations', ''))
            self.evidence_field.setPlainText(self.block_data.get('evidence', ''))
            
    def get_block_data(self):
        """Get block data from dialog"""
        return {
            'number': self.number_field.text(),
            'name': self.name_field.text(),
            'description': self.description_field.toPlainText(),
            'observations': self.observations_field.toPlainText(),
            'evidence': self.evidence_field.toPlainText()
        }

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Security Report Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Security Tools")
    
    # Create and show main window
    window = SecurityReportGenerator()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
