#!/usr/bin/env python3
"""
Test script for Script Automation Upload functionality
"""

import sys
import os
import tempfile
import zipfile
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt

# Add the current directory to the path to import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from export_code_and_files_page import ScriptAutomationUploadDialog

class TestMainWindow(QMainWindow):
    """Test main window for the script automation upload dialog"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Script Automation Upload Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add title
        title_label = QLabel("Script Automation Upload Test")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        # Add description
        desc_label = QLabel("Click the button below to test the Script Automation Upload dialog")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(desc_label)
        
        # Add test button
        test_btn = QPushButton("Test Script Automation Upload")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        test_btn.clicked.connect(self.test_upload_dialog)
        layout.addWidget(test_btn)
        
        # Add create test zip button
        create_zip_btn = QPushButton("Create Test ZIP File")
        create_zip_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        create_zip_btn.clicked.connect(self.create_test_zip)
        layout.addWidget(create_zip_btn)
        
        # Add clear memory button
        clear_memory_btn = QPushButton("Clear Last Upload Memory")
        clear_memory_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)
        clear_memory_btn.clicked.connect(self.clear_memory)
        layout.addWidget(clear_memory_btn)
        
        layout.addStretch()
    
    def test_upload_dialog(self):
        """Test the script automation upload dialog"""
        try:
            dialog = ScriptAutomationUploadDialog(self)
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                print("Upload dialog accepted!")
            else:
                print("Upload dialog cancelled.")
        except Exception as e:
            print(f"Error testing upload dialog: {e}")
    
    def create_test_zip(self):
        """Create a test ZIP file with sample script files"""
        try:
            # Create temporary directory for test files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create sample script files
                test_files = {
                    'main_script.py': '''#!/usr/bin/env python3
"""
Main automation script
"""

def main():
    print("Hello from main script!")
    return True

if __name__ == "__main__":
    main()
''',
                    'utils.py': '''#!/usr/bin/env python3
"""
Utility functions
"""

def helper_function():
    return "Helper function called"

def another_function():
    return "Another function called"
''',
                    'config.json': '''{
    "name": "Test Automation",
    "version": "1.0.0",
    "settings": {
        "debug": true,
        "timeout": 30
    }
}''',
                    'README.md': '''# Test Automation Scripts

This is a test ZIP file containing sample automation scripts.

## Files:
- main_script.py: Main automation script
- utils.py: Utility functions
- config.json: Configuration file
- README.md: This file
'''
                }
                
                # Write test files
                for filename, content in test_files.items():
                    file_path = os.path.join(temp_dir, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                # Create ZIP file
                zip_path = os.path.join(os.getcwd(), "test_automation_scripts.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                print(f"Test ZIP file created: {zip_path}")
                print("You can now use this ZIP file to test the upload functionality.")
                
        except Exception as e:
            print(f"Error creating test ZIP: {e}")
    
    def clear_memory(self):
        """Clear the last uploaded ZIP memory"""
        try:
            import os
            import json
            from PyQt6.QtWidgets import QMessageBox
            
            config_file = os.path.join(os.getcwd(), "last_uploaded_zip.json")
            if os.path.exists(config_file):
                os.remove(config_file)
                print("Last uploaded ZIP memory cleared successfully!")
                QMessageBox.information(self, "Success", "Last uploaded ZIP memory has been cleared.")
            else:
                print("No last uploaded ZIP memory found.")
                QMessageBox.information(self, "Info", "No last uploaded ZIP memory found.")
                
        except Exception as e:
            print(f"Error clearing memory: {e}")
            QMessageBox.critical(self, "Error", f"Failed to clear memory: {str(e)}")

def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QWidget {
            font-family: Arial, sans-serif;
        }
    """)
    
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
