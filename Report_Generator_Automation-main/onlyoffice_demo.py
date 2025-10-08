#!/usr/bin/env python3
"""
Demo application showing OnlyOffice Desktop Embedder integration
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from onlyoffice_desktop_embedder import OnlyOfficeDesktopEmbedder


class OnlyOfficeDemoApp(QMainWindow):
    """Demo application for OnlyOffice Desktop Embedder"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnlyOffice Desktop Embedder Demo")
        self.setGeometry(100, 100, 1400, 900)
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("OnlyOffice Desktop Embedder Demo")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; padding: 20px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Description
        description = QLabel(
            "This demo shows how to embed OnlyOffice Desktop Editors directly into a PyQt6 application.\n"
            "The document will open with full fidelity - headers, footers, and watermarks intact."
        )
        description.setStyleSheet("font-size: 14px; color: #7f8c8d; padding: 10px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)
        
        # OnlyOffice embedder widget
        self.embedder = OnlyOfficeDesktopEmbedder()
        layout.addWidget(self.embedder)
        
        # Footer
        footer = QLabel("OnlyOffice Desktop Editors must be installed for this to work.")
        footer.setStyleSheet("font-size: 12px; color: #95a5a6; padding: 10px;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the demo window
    demo = OnlyOfficeDemoApp()
    demo.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
