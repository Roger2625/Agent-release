#!/usr/bin/env python3
"""
Simple test script for Section 8 Placeholder UI integration
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the placeholder UI
    from section8_placeholder_ui import Section8PlaceholderUI
    
    # Import PyQt6 for testing
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Section 8 Placeholder UI Test")
            self.setGeometry(100, 100, 800, 600)
            
            # Create central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Create layout
            layout = QVBoxLayout(central_widget)
            
            # Add the placeholder UI
            self.placeholder_ui = Section8PlaceholderUI(self)
            layout.addWidget(self.placeholder_ui)
            
            print("[OK] Test window created successfully")
    
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        
        # Create test window
        window = TestWindow()
        window.show()
        
        print("[OK] Section 8 Placeholder UI test window displayed")
        print("You can now test the placeholder management functionality")
        
        sys.exit(app.exec())
        
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Make sure PyQt6 is installed and section8_placeholder_ui.py is in the same directory")
except Exception as e:
    print(f"[ERROR] Error: {e}")
