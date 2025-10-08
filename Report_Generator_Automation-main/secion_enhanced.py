#section 11

#!/usr/bin/env python3
"""
Enhanced Export/Import System for AutoDoc Studio
Updated to store images, scripts, and placeholders per field/question
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class EnhancedExportImport:
    """Enhanced export/import system for AutoDoc Studio with per-field storage"""
    
    def __init__(self, test_case_folder: str, step_widgets: Dict = None):
        print(f"🔧 Initializing EnhancedExportImport with folder: {test_case_folder}")
        self.test_case_folder = test_case_folder
        self.project_name = os.path.basename(test_case_folder)
        self.configuration_folder = os.path.join(test_case_folder, "configuration")
        self.questions_config_path = os.path.join(self.configuration_folder, "questions_config.json")
        self.template_config_path = os.path.join(self.configuration_folder, "template_config.json")
        self.step_widgets = step_widgets or {}
        
        print(f"📁 Creating folders...")
        # Ensure folders exist
        os.makedirs(self.configuration_folder, exist_ok=True)
        os.makedirs(os.path.join(test_case_folder, "raw_logs"), exist_ok=True)
        os.makedirs(os.path.join(test_case_folder, "code"), exist_ok=True)
        print(f"✅ Folders created successfully")
    
    def export_complete_configuration(self, app_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Export complete configuration including all data, images, scripts, and placeholders per field"""
        try:
            print(f"🔍 DEBUG: app_data sections_1_7 in export_complete_configuration: {app_data.get('configuration', {}).get('sections_1_7', {})}")
            # Process and organize all data with per-field storage
            processed_data = self._process_all_data_per_field(app_data)
            
            # Validate the processed data
            is_valid, validation_errors = self._validate_export_data(processed_data)
            
            if not is_valid:
                error_message = "❌ Export validation failed:\n"
                for error in validation_errors:
                    error_message += f"  - {error}\n"
                return False, error_message
            
            # Create questions_config.json (UI-focused)
            questions_config = self._create_questions_config(processed_data)
            
            # Create template_config.json (complete with file paths)
            template_config = self._create_template_config(processed_data)
            
            # Save both files with validation
            questions_success = self._save_json_file(self.questions_config_path, questions_config)
            template_success = self._save_json_file(self.template_config_path, template_config)
            
            # Copy files to proper folders
            files_success = self._copy_files_to_folders(processed_data)
            
            if questions_success and template_success and files_success:
                return True, f"✅ Configuration exported successfully to {self.configuration_folder}"
            else:
                return False, "❌ Failed to export some components"
                
        except Exception as e:
            return False, f"❌ Export failed: {str(e)}"
    
    def import_complete_configuration(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Import complete configuration from JSON files"""
        try:
            # Load both configuration files
            questions_config = self._load_json_file(self.questions_config_path)
            template_config = self._load_json_file(self.template_config_path)
            
            if not template_config:
                return False, f"❌ Template configuration not found at {self.template_config_path}", {}
            
            # Extract configuration data
            configuration = template_config.get("configuration", {})
            
            # Validate imported data
            validation_errors = []
            
            # Check for required sections
            required_sections = ["sections_1_7", "test_execution_cases", "dut_fields", "hash_sections", "itsar_fields"]
            for section in required_sections:
                if section not in configuration:
                    validation_errors.append(f"Missing required section: {section}")
                elif configuration[section] is None:
                    validation_errors.append(f"Required section is null: {section}")
            
            if validation_errors:
                error_message = "❌ Import validation failed:\n"
                for error in validation_errors:
                    error_message += f"  - {error}\n"
                return False, error_message, {}
            
            # Create complete app data structure
            app_data = {
                "export_timestamp": template_config.get("export_timestamp", ""),
                "test_case_name": template_config.get("test_case_name", ""),
                "configuration": configuration,
                "questions_config": questions_config or {}
            }
            
            return True, f"✅ Configuration imported successfully from {self.configuration_folder}", app_data
            
        except Exception as e:
            return False, f"❌ Import failed: {str(e)}", {}
    
    def _process_all_data_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all application data for export with per-field storage"""
        print("113: ", app_data)
        processed_data = {
            "export_timestamp": datetime.now().isoformat(),
            "test_case_name": app_data.get("test_case_name", ""),
            
            # DUT Configuration
            "dut_fields": self._process_dut_fields(app_data.get("dut_fields", [])),
            "hash_sections": self._process_hash_sections(app_data.get("hash_sections", [])),
            "itsar_fields": self._process_itsar_fields(app_data.get("itsar_fields", [])),
            "machine_ip": app_data.get("machine_ip", ""),
            "target_ip": app_data.get("target_ip", ""),
            "ssh_username": app_data.get("ssh_username", "admin"),
            "ssh_password": app_data.get("ssh_password", ""),
            "screenshots": app_data.get("screenshots", []),
            "interfaces": app_data.get("interfaces", []),
            
            # Sections 1-7 with per-field storage
            "sections_1_7": self._process_sections_1_7_per_field(app_data),
            
            # Section 8 Test Plan
            "test_plan_overview": app_data.get("test_plan_overview", ""),
            "test_scenarios": self._process_test_scenarios(app_data.get("test_scenarios", [])),
            "test_bed_diagram": self._process_test_bed_diagram(app_data.get("test_bed_diagram", {})),
            "test_bed_images": self._process_images_for_field(app_data.get("test_bed_images", [])),
            "test_bed_scripts": self._process_scripts_for_field(app_data.get("test_bed_scripts", [])),
            "tools_required": self._process_tools_required(app_data.get("tools_required", [])),
            "execution_steps": self._process_execution_steps(app_data.get("execution_steps", [])),
            "manual_execution_steps": app_data.get("manual_execution_steps", []),
            
            # Section 11 Test Execution
            "test_execution_cases": self._process_test_execution_cases(app_data.get("test_execution_cases", [])),
            "step_images": self._process_images_for_field(app_data.get("step_images", [])),
            
            # Other configuration
            "report_title": app_data.get("report_title", ""),
            "report_number": app_data.get("report_number", ""),
            "template_path": app_data.get("template_path", ""),
            "export_path": app_data.get("export_path", ""),
            "export_filename": app_data.get("export_filename", ""),
            
            # Headings
            "test_scenarios_heading": app_data.get("test_scenarios_heading", "Number of Test Scenarios"),
            "test_bed_diagram_heading": app_data.get("test_bed_diagram_heading", "Test Bed Diagram"),
            "tools_required_heading": app_data.get("tools_required_heading", "Tools Required"),
            "test_execution_steps_heading": app_data.get("test_execution_steps_heading", "Test Execution Steps"),
            "expected_results_heading": app_data.get("expected_results_heading", "Expected Result"),
            "expected_format_evidence_heading": app_data.get("expected_format_evidence_heading", "Expected Format of Evidence"),
            
            # Results and evidence
            "expected_results": self._process_expected_results(app_data.get("expected_results", [])),
            "evidence_format": app_data.get("evidence_format", []),
            "test_case_results": app_data.get("test_case_results", []),
            
            # UI-specific data for questions_config.json
            "essential_questions": app_data.get("essential_questions", []),
            "execution_step_questions": app_data.get("execution_step_questions", []),
            "configuration_fields": app_data.get("configuration_fields", [])
        }
        
        return processed_data
    
    def _process_dut_fields(self, dut_fields: List[Dict]) -> List[Dict]:
        """Process DUT fields with per-field images, scripts, and placeholders"""
        processed_fields = []
        for field in dut_fields:
            if isinstance(field, dict):
                processed_field = field.copy()
                processed_field["images"] = self._process_images_for_field(field.get("images", []))
                processed_field["scripts"] = self._process_scripts_for_field(field.get("scripts", []))
                processed_field["placeholders"] = self._process_placeholders_for_field(field.get("placeholders", []))
                processed_fields.append(processed_field)
        return processed_fields
    
    def _process_hash_sections(self, hash_sections: List[Dict]) -> List[Dict]:
        """Process hash sections with per-field storage"""
        processed_sections = []
        for section in hash_sections:
            if isinstance(section, dict):
                processed_section = section.copy()
                
                # Process direct hash images and scripts
                processed_section["direct_hash_images"] = self._process_images_for_field(section.get("direct_hash_images", []))
                processed_section["direct_hash_scripts"] = self._process_scripts_for_field(section.get("direct_hash_scripts", []))
                
                # Process hash fields
                processed_section["hash_fields"] = self._process_hash_fields(section.get("hash_fields", []))
                
                processed_sections.append(processed_section)
        return processed_sections
    
    def _process_hash_fields(self, hash_fields: List[Dict]) -> List[Dict]:
        """Process hash fields with per-field storage"""
        processed_fields = []
        for field in hash_fields:
            if isinstance(field, dict):
                processed_field = field.copy()
                processed_field["images"] = self._process_images_for_field(field.get("images", []))
                processed_field["scripts"] = self._process_scripts_for_field(field.get("scripts", []))
                processed_field["placeholders"] = self._process_placeholders_for_field(field.get("placeholders", []))
                processed_fields.append(processed_field)
        return processed_fields
    
    def _process_itsar_fields(self, itsar_fields: List[Dict]) -> List[Dict]:
        """Process ITSAR fields with per-field storage"""
        processed_fields = []
        for field in itsar_fields:
            if isinstance(field, dict):
                processed_field = field.copy()
                processed_field["images"] = self._process_images_for_field(field.get("images", []))
                processed_field["scripts"] = self._process_scripts_for_field(field.get("scripts", []))
                processed_field["placeholders"] = self._process_placeholders_for_field(field.get("placeholders", []))
                processed_fields.append(processed_field)
        return processed_fields
    
    def _process_sections_1_7_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sections 1-7 with per-field storage"""
        sections_1_7 = app_data.get("sections_1_7", {})
        processed_sections = {}
        
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
                # Handle placeholders - could be string or list
                placeholders_data = section_data.get("placeholders", [])
                if isinstance(placeholders_data, str):
                    # If it's a string, keep it as is (for sections 2 and 3)
                    processed_placeholders = placeholders_data
                else:
                    # If it's a list, process it normally
                    processed_placeholders = self._process_placeholders_for_field(placeholders_data)
                
                processed_section.update({
                    "heading": section_data.get("heading", ""),
                    "content": section_data.get("content", ""),
                    "text": section_data.get("text", ""),
                    "images": self._process_images_for_field(section_data.get("images", [])),
                    "scripts": self._process_scripts_for_field(section_data.get("scripts", [])),
                    "placeholders": processed_placeholders
                })
            
            processed_sections[section_key] = processed_section
        
        return processed_sections
    
    def _process_test_scenarios(self, test_scenarios: List[Dict]) -> List[Dict]:
        """Process test scenarios with per-field storage"""
        processed_scenarios = []
        for scenario in test_scenarios:
            if isinstance(scenario, dict):
                processed_scenario = scenario.copy()
                processed_scenario["images"] = self._process_images_for_field(scenario.get("images", []))
                processed_scenario["scripts"] = self._process_scripts_for_field(scenario.get("scripts", []))
                processed_scenario["placeholders"] = self._process_placeholders_for_field(scenario.get("placeholders", []))
                processed_scenarios.append(processed_scenario)
        return processed_scenarios
    
    def _process_tools_required(self, tools_required: List[Dict]) -> List[Dict]:
        """Process tools required with per-field storage"""
        processed_tools = []
        for tool in tools_required:
            if isinstance(tool, dict):
                processed_tool = tool.copy()
                processed_tool["images"] = self._process_images_for_field(tool.get("images", []))
                processed_tool["scripts"] = self._process_scripts_for_field(tool.get("scripts", []))
                processed_tool["placeholders"] = self._process_placeholders_for_field(tool.get("placeholders", []))
                processed_tools.append(processed_tool)
        return processed_tools
    
    def _process_execution_steps(self, execution_steps: List[Dict]) -> List[Dict]:
        """Process execution steps with per-field storage"""
        processed_steps = []
        for step in execution_steps:
            if isinstance(step, dict):
                processed_step = step.copy()
                processed_step["images"] = self._process_images_for_field(step.get("images", []))
                processed_step["scripts"] = self._process_scripts_for_field(step.get("scripts", []))
                processed_step["placeholders"] = self._process_placeholders_for_field(step.get("placeholders", []))
                processed_steps.append(processed_step)
        return processed_steps
    
    def _process_test_bed_diagram(self, test_bed_data: Dict) -> Dict:
        """Process test bed diagram data"""
        if not isinstance(test_bed_data, dict):
            return {"heading": "", "images": [], "scripts": []}
        
        processed_data = test_bed_data.copy()
        processed_data["images"] = self._process_images_for_field(test_bed_data.get("images", []))
        processed_data["scripts"] = self._process_scripts_for_field(test_bed_data.get("scripts", []))
        return processed_data

    def _process_test_execution_cases(self, test_execution_cases: List[Dict]) -> List[Dict]:
        """Process test execution cases with per-field storage"""
        print(f"DEBUG: _process_test_execution_cases called with {len(test_execution_cases)} cases")
        processed_cases = []
        for i, case in enumerate(test_execution_cases):
            print(f"DEBUG: Processing case {i}: {case.get('case_number', 'unknown')}")
            if isinstance(case, dict):
                processed_case = case.copy()
                processed_case["images"] = self._process_images_for_field(case.get("images", []))
                
                # CRITICAL FIX: Process case-level scripts from imported data
                case_scripts = case.get("scripts", [])
                print(f"DEBUG: Case {i} has {len(case_scripts)} scripts from imported case data")
                processed_case["scripts"] = self._process_scripts_for_field(case_scripts)
                
                # Get case-level placeholders from step widgets
                case_placeholders = []
                if hasattr(self, 'step_widgets') and self.step_widgets:
                    case_number = case.get('case_number', 1)
                    for step_key, step_widget in self.step_widgets.items():
                        if step_key.startswith(f"{case_number}_") and 'placeholders_list' in step_widget:
                            for placeholder_info in step_widget['placeholders_list']:
                                if isinstance(placeholder_info, dict) and 'name' in placeholder_info:
                                    case_placeholders.append({
                                        'name': placeholder_info['name'],
                                        'type': 'placeholder',
                                        'is_placeholder': True
                                    })
                
                print("349: ", case_placeholders)
                processed_case["placeholders"] = self._process_placeholders_for_field(case_placeholders)
                print("processed_case['placeholders']: ", processed_case["placeholders"])
                # Process step-level data
                if "steps_data" in processed_case:
                    print(f"DEBUG: Processing {len(processed_case['steps_data'])} steps for case {i}")
                    processed_steps_data = []
                    for j, step_data in enumerate(processed_case["steps_data"]):
                        print(f"DEBUG: Processing step {j+1} for case {i}")
                        if isinstance(step_data, dict):
                            processed_step = step_data.copy()
                            processed_step["images"] = self._process_images_for_field(step_data.get("images", []))
                            
                            # CRITICAL FIX: Process scripts from step_data first (imported data)
                            step_scripts = step_data.get("scripts", [])
                            print(f"DEBUG: Step {j+1} has {len(step_scripts)} scripts from imported step_data")
                            
                            # If step_data has scripts, use them; otherwise try to get from step widgets or preserved imported data
                            if step_scripts:
                                print(f"DEBUG: Using scripts from imported step_data for step {j+1}")
                                processed_step["scripts"] = self._process_scripts_for_field(step_scripts)
                            else:
                                # Fallback: Try to get scripts from step widgets or preserved imported data
                                print(f"DEBUG: No scripts in step_data, checking step widgets and preserved imported data for step {j+1}")
                                step_widget_scripts = []
                                
                                # Try to get scripts from step widgets first
                                if hasattr(self, 'step_widgets') and self.step_widgets:
                                    case_number = case.get('case_number', 1)
                                    step_index = step_data.get('step_index', j + 1)
                                    step_key = f"{case_number}_{step_index}"
                                    
                                    if step_key in self.step_widgets:
                                        step_widget = self.step_widgets[step_key]
                                        if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                                            step_widget_scripts = step_widget['upload_scripts_list']
                                            print(f"DEBUG: Found {len(step_widget_scripts)} scripts in step widget {step_key}")
                                
                                # If no scripts in step widgets, try to get from preserved imported data
                                if not step_widget_scripts and hasattr(self, '_imported_test_execution_data') and self._imported_test_execution_data:
                                    case_number = case.get('case_number', 1)
                                    step_index = step_data.get('step_index', j + 1)
                                    
                                    for imported_case in self._imported_test_execution_data:
                                        if imported_case.get('case_number') == case_number and 'steps_data' in imported_case:
                                            for imported_step_data in imported_case['steps_data']:
                                                if imported_step_data.get('step_index') == step_index and 'scripts' in imported_step_data and imported_step_data['scripts']:
                                                    step_widget_scripts = imported_step_data['scripts']
                                                    print(f"DEBUG: Found {len(step_widget_scripts)} scripts in preserved imported data for step {case_number}_{step_index}")
                                                    break
                                            if step_widget_scripts:
                                                break
                                    
                                processed_step["scripts"] = self._process_scripts_for_field(step_widget_scripts)
                            
                            # Get placeholders from step widgets instead of step data
                            step_placeholders = []
                            if hasattr(self, 'step_widgets') and self.step_widgets:
                                case_number = case.get('case_number', 1)
                                step_index = step_data.get('step_index', j + 1)
                                step_key = f"{case_number}_{step_index}"
                                if step_key in self.step_widgets:
                                    step_widget = self.step_widgets[step_key]
                                    if 'placeholders_list' in step_widget and step_widget['placeholders_list']:
                                        for placeholder_info in step_widget['placeholders_list']:
                                            if isinstance(placeholder_info, dict) and 'name' in placeholder_info:
                                                step_placeholders.append({
                                                    'name': placeholder_info['name'],
                                                    'type': 'placeholder',
                                                    'is_placeholder': True
                                                })
                            
                            print(f"DEBUG: Step {j+1} has {len(step_placeholders)} placeholders from step widgets")
                            
                            processed_step["placeholders"] = self._process_placeholders_for_field(step_placeholders)
                            print(f"DEBUG: Step {j+1} has {len(processed_step['placeholders'])} placeholders")
                            processed_steps_data.append(processed_step)
                        else:
                            processed_steps_data.append(step_data)
                    processed_case["steps_data"] = processed_steps_data
                
                processed_cases.append(processed_case)
        return processed_cases
    
    def _process_expected_results(self, expected_results: List[Dict]) -> List[Dict]:
        """Process expected results with per-field storage"""
        processed_results = []
        for result in expected_results:
            if isinstance(result, dict):
                processed_result = result.copy()
                processed_result["images"] = self._process_images_for_field(result.get("images", []))
                processed_result["scripts"] = self._process_scripts_for_field(result.get("scripts", []))
                processed_result["placeholders"] = self._process_placeholders_for_field(result.get("placeholders", []))
                processed_results.append(processed_result)
        return processed_results
    
    def _process_images_for_field(self, images: List[Any]) -> List[Dict[str, Any]]:
        """Process images for a specific field with proper paths"""
        processed_images = []
        
        print(f"DEBUG: _process_images_for_field called with images: {images}")
        print(f"DEBUG: images type: {type(images)}")
        
        for i, image in enumerate(images):
            print(f"DEBUG: Processing image {i}: {image} (type: {type(image)})")
            
            if isinstance(image, dict) and "path" in image:
                filename = os.path.basename(image["path"])
                processed_image = {
                    "path": f"raw_logs/{filename}",
                    "filename": filename,
                    "original_path": image.get("path", ""),
                    "description": image.get("description", "")
                }
                processed_images.append(processed_image)
                print(f"DEBUG: Added image with path: {filename}")
            elif isinstance(image, str):
                filename = os.path.basename(image)
                processed_image = {
                    "path": f"raw_logs/{filename}",
                    "filename": filename,
                    "original_path": image,
                    "description": ""
                }
                processed_images.append(processed_image)
                print(f"DEBUG: Added image from string: {filename}")
            else:
                print(f"ERROR: Image {i} is neither dict with 'path' nor string: {type(image)}")
        
        print(f"DEBUG: _process_images_for_field returning {len(processed_images)} images")
        return processed_images
    
    def _process_scripts_for_field(self, scripts: List[Any]) -> List[Dict[str, Any]]:
        """Process scripts for a specific field with proper paths"""
        processed_scripts = []
        
        print(f"DEBUG: _process_scripts_for_field called with scripts: {scripts}")
        print(f"DEBUG: scripts type: {type(scripts)}")
        
        for i, script in enumerate(scripts):
            print(f"DEBUG: Processing script {i}: {script} (type: {type(script)})")
            
            if isinstance(script, dict):
                print(f"DEBUG: Script {i} is a dict with keys: {list(script.keys())}")
                if "path" in script:
                    filename = os.path.basename(script["path"])
                    # Ensure we have the full absolute path for original_path
                    original_path = script.get("path", "")
                    if original_path and not os.path.isabs(original_path):
                        # Convert relative path to absolute path
                        original_path = os.path.abspath(original_path)
                        print(f"DEBUG: Converted relative path to absolute: {script.get('path', '')} -> {original_path}")
                    
                    processed_script = {
                        "path": f"code/{filename}",
                        "filename": filename,
                        "original_filename": script.get("original_filename", filename),
                        "description": script.get("description", ""),
                        "placeholder": script.get("placeholder", script.get("description", "")),  # Ensure placeholder is included
                        "is_pasted": script.get("is_pasted", False),
                        "original_path": original_path
                    }
                    print(f"🔍 DEBUG Export: Processed script with placeholder: '{script.get('placeholder', script.get('description', ''))}'")
                    processed_scripts.append(processed_script)
                    print(f"DEBUG: Added script with path: {filename}, original_path: {original_path}")
                elif "filename" in script:
                    processed_script = {
                        "path": f"code/{script['filename']}",
                        "filename": script["filename"],
                        "original_filename": script.get("original_filename", script["filename"]),
                        "description": script.get("description", ""),
                        "placeholder": script.get("placeholder", script.get("description", "")),  # Ensure placeholder is included
                        "is_pasted": script.get("is_pasted", False)
                    }
                    print(f"🔍 DEBUG Export: Processed script (filename) with placeholder: '{script.get('placeholder', script.get('description', ''))}'")
                    processed_scripts.append(processed_script)
                    print(f"DEBUG: Added script with filename: {script['filename']}")
                else:
                    print(f"ERROR: Script {i} dict has neither 'path' nor 'filename' key")
            elif isinstance(script, str):
                filename = os.path.basename(script)
                processed_script = {
                    "path": f"code/{filename}",
                    "filename": filename,
                    "original_filename": filename,
                    "description": "",
                    "is_pasted": False,
                    "original_path": script
                }
                processed_scripts.append(processed_script)
                print(f"DEBUG: Added script from string: {filename}")
            else:
                print(f"ERROR: Script {i} is neither dict nor string: {type(script)}")
        
        print(f"DEBUG: _process_scripts_for_field returning {len(processed_scripts)} scripts")
        return processed_scripts
    
    def _process_placeholders_for_field(self, placeholders: List[Any]) -> List[Dict[str, Any]]:
        """Process placeholders for a specific field with proper structure"""
        processed_placeholders = []
        
        print(f"DEBUG: _process_placeholders_for_field called with placeholders: {placeholders}")
        print(f"DEBUG: placeholders type: {type(placeholders)}")
        
        for i, placeholder in enumerate(placeholders):
            print(f"DEBUG: Processing placeholder {i}: {placeholder} (type: {type(placeholder)})")
            
            if isinstance(placeholder, dict):
                # Handle Section 11 placeholder structure
                if "name" in placeholder and "type" in placeholder:
                    processed_placeholder = {
                        "name": placeholder["name"],
                        "type": placeholder["type"],
                        "is_placeholder": placeholder.get("is_placeholder", True)
                    }
                    processed_placeholders.append(processed_placeholder)
                    print(f"DEBUG: Added Section 11 placeholder: {placeholder['name']}")
                # Handle legacy placeholder structure
                elif "placeholder" in placeholder:
                    processed_placeholder = {
                        "name": placeholder["placeholder"],
                        "type": "placeholder",
                        "is_placeholder": True
                    }
                    processed_placeholders.append(processed_placeholder)
                    print(f"DEBUG: Added legacy placeholder: {placeholder['placeholder']}")
                else:
                    print(f"DEBUG: Placeholder {i} dict missing required fields: {placeholder}")
            elif isinstance(placeholder, str):
                # Handle simple string placeholders
                processed_placeholder = {
                    "name": placeholder,
                    "type": "placeholder",
                    "is_placeholder": True
                }
                processed_placeholders.append(processed_placeholder)
                print(f"DEBUG: Added string placeholder: {placeholder}")
            else:
                print(f"ERROR: Placeholder {i} is neither dict nor string: {type(placeholder)}")
        
        print(f"DEBUG: _process_placeholders_for_field returning {len(processed_placeholders)} placeholders")
        return processed_placeholders
    
    def _create_questions_config(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create questions_config.json with UI-focused data"""
        
        # Determine number of scenarios for dynamic Summary generation
        test_scenarios = processed_data.get("test_scenarios", [])
        execution_blocks = processed_data.get("execution_blocks", [])
        test_execution_cases = processed_data.get("test_execution_cases", [])
        
        num_scenarios = 0
        if test_execution_cases:
            num_scenarios = len(test_execution_cases)
        elif execution_blocks:
            num_scenarios = len(execution_blocks)
        elif test_scenarios:
            num_scenarios = len(test_scenarios)
        else:
            num_scenarios = 1  # Default to 1 if no scenarios found
        
        # Generate dynamic Summary section
        summary_section = {}
        for i in range(1, num_scenarios + 1):
            result_key = f"result_{i}"
            remarks_key = f"remarks_{i}"
            summary_section[result_key] = "none"
            summary_section[remarks_key] = "none"
        
        questions_config = {
            "export_timestamp": processed_data["export_timestamp"],
            "test_case_name": processed_data["test_case_name"],
            "ui": {
                "title": "Security Assessment Report Generator"
            },
            "questions": {
                "essential_questions": processed_data["essential_questions"],
                "execution_step_questions": processed_data["execution_step_questions"]
            },
            "metadata": {
                "total_questions": len(processed_data["essential_questions"]) + len(processed_data["execution_step_questions"]),
                "description": "Automation questions configuration",
                "version": "1.0"
            },
            "configuration": {
                "fields": processed_data["configuration_fields"]
            },
            "Summary": summary_section
        }
        
        return questions_config
    
    def _create_template_config(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create template_config.json with complete data including file paths"""
        template_config = {
            "export_timestamp": processed_data["export_timestamp"],
            "test_case_name": processed_data["test_case_name"],
            "configuration": {
                # DUT Configuration
                "dut_fields": processed_data["dut_fields"],
                "hash_sections": processed_data["hash_sections"],
                "itsar_fields": processed_data["itsar_fields"],
                "machine_ip": processed_data["machine_ip"],
                "target_ip": processed_data["target_ip"],
                "ssh_username": processed_data["ssh_username"],
                "ssh_password": processed_data["ssh_password"],
                "screenshots": processed_data["screenshots"],
                "interfaces": processed_data["interfaces"],
                
                # Sections 1-7
                "sections_1_7": processed_data["sections_1_7"],
                
                # Section 8 Test Plan
                "test_plan_overview": processed_data["test_plan_overview"],
                "test_scenarios": processed_data["test_scenarios"],
                "test_bed_diagram": processed_data["test_bed_diagram"],
                "test_bed_images": processed_data["test_bed_images"],
                "test_bed_scripts": processed_data["test_bed_scripts"],
                "tools_required": processed_data["tools_required"],
                "execution_steps": processed_data["execution_steps"],
                "manual_execution_steps": processed_data["manual_execution_steps"],
                
                # Section 11 Test Execution
                "test_execution_cases": processed_data["test_execution_cases"],
                "step_images": processed_data["step_images"],
                
                # Other configuration
                "report_title": processed_data["report_title"],
                "report_number": processed_data["report_number"],
                "template_path": processed_data["template_path"],
                "export_path": processed_data["export_path"],
                "export_filename": processed_data["export_filename"],
                
                # Headings
                "test_scenarios_heading": processed_data["test_scenarios_heading"],
                "test_bed_diagram_heading": processed_data["test_bed_diagram_heading"],
                "tools_required_heading": processed_data["tools_required_heading"],
                "test_execution_steps_heading": processed_data["test_execution_steps_heading"],
                "expected_results_heading": processed_data["expected_results_heading"],
                "expected_format_evidence_heading": processed_data["expected_format_evidence_heading"],
                
                # Results and evidence
                "expected_results": processed_data["expected_results"],
                "evidence_format": processed_data["evidence_format"],
                "test_case_results": processed_data["test_case_results"]
            }
        }
        
        return template_config
    
    def _copy_files_to_folders(self, processed_data: Dict[str, Any]) -> bool:
        """Copy uploaded files to proper folders using raw_logs/ and code/ structure"""
        try:
            # Setup paths
            raw_logs_folder = os.path.join(self.test_case_folder, "raw_logs")
            code_folder = os.path.join(self.test_case_folder, "code")
            
            # Ensure folders exist
            os.makedirs(code_folder, exist_ok=True)
            os.makedirs(raw_logs_folder, exist_ok=True)
            
            # Copy images from all fields
            self._copy_images_from_fields(processed_data, raw_logs_folder)
            
            # Copy scripts from all fields
            self._copy_scripts_from_fields(processed_data, code_folder)
            
            return True
            
        except Exception as e:
            print(f"❌ Error copying files: {e}")
            # Continue with export even if file copying fails
            print(f"⚠️ Continuing with export despite file copying errors")
            return True
    
    def _copy_images_from_fields(self, processed_data: Dict[str, Any], raw_logs_folder: str):
        """Copy images from all fields to raw_logs folder"""
        # Copy from DUT fields
        for field in processed_data.get("dut_fields", []):
            for image in field.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    try:
                        shutil.copy2(src_path, dst_path)
                        print(f"🖼️ Copied DUT image: {image['filename']}")
                    except Exception as e:
                        print(f"⚠️ Failed to copy DUT image {image['filename']}: {e}")
                        # Continue with other files
        
        # Copy from hash sections
        for section in processed_data.get("hash_sections", []):
            # Direct hash images
            for image in section.get("direct_hash_images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"🖼️ Copied hash image: {image['filename']}")
            
            # Hash field images
            for field in section.get("hash_fields", []):
                for image in field.get("images", []):
                    if "original_path" in image and os.path.exists(image["original_path"]):
                        src_path = image["original_path"]
                        dst_path = os.path.join(raw_logs_folder, image["filename"])
                        shutil.copy2(src_path, dst_path)
                        print(f"🖼️ Copied hash field image: {image['filename']}")
        
        # Copy from ITSAR fields
        for field in processed_data.get("itsar_fields", []):
            for image in field.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"🖼️ Copied ITSAR image: {image['filename']}")
        
        # Copy from sections 1-7
        sections_1_7 = processed_data.get("sections_1_7", {})
        if isinstance(sections_1_7, dict):
            for section_key, section_data in sections_1_7.items():
                if isinstance(section_data, dict):
                    # Section images
                    images = section_data.get("images", [])
                    if isinstance(images, list):
                        for image in images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied {section_key} image: {image['filename']}")
                    
                    # Section pairs images
                    if "pairs" in section_data:
                        pairs = section_data["pairs"]
                        if isinstance(pairs, list):
                            for pair in pairs:
                                if isinstance(pair, dict):
                                    pair_images = pair.get("images", [])
                                    if isinstance(pair_images, list):
                                        for image in pair_images:
                                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                                src_path = image["original_path"]
                                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                                shutil.copy2(src_path, dst_path)
                                                print(f"🖼️ Copied {section_key} pair image: {image['filename']}")
        
        # Copy from test scenarios
        test_scenarios = processed_data.get("test_scenarios", [])
        if isinstance(test_scenarios, list):
            for scenario in test_scenarios:
                if isinstance(scenario, dict):
                    scenario_images = scenario.get("images", [])
                    if isinstance(scenario_images, list):
                        for image in scenario_images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied test scenario image: {image['filename']}")
        
        # Copy from test bed diagram
        test_bed_diagram = processed_data.get("test_bed_diagram", {})
        if isinstance(test_bed_diagram, dict):
            for image in test_bed_diagram.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"🖼️ Copied test bed diagram image: {image['filename']}")
        
        # Copy from tools required
        tools_required = processed_data.get("tools_required", [])
        if isinstance(tools_required, list):
            for tool in tools_required:
                if isinstance(tool, dict):
                    tool_images = tool.get("images", [])
                    if isinstance(tool_images, list):
                        for image in tool_images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied tool image: {image['filename']}")
        
        # Copy from execution steps
        execution_steps = processed_data.get("execution_steps", [])
        if isinstance(execution_steps, list):
            for step in execution_steps:
                if isinstance(step, dict):
                    step_images = step.get("images", [])
                    if isinstance(step_images, list):
                        for image in step_images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied execution step image: {image['filename']}")
        
        # Copy from test execution cases
        test_execution_cases = processed_data.get("test_execution_cases", [])
        if isinstance(test_execution_cases, list):
            for case in test_execution_cases:
                if isinstance(case, dict):
                    case_images = case.get("images", [])
                    if isinstance(case_images, list):
                        for image in case_images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied test execution case image: {image['filename']}")
        
        # Copy from expected results
        expected_results = processed_data.get("expected_results", [])
        if isinstance(expected_results, list):
            for result in expected_results:
                if isinstance(result, dict):
                    result_images = result.get("images", [])
                    if isinstance(result_images, list):
                        for image in result_images:
                            if isinstance(image, dict) and "original_path" in image and os.path.exists(image["original_path"]):
                                src_path = image["original_path"]
                                dst_path = os.path.join(raw_logs_folder, image["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"🖼️ Copied expected result image: {image['filename']}")
        
        # Copy from test execution cases
        for case in processed_data.get("test_execution_cases", []):
            # Copy case-level images
            for image in case.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"🖼️ Copied test execution case image: {image['filename']}")
            
            # Copy step-level images
            for step_data in case.get("steps_data", []):
                for image in step_data.get("images", []):
                    if "original_path" in image and os.path.exists(image["original_path"]):
                        src_path = image["original_path"]
                        dst_path = os.path.join(raw_logs_folder, image["filename"])
                        shutil.copy2(src_path, dst_path)
                        print(f"🖼️ Copied test execution step image: {image['filename']}")
        
        # Copy test bed images
        for image in processed_data.get("test_bed_images", []):
            if "original_path" in image and os.path.exists(image["original_path"]):
                src_path = image["original_path"]
                dst_path = os.path.join(raw_logs_folder, image["filename"])
                shutil.copy2(src_path, dst_path)
                print(f"🖼️ Copied test bed image: {image['filename']}")
        
        # Copy step images
        for image in processed_data.get("step_images", []):
            if "original_path" in image and os.path.exists(image["original_path"]):
                src_path = image["original_path"]
                dst_path = os.path.join(raw_logs_folder, image["filename"])
                shutil.copy2(src_path, dst_path)
                print(f"🖼️ Copied step image: {image['filename']}")
    
    def _copy_scripts_from_fields(self, processed_data: Dict[str, Any], code_folder: str):
        """Copy scripts from all fields to code folder"""
        print(f"DEBUG: ===== COPY SCRIPTS FROM FIELDS START =====")
        print(f"DEBUG: Code folder: {code_folder}")
        print(f"DEBUG: Code folder exists: {os.path.exists(code_folder)}")
        
        # Debug test execution cases
        test_execution_cases = processed_data.get("test_execution_cases", [])
        print(f"DEBUG: Found {len(test_execution_cases)} test execution cases")
        
        for i, case in enumerate(test_execution_cases):
            print(f"DEBUG: Case {i+1}: {case.get('case_number', 'unknown')}")
            steps_data = case.get("steps_data", [])
            print(f"DEBUG: Case {i+1} has {len(steps_data)} steps_data")
            
            for j, step_data in enumerate(steps_data):
                scripts = step_data.get("scripts", [])
                print(f"DEBUG: Step {j+1} has {len(scripts)} scripts")
                for script in scripts:
                    print(f"DEBUG: Script in step {j+1}: {script}")
                    if "original_path" in script:
                        print(f"DEBUG: Script original_path: {script['original_path']}")
                        print(f"DEBUG: Script original_path exists: {os.path.exists(script['original_path'])}")
        # Copy from DUT fields
        for field in processed_data.get("dut_fields", []):
            for script in field.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    try:
                        shutil.copy2(src_path, dst_path)
                        print(f"📜 Copied DUT script: {script['filename']}")
                    except Exception as e:
                        print(f"⚠️ Failed to copy DUT script {script['filename']}: {e}")
                        # Continue with other files
        
        # Copy from hash sections
        for section in processed_data.get("hash_sections", []):
            # Direct hash scripts
            for script in section.get("direct_hash_scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied hash script: {script['filename']}")
            
            # Hash field scripts
            for field in section.get("hash_fields", []):
                for script in field.get("scripts", []):
                    if "original_path" in script and os.path.exists(script["original_path"]):
                        src_path = script["original_path"]
                        dst_path = os.path.join(code_folder, script["filename"])
                        shutil.copy2(src_path, dst_path)
                        print(f"📜 Copied hash field script: {script['filename']}")
        
        # Copy from ITSAR fields
        for field in processed_data.get("itsar_fields", []):
            for script in field.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied ITSAR script: {script['filename']}")
        
        # Copy from sections 1-7
        sections_1_7 = processed_data.get("sections_1_7", {})
        for section_key, section_data in sections_1_7.items():
            if isinstance(section_data, dict):
                # Section scripts
                for script in section_data.get("scripts", []):
                    if "original_path" in script and os.path.exists(script["original_path"]):
                        src_path = script["original_path"]
                        dst_path = os.path.join(code_folder, script["filename"])
                        shutil.copy2(src_path, dst_path)
                        print(f"📜 Copied {section_key} script: {script['filename']}")
                
                # Section pairs scripts
                if "pairs" in section_data:
                    for pair in section_data["pairs"]:
                        for script in pair.get("scripts", []):
                            if "original_path" in script and os.path.exists(script["original_path"]):
                                src_path = script["original_path"]
                                dst_path = os.path.join(code_folder, script["filename"])
                                shutil.copy2(src_path, dst_path)
                                print(f"📜 Copied {section_key} pair script: {script['filename']}")
        
        # Copy from test scenarios
        for scenario in processed_data.get("test_scenarios", []):
            for script in scenario.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied test scenario script: {script['filename']}")
        
        # Copy from tools required
        for tool in processed_data.get("tools_required", []):
            for script in tool.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied tool script: {script['filename']}")
        
        # Copy from execution steps
        for step in processed_data.get("execution_steps", []):
            for script in step.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied execution step script: {script['filename']}")
        
        # Copy from test execution cases
        for case in processed_data.get("test_execution_cases", []):
            # Copy case-level scripts
            for script in case.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied test execution case script: {script['filename']}")
            
            # Copy scripts from steps_data (Section 11 execution steps)
            for step_data in case.get("steps_data", []):
                for script in step_data.get("scripts", []):
                    print(f"DEBUG: Processing script from steps_data: {script}")
                    if "original_path" in script and os.path.exists(script["original_path"]):
                        src_path = script["original_path"]
                        dst_path = os.path.join(code_folder, script["filename"])
                        try:
                            shutil.copy2(src_path, dst_path)
                            print(f"📜 Copied step script from steps_data: {script['filename']} (from {src_path})")
                        except Exception as e:
                            print(f"⚠️ Failed to copy step script {script['filename']}: {e}")
                            # Continue with other files
                    else:
                        print(f"⚠️ Script missing original_path or file not found: {script}")
        
        # Copy from expected results
        for result in processed_data.get("expected_results", []):
            for script in result.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied expected result script: {script['filename']}")
        
        print(f"DEBUG: ===== COPY SCRIPTS FROM FIELDS COMPLETED =====")
        
        # Simple script copying from imported data
        print("DEBUG: ===== SIMPLE SCRIPT COPYING START =====")
        if hasattr(self, 'step_widgets') and self.step_widgets:
            print(f"DEBUG: Found step_widgets: {list(self.step_widgets.keys())}")
            for step_key, step_widget in self.step_widgets.items():
                if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                    print(f"DEBUG: Found {len(step_widget['upload_scripts_list'])} scripts in step {step_key}")
                    for script_info in step_widget['upload_scripts_list']:
                        original_path = script_info.get('original_path', '')
                        filename = script_info.get('filename', '')
                        print(f"DEBUG: Script original_path: {original_path}")
                        print(f"DEBUG: Script filename: {filename}")
                        
                        if original_path and os.path.exists(original_path):
                            # Generate unique filename
                            import uuid
                            unique_id = str(uuid.uuid4())[:8]
                            new_filename = f"uploaded_{unique_id}_{filename}"
                            dst_path = os.path.join(code_folder, new_filename)
                            
                            # Copy the file
                            shutil.copy2(original_path, dst_path)
                            print(f"✅ Copied script: {filename} -> {new_filename}")
                        else:
                            print(f"⚠️ Script file not found: {original_path}")
        else:
            print("DEBUG: No step_widgets found for simple script copying")
        print("DEBUG: ===== SIMPLE SCRIPT COPYING COMPLETED =====")
        
        # Verify what files are in the code folder
        if os.path.exists(code_folder):
            files = os.listdir(code_folder)
            print(f"DEBUG: Files in code folder after copying: {files}")
            
            # Check for script files (now using original filenames)
            script_files = [f for f in files if f.endswith('.py')]
            print(f"DEBUG: Found {len(script_files)} script files: {script_files}")
            
            for script in script_files:
                script_path = os.path.join(code_folder, script)
                if os.path.exists(script_path):
                    file_size = os.path.getsize(script_path)
                    print(f"✅ Script {script} exists with size {file_size} bytes")
                else:
                    print(f"⚠️ Script {script} not found in code folder")
        else:
            print(f"⚠️ Code folder does not exist: {code_folder}")
        
        # Copy test bed scripts
        for script in processed_data.get("test_bed_scripts", []):
            if "original_path" in script and os.path.exists(script["original_path"]):
                src_path = script["original_path"]
                dst_path = os.path.join(code_folder, script["filename"])
                shutil.copy2(src_path, dst_path)
                print(f"📜 Copied test bed script: {script['filename']}")
        
        # Copy test bed diagram scripts
        test_bed_diagram = processed_data.get("test_bed_diagram", {})
        if isinstance(test_bed_diagram, dict):
            for script in test_bed_diagram.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    shutil.copy2(src_path, dst_path)
                    print(f"📜 Copied test bed diagram script: {script['filename']}")
    
    def _process_import_data(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process imported data and resolve all references with per-field storage"""
        try:
            configuration = template_config.get("configuration", {})
            
            # Process all fields to resolve relative paths to absolute paths
            self._resolve_field_paths(configuration)
            
            return template_config
            
        except Exception as e:
            print(f"❌ Error processing import data: {e}")
            return template_config
    
    def _resolve_field_paths(self, configuration: Dict[str, Any]):
        """Resolve relative paths to absolute paths for all fields"""
        # Resolve DUT fields
        for field in configuration.get("dut_fields", []):
            self._resolve_field_images_and_scripts(field)
        
        # Resolve hash sections
        for section in configuration.get("hash_sections", []):
            # Direct hash images and scripts
            self._resolve_field_images_and_scripts(section, "direct_hash_images", "direct_hash_scripts")
            
            # Hash fields
            for field in section.get("hash_fields", []):
                self._resolve_field_images_and_scripts(field)
        
        # Resolve ITSAR fields
        for field in configuration.get("itsar_fields", []):
            self._resolve_field_images_and_scripts(field)
        
        # Resolve sections 1-7
        sections_1_7 = configuration.get("sections_1_7", {})
        for section_key, section_data in sections_1_7.items():
            if isinstance(section_data, dict):
                # Section images and scripts
                self._resolve_field_images_and_scripts(section_data)
            
                # Section pairs
                if "pairs" in section_data:
                    for pair in section_data["pairs"]:
                        self._resolve_field_images_and_scripts(pair)
        
        # Resolve test scenarios
        for scenario in configuration.get("test_scenarios", []):
            self._resolve_field_images_and_scripts(scenario)
        
        # Resolve test bed diagram
        test_bed_diagram = configuration.get("test_bed_diagram", {})
        if isinstance(test_bed_diagram, dict):
            self._resolve_field_images_and_scripts(test_bed_diagram)
        
        # Resolve tools required
        for tool in configuration.get("tools_required", []):
            self._resolve_field_images_and_scripts(tool)
        
        # Resolve execution steps
        for step in configuration.get("execution_steps", []):
            self._resolve_field_images_and_scripts(step)
        
        # Resolve test execution cases
        for case in configuration.get("test_execution_cases", []):
            self._resolve_field_images_and_scripts(case)
            
            # Resolve step-level images and scripts
            for step_data in case.get("steps_data", []):
                self._resolve_field_images_and_scripts(step_data)
        
        # Resolve expected results
        for result in configuration.get("expected_results", []):
            self._resolve_field_images_and_scripts(result)
        
        # Resolve test bed images and scripts
        self._resolve_field_images_and_scripts(configuration, "test_bed_images", "test_bed_scripts")
        
        # Resolve step images
        self._resolve_field_images_and_scripts(configuration, "step_images", "")
    
    def _resolve_field_images_and_scripts(self, field: Dict[str, Any], images_key: str = "images", scripts_key: str = "scripts"):
        """Resolve images and scripts paths for a specific field"""
        # Resolve images
        for image in field.get(images_key, []):
            if isinstance(image, dict) and "path" in image:
                relative_path = image["path"]
                if relative_path.startswith("raw_logs/"):
                    filename = relative_path[len("raw_logs/"):]
                    absolute_path = os.path.join(self.test_case_folder, "raw_logs", filename)
                    image["absolute_path"] = absolute_path
        
        # Resolve scripts
        for script in field.get(scripts_key, []):
            if isinstance(script, dict) and "path" in script:
                relative_path = script["path"]
                if relative_path.startswith("code/"):
                    filename = relative_path[len("code/"):]
                    absolute_path = os.path.join(self.test_case_folder, "code", filename)
                    script["absolute_path"] = absolute_path
    

    
    def _validate_imported_files(self, processed_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all referenced files exist in per-field structure"""
        warnings = []
        configuration = processed_data.get("configuration", {})
        
        # Validate all fields recursively
        self._validate_field_files(configuration, warnings)
        
        return len(warnings) == 0, warnings
    
    def _validate_field_files(self, data: Any, warnings: List[str], field_path: str = ""):
        """Recursively validate files in all fields"""
        if isinstance(data, dict):
            # Check images in this field
            for image in data.get("images", []):
                if isinstance(image, dict) and "absolute_path" in image:
                    if not os.path.exists(image["absolute_path"]):
                        warnings.append(f"Image file not found in {field_path}: {image['filename']}")
        
            # Check scripts in this field
            for script in data.get("scripts", []):
                if isinstance(script, dict) and "absolute_path" in script:
                    if not os.path.exists(script["absolute_path"]):
                        warnings.append(f"Script file not found in {field_path}: {script['filename']}")
            
            # Check direct_hash_images and direct_hash_scripts
            for image in data.get("direct_hash_images", []):
                if isinstance(image, dict) and "absolute_path" in image:
                    if not os.path.exists(image["absolute_path"]):
                        warnings.append(f"Direct hash image file not found in {field_path}: {image['filename']}")
            
            for script in data.get("direct_hash_scripts", []):
                if isinstance(script, dict) and "absolute_path" in script:
                    if not os.path.exists(script["absolute_path"]):
                        warnings.append(f"Direct hash script file not found in {field_path}: {script['filename']}")
            
            # Check test_bed_images and test_bed_scripts
            for image in data.get("test_bed_images", []):
                if isinstance(image, dict) and "absolute_path" in image:
                    if not os.path.exists(image["absolute_path"]):
                        warnings.append(f"Test bed image file not found in {field_path}: {image['filename']}")
            
            for script in data.get("test_bed_scripts", []):
                if isinstance(script, dict) and "absolute_path" in script:
                    if not os.path.exists(script["absolute_path"]):
                        warnings.append(f"Test bed script file not found in {field_path}: {script['filename']}")
            
            # Check step_images
            for image in data.get("step_images", []):
                if isinstance(image, dict) and "absolute_path" in image:
                    if not os.path.exists(image["absolute_path"]):
                        warnings.append(f"Step image file not found in {field_path}: {image['filename']}")
            
            # Recursively check nested fields
            for key, value in data.items():
                if key not in ["images", "scripts", "direct_hash_images", "direct_hash_scripts", 
                              "test_bed_images", "test_bed_scripts", "step_images", "placeholders"]:
                    new_path = f"{field_path}.{key}" if field_path else key
                    self._validate_field_files(value, warnings, new_path)
        
        elif isinstance(data, list):
            # Check each item in the list
            for i, item in enumerate(data):
                new_path = f"{field_path}[{i}]" if field_path else f"[{i}]"
                self._validate_field_files(item, warnings, new_path)
    
    def _save_json_file(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON file with proper formatting and validation"""
        try:
            # Validate and clean data before saving
            cleaned_data, validation_errors = self._validate_and_clean_data(data)
            
            if validation_errors:
                print(f"⚠️ Validation warnings for {os.path.basename(file_path)}:")
                for error in validation_errors:
                    print(f"  - {error}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            print(f"❌ Error saving {os.path.basename(file_path)}: {e}")
            return False
    
    def _validate_and_clean_data(self, data: Any, path: str = "root") -> Tuple[Any, List[str]]:
        """
        Recursively validate and clean data to ensure JSON serializability
        
        Args:
            data: The data to validate and clean
            path: Current path in the data structure for error reporting
            
        Returns:
            Tuple of (cleaned_data, validation_errors)
        """
        validation_errors = []
        
        if data is None:
            return None, validation_errors
        
        # Handle Qt widgets and other non-serializable objects
        if hasattr(data, 'text'):
            try:
                return data.text(), validation_errors
            except Exception as e:
                validation_errors.append(f"{path}: Could not extract text from widget: {e}")
                return "", validation_errors
        
        if hasattr(data, 'toPlainText'):
            try:
                return data.toPlainText(), validation_errors
            except Exception as e:
                validation_errors.append(f"{path}: Could not extract plain text from widget: {e}")
                return "", validation_errors
        
        # Handle dictionaries
        if isinstance(data, dict):
            cleaned_dict = {}
            for key, value in data.items():
                # Strip original_path for scripts and images in final JSON (keep internal use elsewhere)
                if key == "original_path":
                    path_value = data.get("path", "")
                    if isinstance(path_value, str) and (
                        path_value.startswith("code/") or path_value.startswith("raw_logs/")
                    ):
                        # Skip writing original_path for scripts and images
                        continue
                cleaned_value, errors = self._validate_and_clean_data(value, f"{path}.{key}")
                cleaned_dict[key] = cleaned_value
                validation_errors.extend(errors)
            return cleaned_dict, validation_errors
        
        # Handle lists
        elif isinstance(data, list):
            cleaned_list = []
            for i, item in enumerate(data):
                cleaned_item, errors = self._validate_and_clean_data(item, f"{path}[{i}]")
                cleaned_list.append(cleaned_item)
                validation_errors.extend(errors)
            return cleaned_list, validation_errors
        
        # Handle basic types that are JSON serializable
        elif isinstance(data, (str, int, float, bool)):
            return data, validation_errors
        
        # Handle other types by converting to string
        else:
            try:
                return str(data), validation_errors
            except Exception as e:
                validation_errors.append(f"{path}: Could not serialize object of type {type(data).__name__}: {e}")
                return "", validation_errors
    
    def _validate_export_data(self, processed_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate export data for completeness and required fields
        
        Args:
            processed_data: The processed data to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        # Check for required top-level fields
        required_fields = [
            "export_timestamp", "test_case_name", "sections_1_7", 
            "test_execution_cases", "dut_fields", "hash_sections", "itsar_fields"
        ]
        
        for field in required_fields:
            if field not in processed_data:
                validation_errors.append(f"Missing required field: {field}")
            elif processed_data[field] is None:
                validation_errors.append(f"Required field is null: {field}")
        
        # Validate sections_1_7 data
        sections_1_7 = processed_data.get("sections_1_7", {})
        if isinstance(sections_1_7, dict):
            for section_key in ["section_1", "section_2", "section_3", "section_4", "section_5", "section_6", "section_7"]:
                if section_key not in sections_1_7:
                    validation_errors.append(f"Missing section in sections_1_7: {section_key}")
                else:
                    section_data = sections_1_7[section_key]
                    if isinstance(section_data, dict):
                        if "heading" not in section_data:
                            validation_errors.append(f"Missing heading in {section_key}")
                        if "content" not in section_data and section_key not in ["section_4", "section_5"]:
                            validation_errors.append(f"Missing content in {section_key}")
        
        # Validate test execution cases (DISABLED - not required for placeholder testing)
        # test_execution_cases = processed_data.get("test_execution_cases", [])
        # if not isinstance(test_execution_cases, list):
        #     validation_errors.append("test_execution_cases must be a list")
        # elif len(test_execution_cases) == 0:
        #     validation_errors.append("No test execution cases found")
        
        # Validate DUT fields (DISABLED - not required for placeholder testing)
        # dut_fields = processed_data.get("dut_fields", [])
        # if not isinstance(dut_fields, list):
        #     validation_errors.append("dut_fields must be a list")
        
        # Validate hash sections (DISABLED - not required for placeholder testing)
        # hash_sections = processed_data.get("hash_sections", [])
        # if not isinstance(hash_sections, list):
        #     validation_errors.append("hash_sections must be a list")
        
        # Validate ITSAR fields (DISABLED - not required for placeholder testing)
        # itsar_fields = processed_data.get("itsar_fields", [])
        # if not isinstance(itsar_fields, list):
        #     validation_errors.append("itsar_fields must be a list")
        
        return len(validation_errors) == 0, validation_errors
    
    def _merge_imported_data_with_current(self, imported_data: Dict[str, Any], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge imported data with current data, ensuring no data loss
        
        Args:
            imported_data: Data from imported JSON
            current_data: Current application data
            
        Returns:
            Merged data with current data taking precedence for conflicts
        """
        merged_data = imported_data.copy()
        
        # Merge sections_1_7 data
        if "sections_1_7" in current_data and "sections_1_7" in imported_data:
            current_sections = current_data["sections_1_7"]
            imported_sections = imported_data["sections_1_7"]
            
            if isinstance(current_sections, dict) and isinstance(imported_sections, dict):
                for section_key in current_sections:
                    if section_key in imported_sections:
                        # Merge section data, current takes precedence
                        current_section = current_sections[section_key]
                        imported_section = imported_sections[section_key]
                        
                        if isinstance(current_section, dict) and isinstance(imported_section, dict):
                            merged_section = imported_section.copy()
                            merged_section.update(current_section)
                            merged_data["sections_1_7"][section_key] = merged_section
                        else:
                            # If one is not a dict, use current
                            merged_data["sections_1_7"][section_key] = current_section
                    else:
                        # Section exists in current but not imported, add it
                        merged_data["sections_1_7"][section_key] = current_sections[section_key]
        
        # Merge test execution cases
        if "test_execution_cases" in current_data and "test_execution_cases" in imported_data:
            current_cases = current_data["test_execution_cases"]
            imported_cases = imported_data["test_execution_cases"]
            
            if isinstance(current_cases, list) and isinstance(imported_cases, list):
                # Use current cases if they exist, otherwise use imported
                merged_data["test_execution_cases"] = current_cases if current_cases else imported_cases
        
        # Merge other fields with current data taking precedence
        for key in current_data:
            if key not in merged_data:
                merged_data[key] = current_data[key]
            elif isinstance(current_data[key], dict) and isinstance(merged_data[key], dict):
                # Deep merge for dictionaries
                merged_data[key].update(current_data[key])
        
        return merged_data
    
    def _load_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load JSON file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"❌ Error loading {os.path.basename(file_path)}: {e}")
            return None
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get summary of exported configuration"""
        summary = {
            "test_case_folder": self.test_case_folder,
            "project_name": self.project_name,
            "questions_config": {
                "exists": os.path.exists(self.questions_config_path),
                "path": self.questions_config_path
            },
            "template_config": {
                "exists": os.path.exists(self.template_config_path),
                "path": self.template_config_path
            }
        }
        
        # Load and analyze configs if they exist
        questions_config = self._load_json_file(self.questions_config_path)
        if questions_config:
            summary["questions_config"]["data"] = {
                "total_questions": len(questions_config.get("questions", {}).get("essential_questions", [])) + 
                                 len(questions_config.get("questions", {}).get("execution_step_questions", []))
            }
        
        template_config = self._load_json_file(self.template_config_path)
        if template_config:
            configuration = template_config.get("configuration", {})
            summary["template_config"]["data"] = {
                "dut_fields_count": len(configuration.get("dut_fields", [])),
                "hash_sections_count": len(configuration.get("hash_sections", [])),
                "itsar_fields_count": len(configuration.get("itsar_fields", [])),
                "test_scenarios_count": len(configuration.get("test_scenarios", [])),
                "test_execution_cases_count": len(configuration.get("test_execution_cases", []))
            }
        
        return summary

    def collect_sections_1_7_data(self, sections_1_7_manager) -> Dict[str, Any]:
        """
        Collect all sections 1-7 data including images and scripts from the UI manager
        
        Args:
            sections_1_7_manager: The Sections1_7Manager instance from the main application
            
        Returns:
            Dictionary containing all sections 1-7 data
        """
        if not sections_1_7_manager:
            return {}
        
        # First, get the base data from the sections manager (includes placeholder data)
        sections_data = sections_1_7_manager.get_sections_1_7_data()
        print(f"🔍 DEBUG: Initial sections_data from manager: {sections_data}")
        
        # Debug: Check if placeholder data exists in sections 2 and 3
        if 'section_2' in sections_data:
            print(f"🔍 DEBUG: Section 2 initial data: {sections_data['section_2']}")
        if 'section_3' in sections_data:
            print(f"🔍 DEBUG: Section 3 initial data: {sections_data['section_3']}")
        
        # Collect data for each section to add images and scripts
        sections = [
            ("section_1", sections_1_7_manager.section_1_heading_edit, sections_1_7_manager.section_1_edit, 
             sections_1_7_manager.section_1_images_list, sections_1_7_manager.section_1_scripts_list),
            ("section_2", sections_1_7_manager.section_2_heading_edit, sections_1_7_manager.section_2_edit,
             sections_1_7_manager.section_2_images_list, sections_1_7_manager.section_2_scripts_list),
            ("section_3", sections_1_7_manager.section_3_heading_edit, sections_1_7_manager.section_3_edit,
             sections_1_7_manager.section_3_images_list, sections_1_7_manager.section_3_scripts_list),
            ("section_6", sections_1_7_manager.section_6_heading_edit, sections_1_7_manager.section_6_edit,
             sections_1_7_manager.section_6_images_list, sections_1_7_manager.section_6_scripts_list),
            ("section_7", sections_1_7_manager.section_7_heading_edit, sections_1_7_manager.section_7_edit,
             sections_1_7_manager.section_7_images_list, sections_1_7_manager.section_7_scripts_list)
        ]
        
        for section_name, heading_edit, content_edit, images_list, scripts_list in sections:
            print(f"🔍 DEBUG: Processing section: {section_name}")
            if hasattr(sections_1_7_manager, f'{section_name}_heading_edit') and hasattr(sections_1_7_manager, f'{section_name}_edit'):
                # Safely extract text content from Qt widgets
                heading_widget = getattr(sections_1_7_manager, f'{section_name}_heading_edit')
                content_widget = getattr(sections_1_7_manager, f'{section_name}_edit')
                
                heading_text = ""
                content_text = ""
                
                # Extract heading text safely
                if heading_widget and hasattr(heading_widget, 'text'):
                    try:
                        heading_text = heading_widget.text()
                    except Exception as e:
                        print(f"Warning: Could not extract heading text for {section_name}: {e}")
                        heading_text = ""
                
                # Extract content text safely
                if content_widget:
                    try:
                        if hasattr(content_widget, 'toPlainText'):
                            content_text = content_widget.toPlainText()
                        elif hasattr(content_widget, 'text'):
                            content_text = content_widget.text()
                        else:
                            content_text = str(content_widget)
                    except Exception as e:
                        print(f"Warning: Could not extract content text for {section_name}: {e}")
                        content_text = ""
                
                # Get existing section data or create new if not exists
                if section_name in sections_data:
                    print(f"🔍 DEBUG: Found existing section data for {section_name}: {sections_data[section_name]}")
                    section_data = sections_data[section_name].copy()  # Make a copy to avoid modifying original
                else:
                    section_data = {
                        "heading": heading_text,
                        "content": content_text,
                        "temp_placeholder": "",
                        "text": content_text,
                        "placeholders": "",  # Will be populated by sections manager
                        "images": [],
                        "scripts": []
                    }
                    print(f"🔍 DEBUG: Created new section data for {section_name}: {section_data}")
                
                # Ensure required fields exist
                if "images" not in section_data:
                    section_data["images"] = []
                if "scripts" not in section_data:
                    section_data["scripts"] = []
                
                # Add images
                if hasattr(sections_1_7_manager, f'{section_name}_images_list'):
                    images_list = getattr(sections_1_7_manager, f'{section_name}_images_list', [])
                    print(f"🔍 DEBUG: {section_name} images_list: {images_list}")
                    for image in images_list:
                        if isinstance(image, dict) and "path" in image:
                            section_data["images"].append(image)
                
                # Add scripts
                if hasattr(sections_1_7_manager, f'{section_name}_scripts_list'):
                    scripts_list = getattr(sections_1_7_manager, f'{section_name}_scripts_list', [])
                    print(f"🔍 DEBUG: {section_name} scripts_list: {scripts_list}")
                    print(f"🔍 DEBUG: {section_name} scripts_list type: {type(scripts_list)}")
                    print(f"🔍 DEBUG: {section_name} scripts_list length: {len(scripts_list) if isinstance(scripts_list, list) else 'Not a list'}")
                    
                    if isinstance(scripts_list, list):
                        for i, script in enumerate(scripts_list):
                            print(f"🔍 DEBUG: {section_name} script {i}: {script}")
                            print(f"🔍 DEBUG: {section_name} script {i} type: {type(script)}")
                            if isinstance(script, dict):
                                print(f"🔍 DEBUG: {section_name} script {i} keys: {list(script.keys())}")
                                # Check for path field or create one from filename if missing
                                if "path" in script:
                                    print(f"🔍 DEBUG: {section_name} script {i} has path: {script['path']}")
                                    section_data["scripts"].append(script)
                                elif "filename" in script:
                                    print(f"🔍 DEBUG: {section_name} script {i} has filename, creating path")
                                    # Create a path field if it's missing
                                    script_copy = script.copy()
                                    script_copy["path"] = script_copy["filename"]
                                    section_data["scripts"].append(script_copy)
                                else:
                                    print(f"🔍 DEBUG: {section_name} script {i} has no path or filename, adding as is")
                                    # If neither path nor filename exists, still add the script
                                    section_data["scripts"].append(script)
                            else:
                                print(f"🔍 DEBUG: {section_name} script {i} is not a dict, skipping")
                    else:
                        print(f"🔍 DEBUG: {section_name} scripts_list is not a list, skipping")
                
                # Preserve existing placeholder data if it exists
                if section_name in sections_data and 'placeholders' in sections_data[section_name]:
                    section_data['placeholders'] = sections_data[section_name]['placeholders']
                    print(f"🔍 DEBUG: Preserved placeholder data for {section_name}: '{section_data['placeholders']}'")
                else:
                    print(f"🔍 DEBUG: No placeholder data to preserve for {section_name}")
                
                # Also preserve temp_placeholder and text fields if they exist
                if section_name in sections_data:
                    if 'temp_placeholder' in sections_data[section_name]:
                        section_data['temp_placeholder'] = sections_data[section_name]['temp_placeholder']
                        print(f"🔍 DEBUG: Preserved temp_placeholder data for {section_name}: '{section_data['temp_placeholder']}'")
                    if 'text' in sections_data[section_name]:
                        section_data['text'] = sections_data[section_name]['text']
                        print(f"🔍 DEBUG: Preserved text data for sas {section_name}: '{section_data['text']}'")
                
                # Update heading and content from widgets if they exist
                if heading_widget and hasattr(heading_widget, 'text'):
                    section_data['heading'] = heading_text
                    print(f"🔍 DEBUG: Updated heading for {section_name}: '{section_data['heading']}'")
                if content_widget:
                    section_data['content'] = content_text
                    print(f"🔍 DEBUG: Updated content for {section_name}: '{section_data['content']}'")
                
                # Update the section data
                sections_data[section_name] = section_data
                print(f"🔍 DEBUG: After processing {section_name}, final data: {section_data}")
                print(f"🔍 DEBUG: Final {section_name} scripts count: {len(section_data.get('scripts', []))}")
        
        # Handle section_4 and section_5 pairs
        if hasattr(sections_1_7_manager, 'section_4_pairs'):
            # Safely extract section 4 heading
            section_4_heading = "DUT Confirmation Details"
            if hasattr(sections_1_7_manager, 'section_4_heading_edit'):
                heading_widget = sections_1_7_manager.section_4_heading_edit
                if heading_widget and hasattr(heading_widget, 'text'):
                    try:
                        section_4_heading = heading_widget.text()
                    except Exception as e:
                        print(f"Warning: Could not extract section 4 heading: {e}")
            
            # Safely extract interfaces description
            interfaces_desc = ""
            if hasattr(sections_1_7_manager, 'section_4_interfaces_desc'):
                desc_widget = sections_1_7_manager.section_4_interfaces_desc
                if desc_widget and hasattr(desc_widget, 'toPlainText'):
                    try:
                        interfaces_desc = desc_widget.toPlainText()
                    except Exception as e:
                        print(f"Warning: Could not extract section 4 interfaces description: {e}")
            
            sections_data["section_4"] = {
                "heading": section_4_heading,
                "pairs": [],
                "interfaces_desc": interfaces_desc,
                "interfaces": sections_1_7_manager.get_section_4_interface_data() if hasattr(sections_1_7_manager, 'get_section_4_interface_data') else []
            }
            
            for pair in sections_1_7_manager.section_4_pairs:
                # Safely extract pair text
                pair_text = ""
                text_edit = pair.get("text_edit")
                if text_edit and hasattr(text_edit, 'toPlainText'):
                    try:
                        pair_text = text_edit.toPlainText()
                    except Exception as e:
                        print(f"Warning: Could not extract section 4 pair text: {e}")
                
                pair_data = {
                    "text": pair_text,
                    "images": [],
                    "scripts": []
                }
                # Add pair images if they exist
                if "images_list" in pair:
                    for image_info in pair["images_list"]:
                        if isinstance(image_info, dict) and "path" in image_info:
                            pair_data["images"].append(image_info)
                # Add pair scripts if they exist
                if "upload_scripts_list" in pair:
                    for script_info in pair["upload_scripts_list"]:
                        if isinstance(script_info, dict) and "path" in script_info:
                            pair_data["scripts"].append(script_info)
                sections_data["section_4"]["pairs"].append(pair_data)
        
        if hasattr(sections_1_7_manager, 'section_5_pairs'):
            # Safely extract section 5 heading
            section_5_heading = "DUT Configuration"
            if hasattr(sections_1_7_manager, 'section_5_heading_edit'):
                heading_widget = sections_1_7_manager.section_5_heading_edit
                if heading_widget and hasattr(heading_widget, 'text'):
                    try:
                        section_5_heading = heading_widget.text()
                    except Exception as e:
                        print(f"Warning: Could not extract section 5 heading: {e}")
            
            sections_data["section_5"] = {
                "heading": section_5_heading,
                "pairs": []
            }
            
            for pair in sections_1_7_manager.section_5_pairs:
                # Safely extract pair text
                pair_text = ""
                text_edit = pair.get("text_edit")
                if text_edit and hasattr(text_edit, 'toPlainText'):
                    try:
                        pair_text = text_edit.toPlainText()
                    except Exception as e:
                        print(f"Warning: Could not extract section 5 pair text: {e}")
                
                pair_data = {
                    "text": pair_text,
                    "images": [],
                    "scripts": []
                }
                # Add pair images if they exist
                if "images_list" in pair:
                    for image_info in pair["images_list"]:
                        if isinstance(image_info, dict) and "path" in image_info:
                            pair_data["images"].append(image_info)
                # Add pair scripts if they exist
                if "upload_scripts_list" in pair:
                    for script_info in pair["upload_scripts_list"]:
                        if isinstance(script_info, dict) and "path" in script_info:
                            pair_data["scripts"].append(script_info)
                sections_data["section_5"]["pairs"].append(pair_data)
        
        print(f"🔍 DEBUG: Final sections_data keys: {list(sections_data.keys())}")
        for section_name, section_data in sections_data.items():
            if isinstance(section_data, dict) and 'scripts' in section_data:
                print(f"🔍 DEBUG: {section_name} final scripts count: {len(section_data['scripts'])}")
                if section_data['scripts']:
                    print(f"🔍 DEBUG: {section_name} first script: {section_data['scripts'][0]}")
        
        return sections_data

    def merge_and_export_after_edit(self, current_app_data: Dict[str, Any], imported_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Merge current application data with imported data and export the result
        
        This method is called after importing JSON and making edits to ensure
        all data is properly merged and exported without loss.
        
        Args:
            current_app_data: Current application data (from UI)
            imported_data: Data from imported JSON
            
        Returns:
            Tuple of (success, message)
        """
        try:
            print("🔄 Merging imported data with current application data...")
            
            # Merge the data with current data taking precedence
            merged_data = self._merge_imported_data_with_current(imported_data, current_app_data)
            
            # Validate the merged data
            is_valid, validation_errors = self._validate_export_data(merged_data)
            
            if not is_valid:
                error_message = "❌ Merged data validation failed:\n"
                for error in validation_errors:
                    error_message += f"  - {error}\n"
                return False, error_message
            
            # Process the merged data for export
            processed_data = self._process_all_data_per_field(merged_data)
            
            # Create configuration files
            questions_config = self._create_questions_config(processed_data)
            template_config = self._create_template_config(processed_data)
            
            # Save files
            questions_success = self._save_json_file(self.questions_config_path, questions_config)
            template_success = self._save_json_file(self.template_config_path, template_config)
            
            # Copy files
            files_success = self._copy_files_to_folders(processed_data)
            
            if questions_success and template_success and files_success:
                return True, f"✅ Merged configuration exported successfully to {self.configuration_folder}"
            else:
                return False, "❌ Failed to export merged configuration"
                
        except Exception as e:
            return False, f"❌ Merge and export failed: {str(e)}"
    
    def get_missing_fields_report(self, app_data: Dict[str, Any]) -> List[str]:
        """
        Generate a report of missing or empty fields in the application data
        
        Args:
            app_data: Application data to check
            
        Returns:
            List of missing field descriptions
        """
        missing_fields = []
        
        # Check top-level required fields
        required_fields = [
            ("test_case_name", "Test Case Name"),
            ("sections_1_7", "Sections 1-7 Data"),
            ("test_execution_cases", "Test Execution Cases"),
            ("dut_fields", "DUT Fields"),
            ("hash_sections", "Hash Sections"),
            ("itsar_fields", "ITSAR Fields")
        ]
        
        for field_key, field_name in required_fields:
            if field_key not in app_data:
                missing_fields.append(f"Missing {field_name}")
            elif app_data[field_key] is None:
                missing_fields.append(f"{field_name} is null")
            elif isinstance(app_data[field_key], list) and len(app_data[field_key]) == 0:
                missing_fields.append(f"{field_name} is empty")
            elif isinstance(app_data[field_key], dict) and len(app_data[field_key]) == 0:
                missing_fields.append(f"{field_name} is empty")
        
        # Check sections_1_7 specific fields
        sections_1_7 = app_data.get("sections_1_7", {})
        if isinstance(sections_1_7, dict):
            section_names = {
                "section_1": "Section 1 - ITSAR Section No & Name",
                "section_2": "Section 2 - Security Requirement No & Name", 
                "section_3": "Section 3 - Requirement Description",
                "section_4": "Section 4 - DUT Confirmation Details",
                "section_5": "Section 5 - DUT Configuration",
                "section_6": "Section 6 - Preconditions",
                "section_7": "Section 7 - Test Objective"
            }
            
            for section_key, section_name in section_names.items():
                if section_key not in sections_1_7:
                    missing_fields.append(f"Missing {section_name}")
                else:
                    section_data = sections_1_7[section_key]
                    if isinstance(section_data, dict):
                        if "heading" not in section_data or not section_data["heading"]:
                            missing_fields.append(f"{section_name} - Missing heading")
                        if "content" not in section_data and section_key not in ["section_4", "section_5"]:
                            missing_fields.append(f"{section_name} - Missing content")
                        elif section_key not in ["section_4", "section_5"] and section_data.get("content") == "":
                            missing_fields.append(f"{section_name} - Empty content")
        
        return missing_fields
