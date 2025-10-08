import os
import shutil
import uuid
import json
from typing import Dict, List, Any


class Section8MediaHandler:
    """
    Section 8 Media Handler - mirrors Section 11's step_widgets pattern
    Uses the same functions and storage approach as Section 11
    """
    
    def __init__(self, parent):
        self.parent = parent
        # Mirror Section 11's step_widgets pattern for Section 8
        self.section8_widgets = {}
        
    def _resolve_import_path(self, file_path: str) -> str:
        """Resolve import path using the same logic as Section 11"""
        if not file_path:
            return ""
        
        # If it's already absolute, return as is
        if os.path.isabs(file_path):
            return file_path
        
        # If it's relative, try multiple resolution strategies
        if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
            # Strategy 1: Combine with import_project_dir
            resolved_path = os.path.join(self.parent.import_project_dir, file_path)
            if os.path.exists(resolved_path):
                return resolved_path
            
            # Strategy 2: Try with current working directory
            cwd_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(cwd_path):
                return cwd_path
            
            # Strategy 3: Try with Report_Generator_Automation-main directory
            main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_path = os.path.join(main_dir, file_path)
            if os.path.exists(main_path):
                return main_path
            
            # Strategy 4: Return the original resolved path (for cases where file might be created later)
            return resolved_path
        
        return file_path
    
    def _find_script_file_in_directory(self, directory: str, filename: str) -> str:
        """Find script file in directory (same as Section 11)"""
        if not directory or not filename:
            return ""
        
        # Check direct path
        direct_path = os.path.join(directory, filename)
        if os.path.exists(direct_path):
            return direct_path
        
        # Check in code subdirectory
        code_path = os.path.join(directory, 'code', filename)
        if os.path.exists(code_path):
            return code_path
        
        # Check in tmp/code subdirectory
        tmp_code_path = os.path.join(directory, 'tmp', 'code', filename)
        if os.path.exists(tmp_code_path):
            return tmp_code_path
        
        # Recursive search in subdirectories
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        
        return ""
    
    def import_section8_media_data(self, config_data: Dict[str, Any]):
        """
        Import Section 8 media data using the same pattern as Section 11
        Stores media in section8_widgets with upload_images_list and upload_scripts_list
        """
        print("=== IMPORTING SECTION 8 MEDIA DATA (Section 11 Pattern) ===")
        
        # 8.1 Test Scenarios
        if 'test_scenarios' in config_data:
            for i, scenario_data in enumerate(config_data['test_scenarios']):
                scenario_key = f"scenario_{i}"
                self.section8_widgets[scenario_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'scenario_data': scenario_data
                }
                
                # Import scenario images
                if 'images' in scenario_data:
                    for image_data in scenario_data['images']:
                        file_path = self._resolve_import_path(image_data.get('path', ''))
                        if os.path.exists(file_path) or image_data.get('is_placeholder', False):
                            image_info = {
                                'path': image_data.get('path', ''),  # Keep original path from JSON
                                'filename': image_data.get('filename', ''),
                                'original_filename': image_data.get('original_filename', ''),
                                'description': image_data.get('description', ''),
                                'is_placeholder': image_data.get('is_placeholder', False)
                            }
                            self.section8_widgets[scenario_key]['upload_images_list'].append(image_info)
                            print(f"✅ Imported scenario image: {image_info['filename']}")
                
                # Import scenario scripts
                if 'scripts' in scenario_data:
                    for script_data in scenario_data['scripts']:
                        original_path = script_data.get('original_path', '')
                        if not original_path:
                            original_path = self._resolve_import_path(script_data.get('path', ''))
                        
                        # If original_path is relative, try to find it
                        if original_path and not os.path.isabs(original_path):
                            if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                                if found_path:
                                    original_path = found_path
                        
                        script_info = {
                            'path': script_data.get('path', ''),  # Keep original path from JSON
                            'filename': script_data.get('filename', ''),
                            'original_filename': script_data.get('original_filename', ''),
                            'description': script_data.get('description', ''),
                            'is_pasted': script_data.get('is_pasted', False),
                            'original_path': original_path  # Store for later copying
                        }
                        self.section8_widgets[scenario_key]['upload_scripts_list'].append(script_info)
                        print(f"✅ Imported scenario script: {script_info['filename']}")
        
        # 8.2 Test Bed Diagram
        if 'test_bed_diagram' in config_data:
            tbd_key = "test_bed_diagram"
            self.section8_widgets[tbd_key] = {
                'upload_images_list': [],
                'upload_scripts_list': [],
                'tbd_data': config_data['test_bed_diagram']
            }
            
            # Import test bed images
            if 'images' in config_data['test_bed_diagram']:
                for image_data in config_data['test_bed_diagram']['images']:
                    file_path = self._resolve_import_path(image_data.get('path', ''))
                    print(f"DEBUG: Resolved image path: {file_path}")
                    print(f"DEBUG: Image file exists: {os.path.exists(file_path)}")
                    print(f"DEBUG: Is placeholder: {image_data.get('is_placeholder', False)}")
                    
                    # Import the image regardless of file existence (the main import process handles file copying)
                    image_info = {
                        'path': image_data.get('path', ''),
                        'filename': image_data.get('filename', ''),
                        'original_filename': image_data.get('original_filename', ''),
                        'description': image_data.get('description', ''),
                        'is_placeholder': image_data.get('is_placeholder', False)
                    }
                    self.section8_widgets[tbd_key]['upload_images_list'].append(image_info)
                    print(f"✅ Imported test bed image: {image_info['filename']}")
            
            # Import test bed scripts
            if 'scripts' in config_data['test_bed_diagram']:
                for script_data in config_data['test_bed_diagram']['scripts']:
                    original_path = script_data.get('original_path', '')
                    if not original_path:
                        original_path = self._resolve_import_path(script_data.get('path', ''))
                    
                    print(f"DEBUG: Resolved script path: {original_path}")
                    print(f"DEBUG: Script file exists: {os.path.exists(original_path)}")
                    
                    if original_path and not os.path.isabs(original_path):
                        if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                            found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                            if found_path:
                                original_path = found_path
                                print(f"DEBUG: Found script in directory: {found_path}")
                    
                    # Import the script regardless of file existence (the main import process handles file copying)
                    script_info = {
                        'path': script_data.get('path', ''),
                        'filename': script_data.get('filename', ''),
                        'original_filename': script_data.get('original_filename', ''),
                        'description': script_data.get('description', ''),
                        'is_pasted': script_data.get('is_pasted', False),
                        'original_path': original_path
                    }
                    self.section8_widgets[tbd_key]['upload_scripts_list'].append(script_info)
                    print(f"✅ Imported test bed script: {script_info['filename']}")
        
        # 8.3 Tools Required
        if 'tools_required' in config_data:
            for i, tool_data in enumerate(config_data['tools_required']):
                tool_key = f"tool_{i}"
                self.section8_widgets[tool_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'tool_data': tool_data
                }
                
                # Import tool images
                if 'images' in tool_data:
                    for image_data in tool_data['images']:
                        file_path = self._resolve_import_path(image_data.get('path', ''))
                        if os.path.exists(file_path) or image_data.get('is_placeholder', False):
                            image_info = {
                                'path': image_data.get('path', ''),
                                'filename': image_data.get('filename', ''),
                                'original_filename': image_data.get('original_filename', ''),
                                'description': image_data.get('description', ''),
                                'is_placeholder': image_data.get('is_placeholder', False)
                            }
                            self.section8_widgets[tool_key]['upload_images_list'].append(image_info)
                            print(f"✅ Imported tool image: {image_info['filename']}")
                
                # Import tool scripts
                if 'scripts' in tool_data:
                    for script_data in tool_data['scripts']:
                        original_path = script_data.get('original_path', '')
                        if not original_path:
                            original_path = self._resolve_import_path(script_data.get('path', ''))
                        
                        if original_path and not os.path.isabs(original_path):
                            if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                                if found_path:
                                    original_path = found_path
                        
                        script_info = {
                            'path': script_data.get('path', ''),
                            'filename': script_data.get('filename', ''),
                            'original_filename': script_data.get('original_filename', ''),
                            'description': script_data.get('description', ''),
                            'is_pasted': script_data.get('is_pasted', False),
                            'original_path': original_path
                        }
                        self.section8_widgets[tool_key]['upload_scripts_list'].append(script_info)
                        print(f"✅ Imported tool script: {script_info['filename']}")
        
        # 8.4 Execution Steps
        if 'execution_steps' in config_data:
            for i, step_data in enumerate(config_data['execution_steps']):
                step_key = f"exec_step_{i}"
                self.section8_widgets[step_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'step_data': step_data
                }
                
                # Import step images
                if 'images' in step_data:
                    for image_data in step_data['images']:
                        file_path = self._resolve_import_path(image_data.get('path', ''))
                        if os.path.exists(file_path) or image_data.get('is_placeholder', False):
                            image_info = {
                                'path': image_data.get('path', ''),
                                'filename': image_data.get('filename', ''),
                                'original_filename': image_data.get('original_filename', ''),
                                'description': image_data.get('description', ''),
                                'is_placeholder': image_data.get('is_placeholder', False)
                            }
                            self.section8_widgets[step_key]['upload_images_list'].append(image_info)
                            print(f"✅ Imported execution step image: {image_info['filename']}")
                
                # Import step scripts
                if 'scripts' in step_data:
                    for script_data in step_data['scripts']:
                        original_path = script_data.get('original_path', '')
                        if not original_path:
                            original_path = self._resolve_import_path(script_data.get('path', ''))
                        
                        if original_path and not os.path.isabs(original_path):
                            if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                                if found_path:
                                    original_path = found_path
                        
                        script_info = {
                            'path': script_data.get('path', ''),
                            'filename': script_data.get('filename', ''),
                            'original_filename': script_data.get('original_filename', ''),
                            'description': script_data.get('description', ''),
                            'is_pasted': script_data.get('is_pasted', False),
                            'original_path': original_path
                        }
                        self.section8_widgets[step_key]['upload_scripts_list'].append(script_info)
                        print(f"✅ Imported execution step script: {script_info['filename']}")
        
        # 9. Expected Results for Pass
        if 'expected_results' in config_data:
            for i, expected_result_data in enumerate(config_data['expected_results']):
                expected_key = f"expected_result_{i}"
                self.section8_widgets[expected_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'expected_result_data': expected_result_data
                }
                
                # Import expected result images
                if 'images' in expected_result_data:
                    for image_data in expected_result_data['images']:
                        file_path = self._resolve_import_path(image_data.get('path', ''))
                        print(f"DEBUG: Resolved expected result image path: {file_path}")
                        print(f"DEBUG: Expected result image file exists: {os.path.exists(file_path)}")
                        print(f"DEBUG: Is placeholder: {image_data.get('is_placeholder', False)}")
                        
                        # Import the image regardless of file existence (the main import process handles file copying)
                        image_info = {
                            'path': image_data.get('path', ''),
                            'filename': image_data.get('filename', ''),
                            'original_filename': image_data.get('original_filename', ''),
                            'description': image_data.get('description', ''),
                            'is_placeholder': image_data.get('is_placeholder', False)
                        }
                        self.section8_widgets[expected_key]['upload_images_list'].append(image_info)
                        print(f"✅ Imported expected result image: {image_info['filename']}")
                
                # Import expected result scripts
                if 'scripts' in expected_result_data:
                    for script_data in expected_result_data['scripts']:
                        original_path = script_data.get('original_path', '')
                        if not original_path:
                            original_path = self._resolve_import_path(script_data.get('path', ''))
                        
                        print(f"DEBUG: Resolved expected result script path: {original_path}")
                        print(f"DEBUG: Expected result script file exists: {os.path.exists(original_path)}")
                        
                        if original_path and not os.path.isabs(original_path):
                            if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                                if found_path:
                                    original_path = found_path
                                    print(f"DEBUG: Found expected result script in directory: {found_path}")
                        
                        # Import the script regardless of file existence (the main import process handles file copying)
                        script_info = {
                            'path': script_data.get('path', ''),
                            'filename': script_data.get('filename', ''),
                            'original_filename': script_data.get('original_filename', ''),
                            'description': script_data.get('description', ''),
                            'is_pasted': script_data.get('is_pasted', False),
                            'original_path': original_path
                        }
                        self.section8_widgets[expected_key]['upload_scripts_list'].append(script_info)
                        print(f"✅ Imported expected result script: {script_info['filename']}")
        
        # 10. Expected Format of Evidence
        if 'evidence_format' in config_data:
            for i, evidence_data in enumerate(config_data['evidence_format']):
                evidence_key = f"evidence_format_{i}"
                self.section8_widgets[evidence_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'evidence_data': evidence_data
                }
                
                # Import evidence format images
                if 'images' in evidence_data:
                    for image_data in evidence_data['images']:
                        file_path = self._resolve_import_path(image_data.get('path', ''))
                        print(f"DEBUG: Resolved evidence format image path: {file_path}")
                        print(f"DEBUG: Evidence format image file exists: {os.path.exists(file_path)}")
                        print(f"DEBUG: Is placeholder: {image_data.get('is_placeholder', False)}")
                        
                        # Import the image regardless of file existence (the main import process handles file copying)
                        image_info = {
                            'path': image_data.get('path', ''),
                            'filename': image_data.get('filename', ''),
                            'original_filename': image_data.get('original_filename', ''),
                            'description': image_data.get('description', ''),
                            'is_placeholder': image_data.get('is_placeholder', False)
                        }
                        self.section8_widgets[evidence_key]['upload_images_list'].append(image_info)
                        print(f"✅ Imported evidence format image: {image_info['filename']}")
                
                # Import evidence format scripts
                if 'scripts' in evidence_data:
                    for script_data in evidence_data['scripts']:
                        original_path = script_data.get('original_path', '')
                        if not original_path:
                            original_path = self._resolve_import_path(script_data.get('path', ''))
                        
                        print(f"DEBUG: Resolved evidence format script path: {original_path}")
                        print(f"DEBUG: Evidence format script file exists: {os.path.exists(original_path)}")
                        
                        if original_path and not os.path.isabs(original_path):
                            if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                found_path = self._find_script_file_in_directory(self.parent.import_project_dir, os.path.basename(original_path))
                                if found_path:
                                    original_path = found_path
                                    print(f"DEBUG: Found evidence format script in directory: {found_path}")
                        
                        # Import the script regardless of file existence (the main import process handles file copying)
                        script_info = {
                            'path': script_data.get('path', ''),
                            'filename': script_data.get('filename', ''),
                            'original_filename': script_data.get('original_filename', ''),
                            'description': script_data.get('description', ''),
                            'is_pasted': script_data.get('is_pasted', False),
                            'original_path': original_path
                        }
                        self.section8_widgets[evidence_key]['upload_scripts_list'].append(script_info)
                        print(f"✅ Imported evidence format script: {script_info['filename']}")
        
        print(f"=== SECTION 8 MEDIA IMPORT COMPLETED: {len(self.section8_widgets)} widgets created ===")
    
    def load_section8_data_to_ui(self):
        """
        Load imported Section 8 data back into the UI widgets
        This populates the actual UI with the imported scripts and images
        """
        print("=== LOADING SECTION 8 DATA TO UI ===")
        
        # Load test bed diagram data
        if 'test_bed_diagram' in self.section8_widgets:
            print("DEBUG: Loading test bed diagram data...")
            tbd_widget = self.section8_widgets['test_bed_diagram']
            
            # Initialize test_bed_diagram_data if it doesn't exist
            if not hasattr(self.parent, 'test_bed_diagram_data'):
                self.parent.test_bed_diagram_data = {
                    'heading': '8.2. Test Bed Diagram',
                    'images': [],
                    'scripts': []
                }
                print("DEBUG: Initialized test_bed_diagram_data")
            else:
                # Clear existing data to prevent duplicates
                print("DEBUG: Clearing existing test bed diagram data to prevent duplicates")
                self.parent.test_bed_diagram_data['images'] = []
                self.parent.test_bed_diagram_data['scripts'] = []
                
                # Also clear old data structures for backward compatibility
                if hasattr(self.parent, 'test_bed_images'):
                    self.parent.test_bed_images = []
                    print("DEBUG: Cleared old test_bed_images list")
                if hasattr(self.parent, 'test_bed_scripts'):
                    self.parent.test_bed_scripts = []
                    print("DEBUG: Cleared old test_bed_scripts list")
            
            # Clear existing UI widgets to prevent duplicates
            if hasattr(self.parent, 'test_bed_images_layout'):
                print("DEBUG: Clearing existing test bed UI widgets")
                while self.parent.test_bed_images_layout.count():
                    child = self.parent.test_bed_images_layout.takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)
                        child.widget().deleteLater()
            
            # Load images
            print(f"DEBUG: Found {len(tbd_widget.get('upload_images_list', []))} test bed diagram images")
            for image_info in tbd_widget.get('upload_images_list', []):
                print(f"DEBUG: Processing image: {image_info['filename']}, is_placeholder: {image_info.get('is_placeholder', False)}")
                # Add to data structure regardless of placeholder status (the main import process handles this)
                self.parent.test_bed_diagram_data['images'].append(image_info)
                print(f"✅ Loaded test bed diagram image to data structure: {image_info['filename']}")
                
                # Also create UI widget and add to layout
                self._create_and_add_image_widget(image_info, 'test_bed_diagram')
            
            # Load scripts
            print(f"DEBUG: Found {len(tbd_widget.get('upload_scripts_list', []))} test bed diagram scripts")
            for script_info in tbd_widget.get('upload_scripts_list', []):
                # Add to data structure
                self.parent.test_bed_diagram_data['scripts'].append(script_info)
                print(f"✅ Loaded test bed diagram script to data structure: {script_info['filename']}")
                
                # Also create UI widget and add to layout
                self._create_and_add_script_widget(script_info, 'test_bed_diagram')
        
        # Load tools required data
        for widget_key, widget_data in self.section8_widgets.items():
            if widget_key.startswith('tool_'):
                tool_index = int(widget_key.split('_')[1])
                
                # Ensure tools_required list is long enough
                if not hasattr(self.parent, 'tools_required'):
                    self.parent.tools_required = []
                
                while len(self.parent.tools_required) <= tool_index:
                    self.parent.tools_required.append({
                        'name': '',
                        'images': [],
                        'scripts': []
                    })
                
                # Load images
                for image_info in widget_data.get('upload_images_list', []):
                    # Add to data structure regardless of placeholder status
                    self.parent.tools_required[tool_index]['images'].append(image_info)
                    print(f"✅ Loaded tool {tool_index} image to data structure: {image_info['filename']}")
                
                # Load scripts
                for script_info in widget_data.get('upload_scripts_list', []):
                    # Add to data structure
                    self.parent.tools_required[tool_index]['scripts'].append(script_info)
                    print(f"✅ Loaded tool {tool_index} script to data structure: {script_info['filename']}")
        
        # Load test scenarios data
        for widget_key, widget_data in self.section8_widgets.items():
            if widget_key.startswith('scenario_'):
                scenario_index = int(widget_key.split('_')[1])
                
                # Ensure test_scenarios list is long enough
                if not hasattr(self.parent, 'test_scenarios'):
                    self.parent.test_scenarios = []
                
                while len(self.parent.test_scenarios) <= scenario_index:
                    self.parent.test_scenarios.append({
                        'key': '',
                        'description': '',
                        'images': [],
                        'scripts': []
                    })
                
                # Load images
                for image_info in widget_data.get('upload_images_list', []):
                    # Add to data structure regardless of placeholder status
                    self.parent.test_scenarios[scenario_index]['images'].append(image_info)
                    print(f"✅ Loaded scenario {scenario_index} image to data structure: {image_info['filename']}")
                
                # Load scripts
                for script_info in widget_data.get('upload_scripts_list', []):
                    # Add to data structure
                    self.parent.test_scenarios[scenario_index]['scripts'].append(script_info)
                    print(f"✅ Loaded scenario {scenario_index} script to data structure: {script_info['filename']}")
        
        # Load expected results data
        for widget_key, widget_data in self.section8_widgets.items():
            if widget_key.startswith('expected_result_'):
                expected_index = int(widget_key.split('_')[2])
                
                # Ensure expected_results list is long enough
                if not hasattr(self.parent, 'expected_results'):
                    self.parent.expected_results = []
                
                while len(self.parent.expected_results) <= expected_index:
                    self.parent.expected_results.append({
                        'scenario_key': '',
                        'scenario_description': '',
                        'expected_result': '',
                        'images': [],
                        'scripts': []
                    })
                
                # Load images
                for image_info in widget_data.get('upload_images_list', []):
                    # Add to data structure regardless of placeholder status
                    self.parent.expected_results[expected_index]['images'].append(image_info)
                    print(f"✅ Loaded expected result {expected_index} image to data structure: {image_info['filename']}")
                    
                    # Also create UI widget and add to layout
                    self._create_and_add_image_widget(image_info, 'expected_result')
                
                # Load scripts
                for script_info in widget_data.get('upload_scripts_list', []):
                    # Add to data structure
                    self.parent.expected_results[expected_index]['scripts'].append(script_info)
                    print(f"✅ Loaded expected result {expected_index} script to data structure: {script_info['filename']}")
                    
                    # Also create UI widget and add to layout
                    self._create_and_add_script_widget(script_info, 'expected_result')
        
        # Load evidence format data
        for widget_key, widget_data in self.section8_widgets.items():
            if widget_key.startswith('evidence_format_'):
                evidence_index = int(widget_key.split('_')[2])
                
                # Ensure evidence_format list is long enough
                if not hasattr(self.parent, 'evidence_format'):
                    self.parent.evidence_format = []
                
                while len(self.parent.evidence_format) <= evidence_index:
                    self.parent.evidence_format.append({
                        'evidence_text': '',
                        'images': [],
                        'scripts': []
                    })
                
                # Load images
                for image_info in widget_data.get('upload_images_list', []):
                    # Add to data structure regardless of placeholder status
                    self.parent.evidence_format[evidence_index]['images'].append(image_info)
                    print(f"✅ Loaded evidence format {evidence_index} image to data structure: {image_info['filename']}")
                    
                    # Also create UI widget and add to layout
                    self._create_and_add_image_widget(image_info, 'evidence_format')
                
                # Load scripts
                for script_info in widget_data.get('upload_scripts_list', []):
                    # Add to data structure
                    self.parent.evidence_format[evidence_index]['scripts'].append(script_info)
                    print(f"✅ Loaded evidence format {evidence_index} script to data structure: {script_info['filename']}")
                    
                    # Also create UI widget and add to layout
                    self._create_and_add_script_widget(script_info, 'evidence_format')
        
        print("=== SECTION 8 DATA LOADED TO UI COMPLETED ===")
    
    def _create_and_add_image_widget(self, image_info, field_type):
        """Create and add an image widget to the UI with exact styling"""
        try:
            from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            
            # Create image widget with horizontal layout
            image_widget = QWidget()
            layout = QHBoxLayout(image_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(10)
            
            # Add image icon (using a simple label with image emoji)
            icon_label = QLabel("🖼️")
            icon_label.setFixedSize(20, 20)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
            
            # Add image filename in green
            filename = image_info.get('original_filename', image_info.get('filename', 'Unknown'))
            image_label = QLabel(filename)
            image_label.setStyleSheet("color: #00ff00; font-weight: bold;")  # Green color
            image_label.setWordWrap(True)
            layout.addWidget(image_label)
            
            # Add stretch to push remove button to the right
            layout.addStretch()
            
            # Add remove button with red styling
            remove_btn = QPushButton("🗑️ Remove")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6666;
                }
                QPushButton:pressed {
                    background-color: #cc3333;
                }
            """)
            
            # Store remove button reference in image_info for proper removal
            image_info['remove_btn'] = remove_btn
            
            if field_type == 'expected_result':
                # For expected results, we need to find the field_info and use remove_field_image
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for scenario in self.parent.test_scenarios:
                        if 'expected_result_field_info' in scenario:
                            field_info = scenario['expected_result_field_info']
                            remove_btn.clicked.connect(lambda checked, fi=field_info, ii=image_info: self.parent.remove_field_image(fi, ii))
                            break
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing expected result image: {image_info['filename']}"))
            elif field_type == 'evidence_format':
                # For evidence format, we need to find the field_info and use remove_field_image
                # Look for evidence_field_info in the parent's evidence_list (not evidence_format)
                if hasattr(self.parent, 'evidence_list') and self.parent.evidence_list:
                    for evidence_item in self.parent.evidence_list:
                        if 'evidence_field_info' in evidence_item:
                            field_info = evidence_item['evidence_field_info']
                            remove_btn.clicked.connect(lambda checked, fi=field_info, ii=image_info: self.parent.remove_field_image(fi, ii))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing evidence format image: {image_info['filename']}"))
                # Fallback: look for evidence_field_info in the parent's evidence format structure
                elif hasattr(self.parent, 'evidence_field_info') and self.parent.evidence_field_info:
                    field_info = self.parent.evidence_field_info
                    remove_btn.clicked.connect(lambda checked, fi=field_info, ii=image_info: self.parent.remove_field_image(fi, ii))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing evidence format image: {image_info['filename']}"))
            elif field_type == 'test_bed_diagram':
                # Use a closure to capture the image_info value
                def create_remove_handler(img_info):
                    return lambda: self.parent.remove_test_bed_image(img_info)
                remove_btn.clicked.connect(create_remove_handler(image_info))
            elif field_type == 'tool_required':
                # For tools, we need to find the tool index and use remove_tool_required_image
                if hasattr(self.parent, 'tools_required') and self.parent.tools_required:
                    for i, tool in enumerate(self.parent.tools_required):
                        if 'images' in tool and image_info in tool['images']:
                            # Use a closure to capture the values
                            def create_remove_handler(tool_idx, img_info):
                                return lambda: self.parent.remove_tool_required_image(tool_idx, img_info)
                            remove_btn.clicked.connect(create_remove_handler(i, image_info))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing tool required image: {image_info['filename']}"))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing tool required image: {image_info['filename']}"))
            elif field_type == 'test_scenario':
                # For test scenarios, we need to find the scenario index and use remove_test_scenario_image
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for i, scenario in enumerate(self.parent.test_scenarios):
                        if 'images' in scenario and image_info in scenario['images']:
                            # Use a closure to capture the values
                            def create_remove_handler(scenario_idx, img_info):
                                return lambda: self.parent.remove_test_scenario_image(scenario_idx, img_info)
                            remove_btn.clicked.connect(create_remove_handler(i, image_info))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing test scenario image: {image_info['filename']}"))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing test scenario image: {image_info['filename']}"))
            elif field_type == 'execution_step':
                # For execution steps, we need to find the step widget and use remove_execution_step_image
                remove_btn.clicked.connect(lambda: print(f"Mock: Removing execution step image: {image_info['filename']}"))
            else:
                remove_btn.clicked.connect(lambda: print(f"Mock: Removing image for unknown field_type {field_type}: {image_info['filename']}"))
            layout.addWidget(remove_btn)
            
            # Add to the appropriate layout
            if field_type == 'test_bed_diagram' and hasattr(self.parent, 'test_bed_images_layout'):
                self.parent.test_bed_images_layout.addWidget(image_widget)
                print(f"✅ Added test bed diagram image widget to UI: {image_info['filename']}")
            elif field_type == 'expected_result':
                # For expected results, we need to find the correct scenario and add to its expected result field
                # Find the matching scenario and add to its images_layout
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for scenario in self.parent.test_scenarios:
                        if 'expected_result_field_info' in scenario:
                            field_info = scenario['expected_result_field_info']
                            if 'images_layout' in field_info:
                                field_info['images_layout'].addWidget(image_widget)
                                print(f"✅ Added expected result image widget to UI: {image_info['filename']}")
                                return
                print(f"⚠️ Could not find expected result images layout for: {image_info['filename']}")
            elif field_type == 'evidence_format':
                # For evidence format, we need to find the evidence field info and add to its images_layout
                # Look for evidence_field_info in the parent's evidence_list (not evidence_format)
                if hasattr(self.parent, 'evidence_list') and self.parent.evidence_list:
                    for evidence_item in self.parent.evidence_list:
                        if 'evidence_field_info' in evidence_item:
                            field_info = evidence_item['evidence_field_info']
                            if 'images_layout' in field_info:
                                field_info['images_layout'].addWidget(image_widget)
                                print(f"✅ Added evidence format image widget to UI: {image_info['filename']}")
                                return
                # Fallback: look for evidence_field_info in the parent's evidence format structure
                elif hasattr(self.parent, 'evidence_field_info') and self.parent.evidence_field_info:
                    field_info = self.parent.evidence_field_info
                    if 'images_layout' in field_info:
                        field_info['images_layout'].addWidget(image_widget)
                        print(f"✅ Added evidence format image widget to UI: {image_info['filename']}")
                        return
                print(f"⚠️ Could not find evidence format images layout for: {image_info['filename']}")
            else:
                print(f"⚠️ Could not add image widget - layout not found for field_type: {field_type}")
                
        except Exception as e:
            print(f"⚠️ Error creating image widget: {e}")
    
    def _create_and_add_script_widget(self, script_info, field_type):
        """Create and add a script widget to the UI with exact styling"""
        try:
            from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QFont
            
            # Create script widget with horizontal layout
            script_widget = QWidget()
            layout = QHBoxLayout(script_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(10)
            
            # Add file icon (using a simple label with document emoji)
            icon_label = QLabel("📄")
            icon_label.setFixedSize(20, 20)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
            
            # Add script filename in green
            filename = script_info.get('original_filename', script_info.get('filename', 'Unknown'))
            script_label = QLabel(filename)
            script_label.setStyleSheet("color: #00ff00; font-weight: bold;")  # Green color
            script_label.setWordWrap(True)
            layout.addWidget(script_label)
            
            # Add stretch to push remove button to the right
            layout.addStretch()
            
            # Add remove button with red styling
            remove_btn = QPushButton("🗑️ Remove")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff6666;
                }
                QPushButton:pressed {
                    background-color: #cc3333;
                }
            """)
            
            # Store remove button reference in script_info for proper removal
            script_info['remove_btn'] = remove_btn
            
            if field_type == 'expected_result':
                # For expected results, we need to find the field_info and use remove_field_script
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for scenario in self.parent.test_scenarios:
                        if 'expected_result_field_info' in scenario:
                            field_info = scenario['expected_result_field_info']
                            remove_btn.clicked.connect(lambda checked, fi=field_info, si=script_info: self.parent.remove_field_script(fi, si))
                            break
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing expected result script: {script_info['filename']}"))
            elif field_type == 'evidence_format':
                # For evidence format, we need to find the field_info and use remove_field_script
                # Look for evidence_field_info in the parent's evidence_list (not evidence_format)
                if hasattr(self.parent, 'evidence_list') and self.parent.evidence_list:
                    for evidence_item in self.parent.evidence_list:
                        if 'evidence_field_info' in evidence_item:
                            field_info = evidence_item['evidence_field_info']
                            remove_btn.clicked.connect(lambda checked, fi=field_info, si=script_info: self.parent.remove_field_script(fi, si))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing evidence format script: {script_info['filename']}"))
                # Fallback: look for evidence_field_info in the parent's evidence format structure
                elif hasattr(self.parent, 'evidence_field_info') and self.parent.evidence_field_info:
                    field_info = self.parent.evidence_field_info
                    remove_btn.clicked.connect(lambda checked, fi=field_info, si=script_info: self.parent.remove_field_script(fi, si))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing evidence format script: {script_info['filename']}"))
            elif field_type == 'test_bed_diagram':
                # Use a closure to capture the script_info value
                def create_remove_handler(scr_info):
                    return lambda: self.parent.remove_test_bed_script(scr_info)
                remove_btn.clicked.connect(create_remove_handler(script_info))
            elif field_type == 'tool_required':
                # For tools, we need to find the tool index and use remove_tool_required_script
                if hasattr(self.parent, 'tools_required') and self.parent.tools_required:
                    for i, tool in enumerate(self.parent.tools_required):
                        if 'scripts' in tool and script_info in tool['scripts']:
                            # Use a closure to capture the values
                            def create_remove_handler(tool_idx, scr_info):
                                return lambda: self.parent.remove_tool_required_script(tool_idx, scr_info)
                            remove_btn.clicked.connect(create_remove_handler(i, script_info))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing tool required script: {script_info['filename']}"))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing tool required script: {script_info['filename']}"))
            elif field_type == 'test_scenario':
                # For test scenarios, we need to find the scenario index and use remove_test_scenario_script
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for i, scenario in enumerate(self.parent.test_scenarios):
                        if 'scripts' in scenario and script_info in scenario['scripts']:
                            # Use a closure to capture the values
                            def create_remove_handler(scenario_idx, scr_info):
                                return lambda: self.parent.remove_test_scenario_script(scenario_idx, scr_info)
                            remove_btn.clicked.connect(create_remove_handler(i, script_info))
                            break
                    else:
                        remove_btn.clicked.connect(lambda: print(f"Mock: Removing test scenario script: {script_info['filename']}"))
                else:
                    remove_btn.clicked.connect(lambda: print(f"Mock: Removing test scenario script: {script_info['filename']}"))
            elif field_type == 'execution_step':
                # For execution steps, we need to find the step widget and use remove_execution_step_script
                remove_btn.clicked.connect(lambda: print(f"Mock: Removing execution step script: {script_info['filename']}"))
            else:
                remove_btn.clicked.connect(lambda: print(f"Mock: Removing script for unknown field_type {field_type}: {script_info['filename']}"))
            layout.addWidget(remove_btn)
            
            # Add to the appropriate layout
            if field_type == 'test_bed_diagram' and hasattr(self.parent, 'test_bed_images_layout'):
                self.parent.test_bed_images_layout.addWidget(script_widget)
                print(f"✅ Added test bed diagram script widget to UI: {script_info['filename']}")
            elif field_type == 'expected_result':
                # For expected results, we need to find the correct scenario and add to its expected result field
                # Find the matching scenario and add to its scripts_layout
                if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
                    for scenario in self.parent.test_scenarios:
                        if 'expected_result_field_info' in scenario:
                            field_info = scenario['expected_result_field_info']
                            if 'scripts_layout' in field_info:
                                field_info['scripts_layout'].addWidget(script_widget)
                                print(f"✅ Added expected result script widget to UI: {script_info['filename']}")
                                return
                print(f"⚠️ Could not find expected result scripts layout for: {script_info['filename']}")
            elif field_type == 'evidence_format':
                # For evidence format, we need to find the evidence field info and add to its scripts_layout
                # Look for evidence_field_info in the parent's evidence_list (not evidence_format)
                if hasattr(self.parent, 'evidence_list') and self.parent.evidence_list:
                    for evidence_item in self.parent.evidence_list:
                        if 'evidence_field_info' in evidence_item:
                            field_info = evidence_item['evidence_field_info']
                            if 'scripts_layout' in field_info:
                                field_info['scripts_layout'].addWidget(script_widget)
                                print(f"✅ Added evidence format script widget to UI: {script_info['filename']}")
                                return
                # Fallback: look for evidence_field_info in the parent's evidence format structure
                elif hasattr(self.parent, 'evidence_field_info') and self.parent.evidence_field_info:
                    field_info = self.parent.evidence_field_info
                    if 'scripts_layout' in field_info:
                        field_info['scripts_layout'].addWidget(script_widget)
                        print(f"✅ Added evidence format script widget to UI: {script_info['filename']}")
                        return
                print(f"⚠️ Could not find evidence format scripts layout for: {script_info['filename']}")
            else:
                print(f"⚠️ Could not add script widget - layout not found for field_type: {field_type}")
                
        except Exception as e:
            print(f"⚠️ Error creating script widget: {e}")
    
    def _add_image_to_ui(self, image_info, field_type, index=None):
        """Add an image to the UI based on field type"""
        try:
            # Use the existing UI creation methods from the parent
            if field_type == 'test_bed_diagram':
                # Create image widget using the same method as the existing code
                from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
                from PyQt6.QtCore import Qt
                
                image_widget = QWidget()
                layout = QVBoxLayout(image_widget)
                
                # Add image label
                image_label = QLabel(f"📷 {image_info.get('original_filename', image_info.get('filename', 'Unknown'))}")
                image_label.setWordWrap(True)
                layout.addWidget(image_label)
                
                # Add remove button
                remove_btn = QPushButton("🗑️ Remove")
                remove_btn.clicked.connect(lambda: self.parent.remove_test_bed_image(image_info))
                layout.addWidget(remove_btn)
                
                # Add to the test bed images layout
                if hasattr(self.parent, 'test_bed_images_layout'):
                    self.parent.test_bed_images_layout.addWidget(image_widget)
                    print(f"✅ Added test bed diagram image widget to UI: {image_info['filename']}")
                    
            elif field_type == 'tool_required':
                # For tools, just add to the data structure (UI will be handled separately)
                print(f"✅ Added tool {index} image to data structure: {image_info['filename']}")
                        
            elif field_type == 'test_scenario':
                # For test scenarios, just add to the data structure (UI will be handled separately)
                print(f"✅ Added scenario {index} image to data structure: {image_info['filename']}")
                    
        except Exception as e:
            print(f"⚠️ Error adding image to UI: {e}")
    
    def _add_script_to_ui(self, script_info, field_type, index=None):
        """Add a script to the UI based on field type"""
        try:
            # Use the existing UI creation methods from the parent
            if field_type == 'test_bed_diagram':
                # Create script widget using the same method as the existing code
                from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
                from PyQt6.QtCore import Qt
                
                script_widget = QWidget()
                layout = QVBoxLayout(script_widget)
                
                # Add script label
                script_label = QLabel(f"📜 {script_info.get('original_filename', script_info.get('filename', 'Unknown'))}")
                script_label.setWordWrap(True)
                layout.addWidget(script_label)
                
                # Add description if available
                if script_info.get('description'):
                    desc_label = QLabel(f"Description: {script_info['description']}")
                    desc_label.setWordWrap(True)
                    layout.addWidget(desc_label)
                
                # Add remove button
                remove_btn = QPushButton("🗑️ Remove")
                remove_btn.clicked.connect(lambda: self.parent.remove_test_bed_script(script_info))
                layout.addWidget(remove_btn)
                
                # Add to the test bed images layout (scripts are added to the same layout)
                if hasattr(self.parent, 'test_bed_images_layout'):
                    self.parent.test_bed_images_layout.addWidget(script_widget)
                    print(f"✅ Added test bed diagram script widget to UI: {script_info['filename']}")
                    
            elif field_type == 'tool_required':
                # For tools, just add to the data structure (UI will be handled separately)
                print(f"✅ Added tool {index} script to data structure: {script_info['filename']}")
                        
            elif field_type == 'test_scenario':
                # For test scenarios, just add to the data structure (UI will be handled separately)
                print(f"✅ Added scenario {index} script to data structure: {script_info['filename']}")
                    
        except Exception as e:
            print(f"⚠️ Error adding script to UI: {e}")
    
    def _remove_image_from_ui(self, image_info, field_type, index=None):
        """Remove an image from the UI"""
        try:
            if field_type == 'test_bed_diagram':
                if hasattr(self.parent, 'test_bed_diagram_data') and image_info in self.parent.test_bed_diagram_data['images']:
                    self.parent.test_bed_diagram_data['images'].remove(image_info)
            elif field_type == 'tool_required' and index is not None:
                if hasattr(self.parent, 'tools_required') and index < len(self.parent.tools_required):
                    if image_info in self.parent.tools_required[index]['images']:
                        self.parent.tools_required[index]['images'].remove(image_info)
            elif field_type == 'test_scenario' and index is not None:
                if hasattr(self.parent, 'test_scenarios') and index < len(self.parent.test_scenarios):
                    if image_info in self.parent.test_scenarios[index]['images']:
                        self.parent.test_scenarios[index]['images'].remove(image_info)
        except Exception as e:
            print(f"⚠️ Error removing image from UI: {e}")
    
    def _remove_script_from_ui(self, script_info, field_type, index=None):
        """Remove a script from the UI"""
        try:
            if field_type == 'test_bed_diagram':
                if hasattr(self.parent, 'test_bed_diagram_data') and script_info in self.parent.test_bed_diagram_data['scripts']:
                    self.parent.test_bed_diagram_data['scripts'].remove(script_info)
            elif field_type == 'tool_required' and index is not None:
                if hasattr(self.parent, 'tools_required') and index < len(self.parent.tools_required):
                    if script_info in self.parent.tools_required[index]['scripts']:
                        self.parent.tools_required[index]['scripts'].remove(script_info)
            elif field_type == 'test_scenario' and index is not None:
                if hasattr(self.parent, 'test_scenarios') and index < len(self.parent.test_scenarios):
                    if script_info in self.parent.test_scenarios[index]['scripts']:
                        self.parent.test_scenarios[index]['scripts'].remove(script_info)
        except Exception as e:
            print(f"⚠️ Error removing script from UI: {e}")
    
    def _populate_section8_widgets_from_ui(self):
        """
        Populate section8_widgets with current UI data for export
        This ensures UI-uploaded files are included in the export process
        """
        print("DEBUG: Populating section8_widgets from current UI state")
        
        # 8.1 Test Scenarios - populate from self.test_scenarios
        if hasattr(self.parent, 'test_scenarios') and self.parent.test_scenarios:
            for i, scenario in enumerate(self.parent.test_scenarios):
                scenario_key = f"scenario_{i}"
                
                # Initialize widget data if not exists
                if scenario_key not in self.section8_widgets:
                    self.section8_widgets[scenario_key] = {
                        'upload_images_list': [],
                        'upload_scripts_list': [],
                        'scenario_data': scenario
                    }
                
                # Add images from scenario
                if 'images' in scenario and scenario['images']:
                    for image_info in scenario['images']:
                        # Convert UI image info to export format
                        export_image_info = {
                            'path': image_info.get('path', ''),
                            'filename': image_info.get('filename', ''),
                            'original_filename': image_info.get('original_filename', ''),
                            'description': image_info.get('description', ''),
                            'is_placeholder': image_info.get('is_placeholder', False)
                        }
                        self.section8_widgets[scenario_key]['upload_images_list'].append(export_image_info)
                        print(f"DEBUG: Added UI image to section8_widgets: {export_image_info['filename']}")
                
                # Add scripts from scenario
                if 'scripts' in scenario and scenario['scripts']:
                    for script_info in scenario['scripts']:
                        # Convert UI script info to export format
                        export_script_info = {
                            'path': script_info.get('path', ''),
                            'filename': script_info.get('filename', ''),
                            'original_filename': script_info.get('original_filename', ''),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        }
                        self.section8_widgets[scenario_key]['upload_scripts_list'].append(export_script_info)
                        print(f"DEBUG: Added UI script to section8_widgets: {export_script_info['filename']}")
        
        # 8.2 Test Bed Diagram - populate from self.test_bed_diagram_data
        if hasattr(self.parent, 'test_bed_diagram_data') and self.parent.test_bed_diagram_data:
            tbd_key = "test_bed_diagram"
            
            # Initialize widget data if not exists
            if tbd_key not in self.section8_widgets:
                self.section8_widgets[tbd_key] = {
                    'upload_images_list': [],
                    'upload_scripts_list': [],
                    'tbd_data': self.parent.test_bed_diagram_data
                }
            
            # Add images from test bed diagram
            if 'images' in self.parent.test_bed_diagram_data and self.parent.test_bed_diagram_data['images']:
                for image_info in self.parent.test_bed_diagram_data['images']:
                    export_image_info = {
                        'path': image_info.get('path', ''),
                        'filename': image_info.get('filename', ''),
                        'original_filename': image_info.get('original_filename', ''),
                        'description': image_info.get('description', ''),
                        'is_placeholder': image_info.get('is_placeholder', False)
                    }
                    self.section8_widgets[tbd_key]['upload_images_list'].append(export_image_info)
                    print(f"DEBUG: Added UI test bed image to section8_widgets: {export_image_info['filename']}")
            
            # Add scripts from test bed diagram
            if 'scripts' in self.parent.test_bed_diagram_data and self.parent.test_bed_diagram_data['scripts']:
                for script_info in self.parent.test_bed_diagram_data['scripts']:
                    export_script_info = {
                        'path': script_info.get('path', ''),
                        'filename': script_info.get('filename', ''),
                        'original_filename': script_info.get('original_filename', ''),
                        'description': script_info.get('description', ''),
                        'is_pasted': script_info.get('is_pasted', False)
                    }
                    self.section8_widgets[tbd_key]['upload_scripts_list'].append(export_script_info)
                    print(f"DEBUG: Added UI test bed script to section8_widgets: {export_script_info['filename']}")
        
        # 8.3 Tools Required - populate from self.tools_required
        if hasattr(self.parent, 'tools_required') and self.parent.tools_required:
            for i, tool in enumerate(self.parent.tools_required):
                tool_key = f"tool_{i}"
                
                # Initialize widget data if not exists
                if tool_key not in self.section8_widgets:
                    self.section8_widgets[tool_key] = {
                        'upload_images_list': [],
                        'upload_scripts_list': [],
                        'tool_data': tool
                    }
                
                # Add images from tool
                if 'images' in tool and tool['images']:
                    for image_info in tool['images']:
                        # Convert UI image info to export format
                        export_image_info = {
                            'path': image_info.get('path', ''),
                            'filename': image_info.get('filename', ''),
                            'original_filename': image_info.get('original_filename', ''),
                            'description': image_info.get('description', ''),
                            'is_placeholder': image_info.get('is_placeholder', False)
                        }
                        self.section8_widgets[tool_key]['upload_images_list'].append(export_image_info)
                        print(f"DEBUG: Added UI tool image to section8_widgets: {export_image_info['filename']}")
                
                # Add scripts from tool
                if 'scripts' in tool and tool['scripts']:
                    for script_info in tool['scripts']:
                        # Convert UI script info to export format
                        export_script_info = {
                            'path': script_info.get('path', ''),
                            'filename': script_info.get('filename', ''),
                            'original_filename': script_info.get('original_filename', ''),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        }
                        self.section8_widgets[tool_key]['upload_scripts_list'].append(export_script_info)
                        print(f"DEBUG: Added UI tool script to section8_widgets: {export_script_info['filename']}")
        
        # 8.4 Execution Steps - populate from self.execution_steps
        if hasattr(self.parent, 'execution_steps') and self.parent.execution_steps:
            for scenario_index, scenario in enumerate(self.parent.execution_steps):
                for step_index, step in enumerate(scenario.get('steps', [])):
                    step_key = f"exec_step_{scenario_index}_{step_index}"
                    
                    # Initialize widget data if not exists
                    if step_key not in self.section8_widgets:
                        self.section8_widgets[step_key] = {
                            'upload_images_list': [],
                            'upload_scripts_list': [],
                            'step_data': step
                        }
                    
                    # Add images from step
                    if 'images' in step and step['images']:
                        for image_info in step['images']:
                            # Convert UI image info to export format
                            export_image_info = {
                                'path': image_info.get('path', ''),
                                'filename': image_info.get('filename', ''),
                                'original_filename': image_info.get('original_filename', ''),
                                'description': image_info.get('description', ''),
                                'is_placeholder': image_info.get('is_placeholder', False)
                            }
                            self.section8_widgets[step_key]['upload_images_list'].append(export_image_info)
                            print(f"DEBUG: Added UI execution step image to section8_widgets: {export_image_info['filename']}")
                    
                    # Add scripts from step
                    if 'scripts' in step and step['scripts']:
                        for script_info in step['scripts']:
                            # Convert UI script info to export format
                            export_script_info = {
                                'path': script_info.get('path', ''),
                                'filename': script_info.get('filename', ''),
                                'original_filename': script_info.get('original_filename', ''),
                                'description': script_info.get('description', ''),
                                'is_pasted': script_info.get('is_pasted', False)
                            }
                            self.section8_widgets[step_key]['upload_scripts_list'].append(export_script_info)
                            print(f"DEBUG: Added UI execution step script to section8_widgets: {export_script_info['filename']}")
        
        # 9. Expected Results - populate from self.expected_results
        if hasattr(self.parent, 'expected_results') and self.parent.expected_results:
            for i, expected_result in enumerate(self.parent.expected_results):
                expected_key = f"expected_result_{i}"
                
                # Initialize widget data if not exists
                if expected_key not in self.section8_widgets:
                    self.section8_widgets[expected_key] = {
                        'upload_images_list': [],
                        'upload_scripts_list': [],
                        'expected_result_data': expected_result
                    }
                
                # Add images from expected result
                if 'images' in expected_result and expected_result['images']:
                    for image_info in expected_result['images']:
                        # Convert UI image info to export format
                        export_image_info = {
                            'path': image_info.get('path', ''),
                            'filename': image_info.get('filename', ''),
                            'original_filename': image_info.get('original_filename', ''),
                            'description': image_info.get('description', ''),
                            'is_placeholder': image_info.get('is_placeholder', False)
                        }
                        self.section8_widgets[expected_key]['upload_images_list'].append(export_image_info)
                        print(f"DEBUG: Added UI expected result image to section8_widgets: {export_image_info['filename']}")
                
                # Add scripts from expected result
                if 'scripts' in expected_result and expected_result['scripts']:
                    for script_info in expected_result['scripts']:
                        # Convert UI script info to export format
                        export_script_info = {
                            'path': script_info.get('path', ''),
                            'filename': script_info.get('filename', ''),
                            'original_filename': script_info.get('original_filename', ''),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        }
                        self.section8_widgets[expected_key]['upload_scripts_list'].append(export_script_info)
                        print(f"DEBUG: Added UI expected result script to section8_widgets: {export_script_info['filename']}")
        
        # 10. Evidence Format - populate from self.evidence_format
        if hasattr(self.parent, 'evidence_format') and self.parent.evidence_format:
            for i, evidence_data in enumerate(self.parent.evidence_format):
                evidence_key = f"evidence_format_{i}"
                
                # Initialize widget data if not exists
                if evidence_key not in self.section8_widgets:
                    self.section8_widgets[evidence_key] = {
                        'upload_images_list': [],
                        'upload_scripts_list': [],
                        'evidence_data': evidence_data
                    }
                
                # Add images from evidence format
                if 'images' in evidence_data and evidence_data['images']:
                    for image_info in evidence_data['images']:
                        # Convert UI image info to export format
                        export_image_info = {
                            'path': image_info.get('path', ''),
                            'filename': image_info.get('filename', ''),
                            'original_filename': image_info.get('original_filename', ''),
                            'description': image_info.get('description', ''),
                            'is_placeholder': image_info.get('is_placeholder', False)
                        }
                        self.section8_widgets[evidence_key]['upload_images_list'].append(export_image_info)
                        print(f"DEBUG: Added UI evidence format image to section8_widgets: {export_image_info['filename']}")
                
                # Add scripts from evidence format
                if 'scripts' in evidence_data and evidence_data['scripts']:
                    for script_info in evidence_data['scripts']:
                        # Convert UI script info to export format
                        export_script_info = {
                            'path': script_info.get('path', ''),
                            'filename': script_info.get('filename', ''),
                            'original_filename': script_info.get('original_filename', ''),
                            'description': script_info.get('description', ''),
                            'is_pasted': script_info.get('is_pasted', False)
                        }
                        self.section8_widgets[evidence_key]['upload_scripts_list'].append(export_script_info)
                        print(f"DEBUG: Added UI evidence format script to section8_widgets: {export_script_info['filename']}")
        
        print(f"DEBUG: Section8_widgets populated from UI: {len(self.section8_widgets)} widgets")
    
    def copy_section8_media_on_export(self, test_case_folder: str, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy Section 8 media during export using the same pattern as Section 11
        Mirrors the Section 11 script copying logic exactly
        """
        print("DEBUG: ===== SECTION 8 MEDIA COPYING START (Section 11 Pattern) =====")
        print(f"DEBUG: Export called for test_case_folder: {test_case_folder}")
        print(f"DEBUG: Current section8_widgets count: {len(self.section8_widgets)}")
        
        # First, populate section8_widgets with current UI data if not already populated
        self._populate_section8_widgets_from_ui()
        
        code_folder = os.path.join(test_case_folder, "code")
        raw_logs_folder = os.path.join(test_case_folder, "raw_logs")
        template_config_path = os.path.join(test_case_folder, "configuration", "template_config.json")
        
        # Ensure folders exist
        os.makedirs(code_folder, exist_ok=True)
        os.makedirs(raw_logs_folder, exist_ok=True)
        
        # Debug import project directory
        if hasattr(self.parent, 'import_project_dir'):
            print(f"DEBUG: Using import_project_dir: {self.parent.import_project_dir}")
        else:
            print("DEBUG: No import_project_dir found")
        
        if self.section8_widgets:
            print(f"DEBUG: Found section8_widgets: {list(self.section8_widgets.keys())}")
            scripts_copied = 0
            images_copied = 0
            
            for widget_key, widget_data in self.section8_widgets.items():
                # Copy scripts (same as Section 11)
                if 'upload_scripts_list' in widget_data and widget_data['upload_scripts_list']:
                    print(f"DEBUG: Found {len(widget_data['upload_scripts_list'])} scripts in {widget_key}")
                    for script_info in widget_data['upload_scripts_list']:
                        # Use 'path' field instead of 'original_path' (same as Section 11)
                        relative_path = script_info.get('path', '')
                        filename = script_info.get('filename', '')
                        print(f"DEBUG: Script path from JSON: {relative_path}")
                        print(f"DEBUG: Script filename: {filename}")
                        
                        if relative_path:
                            # Determine if this is a UI-uploaded file or imported file
                            if relative_path.startswith('tmp/') and hasattr(self.parent, 'absolute_path'):
                                # UI-uploaded file - use absolute_path directly
                                absolute_path = script_info.get('absolute_path', '')
                                if not absolute_path:
                                    # Fallback: construct from relative path
                                    absolute_path = os.path.join(os.getcwd(), relative_path)
                            else:
                                # Imported file - combine with import_project_dir
                                if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                    absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                                else:
                                    absolute_path = os.path.join(os.getcwd(), relative_path)
                            
                            print(f"DEBUG: Resolved absolute path: {absolute_path}")
                            
                            if os.path.exists(absolute_path):
                                new_filename = filename
                                dst_path = os.path.join(code_folder, new_filename)
                                
                                # Copy the file (same as Section 11)
                                print(f"DEBUG: About to copy file from {absolute_path} to {dst_path}")
                                shutil.copy2(absolute_path, dst_path)
                                print(f"✅ Copied Section 8 script: {filename} (keeping original filename)")
                                scripts_copied += 1
                                
                                # Update template_config.json with the new script information (same as Section 11)
                                self._update_template_config_with_section8_script(template_config, widget_key, script_info, new_filename, dst_path)
                            else:
                                print(f"⚠️ Section 8 script file not found at absolute path: {absolute_path}")
                        else:
                            print(f"⚠️ Missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
                
                # Copy images (same pattern as scripts)
                if 'upload_images_list' in widget_data and widget_data['upload_images_list']:
                    print(f"DEBUG: Found {len(widget_data['upload_images_list'])} images in {widget_key}")
                    for image_info in widget_data['upload_images_list']:
                        relative_path = image_info.get('path', '')
                        filename = image_info.get('filename', '')
                        print(f"DEBUG: Image path from JSON: {relative_path}")
                        print(f"DEBUG: Image filename: {filename}")
                        
                        if relative_path:
                            # Determine if this is a UI-uploaded file or imported file
                            if relative_path.startswith('tmp/') and hasattr(self.parent, 'absolute_path'):
                                # UI-uploaded file - use absolute_path directly
                                absolute_path = image_info.get('absolute_path', '')
                                if not absolute_path:
                                    # Fallback: construct from relative path
                                    absolute_path = os.path.join(os.getcwd(), relative_path)
                            else:
                                # Imported file - combine with import_project_dir
                                if hasattr(self.parent, 'import_project_dir') and self.parent.import_project_dir:
                                    absolute_path = os.path.join(self.parent.import_project_dir, relative_path)
                                else:
                                    absolute_path = os.path.join(os.getcwd(), relative_path)
                            
                            print(f"DEBUG: Resolved absolute path: {absolute_path}")
                            
                            if os.path.exists(absolute_path):
                                new_filename = filename
                                dst_path = os.path.join(raw_logs_folder, new_filename)
                                
                                print(f"DEBUG: About to copy image from {absolute_path} to {dst_path}")
                                shutil.copy2(absolute_path, dst_path)
                                print(f"✅ Copied Section 8 image: {filename} -> {new_filename}")
                                images_copied += 1
                                
                                # Update template_config.json with the new image information
                                self._update_template_config_with_section8_image(template_config, widget_key, image_info, new_filename, dst_path)
                            else:
                                print(f"⚠️ Section 8 image file not found at absolute path: {absolute_path}")
                        else:
                            print(f"⚠️ Missing path or import_project_dir: path={relative_path}, import_project_dir={getattr(self.parent, 'import_project_dir', 'Not set')}")
            
            print(f"DEBUG: Total Section 8 scripts copied: {scripts_copied}")
            print(f"DEBUG: Total Section 8 images copied: {images_copied}")
        else:
            print("DEBUG: No section8_widgets found for Section 8 media copying")
        
        print("DEBUG: ===== SECTION 8 MEDIA COPYING COMPLETED =====")
        return template_config
    
    def _update_template_config_with_section8_script(self, template_config: Dict[str, Any], widget_key: str, script_info: Dict[str, Any], new_filename: str, dst_path: str):
        """Update template_config.json with new Section 8 script data (same pattern as Section 11)"""
        try:
            print(f"DEBUG: Updating template_config.json for {widget_key} with script {new_filename}")
            
            # Get the configuration section
            configuration = template_config.get('configuration', {})
            
            # Determine which section this widget belongs to and update accordingly
            if widget_key.startswith('scenario_'):
                # Update test_scenarios
                scenario_index = int(widget_key.split('_')[1])
                test_scenarios = configuration.get('test_scenarios', [])
                if scenario_index < len(test_scenarios):
                    if 'scripts' not in test_scenarios[scenario_index]:
                        test_scenarios[scenario_index]['scripts'] = []
                    
                    new_script_data = {
                        "path": f"code/{new_filename}",
                        "filename": new_filename,
                        "original_filename": script_info.get('original_filename', script_info.get('filename', '')),
                        "description": script_info.get('description', ''),
                        "is_pasted": False
                    }
                    test_scenarios[scenario_index]['scripts'].append(new_script_data)
                    print(f"✅ Added script data to test_scenarios[{scenario_index}]: {new_filename}")
            
            elif widget_key == 'test_bed_diagram':
                # Update test_bed_diagram
                test_bed_diagram = configuration.get('test_bed_diagram', {})
                if 'scripts' not in test_bed_diagram:
                    test_bed_diagram['scripts'] = []
                
                # Check if script with same original filename already exists to prevent duplicates
                original_filename = script_info.get('original_filename', script_info.get('filename', ''))
                existing_script_index = None
                for i, existing_script in enumerate(test_bed_diagram['scripts']):
                    if existing_script.get('original_filename') == original_filename:
                        existing_script_index = i
                        break
                
                new_script_data = {
                    "path": f"code/{new_filename}",
                    "filename": new_filename,
                    "original_filename": original_filename,
                    "description": script_info.get('description', ''),
                    "is_pasted": False
                }
                
                if existing_script_index is not None:
                    # Update existing entry instead of adding duplicate
                    test_bed_diagram['scripts'][existing_script_index] = new_script_data
                    print(f"✅ Updated existing script data in test_bed_diagram: {new_filename}")
                else:
                    # Add new entry only if no duplicate exists
                    test_bed_diagram['scripts'].append(new_script_data)
                    print(f"✅ Added new script data to test_bed_diagram: {new_filename}")
            
            elif widget_key.startswith('tool_'):
                # Update tools_required
                tool_index = int(widget_key.split('_')[1])
                tools_required = configuration.get('tools_required', [])
                if tool_index < len(tools_required):
                    if 'scripts' not in tools_required[tool_index]:
                        tools_required[tool_index]['scripts'] = []
                    
                    new_script_data = {
                        "path": f"code/{new_filename}",
                        "filename": new_filename,
                        "original_filename": script_info.get('original_filename', script_info.get('filename', '')),
                        "description": script_info.get('description', ''),
                        "is_pasted": False
                    }
                    tools_required[tool_index]['scripts'].append(new_script_data)
                    print(f"✅ Added script data to tools_required[{tool_index}]: {new_filename}")
            
            elif widget_key.startswith('exec_step_'):
                # Update execution_steps
                step_index = int(widget_key.split('_')[2])
                execution_steps = configuration.get('execution_steps', [])
                if step_index < len(execution_steps):
                    if 'scripts' not in execution_steps[step_index]:
                        execution_steps[step_index]['scripts'] = []
                    
                    new_script_data = {
                        "path": f"code/{new_filename}",
                        "filename": new_filename,
                        "original_filename": script_info.get('original_filename', script_info.get('filename', '')),
                        "description": script_info.get('description', ''),
                        "is_pasted": False
                    }
                    execution_steps[step_index]['scripts'].append(new_script_data)
                    print(f"✅ Added script data to execution_steps[{step_index}]: {new_filename}")
            
            elif widget_key.startswith('expected_result_'):
                # Update expected_results
                expected_index = int(widget_key.split('_')[2])
                expected_results = configuration.get('expected_results', [])
                if expected_index < len(expected_results):
                    if 'scripts' not in expected_results[expected_index]:
                        expected_results[expected_index]['scripts'] = []
                    
                    new_script_data = {
                        "path": f"code/{new_filename}",
                        "filename": new_filename,
                        "original_filename": script_info.get('original_filename', script_info.get('filename', '')),
                        "description": script_info.get('description', ''),
                        "is_pasted": False
                    }
                    expected_results[expected_index]['scripts'].append(new_script_data)
                    print(f"✅ Added script data to expected_results[{expected_index}]: {new_filename}")
            
            elif widget_key.startswith('evidence_format_'):
                # Update evidence_format
                evidence_index = int(widget_key.split('_')[2])
                evidence_format = configuration.get('evidence_format', [])
                if evidence_index < len(evidence_format):
                    if 'scripts' not in evidence_format[evidence_index]:
                        evidence_format[evidence_index]['scripts'] = []
                    
                    new_script_data = {
                        "path": f"code/{new_filename}",
                        "filename": new_filename,
                        "original_filename": script_info.get('original_filename', script_info.get('filename', '')),
                        "description": script_info.get('description', ''),
                        "is_pasted": False
                    }
                    evidence_format[evidence_index]['scripts'].append(new_script_data)
                    print(f"✅ Added script data to evidence_format[{evidence_index}]: {new_filename}")
                
        except Exception as e:
            print(f"⚠️ Error updating template_config.json for Section 8 script: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_template_config_with_section8_image(self, template_config: Dict[str, Any], widget_key: str, image_info: Dict[str, Any], new_filename: str, dst_path: str):
        """Update template_config.json with new Section 8 image data"""
        try:
            print(f"DEBUG: Updating template_config.json for {widget_key} with image {new_filename}")
            
            configuration = template_config.get('configuration', {})
            
            # Determine which section this widget belongs to and update accordingly
            if widget_key.startswith('scenario_'):
                scenario_index = int(widget_key.split('_')[1])
                test_scenarios = configuration.get('test_scenarios', [])
                if scenario_index < len(test_scenarios):
                    if 'images' not in test_scenarios[scenario_index]:
                        test_scenarios[scenario_index]['images'] = []
                    
                    new_image_data = {
                        "path": f"raw_logs/{new_filename}",
                        "filename": new_filename,
                        "original_filename": image_info.get('original_filename', image_info.get('filename', '')),
                        "description": image_info.get('description', ''),
                        "is_placeholder": False
                    }
                    test_scenarios[scenario_index]['images'].append(new_image_data)
                    print(f"✅ Added image data to test_scenarios[{scenario_index}]: {new_filename}")
            
            elif widget_key == 'test_bed_diagram':
                test_bed_diagram = configuration.get('test_bed_diagram', {})
                if 'images' not in test_bed_diagram:
                    test_bed_diagram['images'] = []
                
                # Check if image with same original filename already exists to prevent duplicates
                original_filename = image_info.get('original_filename', image_info.get('filename', ''))
                existing_image_index = None
                for i, existing_image in enumerate(test_bed_diagram['images']):
                    if existing_image.get('original_filename') == original_filename:
                        existing_image_index = i
                        break
                
                new_image_data = {
                    "path": f"raw_logs/{new_filename}",
                    "filename": new_filename,
                    "original_filename": original_filename,
                    "description": image_info.get('description', ''),
                    "is_placeholder": False
                }
                
                if existing_image_index is not None:
                    # Update existing entry instead of adding duplicate
                    test_bed_diagram['images'][existing_image_index] = new_image_data
                    print(f"✅ Updated existing image data in test_bed_diagram: {new_filename}")
                else:
                    # Add new entry only if no duplicate exists
                    test_bed_diagram['images'].append(new_image_data)
                    print(f"✅ Added new image data to test_bed_diagram: {new_filename}")
            
            elif widget_key.startswith('tool_'):
                tool_index = int(widget_key.split('_')[1])
                tools_required = configuration.get('tools_required', [])
                if tool_index < len(tools_required):
                    if 'images' not in tools_required[tool_index]:
                        tools_required[tool_index]['images'] = []
                    
                    new_image_data = {
                        "path": f"raw_logs/{new_filename}",
                        "filename": new_filename,
                        "original_filename": image_info.get('original_filename', image_info.get('filename', '')),
                        "description": image_info.get('description', ''),
                        "is_placeholder": False
                    }
                    tools_required[tool_index]['images'].append(new_image_data)
                    print(f"✅ Added image data to tools_required[{tool_index}]: {new_filename}")
            
            elif widget_key.startswith('exec_step_'):
                step_index = int(widget_key.split('_')[2])
                execution_steps = configuration.get('execution_steps', [])
                if step_index < len(execution_steps):
                    if 'images' not in execution_steps[step_index]:
                        execution_steps[step_index]['images'] = []
                    
                    new_image_data = {
                        "path": f"raw_logs/{new_filename}",
                        "filename": new_filename,
                        "original_filename": image_info.get('original_filename', image_info.get('filename', '')),
                        "description": image_info.get('description', ''),
                        "is_placeholder": False
                    }
                    execution_steps[step_index]['images'].append(new_image_data)
                    print(f"✅ Added image data to execution_steps[{step_index}]: {new_filename}")
            
            elif widget_key.startswith('expected_result_'):
                # Update expected_results
                expected_index = int(widget_key.split('_')[2])
                expected_results = configuration.get('expected_results', [])
                if expected_index < len(expected_results):
                    if 'images' not in expected_results[expected_index]:
                        expected_results[expected_index]['images'] = []
                    
                    new_image_data = {
                        "path": f"raw_logs/{new_filename}",
                        "filename": new_filename,
                        "original_filename": image_info.get('original_filename', image_info.get('filename', '')),
                        "description": image_info.get('description', ''),
                        "is_placeholder": False
                    }
                    expected_results[expected_index]['images'].append(new_image_data)
                    print(f"✅ Added image data to expected_results[{expected_index}]: {new_filename}")
            
            elif widget_key.startswith('evidence_format_'):
                # Update evidence_format
                evidence_index = int(widget_key.split('_')[2])
                evidence_format = configuration.get('evidence_format', [])
                if evidence_index < len(evidence_format):
                    if 'images' not in evidence_format[evidence_index]:
                        evidence_format[evidence_index]['images'] = []
                    
                    new_image_data = {
                        "path": f"raw_logs/{new_filename}",
                        "filename": new_filename,
                        "original_filename": image_info.get('original_filename', image_info.get('filename', '')),
                        "description": image_info.get('description', ''),
                        "is_placeholder": False
                    }
                    evidence_format[evidence_index]['images'].append(new_image_data)
                    print(f"✅ Added image data to evidence_format[{evidence_index}]: {new_filename}")
                
        except Exception as e:
            print(f"⚠️ Error updating template_config.json for Section 8 image: {e}")
            import traceback
            traceback.print_exc()
