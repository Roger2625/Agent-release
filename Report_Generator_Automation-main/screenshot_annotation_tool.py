#!/usr/bin/env python3
"""
Screenshot Annotation Tool - Advanced screenshot capture and annotation
Provides professional screenshot capabilities with drawing tools and annotation features
"""

import os
import sys
import tempfile
import subprocess
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QDialog, QButtonGroup, QRadioButton, QSpinBox, QColorDialog,
    QFileDialog, QMessageBox, QScrollArea, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent, QPaintEvent, QFont

class AnnotationCanvas(QWidget):
    """Canvas widget for drawing annotations on screenshots"""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap.copy()
        self.annotations = []
        self.current_annotation = None
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        
        # Drawing settings
        self.pen_color = QColor(255, 0, 0)  # Red
        self.pen_width = 3
        self.current_tool = 'rectangle'  # rectangle, ellipse, line, arrow, text
        self.text_annotations = []  # Store text annotations separately
        
        self.setMinimumSize(self.current_pixmap.size())
        self.setMaximumSize(self.current_pixmap.size())
        
    def set_pen_color(self, color):
        """Set pen color for annotations"""
        self.pen_color = color
        
    def set_pen_width(self, width):
        """Set pen width for annotations"""
        self.pen_width = width
        
    def set_tool(self, tool):
        """Set current drawing tool"""
        self.current_tool = tool
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing:
            self.end_point = event.position().toPoint()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.position().toPoint()
            
            if self.current_tool == 'text':
                # Handle text annotation
                self.add_text_annotation(event.position().toPoint())
            else:
                # Create drawing annotation
                annotation = {
                    'type': self.current_tool,
                    'start': self.start_point,
                    'end': self.end_point,
                    'color': QColor(self.pen_color),
                    'width': self.pen_width
                }
                
                self.annotations.append(annotation)
                self.apply_annotations()
                self.update()
    
    def add_text_annotation(self, position):
        """Add a text annotation at the specified position"""
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text to add:")
        if ok and text:
            text_annotation = {
                'type': 'text',
                'position': position,
                'text': text,
                'color': QColor(self.pen_color),
                'font_size': max(8, self.pen_width * 3)  # Scale font size with pen width
            }
            
            self.text_annotations.append(text_annotation)
            self.apply_annotations()
            self.update()
            
    def paintEvent(self, event):
        """Paint the canvas"""
        painter = QPainter(self)
        
        # Draw the pixmap
        painter.drawPixmap(0, 0, self.current_pixmap)
        
        # Draw current annotation being drawn
        if self.drawing:
            pen = QPen(self.pen_color, self.pen_width)
            painter.setPen(pen)
            
            if self.current_tool == 'rectangle':
                rect = QRect(self.start_point, self.end_point)
                painter.drawRect(rect)
            elif self.current_tool == 'ellipse':
                rect = QRect(self.start_point, self.end_point)
                painter.drawEllipse(rect)
            elif self.current_tool == 'line':
                painter.drawLine(self.start_point, self.end_point)
            elif self.current_tool == 'arrow':
                self.draw_arrow(painter, self.start_point, self.end_point)
                
    def draw_arrow(self, painter, start, end):
        """Draw a sharp arrow from start to end point"""
        # Draw the main line
        painter.drawLine(start, end)
        
        # Calculate arrow head
        angle = 30  # Arrow head angle in degrees
        length = 15  # Arrow head length
        
        # Calculate direction vector
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # Normalize and calculate perpendicular
        if dx != 0 or dy != 0:
            # Calculate arrow head points
            import math
            angle_rad = math.atan2(dy, dx)
            
            # Left arrow head point
            left_angle = angle_rad + math.radians(angle)
            left_x = end.x() - length * math.cos(left_angle)
            left_y = end.y() - length * math.sin(left_angle)
            
            # Right arrow head point
            right_angle = angle_rad - math.radians(angle)
            right_x = end.x() - length * math.cos(right_angle)
            right_y = end.y() - length * math.sin(right_angle)
            
            # Draw arrow head
            painter.drawLine(end, QPoint(int(left_x), int(left_y)))
            painter.drawLine(end, QPoint(int(right_x), int(right_y)))
    
    def apply_annotations(self):
        """Apply all annotations to the pixmap"""
        self.current_pixmap = self.original_pixmap.copy()
        painter = QPainter(self.current_pixmap)
        
        # Apply drawing annotations
        for annotation in self.annotations:
            pen = QPen(annotation['color'], annotation['width'])
            painter.setPen(pen)
            
            if annotation['type'] == 'rectangle':
                rect = QRect(annotation['start'], annotation['end'])
                painter.drawRect(rect)
            elif annotation['type'] == 'ellipse':
                rect = QRect(annotation['start'], annotation['end'])
                painter.drawEllipse(rect)
            elif annotation['type'] == 'line':
                painter.drawLine(annotation['start'], annotation['end'])
            elif annotation['type'] == 'arrow':
                self.draw_arrow(painter, annotation['start'], annotation['end'])
        
        # Apply text annotations
        for text_annotation in self.text_annotations:
            font = QFont("Arial", text_annotation['font_size'])
            painter.setFont(font)
            painter.setPen(QPen(text_annotation['color'], 1))
            painter.drawText(text_annotation['position'], text_annotation['text'])
        
        painter.end()
        
    def undo_last_annotation(self):
        """Remove the last annotation"""
        if self.annotations:
            self.annotations.pop()
            self.apply_annotations()
            self.update()
            
    def clear_annotations(self):
        """Clear all annotations"""
        self.annotations.clear()
        self.text_annotations.clear()
        self.current_pixmap = self.original_pixmap.copy()
        self.update()
        
    def get_annotated_pixmap(self):
        """Get the current pixmap with annotations"""
        return self.current_pixmap

class ScreenshotAnnotationDialog(QDialog):
    """Dialog for annotating screenshots"""
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.annotated_path = None
        self.init_ui()
        self.load_image()
        
    def init_ui(self):
        """Initialize the annotation dialog UI"""
        self.setWindowTitle("Annotate Screenshot")
        self.setGeometry(100, 100, 1000, 700)
        
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Tool selection
        tool_label = QLabel("Tool:")
        toolbar.addWidget(tool_label)
        
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["Rectangle", "Ellipse", "Line", "Arrow", "Text"])
        self.tool_combo.setCurrentText("Arrow")  # Set arrow as default
        self.tool_combo.currentTextChanged.connect(self.set_tool)
        toolbar.addWidget(self.tool_combo)
        
        # Color selection
        color_label = QLabel("Color:")
        toolbar.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Red", "Green", "Blue", "Yellow", "Orange", "Purple", "White"])
        self.color_combo.setCurrentText("Red")
        self.color_combo.currentTextChanged.connect(self.set_color)
        toolbar.addWidget(self.color_combo)
        
        # Width selection
        width_label = QLabel("Width:")
        toolbar.addWidget(width_label)
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 10)
        self.width_spinbox.setValue(3)
        self.width_spinbox.valueChanged.connect(self.set_width)
        toolbar.addWidget(self.width_spinbox)
        
        # Undo button
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo_annotation)
        toolbar.addWidget(undo_btn)
        
        # Clear button
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_annotations)
        toolbar.addWidget(clear_btn)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_annotated)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Screenshot display area
        scroll_area = QScrollArea()
        self.canvas = AnnotationCanvas(QPixmap(self.image_path), self)
        scroll_area.setWidget(self.canvas)
        layout.addWidget(scroll_area)
        
    def load_image(self):
        """Load the image into the canvas"""
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                self.canvas = AnnotationCanvas(pixmap, self)
                # Update the scroll area widget
                scroll_area = self.findChild(QScrollArea)
                if scroll_area:
                    scroll_area.setWidget(self.canvas)
        
    def set_tool(self, tool_name):
        """Set the current drawing tool"""
        tool_map = {
            "Rectangle": "rectangle",
            "Ellipse": "ellipse", 
            "Line": "line",
            "Arrow": "arrow",
            "Text": "text"
        }
        self.canvas.set_tool(tool_map.get(tool_name, "rectangle"))
        
    def set_color(self, color_name):
        """Set the drawing color"""
        color_map = {
            "Red": QColor(255, 0, 0),
            "Green": QColor(0, 255, 0),
            "Blue": QColor(0, 0, 255),
            "Yellow": QColor(255, 255, 0),
            "Orange": QColor(255, 165, 0),
            "Purple": QColor(128, 0, 128),
            "White": QColor(255, 255, 255)
        }
        self.canvas.set_pen_color(color_map.get(color_name, QColor(255, 0, 0)))
        
    def set_width(self, width):
        """Set the pen width"""
        self.canvas.set_pen_width(width)
        
    def undo_annotation(self):
        """Undo the last annotation"""
        self.canvas.undo_last_annotation()
        
    def clear_annotations(self):
        """Clear all annotations"""
        self.canvas.clear_annotations()
        
    def save_annotated(self):
        """Save the annotated screenshot"""
        try:
            annotated_pixmap = self.canvas.get_annotated_pixmap()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            
            # Remove _annotated suffix if it exists
            if base_name.endswith('_annotated'):
                base_name = base_name[:-10]
            
            filename = f"{base_name}_annotated_{timestamp}.png"
            
            # Save the annotated screenshot
            if annotated_pixmap.save(filename):
                self.annotated_path = filename
                QMessageBox.information(self, "Success", f"Annotated screenshot saved as: {filename}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save annotated screenshot")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save annotated screenshot: {str(e)}")
    
    def get_annotated_path(self):
        """Get the path of the annotated screenshot"""
        return self.annotated_path
    
    def accept(self):
        """Handle dialog acceptance"""
        if not self.annotated_path:
            # Use original image if no annotations
            self.annotated_path = self.image_path
            
        super().accept()

class ScreenshotCaptureTool:
    """Enhanced screenshot capture tool with annotation capabilities"""
    
    @staticmethod
    def get_incremental_filename(base_name):
        """Generate incremental filename (e.g., ifconfig.png, ifconfig_1.png, ifconfig_2.png)"""
        if not base_name:
            return None
            
        # Clean the base name for filename
        clean_name = re.sub(r'[^\w\-_]', '_', base_name)
        
        # Check if base file exists
        base_filename = f"{clean_name}.png"
        if not os.path.exists(base_filename):
            return base_filename
        
        # Find the next available number
        counter = 1
        while True:
            filename = f"{clean_name}_{counter}.png"
            if not os.path.exists(filename):
                return filename
            counter += 1
    
    @staticmethod
    def capture_screenshot_with_annotation(parent_widget=None, command_name=None):
        """Capture screenshot with annotation capabilities and hide mouse pointer"""
        try:
            # Hide mouse pointer during capture
            hide_cursor_commands = [
                "unclutter -idle 0.1 -root &",
                "xsetroot -cursor_name left_ptr &",
                "xdotool mousemove 9999 9999 &"
            ]
            
            # Try to hide cursor
            for cmd in hide_cursor_commands:
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=2)
                except:
                    continue
            
            # Wait a moment for cursor to hide
            import time
            time.sleep(0.2)
            
            # Try different screenshot methods with mouse pointer hiding
            screenshot_commands = [
                "gnome-screenshot -f /tmp/temp_screenshot.png --hide-cursor",
                "scrot /tmp/temp_screenshot.png -p",  # -p hides cursor
                "import -window root /tmp/temp_screenshot.png",
                "screencapture /tmp/temp_screenshot.png"  # macOS
            ]
            
            temp_path = "/tmp/temp_screenshot.png"
            screenshot_captured = False
            
            for cmd in screenshot_commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                    if result.returncode == 0 and os.path.exists(temp_path):
                        screenshot_captured = True
                        break
                except:
                    continue
            
            if not screenshot_captured:
                # Fallback: capture specific window or widget
                if parent_widget:
                    pixmap = parent_widget.grab()
                    temp_path = tempfile.mktemp(suffix='.png')
                    pixmap.save(temp_path)
                    screenshot_captured = True
            
            # Restore mouse pointer
            try:
                subprocess.run("killall unclutter", shell=True, capture_output=True)
            except:
                pass
            
            if screenshot_captured and os.path.exists(temp_path):
                # Open annotation dialog
                annotation_dialog = ScreenshotAnnotationDialog(temp_path, parent_widget)
                if annotation_dialog.exec() == QDialog.DialogCode.Accepted:
                    return annotation_dialog.get_annotated_path()
                else:
                    # Clean up temp file if user cancelled
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return None
            else:
                raise Exception("Could not capture screenshot")
                
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Screenshot Error", f"Failed to capture screenshot:\n{str(e)}")
            return None
    
    @staticmethod
    def capture_terminal_output_screenshot(terminal_widget, command_name, parent_widget=None):
        """Capture full terminal output screenshot with proper naming and no cut-off"""
        try:
            # Create a temporary widget to render the full command output
            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            
            # Create text display with terminal styling
            text_display = QTextEdit()
            text_display.setStyleSheet("""
                QTextEdit {
                    background-color: #000000;
                    color: #ffffff;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    border: none;
                    padding: 10px;
                }
            """)
            text_display.setReadOnly(True)
            
            # Get the full terminal content
            terminal_content = terminal_widget.toPlainText()
            
            # Find the command and its output
            if command_name and command_name in terminal_content:
                # Find the line with the command
                lines = terminal_content.split('\n')
                command_line_index = -1
                
                for i, line in enumerate(lines):
                    if f"$ {command_name}" in line or line.strip() == command_name:
                        command_line_index = i
                        break
                
                if command_line_index >= 0:
                    # Get everything from the command line to the end
                    output_lines = lines[command_line_index:]
                    full_output = '\n'.join(output_lines)
                else:
                    # If command not found, use last few lines
                    full_output = '\n'.join(lines[-20:])  # Last 20 lines
            else:
                # Use the full terminal content
                full_output = terminal_content
            
            # Set the content
            text_display.setPlainText(full_output)
            
            # Calculate proper size based on content
            doc_height = text_display.document().size().height()
            content_height = int(doc_height) + 20  # Add padding
            
            # Set size to accommodate full content
            text_display.setFixedSize(800, max(400, content_height))
            
            temp_layout.addWidget(text_display)
            temp_widget.show()
            
            # Hide mouse pointer during capture
            try:
                subprocess.run("unclutter -idle 0.1 -root &", shell=True, capture_output=True, timeout=2)
                import time
                time.sleep(0.2)
            except:
                pass
            
            # Capture screenshot
            pixmap = text_display.grab()
            temp_widget.close()
            
            # Restore mouse pointer
            try:
                subprocess.run("killall unclutter", shell=True, capture_output=True)
            except:
                pass
            
            # Save with incremental command name
            if command_name:
                filename = ScreenshotCaptureTool.get_incremental_filename(command_name)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"terminal_output_{timestamp}.png"
            
            # Save the screenshot
            temp_path = tempfile.mktemp(suffix='.png')
            pixmap.save(temp_path)
            
            # Open annotation dialog
            annotation_dialog = ScreenshotAnnotationDialog(temp_path, parent_widget)
            if annotation_dialog.exec() == QDialog.DialogCode.Accepted:
                return annotation_dialog.get_annotated_path()
            else:
                # Clean up temp file if user cancelled
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
                
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Screenshot Error", f"Failed to capture terminal screenshot:\n{str(e)}")
            return None
    
    @staticmethod
    def capture_widget_screenshot(widget, parent_widget=None):
        """Capture screenshot of a specific widget with annotation"""
        try:
            # Hide mouse pointer during capture
            try:
                subprocess.run("unclutter -idle 0.1 -root &", shell=True, capture_output=True, timeout=2)
                import time
                time.sleep(0.2)
            except:
                pass
            
            # Capture the widget
            pixmap = widget.grab()
            temp_path = tempfile.mktemp(suffix='.png')
            pixmap.save(temp_path)
            
            # Restore mouse pointer
            try:
                subprocess.run("killall unclutter", shell=True, capture_output=True)
            except:
                pass
            
            # Open annotation dialog
            annotation_dialog = ScreenshotAnnotationDialog(temp_path, parent_widget)
            if annotation_dialog.exec() == QDialog.DialogCode.Accepted:
                return annotation_dialog.get_annotated_path()
            else:
                # Clean up temp file if user cancelled
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
                
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Screenshot Error", f"Failed to capture widget screenshot:\n{str(e)}")
            return None
    
    @staticmethod
    def annotate_existing_screenshot(image_path, parent_widget=None):
        """Annotate an existing screenshot file"""
        try:
            if not os.path.exists(image_path):
                raise Exception(f"Image file not found: {image_path}")
            
            # Open annotation dialog
            annotation_dialog = ScreenshotAnnotationDialog(image_path, parent_widget)
            if annotation_dialog.exec() == QDialog.DialogCode.Accepted:
                return annotation_dialog.get_annotated_path()
            else:
                return None
                
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Annotation Error", f"Failed to annotate screenshot:\n{str(e)}")
            return None 