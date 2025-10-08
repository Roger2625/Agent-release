#!/usr/bin/env python3
"""
Script Upload Widget - Replaces image uploads with Python script uploads
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QTextEdit, QLineEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from script_executor import ScriptManager, SafeScriptExecutor

class ScriptUploadWidget(QWidget):
    """Widget for uploading and managing Python scripts"""
    
    script_uploaded = pyqtSignal(str)  # Emits script_id when uploaded
    script_removed = pyqtSignal(str)   # Emits script_id when removed
    script_executed = pyqtSignal(str, dict)  # Emits script_id and execution result
    
    def __init__(self, section_name=None, step_name=None, parent=None):
        super().__init__(parent)
        self.section_name = section_name
        self.step_name = step_name
        self.script_manager = ScriptManager()
        self.executor = SafeScriptExecutor()
        
        self.uploaded_scripts = {}  # {script_id: script_info}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Python Script Upload")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Upload button
        upload_btn = QPushButton("📁 Upload Python Script (.py)")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        upload_btn.clicked.connect(self.upload_script)
        layout.addWidget(upload_btn)
        
        # Scripts container
        self.scripts_container = QWidget()
        self.scripts_layout = QVBoxLayout(self.scripts_container)
        layout.addWidget(self.scripts_container)
        
        # Info label
        info_label = QLabel("Upload Python scripts (.py files) for automated test execution")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
    
    def upload_script(self):
        """Upload a Python script file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python Script",
            "",
            "Python Files (*.py)"
        )
        
        if file_path:
            try:
                # Validate file extension
                if not file_path.lower().endswith('.py'):
                    QMessageBox.warning(self, "Invalid File", "Please select a Python script (.py file)")
                    return
                
                # Upload script
                script_id = self.script_manager.upload_script(
                    file_path, 
                    self.section_name, 
                    self.step_name
                )
                
                # Add to local tracking
                script_info = self.script_manager.get_script_info(script_id)
                self.uploaded_scripts[script_id] = script_info
                
                # Create script display widget
                self.create_script_widget(script_id, script_info)
                
                # Emit signal
                self.script_uploaded.emit(script_id)
                
                QMessageBox.information(
                    self, 
                    "Script Uploaded", 
                    f"Script '{os.path.basename(file_path)}' uploaded successfully"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Upload Error", 
                    f"Failed to upload script: {str(e)}"
                )
    
    def create_script_widget(self, script_id, script_info):
        """Create a widget to display script information and controls"""
        script_widget = QGroupBox(f"📄 {script_info['filename']}")
        script_layout = QVBoxLayout(script_widget)
        
        # Script info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"File: {script_info['filename']}"))
        info_layout.addStretch()
        
        # Execute button
        execute_btn = QPushButton("▶ Execute")
        execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        execute_btn.clicked.connect(lambda: self.execute_script(script_id))
        info_layout.addWidget(execute_btn)
        
        # Remove button
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_script(script_id))
        info_layout.addWidget(remove_btn)
        
        script_layout.addLayout(info_layout)
        
        # Output display area
        output_label = QLabel("Execution Output:")
        script_layout.addWidget(output_label)
        
        output_text = QTextEdit()
        output_text.setMaximumHeight(100)
        output_text.setReadOnly(True)
        output_text.setPlaceholderText("Script output will appear here after execution...")
        script_layout.addWidget(output_text)
        
        # Store references
        script_info['widget'] = script_widget
        script_info['output_text'] = output_text
        script_info['execute_btn'] = execute_btn
        
        # Add to container
        self.scripts_layout.addWidget(script_widget)
    
    def execute_script(self, script_id):
        """Execute a specific script"""
        try:
            # Update button state
            script_info = self.uploaded_scripts[script_id]
            script_info['execute_btn'].setText("⏳ Executing...")
            script_info['execute_btn'].setEnabled(False)
            
            # Clear previous output
            script_info['output_text'].clear()
            script_info['output_text'].append("Executing script...\n")
            
            # Execute script
            result = self.executor.execute_script(script_info['stored_path'])
            
            # Display results
            output_text = script_info['output_text']
            
            if result.success:
                output_text.append("✅ Script executed successfully!\n")
                output_text.append(f"Execution time: {result.execution_time:.2f} seconds\n")
                output_text.append(f"Exit code: {result.exit_code}\n")
                
                if result.stdout:
                    output_text.append("--- STDOUT ---\n")
                    output_text.append(result.stdout)
                
                if result.stderr:
                    output_text.append("--- STDERR ---\n")
                    output_text.append(result.stderr)
            else:
                output_text.append("❌ Script execution failed!\n")
                output_text.append(f"Error: {result.error_message}\n")
                output_text.append(f"Exit code: {result.exit_code}\n")
                
                if result.stderr:
                    output_text.append("--- ERROR OUTPUT ---\n")
                    output_text.append(result.stderr)
            
            # Emit signal
            self.script_executed.emit(script_id, {
                'success': result.success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': result.execution_time,
                'exit_code': result.exit_code,
                'error_message': result.error_message
            })
            
        except Exception as e:
            script_info['output_text'].append(f"❌ Execution error: {str(e)}\n")
        finally:
            # Restore button state
            script_info['execute_btn'].setText("▶ Execute")
            script_info['execute_btn'].setEnabled(True)
    
    def remove_script(self, script_id):
        """Remove a script"""
        script_info = self.uploaded_scripts[script_id]
        
        reply = QMessageBox.question(
            self,
            "Remove Script",
            f"Are you sure you want to remove '{script_info['filename']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove from storage
                self.script_manager.remove_script(script_id)
                
                # Remove widget
                script_info['widget'].setParent(None)
                
                # Remove from local tracking
                del self.uploaded_scripts[script_id]
                
                # Emit signal
                self.script_removed.emit(script_id)
                
                QMessageBox.information(
                    self, 
                    "Script Removed", 
                    f"Script '{script_info['filename']}' removed successfully"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Remove Error", 
                    f"Failed to remove script: {str(e)}"
                )
    
    def execute_all_scripts(self):
        """Execute all uploaded scripts sequentially"""
        if not self.uploaded_scripts:
            QMessageBox.information(self, "No Scripts", "No scripts to execute")
            return
        
        try:
            # Get all script paths in order
            script_paths = [
                script_info['stored_path'] 
                for script_info in self.uploaded_scripts.values()
            ]
            
            # Sort by upload time
            script_paths.sort(key=lambda x: self.uploaded_scripts.get(
                os.path.basename(x).split('_')[0], {}).get('upload_time', 0)
            )
            
            # Execute sequentially
            results = self.executor.execute_scripts_sequentially(script_paths)
            
            # Display summary
            successful = sum(1 for r in results if r.success)
            total = len(results)
            
            QMessageBox.information(
                self,
                "Execution Complete",
                f"Executed {total} scripts: {successful} successful, {total - successful} failed"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Execution Error",
                f"Failed to execute scripts: {str(e)}"
            )
    
    def get_uploaded_scripts(self):
        """Get all uploaded scripts"""
        return list(self.uploaded_scripts.values())
    
    def get_script_execution_results(self):
        """Get execution results for all scripts"""
        results = {}
        for script_id, script_info in self.uploaded_scripts.items():
            # This would need to be implemented to store actual execution results
            # For now, return basic info
            results[script_id] = {
                'filename': script_info['filename'],
                'section_name': script_info['section_name'],
                'step_name': script_info['step_name']
            }
        return results 