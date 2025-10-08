#!/usr/bin/env python3
"""
Fix for Sections 1-7 Empty Data Issue

This script provides a targeted fix for the issue where sections 1-7 
show empty arrays for images and scripts in the exported JSON.

The issue is that the current export process is not properly collecting
the uploaded images and scripts from the Section 8 Test Plan area when
they are uploaded to sections 1 and 3.
"""

import os
import json

def fix_enhanced_export_import():
    """
    Apply the fix to enhanced_export_import.py to properly handle sections 1-7 data
    """
    
    enhanced_export_import_path = "enhanced_export_import.py"
    
    if not os.path.exists(enhanced_export_import_path):
        print(f"❌ {enhanced_export_import_path} not found")
        return False
    
    # Read the current file
    with open(enhanced_export_import_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if "DEBUG: _process_sections_1_7_per_field enhanced with data collection" in content:
        print("✅ Fix already applied to enhanced_export_import.py")
        return True
    
    # Find the _process_sections_1_7_per_field method
    method_start = content.find("def _process_sections_1_7_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:")
    
    if method_start == -1:
        print("❌ Could not find _process_sections_1_7_per_field method")
        return False
    
    # Find the end of the method (next def or class at same indentation level)
    lines = content.split('\n')
    start_line = None
    for i, line in enumerate(lines):
        if "_process_sections_1_7_per_field" in line and "def" in line:
            start_line = i
            break
    
    if start_line is None:
        print("❌ Could not find method start line")
        return False
    
    # Find the end of the method
    end_line = len(lines)
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        # Look for next method or end of class
        if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
            end_line = i
            break
        elif line.strip().startswith('def ') and not line.startswith('        def'):
            end_line = i
            break
    
    # Create the enhanced method
    enhanced_method = '''    def _process_sections_1_7_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sections 1-7 with per-field storage"""
        print(f"DEBUG: _process_sections_1_7_per_field enhanced with data collection")
        
        sections_1_7 = app_data.get("sections_1_7", {})
        processed_sections = {}
        
        # Debug: Print what we received
        print(f"DEBUG: app_data sections_1_7 keys: {list(sections_1_7.keys()) if isinstance(sections_1_7, dict) else 'Not a dict'}")
        
        # Try to get data from parent_app if available
        if hasattr(self, 'parent_app') and self.parent_app:
            print(f"DEBUG: parent_app available, trying to collect fresh data")
            
            # Look for sections_1_7_manager
            if hasattr(self.parent_app, 'sections_1_7_manager'):
                try:
                    print(f"DEBUG: Found sections_1_7_manager, collecting fresh data")
                    fresh_data = self.collect_sections_1_7_data(self.parent_app.sections_1_7_manager)
                    if fresh_data:
                        print(f"DEBUG: Got fresh sections 1-7 data: {list(fresh_data.keys())}")
                        sections_1_7.update(fresh_data)
                    else:
                        print(f"DEBUG: No fresh data collected")
                except Exception as e:
                    print(f"DEBUG: Error collecting fresh data: {e}")
        
        # Ensure sections_1_7 is a dictionary
        if not isinstance(sections_1_7, dict):
            print(f"WARNING: sections_1_7 is not a dictionary: {type(sections_1_7)}")
            return processed_sections
        
        for section_key, section_data in sections_1_7.items():
            # Handle non-dictionary section data
            if not isinstance(section_data, dict):
                print(f"WARNING: Section {section_key} data is not a dictionary: {type(section_data)}")
                processed_sections[section_key] = section_data
                continue
            
            processed_section = section_data.copy()
            
            # Process section_4 and section_5 pairs
            if section_key in ["section_4", "section_5"] and "pairs" in section_data:
                processed_pairs = []
                pairs_data = section_data["pairs"]
                
                # Ensure pairs is a list
                if not isinstance(pairs_data, list):
                    print(f"WARNING: Section {section_key} pairs is not a list: {type(pairs_data)}")
                    processed_section["pairs"] = []
                else:
                    for pair in pairs_data:
                        if isinstance(pair, dict):
                            processed_pair = {
                                "text": pair.get("text", ""),
                                "images": self._process_images_for_field(pair.get("images", [])),
                                "scripts": self._process_scripts_for_field(pair.get("scripts", [])),
                                "placeholders": self._process_placeholders_for_field(pair.get("placeholders", []))
                            }
                            processed_pairs.append(processed_pair)
                        else:
                            print(f"WARNING: Pair in section {section_key} is not a dictionary: {type(pair)}")
                    
                    processed_section["pairs"] = processed_pairs
            
            # Process sections 1, 2, 3, 6, 7
            elif section_key in ["section_1", "section_2", "section_3", "section_6", "section_7"]:
                processed_section.update({
                    "heading": section_data.get("heading", ""),
                    "content": section_data.get("content", ""),
                    "text": section_data.get("text", ""),
                    "images": self._process_images_for_field(section_data.get("images", [])),
                    "scripts": self._process_scripts_for_field(section_data.get("scripts", [])),
                    "placeholders": self._process_placeholders_for_field(section_data.get("placeholders", []))
                })
                
                # Debug: Print processed data for sections 1 and 3
                if section_key in ["section_1", "section_3"]:
                    print(f"DEBUG: Processed {section_key}:")
                    print(f"  Images: {len(processed_section['images'])} items")
                    print(f"  Scripts: {len(processed_section['scripts'])} items")
                    if processed_section['images']:
                        print(f"  First image: {processed_section['images'][0]}")
                    if processed_section['scripts']:
                        print(f"  First script: {processed_section['scripts'][0]}")
            
            processed_sections[section_key] = processed_section
        
        print(f"DEBUG: Final processed sections 1-7: {list(processed_sections.keys())}")
        return processed_sections'''
    
    # Replace the method
    new_lines = lines[:start_line] + enhanced_method.split('\n') + lines[end_line:]
    new_content = '\n'.join(new_lines)
    
    # Write the updated file
    with open(enhanced_export_import_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Applied fix to enhanced_export_import.py")
    print("📋 The fix adds:")
    print("  - Enhanced data collection from UI")
    print("  - Debug logging for sections 1-7 processing")
    print("  - Better handling of empty/missing data")
    print("  - Fresh data collection from sections_1_7_manager")
    
    return True

def verify_fix():
    """
    Verify that the fix was applied correctly
    """
    enhanced_export_import_path = "enhanced_export_import.py"
    
    if not os.path.exists(enhanced_export_import_path):
        print(f"❌ {enhanced_export_import_path} not found")
        return False
    
    with open(enhanced_export_import_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "DEBUG: _process_sections_1_7_per_field enhanced with data collection" in content:
        print("✅ Fix is present in enhanced_export_import.py")
        return True
    else:
        print("❌ Fix is not present in enhanced_export_import.py")
        return False

if __name__ == "__main__":
    print("🔧 Applying Sections 1-7 Empty Data Fix")
    print("=" * 50)
    
    if fix_enhanced_export_import():
        print("\n🔍 Verifying fix...")
        if verify_fix():
            print("\n✅ Fix applied successfully!")
            print("\n📝 What this fix does:")
            print("1. Enhances the _process_sections_1_7_per_field method")
            print("2. Adds fresh data collection from the UI sections_1_7_manager")
            print("3. Provides debug logging to track data processing")
            print("4. Ensures uploaded images and scripts are properly captured")
            print("\n🎯 This should resolve the issue where sections 1 and 3")
            print("   show empty arrays for images and scripts in the exported JSON.")
            print("\nThe fix will take effect the next time you export a test case.")
        else:
            print("\n❌ Fix verification failed")
    else:
        print("\n❌ Failed to apply fix")
