#!/usr/bin/env python3
"""
Test script to verify that the sections 1-7 path fix works correctly.
This script tests that uploaded scripts and images in sections 1-7 are properly
saved as paths in the JSON for import.
"""

import os
import json
import tempfile
import shutil
from enhanced_export_import import EnhancedExportImport

def create_test_sections_1_7_data():
    """Create test data with sections 1-7 containing images and scripts"""
    return {
        "test_case_name": "Sections 1-7 Path Fix Test",
        "sections_1_7": {
            "section_1": {
                "heading": "ITSAR Section No & Name",
                "content": "Section 1.9 Vulnerability Testing Requirements",
                "text": "Section 1.9 Vulnerability Testing Requirements",
                "images": [
                    {
                        "path": "/tmp/test_section1_image.png",
                        "filename": "test_section1_image.png",
                        "original_filename": "test_section1_image.png",
                        "description": "Section 1 Test Image"
                    }
                ],
                "scripts": [
                    {
                        "path": "/tmp/test_section1_script.py",
                        "filename": "test_section1_script.py",
                        "original_filename": "test_section1_script.py",
                        "description": "Section 1 Test Script",
                        "is_pasted": False
                    }
                ]
            },
            "section_3": {
                "heading": "Requirement Description",
                "content": "The system shall be tested for known vulnerabilities.",
                "text": "The system shall be tested for known vulnerabilities.",
                "images": [
                    {
                        "path": "/tmp/test_section3_image.png",
                        "filename": "test_section3_image.png",
                        "original_filename": "test_section3_image.png",
                        "description": "Section 3 Test Image"
                    }
                ],
                "scripts": [
                    {
                        "path": "/tmp/test_section3_script.py",
                        "filename": "test_section3_script.py",
                        "original_filename": "test_section3_script.py",
                        "description": "Section 3 Test Script",
                        "is_pasted": False
                    }
                ]
            }
        }
    }

def create_test_files():
    """Create test files for the test"""
    test_files = {}
    
    # Create test image files
    test_image_path = "/tmp/test_section1_image.png"
    with open(test_image_path, 'w') as f:
        f.write("Test image content")
    test_files[test_image_path] = "test_section1_image.png"
    
    test_image_path = "/tmp/test_section3_image.png"
    with open(test_image_path, 'w') as f:
        f.write("Test image content")
    test_files[test_image_path] = "test_section3_image.png"
    
    # Create test script files
    test_script_path = "/tmp/test_section1_script.py"
    with open(test_script_path, 'w') as f:
        f.write("print('Test script content')")
    test_files[test_script_path] = "test_section1_script.py"
    
    test_script_path = "/tmp/test_section3_script.py"
    with open(test_script_path, 'w') as f:
        f.write("print('Test script content')")
    test_files[test_script_path] = "test_section3_script.py"
    
    return test_files

def cleanup_test_files(test_files):
    """Clean up test files"""
    for file_path in test_files.keys():
        if os.path.exists(file_path):
            os.remove(file_path)

def test_sections_1_7_path_fix():
    """Test that sections 1-7 paths are properly updated in template config"""
    print("🚀 Testing Sections 1-7 Path Fix")
    print("=" * 50)
    
    # Create test files
    test_files = create_test_files()
    
    try:
        # Create temporary test case folder
        with tempfile.TemporaryDirectory() as temp_dir:
            test_case_folder = os.path.join(temp_dir, "test_sections_1_7_path_fix")
            os.makedirs(test_case_folder, exist_ok=True)
            
            print(f"📁 Test case folder: {test_case_folder}")
            
            # Initialize the enhanced export/import system
            export_import = EnhancedExportImport(test_case_folder)
            
            # Create test data
            test_data = create_test_sections_1_7_data()
            
            # Test export
            print("\n📤 Testing export...")
            success, message = export_import.export_complete_configuration(test_data)
            print(f"Export result: {message}")
            
            if not success:
                print("❌ Export failed")
                return False
            
            # Check if template config was created
            template_config_path = os.path.join(test_case_folder, "configuration", "template_config.json")
            if not os.path.exists(template_config_path):
                print("❌ Template config not found")
                return False
            
            # Load and check the template config
            with open(template_config_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
            
            print("\n📋 Checking template config...")
            
            # Check sections 1-7 data
            sections_1_7 = template_config.get('configuration', {}).get('sections_1_7', {})
            
            # Check section 1
            if 'section_1' in sections_1_7:
                section_1 = sections_1_7['section_1']
                print(f"✅ Section 1 found")
                
                # Check images
                if 'images' in section_1 and section_1['images']:
                    for image in section_1['images']:
                        print(f"  📷 Image: {image.get('path', 'No path')}")
                        if not image.get('path', '').startswith('raw_logs/'):
                            print(f"    ❌ Image path not updated correctly")
                            return False
                        else:
                            print(f"    ✅ Image path updated correctly")
                
                # Check scripts
                if 'scripts' in section_1 and section_1['scripts']:
                    for script in section_1['scripts']:
                        print(f"  📜 Script: {script.get('path', 'No path')}")
                        if not script.get('path', '').startswith('code/'):
                            print(f"    ❌ Script path not updated correctly")
                            return False
                        else:
                            print(f"    ✅ Script path updated correctly")
            
            # Check section 3
            if 'section_3' in sections_1_7:
                section_3 = sections_1_7['section_3']
                print(f"✅ Section 3 found")
                
                # Check images
                if 'images' in section_3 and section_3['images']:
                    for image in section_3['images']:
                        print(f"  📷 Image: {image.get('path', 'No path')}")
                        if not image.get('path', '').startswith('raw_logs/'):
                            print(f"    ❌ Image path not updated correctly")
                            return False
                        else:
                            print(f"    ✅ Image path updated correctly")
                
                # Check scripts
                if 'scripts' in section_3 and section_3['scripts']:
                    for script in section_3['scripts']:
                        print(f"  📜 Script: {script.get('path', 'No path')}")
                        if not script.get('path', '').startswith('code/'):
                            print(f"    ❌ Script path not updated correctly")
                            return False
                        else:
                            print(f"    ✅ Script path updated correctly")
            
            # Check if files were copied to the correct folders
            code_folder = os.path.join(test_case_folder, "code")
            raw_logs_folder = os.path.join(test_case_folder, "raw_logs")
            
            print(f"\n📁 Checking copied files...")
            
            if os.path.exists(code_folder):
                code_files = os.listdir(code_folder)
                print(f"  📂 Code folder: {code_files}")
                if not any('test_section1_script.py' in f for f in code_files):
                    print(f"    ❌ Section 1 script not found in code folder")
                    return False
                if not any('test_section3_script.py' in f for f in code_files):
                    print(f"    ❌ Section 3 script not found in code folder")
                    return False
            else:
                print(f"    ❌ Code folder not found")
                return False
            
            if os.path.exists(raw_logs_folder):
                raw_logs_files = os.listdir(raw_logs_folder)
                print(f"  📂 Raw logs folder: {raw_logs_files}")
                if not any('test_section1_image.png' in f for f in raw_logs_files):
                    print(f"    ❌ Section 1 image not found in raw_logs folder")
                    return False
                if not any('test_section3_image.png' in f for f in raw_logs_files):
                    print(f"    ❌ Section 3 image not found in raw_logs folder")
                    return False
            else:
                print(f"    ❌ Raw logs folder not found")
                return False
            
            print("\n✅ All tests passed! Sections 1-7 paths are properly updated.")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test files
        cleanup_test_files(test_files)

if __name__ == "__main__":
    success = test_sections_1_7_path_fix()
    if success:
        print("\n🎉 Sections 1-7 Path Fix Test PASSED!")
        exit(0)
    else:
        print("\n💥 Sections 1-7 Path Fix Test FAILED!")
        exit(1)
