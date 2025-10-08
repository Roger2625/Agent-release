#!/usr/bin/env python3
"""
Example: How to integrate Section 8 Placeholder Manager with existing code
"""

# Import the existing EnhancedExportImport class
from enhanced_export_import import EnhancedExportImport

# Import the placeholder manager
from section8_placeholder_manager import integrate_section8_placeholder_manager

# Create your EnhancedExportImport instance as usual
test_case_folder = "your_test_case_folder"
exporter = EnhancedExportImport(test_case_folder)

# Integrate the Section 8 Placeholder Manager
exporter = integrate_section8_placeholder_manager(exporter, test_case_folder)

# Now all Section 8 Test Plan processing methods are enhanced with placeholder management
# The exporter will automatically:
# - Add placeholder_content_management to all Section 8 data
# - Track placeholder context and associations
# - Provide enhanced placeholder processing

# Export your configuration as usual
app_data = {}  # Your application data here
success, message = exporter.export_complete_configuration(app_data)

if success:
            print("Configuration exported with enhanced Section 8 placeholder management")
    
    # Generate a placeholder report
    placeholder_manager = exporter.section8_placeholder_manager
    report_path = f"{test_case_folder}/section8_placeholder_report.json"
    
    if placeholder_manager.export_placeholder_report(exporter.processed_data, report_path):
        print(f"Section 8 placeholder report generated: {report_path}")
else:
            print(f"Export failed: {message}")
