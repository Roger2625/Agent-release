#!/usr/bin/env python3
"""
Enhanced Export/Import System for AutoDoc Studio
Updated to store images, scripts, and placeholders per field/question
"""

import os
import json
import shutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

def is_file_locked(file_path: str) -> bool:
    """Check if a file is locked/in use"""
    try:
        # Try to open the file in append mode to check if it's locked
        with open(file_path, 'a') as f:
            pass
        return False
    except (IOError, PermissionError, OSError):
        return True

def should_skip_copy(src_path: str, test_case_folder: str) -> bool:
    """Check if copying should be skipped because file is already in test case folder"""
    if not src_path:
        return False
    
    # Normalize paths
    src_path = os.path.normpath(src_path)
    test_case_folder = os.path.normpath(test_case_folder)
    
    # Check if source is already in the test case folder
    if test_case_folder in os.path.abspath(src_path):
        return True
    
    # Check if source is already a relative path in the destination structure
    # Handle both forward and backward slashes for cross-platform compatibility
    if not os.path.isabs(src_path):
        normalized_src = src_path.replace('\\', '/')
        if normalized_src.startswith(("raw_logs/", "code/", "tmp/")):
            return True
    
    return False

def safe_copy_file(src_path: str, dst_path: str, max_retries: int = 3) -> bool:
    """Safely copy a file with retry logic and error handling"""
    print(f"DEBUG: safe_copy_file called with src: {src_path}, dst: {dst_path}")
    
    # Normalize paths to handle different path separators and relative/absolute paths
    src_path = os.path.normpath(src_path)
    dst_path = os.path.normpath(dst_path)
    
    # Check if source file exists
    if not os.path.exists(src_path):
        print(f"❌ Source file does not exist: {src_path}")
        return False
    
    # Check if source and destination are the same file
    if os.path.abspath(src_path) == os.path.abspath(dst_path):
        print(f"ℹ️ Source and destination are the same file, skipping copy: {src_path}")
        return True
    

    
    # Check if source file is locked
    if is_file_locked(src_path):
        print(f"⚠️ File is locked: {src_path}")
        time.sleep(2)  # Wait longer for file to be released
    
    for attempt in range(max_retries):
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # Try copy2 first (preserves metadata)
            print(f"DEBUG: Attempt {attempt + 1}: Trying shutil.copy2")
            shutil.copy2(src_path, dst_path)
            print(f"✅ File copied successfully: {src_path} -> {dst_path}")
            return True
        except PermissionError as e:
            print(f"⚠️ Permission error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait longer before retry
                continue
            else:
                # Try alternative copy method
                try:
                    print(f"DEBUG: Trying alternative copy method: shutil.copyfile")
                    shutil.copyfile(src_path, dst_path)
                    print(f"✅ File copied successfully (alternative method): {src_path} -> {dst_path}")
                    return True
                except Exception as e2:
                    print(f"❌ Alternative copy also failed: {e2}")
                    return False
        except Exception as e:
            print(f"❌ Copy error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)  # Wait longer before retry
                continue
            else:
                # Try one more alternative method
                try:
                    print(f"DEBUG: Trying final alternative: copy with different approach")
                    # import shutil
                    # Try to copy with different permissions
                    shutil.copy(src_path, dst_path)
                    print(f"✅ File copied successfully (final alternative): {src_path} -> {dst_path}")
                    return True
                except Exception as e3:
                    print(f"❌ All copy methods failed: {e3}")
                    return False
    return False

class EnhancedExportImport:
    """Enhanced export/import system for AutoDoc Studio with per-field storage"""
    
    def __init__(self, test_case_folder: str, global_step_scripts: dict = None, parent_app=None):
        print(f"🔧 Initializing EnhancedExportImport with folder: {test_case_folder}")
        self.test_case_folder = test_case_folder
        self.global_step_scripts = global_step_scripts or {}
        self.parent_app = parent_app  # Reference to the main application
        print(f"🔧 Global step scripts provided: {len(self.global_step_scripts)} step keys")
        if self.global_step_scripts:
            print(f"🔧 Step keys: {list(self.global_step_scripts.keys())}")
            for step_key, scripts in self.global_step_scripts.items():
                print(f"🔧 Step {step_key}: {len(scripts)} scripts")
                for script in scripts:
                    print(f"🔧   - {script.get('filename', 'Unknown')}: placeholder='{script.get('placeholder', 'None')}'")
        self.project_name = os.path.basename(test_case_folder)
        self.configuration_folder = os.path.join(test_case_folder, "configuration")
        self.questions_config_path = os.path.join(self.configuration_folder, "questions_config.json")
        self.template_config_path = os.path.join(self.configuration_folder, "template_config.json")
        
        print(f"📁 Creating folders...")
        # Ensure folders exist
        os.makedirs(self.configuration_folder, exist_ok=True)
        os.makedirs(os.path.join(test_case_folder, "raw_logs"), exist_ok=True)
        os.makedirs(os.path.join(test_case_folder, "code"), exist_ok=True)
        print(f"✅ Folders created successfully")
    
    def export_complete_configuration(self, app_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Export complete configuration including all data, images, scripts, and placeholders per field"""
        try:
            # Process and organize all data with per-field storage
            processed_data = self._process_all_data_per_field(app_data)
            
            # Create template_config.json (complete with file paths)
            template_config = self._create_template_config(processed_data)
            
            # Save template_config.json only
            questions_success = True  # Skip questions_config.json creation
            template_success = self._save_json_file(self.template_config_path, template_config)
            
            # Copy files to proper folders
            files_success = self._copy_files_to_folders(processed_data)
            
            # Check what failed and provide specific error messages
            failed_components = []
            if not template_success:
                failed_components.append("template_config.json")
            if not files_success:
                failed_components.append("file copying")
            
            if questions_success and template_success:
                if files_success:
                    return True, f"✅ Configuration exported successfully to {self.configuration_folder}"
                else:
                    # JSON files were saved successfully, but file copying had issues
                    return True, f"✅ Configuration exported successfully to {self.configuration_folder}\n⚠️ Some files could not be copied due to file locking issues, but the configuration is complete."
            else:
                return False, f"❌ Failed to export some components: {', '.join(failed_components)}"
                
        except Exception as e:
            return False, f"❌ Export failed: {str(e)}"
    
    def import_complete_configuration(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Import complete configuration and prepare for UI repopulation"""
        try:
            # Load template_config.json
            template_config = self._load_json_file(self.template_config_path)
            if not template_config:
                return False, "❌ template_config.json not found", {}
            
            # Process and resolve all references
            processed_data = self._process_import_data(template_config)
            
            # Validate file existence
            validation_result = self._validate_imported_files(processed_data)
            if not validation_result[0]:
                print(f"⚠️ Import warnings: {validation_result[1]}")
            
            return True, "✅ Configuration imported successfully", processed_data
            
        except Exception as e:
            return False, f"❌ Import failed: {str(e)}", {}
    
    def _process_all_data_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all application data for export with per-field storage"""
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
            "header_text": app_data.get("header_text", ""),
            "header_start_page": app_data.get("header_start_page", 0),
            "export_path": app_data.get("export_path", ""),
            "export_filename": app_data.get("export_filename", ""),
            
            # Headings
            "test_scenarios_heading": app_data.get("test_scenarios_heading", "Number of Test Scenarios"),
            "test_bed_diagram_heading": app_data.get("test_bed_diagram_heading", "Test Bed Diagram"),
            "test_bed_diagram_notes": app_data.get("test_bed_diagram_notes", ""),
            "tools_required_heading": app_data.get("tools_required_heading", "Tools Required"),
            "test_execution_steps_heading": app_data.get("test_execution_steps_heading", "Test Execution Steps"),
            "expected_results_heading": app_data.get("expected_results_heading", "Expected Result"),
            "expected_format_evidence_heading": app_data.get("expected_format_evidence_heading", "Expected Format of Evidence"),
            
            # Results and evidence
            "expected_results": self._process_expected_results(app_data.get("expected_results", [])),
            "evidence_format": self._process_evidence_format(app_data.get("evidence_format", [])),
            "test_case_results": app_data.get("test_case_results", []),
            
            # UI-specific data for questions_config.json
            "essential_questions": app_data.get("essential_questions", []),
            "execution_step_questions": app_data.get("execution_step_questions", []),
            "dependencies": app_data.get("dependencies", []),
            "configuration_fields": app_data.get("configuration_fields", [])
        }
        
        
        return processed_data
    
    def _process_dut_fields(self, dut_fields: List[Dict]) -> List[Dict]:
        """Process DUT fields with per-field images, scripts, and placeholders"""
        processed_fields = []
        
        # Get all placeholders for DUT Details section
        dut_placeholders = self._get_section8_placeholders_for_section("DUT Details")
        
        for field in dut_fields:
            if isinstance(field, dict):
                processed_field = field.copy()
                processed_field["images"] = self._process_images_for_field(field.get("images", []))
                processed_field["scripts"] = self._process_scripts_for_field(field.get("scripts", []))
                
                # Add placeholders to each field (all fields share the same placeholders for this section)
                if dut_placeholders:
                    processed_field["placeholders"] = self._process_placeholders_for_field(dut_placeholders)
                else:
                    processed_field["placeholders"] = self._process_placeholders_for_field(field.get("placeholders", []))
                
                processed_fields.append(processed_field)
        
        # If no fields exist but we have placeholders, create a default field entry
        if not processed_fields and dut_placeholders:
            default_field = {
                "label": "DUT Details",
                "value": "",
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(dut_placeholders)
            }
            processed_fields.append(default_field)
        
        return processed_fields
    
    def _process_hash_sections(self, hash_sections: List[Dict]) -> List[Dict]:
        """Process hash sections with per-field storage"""
        processed_sections = []
        
        # Get all placeholders for Hash Sections
        hash_placeholders = self._get_section8_placeholders_for_section("Hash Sections")
        
        for section in hash_sections:
            if isinstance(section, dict):
                processed_section = section.copy()
                
                # Process direct hash images and scripts
                processed_section["direct_hash_images"] = self._process_images_for_field(section.get("direct_hash_images", []))
                processed_section["direct_hash_scripts"] = self._process_scripts_for_field(section.get("direct_hash_scripts", []))
                
                # Process hash fields
                processed_section["hash_fields"] = self._process_hash_fields(section.get("hash_fields", []))
                
                # Add placeholders to each section (all sections share the same placeholders for this section)
                if hash_placeholders:
                    processed_section["placeholders"] = self._process_placeholders_for_field(hash_placeholders)
                else:
                    processed_section["placeholders"] = self._process_placeholders_for_field(section.get("placeholders", []))
                
                processed_sections.append(processed_section)
        
        # If no sections exist but we have placeholders, create a default section entry
        if not processed_sections and hash_placeholders:
            default_section = {
                "heading": "Hash Sections",
                "direct_hash_images": [],
                "direct_hash_scripts": [],
                "hash_fields": [],
                "placeholders": self._process_placeholders_for_field(hash_placeholders)
            }
            processed_sections.append(default_section)
        
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
        
        # Get all placeholders for ITSAR Information section
        itsar_placeholders = self._get_section8_placeholders_for_section("ITSAR Information")
        
        for field in itsar_fields:
            if isinstance(field, dict):
                processed_field = field.copy()
                processed_field["images"] = self._process_images_for_field(field.get("images", []))
                processed_field["scripts"] = self._process_scripts_for_field(field.get("scripts", []))
                
                # Add placeholders to each field (all fields share the same placeholders for this section)
                if itsar_placeholders:
                    processed_field["placeholders"] = self._process_placeholders_for_field(itsar_placeholders)
                else:
                    processed_field["placeholders"] = self._process_placeholders_for_field(field.get("placeholders", []))
                
                processed_fields.append(processed_field)
        
        # If no fields exist but we have placeholders, create a default field entry
        if not processed_fields and itsar_placeholders:
            default_field = {
                "label": "ITSAR Information",
                "value": "",
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(itsar_placeholders)
            }
            processed_fields.append(default_field)
        
        return processed_fields
    
    def _process_sections_1_7_per_field(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
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
                    print(f"DEBUG: sections_1_7_manager type: {type(self.parent_app.sections_1_7_manager)}")
                    print(f"DEBUG: sections_1_7_manager attributes: {[attr for attr in dir(self.parent_app.sections_1_7_manager) if not attr.startswith('_')]}")
                    
                    # Check if section_1_scripts_list exists and has content
                    if hasattr(self.parent_app.sections_1_7_manager, 'section_1_scripts_list'):
                        scripts_list = getattr(self.parent_app.sections_1_7_manager, 'section_1_scripts_list', [])
                        print(f"DEBUG: section_1_scripts_list exists: {scripts_list}")
                        print(f"DEBUG: section_1_scripts_list type: {type(scripts_list)}")
                        print(f"DEBUG: section_1_scripts_list length: {len(scripts_list) if isinstance(scripts_list, list) else 'Not a list'}")
                        if isinstance(scripts_list, list) and scripts_list:
                            print(f"DEBUG: First script in section_1_scripts_list: {scripts_list[0]}")
                            if isinstance(scripts_list[0], dict):
                                print(f"DEBUG: First script keys: {list(scripts_list[0].keys())}")
                    else:
                        print(f"DEBUG: section_1_scripts_list does not exist")
                    
                    fresh_data = self.collect_sections_1_7_data(self.parent_app.sections_1_7_manager)
                    if fresh_data:
                        print(f"DEBUG: Got fresh sections 1-7 data: {list(fresh_data.keys())}")
                        sections_1_7.update(fresh_data)
                    else:
                        print(f"DEBUG: No fresh data collected")
                except Exception as e:
                    print(f"DEBUG: Error collecting fresh data: {e}")
                    import traceback
                    traceback.print_exc()
        
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
                
                # Add placeholder_content_management for sections 4 and 5
                processed_section["placeholder_content_management"] = section_data.get("placeholder_content_management", [])
            
            # Process sections 1, 2, 3, 6, 7
            elif section_key in ["section_1", "section_2", "section_3", "section_6", "section_7"]:
                processed_section.update({
                    "heading": section_data.get("heading", ""),
                    "content": section_data.get("content", ""),
                    "text": section_data.get("text", ""),
                    "images": self._process_images_for_field(section_data.get("images", [])),
                    "scripts": self._process_scripts_for_field(section_data.get("scripts", [])),
                    "placeholders": self._process_placeholders_for_field(section_data.get("placeholders", [])),
                    "placeholder_content_management": section_data.get("placeholder_content_management", [])
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
                        print(f"  Script keys: {list(processed_section['scripts'][0].keys()) if isinstance(processed_section['scripts'][0], dict) else 'Not a dict'}")
                        print(f"  Script has original_path: {'original_path' in processed_section['scripts'][0] if isinstance(processed_section['scripts'][0], dict) else False}")
                        print(f"  Script has path: {'path' in processed_section['scripts'][0] if isinstance(processed_section['scripts'][0], dict) else False}")
            
            processed_sections[section_key] = processed_section
        
        print(f"DEBUG: Final processed sections 1-7: {list(processed_sections.keys())}")
        return processed_sections
    def _process_test_scenarios(self, test_scenarios: List[Dict]) -> List[Dict]:
        """Process test scenarios with per-field storage"""
        processed_scenarios = []
        for scenario in test_scenarios:
            if isinstance(scenario, dict):
                processed_scenario = scenario.copy()
                processed_scenario["images"] = self._process_images_for_field(scenario.get("images", []))
                processed_scenario["scripts"] = self._process_scripts_for_field(scenario.get("scripts", []))
                
                # Get placeholders from scenario_placeholders if available
                scenario_key = scenario.get("key", "")
                print(f"DEBUG: Processing test scenario with key: '{scenario_key}'")
                
                # If scenario key is empty, try "New Scenario" as fallback
                if not scenario_key:
                    scenario_key = "New Scenario"
                    print(f"DEBUG: Using fallback scenario key: '{scenario_key}'")
                
                section8_placeholders = self._get_section8_placeholders_for_scenario(scenario_key)
                if section8_placeholders:
                    processed_scenario["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
                    print(f"DEBUG: Added {len(section8_placeholders)} placeholders to scenario")
                else:
                    processed_scenario["placeholders"] = self._process_placeholders_for_field(scenario.get("placeholders", []))
                    print(f"DEBUG: No placeholders found for scenario key '{scenario_key}'")
                
                processed_scenarios.append(processed_scenario)
        return processed_scenarios
    
    def _process_tools_required(self, tools_required: List[Dict]) -> List[Dict]:
        """Process tools required with per-field storage"""
        processed_tools = []
        
        # Get all placeholders for Tools Required section
        section8_placeholders = self._get_section8_placeholders_for_section("8.3. Tools Required")
        
        for tool in tools_required:
            if isinstance(tool, dict):
                processed_tool = tool.copy()
                processed_tool["images"] = self._process_images_for_field(tool.get("images", []))
                processed_tool["scripts"] = self._process_scripts_for_field(tool.get("scripts", []))
                
                # Add placeholders to each tool (all tools share the same placeholders for this section)
                if section8_placeholders:
                    processed_tool["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
                else:
                    processed_tool["placeholders"] = self._process_placeholders_for_field(tool.get("placeholders", []))
                
                processed_tools.append(processed_tool)
        
        # If no tools exist but we have placeholders, create a default tool entry
        if not processed_tools and section8_placeholders:
            default_tool = {
                "name": "Tools Required",
                "description": "",
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(section8_placeholders)
            }
            processed_tools.append(default_tool)
        
        return processed_tools
    
    def _process_execution_steps(self, execution_steps: List[Dict]) -> List[Dict]:
        """Process execution steps with per-field storage"""
        processed_steps = []
        
        # Get all placeholders for Execution Steps section
        section8_placeholders = self._get_section8_placeholders_for_section("8.4. Test Execution Steps")
        
        for step in execution_steps:
            if isinstance(step, dict):
                processed_step = step.copy()
                processed_step["images"] = self._process_images_for_field(step.get("images", []))
                processed_step["scripts"] = self._process_scripts_for_field(step.get("scripts", []))
                
                # Add placeholders to each step (all steps share the same placeholders for this section)
                if section8_placeholders:
                    processed_step["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
                else:
                    processed_step["placeholders"] = self._process_placeholders_for_field(step.get("placeholders", []))
                
                processed_steps.append(processed_step)
        
        # If no steps exist but we have placeholders, create a default step entry
        if not processed_steps and section8_placeholders:
            default_step = {
                "Custom_input": [],
                "scenario_key": "",
                "scenario_description": "",
                "steps": [],
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(section8_placeholders)
            }
            processed_steps.append(default_step)
        
        return processed_steps
    
    def _process_test_bed_diagram(self, test_bed_data: Dict) -> Dict:
        """Process test bed diagram data"""
        if not isinstance(test_bed_data, dict):
            return {"heading": "", "images": [], "scripts": [], "placeholders": []}
        
        processed_data = test_bed_data.copy()
        processed_data["images"] = self._process_images_for_field(test_bed_data.get("images", []))
        processed_data["scripts"] = self._process_scripts_for_field(test_bed_data.get("scripts", []))
        
        # Get placeholders from scenario_placeholders for Test Bed Diagram section
        section8_placeholders = self._get_section8_placeholders_for_section("8.2. Test Bed Diagram")
        if section8_placeholders:
            processed_data["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
        else:
            processed_data["placeholders"] = self._process_placeholders_for_field(test_bed_data.get("placeholders", []))
        
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
                # CRITICAL FIX: Prioritize current UI state over imported data for case-level scripts
                # This ensures that user modifications (new scripts added after import) are preserved
                case_scripts = case.get("scripts", [])
                print(f"DEBUG: Case {i} has {len(case_scripts)} scripts from imported case data")
                
                # Check if there are any case-level scripts in the current UI state
                case_widget_scripts = []
                if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, 'test_execution_cases'):
                    # Look for case-level scripts in the current UI state
                    for ui_case in self.parent_app.test_execution_cases:
                        if ui_case.get('case_number') == case.get('case_number') and 'scripts' in ui_case:
                            case_widget_scripts = ui_case.get('scripts', [])
                            print(f"DEBUG: Found {len(case_widget_scripts)} case-level scripts in current UI state")
                            break
                
                # Use current UI state if available, otherwise fall back to imported data
                if case_widget_scripts:
                    print(f"DEBUG: Using case-level scripts from current UI state for case {i} (prioritizing user modifications)")
                    processed_case["scripts"] = self._process_scripts_for_field(case_widget_scripts)
                else:
                    print(f"DEBUG: Using case-level scripts from imported data for case {i} (fallback)")
                    processed_case["scripts"] = self._process_scripts_for_field(case_scripts)
                
                # Get case-level placeholders from step widgets
                case_placeholders = []
                if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, 'step_widgets') and self.parent_app.step_widgets:
                    case_number = case.get('case_number', 1)
                    print(f"DEBUG: Looking for case-level placeholders for case {case_number}")
                    print(f"DEBUG: Available step keys: {list(self.parent_app.step_widgets.keys())}")
                    
                    for step_key, step_widget in self.parent_app.step_widgets.items():
                        if step_key.startswith(f"{case_number}_") and 'placeholders_list' in step_widget:
                            print(f"DEBUG: Found step_widget {step_key} for case {case_number}")
                            if step_widget['placeholders_list']:
                                print(f"DEBUG: Found {len(step_widget['placeholders_list'])} placeholders in {step_key}")
                                for placeholder_info in step_widget['placeholders_list']:
                                    if isinstance(placeholder_info, dict) and 'name' in placeholder_info:
                                        case_placeholders.append({
                                            'name': placeholder_info['name'],
                                            'type': 'placeholder',
                                            'is_placeholder': True
                                        })
                                        print(f"DEBUG: Added case-level placeholder: {placeholder_info['name']}")
                            else:
                                print(f"DEBUG: No placeholders in {step_key}")
                else:
                    print(f"DEBUG: No parent_app or step_widgets access available for case-level placeholders")
                
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
                            
                            # CRITICAL FIX: Prioritize current UI state over imported data for scripts
                            # This ensures that user modifications (new scripts added after import) are preserved
                            step_scripts = step_data.get("scripts", [])
                            print(f"DEBUG: Step {j+1} has {len(step_scripts)} scripts from imported step_data")
                            
                            # Always check current UI state first (step widgets) to get the most up-to-date scripts
                            step_widget_scripts = []
                            if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, 'step_widgets') and self.parent_app.step_widgets:
                                case_number = case.get('case_number', 1)
                                step_index = step_data.get('step_index', j + 1)
                                step_key = f"{case_number}_{step_index}"
                                
                                if step_key in self.parent_app.step_widgets:
                                    step_widget = self.parent_app.step_widgets[step_key]
                                    if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                                        step_widget_scripts = step_widget['upload_scripts_list']
                                        print(f"DEBUG: Found {len(step_widget_scripts)} scripts in current UI step widget {step_key}")
                            
                            # Use current UI state if available, otherwise fall back to imported data
                            if step_widget_scripts:
                                print(f"DEBUG: Using scripts from current UI state for step {j+1} (prioritizing user modifications)")
                                processed_step["scripts"] = self._process_scripts_for_field(step_widget_scripts)
                            elif step_scripts:
                                print(f"DEBUG: Using scripts from imported step_data for step {j+1} (fallback)")
                                processed_step["scripts"] = self._process_scripts_for_field(step_scripts)
                            else:
                                # Final fallback: Try to get from preserved imported data
                                print(f"DEBUG: No scripts in UI or step_data, checking preserved imported data for step {j+1}")
                                preserved_scripts = []
                                if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, '_imported_test_execution_data') and self.parent_app._imported_test_execution_data:
                                    case_number = case.get('case_number', 1)
                                    step_index = step_data.get('step_index', j + 1)
                                    
                                    for imported_case in self.parent_app._imported_test_execution_data:
                                        if imported_case.get('case_number') == case_number and 'steps_data' in imported_case:
                                            for imported_step_data in imported_case['steps_data']:
                                                if imported_step_data.get('step_index') == step_index and 'scripts' in imported_step_data and imported_step_data['scripts']:
                                                    preserved_scripts = imported_step_data['scripts']
                                                    print(f"DEBUG: Found {len(preserved_scripts)} scripts in preserved imported data for step {case_number}_{step_index}")
                                                    break
                                            if preserved_scripts:
                                                break
                                
                                processed_step["scripts"] = self._process_scripts_for_field(preserved_scripts)
                            
                            # Get placeholders from step widgets instead of step data
                            step_placeholders = []
                            if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, 'step_widgets') and self.parent_app.step_widgets:
                                case_number = case.get('case_number', 1)
                                step_index = step_data.get('step_index', j + 1)
                                step_key = f"{case_number}_{step_index}"
                                print(f"DEBUG: Looking for step_key: {step_key} in parent_app.step_widgets")
                                print(f"DEBUG: Available step keys: {list(self.parent_app.step_widgets.keys())}")
                                
                                if step_key in self.parent_app.step_widgets:
                                    step_widget = self.parent_app.step_widgets[step_key]
                                    print(f"DEBUG: Found step_widget for {step_key}: {step_widget}")
                                    if 'placeholders_list' in step_widget and step_widget['placeholders_list']:
                                        print(f"DEBUG: Found {len(step_widget['placeholders_list'])} placeholders in step_widget")
                                        for placeholder_info in step_widget['placeholders_list']:
                                            if isinstance(placeholder_info, dict) and 'name' in placeholder_info:
                                                step_placeholders.append({
                                                    'name': placeholder_info['name'],
                                                    'type': 'placeholder',
                                                    'is_placeholder': True
                                                })
                                                print(f"DEBUG: Added placeholder: {placeholder_info['name']}")
                                    else:
                                        print(f"DEBUG: No placeholders_list found in step_widget")
                                        print(f"DEBUG: step_widget keys: {list(step_widget.keys())}")
                                else:
                                    print(f"DEBUG: step_key {step_key} not found in parent_app.step_widgets")
                                    
                                    # FALLBACK: Check global storage for placeholders
                                    if hasattr(self.parent_app, '_global_step_placeholders') and step_key in self.parent_app._global_step_placeholders:
                                        global_placeholders = self.parent_app._global_step_placeholders[step_key]
                                        print(f"DEBUG: Found {len(global_placeholders)} placeholders in global storage for step {step_key}")
                                        for placeholder_info in global_placeholders:
                                            if isinstance(placeholder_info, dict) and 'name' in placeholder_info:
                                                step_placeholders.append({
                                                    'name': placeholder_info['name'],
                                                    'type': 'placeholder',
                                                    'is_placeholder': True
                                                })
                                                print(f"DEBUG: Added placeholder from global storage: {placeholder_info['name']}")
                            else:
                                print(f"DEBUG: No parent_app or step_widgets access available")
                            
                            # CRITICAL FIX: Extract placeholders from scripts if no placeholders found in UI
                            if not step_placeholders and step_scripts:
                                print(f"DEBUG: No placeholders found in UI, extracting from scripts for step {j+1}")
                                for script_info in step_scripts:
                                    if isinstance(script_info, dict) and 'placeholder' in script_info and script_info['placeholder']:
                                        placeholder_name = script_info['placeholder']
                                        print(f"DEBUG: Found placeholder '{placeholder_name}' in script: {script_info.get('filename', 'Unknown')}")
                                        step_placeholders.append({
                                            'name': placeholder_name,
                                            'type': 'placeholder',
                                            'is_placeholder': True
                                        })
                                        print(f"DEBUG: Added placeholder from script: {placeholder_name}")
                            
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
        
        # Get all placeholders for Expected Results section
        section8_placeholders = self._get_section8_placeholders_for_section("9. Expected Results for Pass")
        
        for result in expected_results:
            if isinstance(result, dict):
                processed_result = result.copy()
                processed_result["images"] = self._process_images_for_field(result.get("images", []))
                processed_result["scripts"] = self._process_scripts_for_field(result.get("scripts", []))
                
                # Add placeholders to each result (all results share the same placeholders for this section)
                if section8_placeholders:
                    processed_result["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
                else:
                    processed_result["placeholders"] = self._process_placeholders_for_field(result.get("placeholders", []))
                
                processed_results.append(processed_result)
        
        # If no results exist but we have placeholders, create a default result entry
        if not processed_results and section8_placeholders:
            default_result = {
                "scenario_key": "",
                "scenario_description": "",
                "expected_result": "",
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(section8_placeholders)
            }
            processed_results.append(default_result)
        
        return processed_results
    
    def _process_evidence_format(self, evidence_format: List[Dict]) -> List[Dict]:
        """Process evidence format with per-field storage"""
        processed_evidence = []
        
        # Get all placeholders for Evidence Format section
        section8_placeholders = self._get_section8_placeholders_for_section("10. Expected Format of Evidence")
        
        for evidence in evidence_format:
            if isinstance(evidence, dict):
                processed_item = evidence.copy()
                processed_item["images"] = self._process_images_for_field(evidence.get("images", []))
                processed_item["scripts"] = self._process_scripts_for_field(evidence.get("scripts", []))
                
                # Add placeholders to each evidence item (all items share the same placeholders for this section)
                if section8_placeholders:
                    processed_item["placeholders"] = self._process_placeholders_for_field(section8_placeholders)
                else:
                    processed_item["placeholders"] = self._process_placeholders_for_field(evidence.get("placeholders", []))
                
                processed_evidence.append(processed_item)
        
        # If no evidence exists but we have placeholders, create a default evidence entry
        if not processed_evidence and section8_placeholders:
            default_evidence = {
                "evidence_text": "Screenshot of Burp Suit pro, Nessus, Nmap and Firefox",
                "images": [],
                "scripts": [],
                "placeholders": self._process_placeholders_for_field(section8_placeholders)
            }
            processed_evidence.append(default_evidence)
        
        return processed_evidence
    
    def _get_section8_placeholders_for_scenario(self, scenario_key: str) -> List[Dict]:
        """Get placeholders for a specific test scenario from scenario_placeholders"""
        try:
            if hasattr(self.parent_app, 'scenario_placeholders') and self.parent_app.scenario_placeholders:
                placeholders = self.parent_app.scenario_placeholders.get(scenario_key, [])
                print(f"DEBUG: Found {len(placeholders)} placeholders for scenario '{scenario_key}': {placeholders}")
                return placeholders
            print(f"DEBUG: No scenario_placeholders found for scenario '{scenario_key}'")
            return []
        except Exception as e:
            print(f"DEBUG: Error getting scenario placeholders for '{scenario_key}': {e}")
            return []
    
    def _get_section8_placeholders_for_section(self, section_name: str) -> List[Dict]:
        """Get placeholders for a specific Section 8 subsection from scenario_placeholders"""
        try:
            if hasattr(self.parent_app, 'scenario_placeholders') and self.parent_app.scenario_placeholders:
                placeholders = self.parent_app.scenario_placeholders.get(section_name, [])
                print(f"DEBUG: Found {len(placeholders)} placeholders for section '{section_name}': {placeholders}")
                return placeholders
            print(f"DEBUG: No scenario_placeholders found for section '{section_name}'")
            return []
        except Exception as e:
            print(f"DEBUG: Error getting section placeholders for '{section_name}': {e}")
            return []
    
    def _process_images_for_field(self, images: List[Any]) -> List[Dict[str, Any]]:
        """Process images for a specific field with proper paths"""
        processed_images = []
        
        print(f"DEBUG: _process_images_for_field called with images: {images}")
        print(f"DEBUG: images type: {type(images)}")
        
        for i, image in enumerate(images):
            print(f"DEBUG: Processing image {i}: {image} (type: {type(image)})")
            
            if isinstance(image, dict):
                # Handle new image structure with absolute_path
                if "absolute_path" in image and image["absolute_path"]:
                    filename = os.path.basename(image["absolute_path"])
                    # Check if the absolute_path is already within the test case folder
                    if self.test_case_folder in image["absolute_path"]:
                        # Image is already in the test case folder, use relative path
                        relative_path = os.path.relpath(image["absolute_path"], self.test_case_folder)
                        processed_image = {
                            "path": relative_path,
                            "filename": filename,
                            "original_path": relative_path,  # Use relative path to avoid unnecessary copying
                            "description": image.get("description", ""),
                            "original_filename": image.get("original_filename", filename)
                        }
                        print(f"DEBUG: Added image already in test case folder: {relative_path}")
                    else:
                        # Image is outside test case folder, use absolute path for copying
                        processed_image = {
                            "path": f"raw_logs/{filename}",
                            "filename": filename,
                            "original_path": image["absolute_path"],
                            "description": image.get("description", ""),
                            "original_filename": image.get("original_filename", filename)
                        }
                        print(f"DEBUG: Added image with absolute_path: {filename}")
                    processed_images.append(processed_image)
                # Handle legacy structure with path
                elif "path" in image:
                    filename = os.path.basename(image["path"])
                    # Check if the path is already relative to test case folder
                    if image["path"].startswith(("raw_logs/", "code/", "tmp/")):
                        # Path is already relative, use as is
                        processed_image = {
                            "path": image["path"],
                            "filename": filename,
                            "original_path": image["path"],  # Use same path to avoid unnecessary copying
                            "description": image.get("description", ""),
                            "original_filename": image.get("original_filename", filename)
                        }
                        print(f"DEBUG: Added image with existing relative path: {image['path']}")
                    else:
                        # Path is absolute or needs to be copied
                        processed_image = {
                            "path": f"raw_logs/{filename}",
                            "filename": filename,
                            "original_path": image.get("path", ""),
                            "description": image.get("description", ""),
                            "original_filename": image.get("original_filename", filename)
                        }
                        print(f"DEBUG: Added image with path: {filename}")
                    processed_images.append(processed_image)
                # Handle structure with just filename
                elif "filename" in image:
                    filename = image["filename"]
                    processed_image = {
                        "path": f"raw_logs/{filename}",
                        "filename": filename,
                        "original_path": image.get("path", ""),
                        "description": image.get("description", ""),
                        "original_filename": image.get("original_filename", filename)
                    }
                    processed_images.append(processed_image)
                    print(f"DEBUG: Added image with filename: {filename}")
                else:
                    print(f"ERROR: Image {i} dict has no valid path/absolute_path/filename key: {list(image.keys())}")
            elif isinstance(image, str):
                filename = os.path.basename(image)
                processed_image = {
                    "path": f"raw_logs/{filename}",
                    "filename": filename,
                    "original_path": image,
                    "description": "",
                    "original_filename": filename
                }
                processed_images.append(processed_image)
                print(f"DEBUG: Added image from string: {filename}")
            else:
                print(f"ERROR: Image {i} is neither dict nor string: {type(image)}")
        
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
                print(f"DEBUG: Script {i} has absolute_path: {'absolute_path' in script}")
                print(f"DEBUG: Script {i} has path: {'path' in script}")
                print(f"DEBUG: Script {i} has original_path: {'original_path' in script}")
                print(f"DEBUG: Script {i} has filename: {'filename' in script}")
                
                # Handle new script structure with absolute_path
                if "absolute_path" in script and script["absolute_path"]:
                    filename = os.path.basename(script["absolute_path"])
                    # Check if the absolute_path is already within the test case folder
                    if self.test_case_folder in script["absolute_path"]:
                        # Script is already in the test case folder, use relative path
                        relative_path = os.path.relpath(script["absolute_path"], self.test_case_folder)
                        processed_script = {
                            "path": relative_path,
                            "filename": filename,
                            "original_filename": script.get("original_filename", filename),
                            "description": script.get("description", ""),
                            "is_pasted": script.get("is_pasted", False),
                            "original_path": relative_path,  # Use relative path to avoid unnecessary copying
                            "placeholder": script.get("placeholder", script.get("description", ""))
                        }
                        processed_scripts.append(processed_script)
                        print(f"DEBUG: Added script already in test case folder: {relative_path}")
                    else:
                        # Script is outside test case folder, use absolute path for copying
                        original_path = script["absolute_path"]
                        processed_script = {
                            "path": f"code/{filename}",
                            "filename": filename,
                            "original_filename": script.get("original_filename", filename),
                            "description": script.get("description", ""),
                            "is_pasted": script.get("is_pasted", False),
                            "original_path": original_path,
                            "placeholder": script.get("placeholder", script.get("description", ""))
                        }
                        processed_scripts.append(processed_script)
                        print(f"DEBUG: Added script with absolute_path: {filename}, original_path: {original_path}")
                # Handle legacy structure with path
                elif "path" in script:
                    filename = os.path.basename(script["path"])
                    # Check if the path is already relative to test case folder
                    if script["path"].startswith(("raw_logs/", "code/", "tmp/")):
                        # Path is already relative, use as is
                        processed_script = {
                            "path": script["path"],
                            "filename": filename,
                            "original_filename": script.get("original_filename", filename),
                            "description": script.get("description", ""),
                            "is_pasted": script.get("is_pasted", False),
                            "original_path": script["path"],  # Use same path to avoid unnecessary copying
                            "placeholder": script.get("placeholder", script.get("description", ""))
                        }
                        processed_scripts.append(processed_script)
                        print(f"DEBUG: Added script with existing relative path: {script['path']}")
                    else:
                        # Path is absolute or needs to be copied
                        # Store the original path as relative to project root for portability
                        original_path = script.get("path", "")
                        if original_path and os.path.isabs(original_path):
                            # Convert absolute path to relative path from project root
                            project_root = os.getcwd()
                            try:
                                original_path = os.path.relpath(original_path, project_root)
                                print(f"DEBUG: Converted absolute path to relative: {script.get('path', '')} -> {original_path}")
                            except ValueError:
                                # If paths are on different drives, keep the absolute path
                                print(f"DEBUG: Keeping absolute path (different drive): {original_path}")
                        elif original_path and not os.path.isabs(original_path):
                            # Already relative, keep as is
                            print(f"DEBUG: Path already relative: {original_path}")
                        
                        processed_script = {
                            "path": f"code/{filename}",
                            "filename": filename,
                            "original_filename": script.get("original_filename", filename),
                            "description": script.get("description", ""),
                            "is_pasted": script.get("is_pasted", False),
                            "original_path": original_path,
                            "placeholder": script.get("placeholder", script.get("description", ""))
                        }
                        processed_scripts.append(processed_script)
                        print(f"DEBUG: Added script with path: {filename}, original_path: {original_path}")
                # Handle structure with just filename
                elif "filename" in script:
                    processed_script = {
                        "path": f"code/{script['filename']}",
                        "filename": script["filename"],
                        "original_filename": script.get("original_filename", script["filename"]),
                        "description": script.get("description", ""),
                        "is_pasted": script.get("is_pasted", False),
                        "placeholder": script.get("placeholder", script.get("description", ""))
                    }
                    processed_scripts.append(processed_script)
                    print(f"DEBUG: Added script with filename: {script['filename']}")
                else:
                    print(f"ERROR: Script {i} dict has no valid path/absolute_path/filename key: {list(script.keys())}")
            elif isinstance(script, str):
                filename = os.path.basename(script)
                
                # Try to find the actual script info from global storage to get placeholder
                placeholder = ""
                description = ""
                is_pasted = False
                original_filename = filename
                
                # Look for script info in global storage
                if hasattr(self, 'global_step_scripts') and self.global_step_scripts:
                    print(f"DEBUG: Searching global storage for script: {filename}")
                    print(f"DEBUG: Available step keys: {list(self.global_step_scripts.keys())}")
                    
                    for step_key, scripts in self.global_step_scripts.items():
                        print(f"DEBUG: Checking step {step_key} with {len(scripts)} scripts")
                        for script_info in scripts:
                            script_filename = script_info.get('filename', '')
                            script_original = script_info.get('original_filename', '')
                            print(f"DEBUG: Comparing '{filename}' with '{script_filename}' and '{script_original}'")
                            
                            if script_filename == filename or script_original == filename:
                                placeholder = script_info.get('placeholder', script_info.get('description', ''))
                                description = script_info.get('description', '')
                                is_pasted = script_info.get('is_pasted', False)
                                original_filename = script_info.get('original_filename', filename)
                                print(f"DEBUG: Found script info for {filename} - placeholder: '{placeholder}'")
                                break
                        if placeholder:  # Found it, no need to continue searching
                            break
                
                # Fallback: If no placeholder found, generate one from filename
                if not placeholder:
                    # Try a more flexible search - look for scripts that contain the base filename
                    base_filename = filename.replace('.py', '').replace('uploaded_', '')
                    print(f"DEBUG: Trying flexible search with base filename: {base_filename}")
                    
                    if hasattr(self, 'global_step_scripts') and self.global_step_scripts:
                        for step_key, scripts in self.global_step_scripts.items():
                            for script_info in scripts:
                                script_filename = script_info.get('filename', '')
                                script_original = script_info.get('original_filename', '')
                                
                                # Check if the base filename is contained in either field
                                if (base_filename in script_filename or 
                                    base_filename in script_original or
                                    script_filename.replace('.py', '') == base_filename or
                                    script_original.replace('.py', '') == base_filename):
                                    
                                    placeholder = script_info.get('placeholder', script_info.get('description', ''))
                                    description = script_info.get('description', '')
                                    is_pasted = script_info.get('is_pasted', False)
                                    original_filename = script_info.get('original_filename', filename)
                                    print(f"DEBUG: Found script info via flexible search for {filename} - placeholder: '{placeholder}'")
                                    break
                            if placeholder:  # Found it, no need to continue searching
                                break
                    
                    # If still no placeholder found, use fallback
                    if not placeholder:
                        placeholder = f"script_{filename.replace('.py', '')}"
                        print(f"DEBUG: Using fallback placeholder for {filename}: '{placeholder}'")
                
                processed_script = {
                    "path": f"code/{filename}",
                    "filename": filename,
                    "original_filename": original_filename,
                    "description": description,
                    "is_pasted": is_pasted,
                    "original_path": script,
                    "placeholder": placeholder
                }
                processed_scripts.append(processed_script)
                print(f"DEBUG: Added script from string: {filename} with placeholder: '{placeholder}'")
            else:
                print(f"ERROR: Script {i} is neither dict nor string: {type(script)}")
        
        print(f"DEBUG: _process_scripts_for_field returning {len(processed_scripts)} scripts")
        return processed_scripts
    
    def _process_placeholders_for_field(self, placeholders: List[Any]) -> List[str]:
        """Process placeholders for a specific field"""
        processed_placeholders = []
        
        print(f"DEBUG: _process_placeholders_for_field called with placeholders: {placeholders}")
        print(f"DEBUG: placeholders type: {type(placeholders)}")
        
        for i, placeholder in enumerate(placeholders):
            print(f"DEBUG: Processing placeholder {i}: {placeholder} (type: {type(placeholder)})")
            
            if isinstance(placeholder, dict):
                # Handle Section 11 placeholder structure
                if "name" in placeholder and "type" in placeholder:
                    processed_placeholders.append(placeholder["name"])
                    print(f"DEBUG: Added Section 11 placeholder: {placeholder['name']}")
                # Handle legacy placeholder structure
                elif "placeholder" in placeholder:
                    processed_placeholders.append(placeholder["placeholder"])
                    print(f"DEBUG: Added legacy placeholder: {placeholder['placeholder']}")
                else:
                    print(f"DEBUG: Placeholder {i} dict missing required fields: {placeholder}")
            elif isinstance(placeholder, str):
                processed_placeholders.append(placeholder)
                print(f"DEBUG: Added string placeholder: {placeholder}")
            else:
                print(f"DEBUG: Placeholder {i} is neither dict nor string: {type(placeholder)}")
        
        print(f"DEBUG: _process_placeholders_for_field returning {len(processed_placeholders)} placeholders: {processed_placeholders}")
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
            "dependencies": processed_data["dependencies"],
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
                "header_text": processed_data.get("header_text", ""),
                "header_start_page": processed_data.get("header_start_page", 0),
                "export_path": processed_data["export_path"],
                "export_filename": processed_data["export_filename"],
                
                # Headings
                "test_scenarios_heading": processed_data["test_scenarios_heading"],
                "test_bed_diagram_heading": processed_data["test_bed_diagram_heading"],
                "test_bed_diagram_notes": processed_data["test_bed_diagram_notes"],
                "tools_required_heading": processed_data["tools_required_heading"],
                "test_execution_steps_heading": processed_data["test_execution_steps_heading"],
                "expected_results_heading": processed_data["expected_results_heading"],
                "expected_format_evidence_heading": processed_data["expected_format_evidence_heading"],
                
                # Results and evidence
                "expected_results": processed_data["expected_results"],
                "evidence_format": processed_data["evidence_format"],
                "test_case_results": processed_data["test_case_results"],
                
                # Dependencies
                "dependencies": processed_data["dependencies"],
                
                # Configuration fields
                "configuration_fields": processed_data.get("configuration_fields", {})
            }
        }
        
        
        return template_config
    
    def _copy_files_to_folders(self, processed_data: Dict[str, Any]) -> bool:
        """Copy uploaded files to proper folders using raw_logs/ and code/ structure"""
        try:
            print(f"DEBUG: _copy_files_to_folders called")
            # Setup paths
            raw_logs_folder = os.path.join(self.test_case_folder, "raw_logs")
            code_folder = os.path.join(self.test_case_folder, "code")
            
            print(f"DEBUG: raw_logs_folder: {raw_logs_folder}")
            print(f"DEBUG: code_folder: {code_folder}")
            
            # Ensure folders exist
            os.makedirs(code_folder, exist_ok=True)
            os.makedirs(raw_logs_folder, exist_ok=True)
            
            # Copy images from all fields
            images_success = self._copy_images_from_fields(processed_data, raw_logs_folder)
            
            # Copy scripts from all fields
            scripts_success = self._copy_scripts_from_fields(processed_data, code_folder)
            
            # Verify Section 11 scripts are copied
            section11_verification = self._verify_section11_scripts_copied(code_folder)
            
            return images_success and scripts_success and section11_verification
            
        except Exception as e:
            print(f"❌ Error copying files: {e}")
            return False
    
    def _copy_images_from_fields(self, processed_data: Dict[str, Any], raw_logs_folder: str) -> bool:
        """Copy images from all fields to raw_logs folder"""
        success = True
        # Copy from DUT fields
        for field in processed_data.get("dut_fields", []):
            for image in field.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    
                    # Skip copying if source is already in the test case folder
                    if should_skip_copy(src_path, self.test_case_folder):
                        print(f"ℹ️ Skipping copy for DUT image (already in test case folder): {image['filename']}")
                        continue
                    
                    if safe_copy_file(src_path, dst_path):
                        print(f"🖼️ Copied DUT image: {image['filename']}")
                    else:
                        print(f"❌ Failed to copy DUT image: {image['filename']}")
                        success = False
        
        # Copy from hash sections
        for section in processed_data.get("hash_sections", []):
            # Direct hash images
            for image in section.get("direct_hash_images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    
                    # Skip copying if source is already in the test case folder
                    if should_skip_copy(src_path, self.test_case_folder):
                        print(f"ℹ️ Skipping copy for hash image (already in test case folder): {image['filename']}")
                        continue
                    
                    if safe_copy_file(src_path, dst_path):
                        print(f"🖼️ Copied hash image: {image['filename']}")
                    else:
                        print(f"❌ Failed to copy hash image: {image['filename']}")
                        success = False
            
            # Hash field images
            for field in section.get("hash_fields", []):
                for image in field.get("images", []):
                    if "original_path" in image and os.path.exists(image["original_path"]):
                        src_path = image["original_path"]
                        dst_path = os.path.join(raw_logs_folder, image["filename"])
                        if safe_copy_file(src_path, dst_path):
                            print(f"🖼️ Copied hash field image: {image['filename']}")
                        else:
                            print(f"❌ Failed to copy hash field image: {image['filename']}")
                            success = False
        
        # Copy from ITSAR fields
        for field in processed_data.get("itsar_fields", []):
            for image in field.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"🖼️ Copied ITSAR image: {image['filename']}")
                    else:
                        print(f"❌ Failed to copy ITSAR image: {image['filename']}")
                        success = False
        
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
                                
                                # Skip copying if source is already in the test case folder
                                if should_skip_copy(src_path, self.test_case_folder):
                                    print(f"ℹ️ Skipping copy for {section_key} image (already in test case folder): {image['filename']}")
                                    continue
                                
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied {section_key} image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy {section_key} image: {image['filename']}")
                                    success = False
                    
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
                                                if safe_copy_file(src_path, dst_path):
                                                    print(f"🖼️ Copied {section_key} pair image: {image['filename']}")
                                                else:
                                                    print(f"❌ Failed to copy {section_key} pair image: {image['filename']}")
                                                    success = False
        
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
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied test scenario image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy test scenario image: {image['filename']}")
                                    success = False
        
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
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied tool image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy tool image: {image['filename']}")
                                    success = False
        
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
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied execution step image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy execution step image: {image['filename']}")
                                    success = False
        
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
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied test execution case image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy test execution case image: {image['filename']}")
                                    success = False
        
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
                                if safe_copy_file(src_path, dst_path):
                                    print(f"🖼️ Copied expected result image: {image['filename']}")
                                else:
                                    print(f"❌ Failed to copy expected result image: {image['filename']}")
                                    success = False
        
        # Copy from test execution cases
        for case in processed_data.get("test_execution_cases", []):
            # Copy case-level images
            for image in case.get("images", []):
                if "original_path" in image and os.path.exists(image["original_path"]):
                    src_path = image["original_path"]
                    dst_path = os.path.join(raw_logs_folder, image["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"🖼️ Copied test execution case image: {image['filename']}")
                    else:
                        print(f"❌ Failed to copy test execution case image: {image['filename']}")
                        success = False
            
            # Copy step-level images
            for step_data in case.get("steps_data", []):
                for image in step_data.get("images", []):
                    if "original_path" in image and os.path.exists(image["original_path"]):
                        src_path = image["original_path"]
                        dst_path = os.path.join(raw_logs_folder, image["filename"])
                        if safe_copy_file(src_path, dst_path):
                            print(f"🖼️ Copied test execution step image: {image['filename']}")
                        else:
                            print(f"❌ Failed to copy test execution step image: {image['filename']}")
                            success = False
        
        # Copy test bed images
        for image in processed_data.get("test_bed_images", []):
            if "original_path" in image and os.path.exists(image["original_path"]):
                src_path = image["original_path"]
                dst_path = os.path.join(raw_logs_folder, image["filename"])
                if safe_copy_file(src_path, dst_path):
                    print(f"🖼️ Copied test bed image: {image['filename']}")
                else:
                    print(f"❌ Failed to copy test bed image: {image['filename']}")
                    success = False
        
        # Copy step images
        for image in processed_data.get("step_images", []):
            if "original_path" in image and os.path.exists(image["original_path"]):
                src_path = image["original_path"]
                dst_path = os.path.join(raw_logs_folder, image["filename"])
                if safe_copy_file(src_path, dst_path):
                    print(f"🖼️ Copied step image: {image['filename']}")
                else:
                    print(f"❌ Failed to copy step image: {image['filename']}")
                    success = False
        
        return success
        
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
                    if shutil.copy2(src_path, dst_path):
                        print(f"📜 Copied hash script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy hash script: {script['filename']}")
                        success = False
            
            # Hash field scripts
            for field in section.get("hash_fields", []):
                for script in field.get("scripts", []):
                    if "original_path" in script and os.path.exists(script["original_path"]):
                        src_path = script["original_path"]
                        dst_path = os.path.join(code_folder, script["filename"])
                        if safe_copy_file(src_path, dst_path):
                            print(f"📜 Copied hash field script: {script['filename']}")
                        else:
                            print(f"❌ Failed to copy hash field script: {script['filename']}")
                            success = False
        
        # Copy from ITSAR fields
        for field in processed_data.get("itsar_fields", []):
            for script in field.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"📜 Copied ITSAR script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy ITSAR script: {script['filename']}")
                        success = False
        
        # Copy from sections 1-7
        sections_1_7 = processed_data.get("sections_1_7", {})
        for section_key, section_data in sections_1_7.items():
            if isinstance(section_data, dict):
                # Section scripts
                for script in section_data.get("scripts", []):
                    if "original_path" in script and os.path.exists(script["original_path"]):
                        src_path = script["original_path"]
                        dst_path = os.path.join(code_folder, script["filename"])
                        if safe_copy_file(src_path, dst_path):
                            print(f"📜 Copied {section_key} script: {script['filename']}")
                        else:
                            print(f"❌ Failed to copy {section_key} script: {script['filename']}")
                            success = False
                
                # Section pairs scripts
                if "pairs" in section_data:
                    for pair in section_data["pairs"]:
                        for script in pair.get("scripts", []):
                            if "original_path" in script and os.path.exists(script["original_path"]):
                                src_path = script["original_path"]
                                dst_path = os.path.join(code_folder, script["filename"])
                                if safe_copy_file(src_path, dst_path):
                                    print(f"📜 Copied {section_key} pair script: {script['filename']}")
                                else:
                                    print(f"❌ Failed to copy {section_key} pair script: {script['filename']}")
                                    success = False
        
        # Copy from test scenarios
        for scenario in processed_data.get("test_scenarios", []):
            for script in scenario.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"📜 Copied test scenario script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy test scenario script: {script['filename']}")
                        success = False
        
        # Copy from tools required
        for tool in processed_data.get("tools_required", []):
            for script in tool.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"📜 Copied tool script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy tool script: {script['filename']}")
                        success = False
        
        # Copy from execution steps
        for step in processed_data.get("execution_steps", []):
            for script in step.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"📜 Copied execution step script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy execution step script: {script['filename']}")
                        success = False
        
        # Copy from test execution cases
        for case in processed_data.get("test_execution_cases", []):
            for script in case.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if shutil.copy2(src_path, dst_path):
                        print(f"📜 Copied test execution case script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy test execution case script: {script['filename']}")
                        success = False
            
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
                        print(f"❌ Failed to copy test execution case script: {script['filename']}")
                        success = False
        
        # Copy from expected results
        for result in processed_data.get("expected_results", []):
            for script in result.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if safe_copy_file(src_path, dst_path):
                        print(f"📜 Copied expected result script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy expected result script: {script['filename']}")
                        success = False
        
        # Copy from test execution cases
        for case in processed_data.get("test_execution_cases", []):
            # Copy case-level scripts
            for script in case.get("scripts", []):
                if "original_path" in script and os.path.exists(script["original_path"]):
                    src_path = script["original_path"]
                    dst_path = os.path.join(code_folder, script["filename"])
                    if shutil.copy2(src_path, dst_path):
                        print(f"📜 Copied test execution case script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy test execution case script: {script['filename']}")
                        success = False
            
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
                    if shutil.copy2(src_path, dst_path):
                        print(f"📜 Copied expected result script: {script['filename']}")
                    else:
                        print(f"❌ Failed to copy expected result script: {script['filename']}")
                        success = False
        
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
        
        # NEW: Copy Section 11 scripts from parent step_widgets
        print("DEBUG: ===== SECTION 11 STEP WIDGETS SCRIPT COPYING START =====")
        print(f"DEBUG: parent_app exists: {hasattr(self, 'parent_app')}")
        if hasattr(self, 'parent_app'):
            print(f"DEBUG: parent_app is not None: {self.parent_app is not None}")
            if self.parent_app:
                print(f"DEBUG: parent_app has step_widgets: {hasattr(self.parent_app, 'step_widgets')}")
                if hasattr(self.parent_app, 'step_widgets'):
                    print(f"DEBUG: step_widgets is not None/empty: {self.parent_app.step_widgets is not None and bool(self.parent_app.step_widgets)}")
                    if self.parent_app.step_widgets:
                        print(f"DEBUG: step_widgets keys: {list(self.parent_app.step_widgets.keys())}")
        
        if hasattr(self, 'parent_app') and self.parent_app and hasattr(self.parent_app, 'step_widgets') and self.parent_app.step_widgets:
            print(f"DEBUG: Found parent step_widgets: {list(self.parent_app.step_widgets.keys())}")
            for step_key, step_widget in self.parent_app.step_widgets.items():
                if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                    print(f"DEBUG: Found {len(step_widget['upload_scripts_list'])} scripts in step {step_key}")
                    for script_info in step_widget['upload_scripts_list']:
                        # Try different path fields that might contain the script location
                        script_path = None
                        filename = script_info.get('filename', '')
                        
                        # Check for 'path' field first (relative path)
                        if 'path' in script_info and script_info['path']:
                            relative_path = script_info['path']
                            # Try to resolve absolute path using import_project_dir
                            if hasattr(self.parent_app, 'import_project_dir') and self.parent_app.import_project_dir:
                                script_path = os.path.join(self.parent_app.import_project_dir, relative_path)
                                print(f"DEBUG: Resolved script path from import_project_dir: {script_path}")
                            else:
                                # Try relative to current working directory
                                script_path = os.path.join(os.getcwd(), relative_path)
                                print(f"DEBUG: Resolved script path from cwd: {script_path}")
                        
                        # Fallback to 'original_path' field
                        if not script_path and 'original_path' in script_info and script_info['original_path']:
                            script_path = script_info['original_path']
                            print(f"DEBUG: Using original_path: {script_path}")
                        
                        if script_path and os.path.exists(script_path):
                            dst_path = os.path.join(code_folder, filename)
                            try:
                                shutil.copy2(script_path, dst_path)
                                print(f"📜 Copied Section 11 step widget script: {filename} (from {script_path})")
                                success = True
                            except Exception as e:
                                print(f"⚠️ Failed to copy Section 11 step widget script {filename}: {e}")
                        else:
                            print(f"⚠️ Section 11 step widget script not found: {script_info}")
                            print(f"   - Tried path: {script_path}")
                            print(f"   - File exists: {os.path.exists(script_path) if script_path else 'N/A'}")
        else:
            print("DEBUG: No parent step_widgets found for Section 11 script copying")
        print("DEBUG: ===== SECTION 11 STEP WIDGETS SCRIPT COPYING COMPLETED =====")
        
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
                # Skip certain fields that shouldn't be serialized
                if key in ['remove_btn', 'widget', 'layout']:
                    continue
                # Strip original_path for scripts and images in final JSON (keep internal use elsewhere)
                if key == "original_path":
                    path_value = data.get("path", "")
                    if isinstance(path_value, str) and (
                        path_value.startswith("code/") or path_value.startswith("raw_logs/")
                    ):
                        # Skip writing original_path for scripts and images
                        # But ensure the script/image itself is preserved
                        print(f"DEBUG: Stripping original_path from {path} - path_value: {path_value}")
                        continue
                cleaned_value, errors = self._validate_and_clean_data(value, f"{path}.{key}")
                cleaned_dict[key] = cleaned_value
                validation_errors.extend(errors)
            
            # Debug: Log what's being cleaned for scripts
            if "scripts" in cleaned_dict and cleaned_dict["scripts"]:
                print(f"DEBUG: Cleaned scripts for {path}: {len(cleaned_dict['scripts'])} scripts")
                for i, script in enumerate(cleaned_dict["scripts"]):
                    if isinstance(script, dict):
                        print(f"DEBUG: Cleaned script {i} keys: {list(script.keys())}")
                        print(f"DEBUG: Cleaned script {i} has path: {'path' in script}")
                        print(f"DEBUG: Cleaned script {i} has filename: {'filename' in script}")
        
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
            "template_config": {
                "exists": os.path.exists(self.template_config_path),
                "path": self.template_config_path
            }
        }
        
        # Load and analyze template config if it exists
        
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

    def _get_text_from_widget(self, widget):
        """Helper method to get text from either QLineEdit or QTextEdit widgets"""
        if widget is None:
            return ""
        
        try:
            # Try to get text from QLineEdit (has .text() method)
            if hasattr(widget, 'text'):
                return widget.text()
            # Try to get text from QTextEdit (has .toPlainText() method)
            elif hasattr(widget, 'toPlainText'):
                return widget.toPlainText()
            else:
                return ""
        except Exception as e:
            print(f"DEBUG: Error getting text from widget {type(widget)}: {e}")
            return ""

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
        
        # Debug: Print the sections_1_7_manager attributes
        print(f"🔍 DEBUG: sections_1_7_manager attributes: {[attr for attr in dir(sections_1_7_manager) if not attr.startswith('_')]}")
        
        sections_data = {}
        
        # Collect data for each section
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
            if hasattr(sections_1_7_manager, f'{section_name}_heading_edit') and hasattr(sections_1_7_manager, f'{section_name}_edit'):
                section_data = {
                    "heading": getattr(sections_1_7_manager, f'{section_name}_heading_edit').text() if getattr(sections_1_7_manager, f'{section_name}_heading_edit') else "",
                    "content": self._get_text_from_widget(getattr(sections_1_7_manager, f'{section_name}_edit', None)),
                    "images": [],
                    "scripts": [],
                    "placeholder_content_management": []
                }
                
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
                    print(f"🔍 DEBUG: {section_name} scripts_list attribute name: {section_name}_scripts_list")
                    print(f"🔍 DEBUG: sections_1_7_manager has {section_name}_scripts_list: {hasattr(sections_1_7_manager, f'{section_name}_scripts_list')}")
                    print(f"🔍 DEBUG: sections_1_7_manager attributes: {[attr for attr in dir(sections_1_7_manager) if not attr.startswith('_') and 'script' in attr.lower()]}")
                    
                    if isinstance(scripts_list, list):
                        for i, script in enumerate(scripts_list):
                            print(f"🔍 DEBUG: {section_name} script {i}: {script}")
                            print(f"🔍 DEBUG: {section_name} script {i} type: {type(script)}")
                            if isinstance(script, dict):
                                print(f"🔍 DEBUG: {section_name} script {i} keys: {list(script.keys())}")
                                print(f"🔍 DEBUG: {section_name} script {i} has path: {'path' in script}")
                                print(f"🔍 DEBUG: {section_name} script {i} has absolute_path: {'absolute_path' in script}")
                                print(f"🔍 DEBUG: {section_name} script {i} has filename: {'filename' in script}")
                                
                                # Ensure script has all required fields for processing
                                script_copy = script.copy()
                                
                                # Ensure path field exists
                                if "path" not in script_copy:
                                    if "filename" in script_copy:
                                        script_copy["path"] = script_copy["filename"]
                                    else:
                                        # Create a default path if neither exists
                                        script_copy["path"] = f"script_{i}.py"
                                
                                # Ensure original_path field exists for processing
                                if "original_path" not in script_copy:
                                    if "absolute_path" in script_copy:
                                        # Use absolute_path if available (this is what the UI provides)
                                        script_copy["original_path"] = script_copy["absolute_path"]
                                        print(f"🔍 DEBUG: {section_name} script {i} using absolute_path as original_path: {script_copy['absolute_path']}")
                                    elif "path" in script_copy:
                                        script_copy["original_path"] = script_copy["path"]
                                    else:
                                        script_copy["original_path"] = script_copy.get("filename", f"script_{i}.py")
                                
                                # Ensure filename field exists
                                if "filename" not in script_copy:
                                    if "path" in script_copy:
                                        script_copy["filename"] = os.path.basename(script_copy["path"])
                                    else:
                                        script_copy["filename"] = f"script_{i}.py"
                                
                                print(f"🔍 DEBUG: {section_name} script {i} processed: {script_copy}")
                                section_data["scripts"].append(script_copy)
                            else:
                                print(f"🔍 DEBUG: {section_name} script {i} is not a dict, skipping")
                    else:
                        print(f"🔍 DEBUG: {section_name} scripts_list is not a list, skipping")
                
                # Add Placeholder Content Management placeholders
                placeholder_attr_name = f'{section_name}_placeholders'
                if hasattr(sections_1_7_manager, placeholder_attr_name):
                    placeholder_list = getattr(sections_1_7_manager, placeholder_attr_name, [])
                    print(f"🔍 DEBUG: {section_name} placeholder_content_management: {placeholder_list}")
                    if isinstance(placeholder_list, list):
                        for placeholder_info in placeholder_list:
                            if isinstance(placeholder_info, dict) and "placeholder" in placeholder_info:
                                section_data["placeholder_content_management"].append({
                                    "placeholder": placeholder_info["placeholder"],
                                    "image_path": placeholder_info.get("image_path")
                                })
                                print(f"🔍 DEBUG: Added placeholder: {placeholder_info['placeholder']}")
                
                sections_data[section_name] = section_data
                print(f"🔍 DEBUG: Final {section_name} data: {section_data}")
                print(f"🔍 DEBUG: Final {section_name} scripts count: {len(section_data.get('scripts', []))}")
                print(f"🔍 DEBUG: Final {section_name} placeholder_content_management count: {len(section_data.get('placeholder_content_management', []))}")
        
        # Handle section_4 and section_5 pairs
        if hasattr(sections_1_7_manager, 'section_4_pairs'):
            sections_data["section_4"] = {
                "heading": getattr(sections_1_7_manager, 'section_4_heading_edit').text() if hasattr(sections_1_7_manager, 'section_4_heading_edit') else "DUT Confirmation Details",
                "pairs": [],
                "interfaces_desc": self._get_text_from_widget(getattr(sections_1_7_manager, 'section_4_interfaces_desc', None)),
                "interfaces": sections_1_7_manager.get_section_4_interface_data() if hasattr(sections_1_7_manager, 'get_section_4_interface_data') else [],
                "placeholder_content_management": []
            }
            for pair in sections_1_7_manager.section_4_pairs:
                pair_data = {
                    "text": self._get_text_from_widget(pair.get("text_edit", None)),
                    "images": [],
                    "scripts": [],
                    "placeholders": []
                }
                # Add pair images if they exist
                if "images_list" in pair:
                    for image_info in pair["images_list"]:
                        if isinstance(image_info, dict) and "path" in image_info:
                            pair_data["images"].append(image_info)
                # Add pair scripts if they exist
                if "upload_scripts_list" in pair:
                    for script_info in pair["upload_scripts_list"]:
                        if isinstance(script_info, dict):
                            # Ensure script has all required fields for processing
                            script_copy = script_info.copy()
                            
                            # Ensure path field exists
                            if "path" not in script_copy:
                                if "filename" in script_copy:
                                    script_copy["path"] = script_copy["filename"]
                                else:
                                    # Create a default path if neither exists
                                    script_copy["path"] = "pair_script.py"
                            
                            # Ensure original_path field exists for processing
                            if "original_path" not in script_copy:
                                if "path" in script_copy:
                                    script_copy["original_path"] = script_copy["path"]
                                else:
                                    script_copy["original_path"] = script_copy.get("filename", "pair_script.py")
                            
                            # Ensure filename field exists
                            if "filename" not in script_copy:
                                if "path" in script_copy:
                                    script_copy["filename"] = os.path.basename(script_copy["path"])
                                else:
                                    script_copy["filename"] = "pair_script.py"
                            
                            print(f"🔍 DEBUG: Section 4 pair script processed: {script_copy}")
                            pair_data["scripts"].append(script_copy)
                
                # Add pair placeholders if they exist
                if "placeholders" in pair:
                    pair_data["placeholders"] = pair["placeholders"]
                    # Also add to section's placeholder_content_management
                    for placeholder_info in pair["placeholders"]:
                        if isinstance(placeholder_info, dict) and "placeholder" in placeholder_info:
                            sections_data["section_4"]["placeholder_content_management"].append({
                                "placeholder": placeholder_info["placeholder"],
                                "image_path": placeholder_info.get("image_path")
                            })
                
                sections_data["section_4"]["pairs"].append(pair_data)
            
            # Add Placeholder Content Management placeholders for section 4
            if hasattr(sections_1_7_manager, 'section_4_placeholders'):
                placeholder_list = getattr(sections_1_7_manager, 'section_4_placeholders', [])
                print(f"🔍 DEBUG: section_4 placeholder_content_management: {placeholder_list}")
                if isinstance(placeholder_list, list):
                    for placeholder_info in placeholder_list:
                        if isinstance(placeholder_info, dict) and "placeholder" in placeholder_info:
                            sections_data["section_4"]["placeholder_content_management"].append({
                                "placeholder": placeholder_info["placeholder"],
                                "image_path": placeholder_info.get("image_path")
                            })
                            print(f"🔍 DEBUG: Added section 4 placeholder: {placeholder_info['placeholder']}")
        
        if hasattr(sections_1_7_manager, 'section_5_pairs'):
            sections_data["section_5"] = {
                "heading": getattr(sections_1_7_manager, 'section_5_heading_edit').text() if hasattr(sections_1_7_manager, 'section_5_heading_edit') else "DUT Configuration",
                "pairs": [],
                "placeholder_content_management": []
            }
            for pair in sections_1_7_manager.section_5_pairs:
                pair_data = {
                    "text": self._get_text_from_widget(pair.get("text_edit", None)),
                    "images": [],
                    "scripts": [],
                    "placeholders": []
                }
                # Add pair images if they exist
                if "images_list" in pair:
                    for image_info in pair["images_list"]:
                        if isinstance(image_info, dict) and "path" in image_info:
                            pair_data["images"].append(image_info)
                # Add pair scripts if they exist
                if "upload_scripts_list" in pair:
                    for script_info in pair["upload_scripts_list"]:
                        if isinstance(script_info, dict):
                            # Ensure script has all required fields for processing
                            script_copy = script_info.copy()
                            
                            # Ensure path field exists
                            if "path" not in script_copy:
                                if "filename" in script_copy:
                                    script_copy["path"] = script_copy["filename"]
                                else:
                                    # Create a default path if neither exists
                                    script_copy["path"] = "pair_script.py"
                            
                            # Ensure original_path field exists for processing
                            if "original_path" not in script_copy:
                                if "path" in script_copy:
                                    script_copy["original_path"] = script_copy["path"]
                                else:
                                    script_copy["original_path"] = script_copy.get("filename", "pair_script.py")
                            
                            # Ensure filename field exists
                            if "filename" not in script_copy:
                                if "path" in script_copy:
                                    script_copy["filename"] = os.path.basename(script_copy["path"])
                                else:
                                    script_copy["filename"] = "pair_script.py"
                            
                            print(f"🔍 DEBUG: Section 5 pair script processed: {script_copy}")
                            pair_data["scripts"].append(script_copy)
                
                # Add pair placeholders if they exist
                if "placeholders" in pair:
                    pair_data["placeholders"] = pair["placeholders"]
                    # Also add to section's placeholder_content_management
                    for placeholder_info in pair["placeholders"]:
                        if isinstance(placeholder_info, dict) and "placeholder" in placeholder_info:
                            sections_data["section_5"]["placeholder_content_management"].append({
                                "placeholder": placeholder_info["placeholder"],
                                "image_path": placeholder_info.get("image_path")
                            })
                
                sections_data["section_5"]["pairs"].append(pair_data)
            
            # Add Placeholder Content Management placeholders for section 5
            if hasattr(sections_1_7_manager, 'section_5_placeholders'):
                placeholder_list = getattr(sections_1_7_manager, 'section_5_placeholders', [])
                print(f"🔍 DEBUG: section_5 placeholder_content_management: {placeholder_list}")
                if isinstance(placeholder_list, list):
                    for placeholder_info in placeholder_list:
                        if isinstance(placeholder_info, dict) and "placeholder" in placeholder_info:
                            sections_data["section_5"]["placeholder_content_management"].append({
                                "placeholder": placeholder_info["placeholder"],
                                "image_path": placeholder_info.get("image_path")
                            })
                            print(f"🔍 DEBUG: Added section 5 placeholder: {placeholder_info['placeholder']}")
        
        print(f"🔍 DEBUG: Final sections_data keys: {list(sections_data.keys())}")
        for section_name, section_data in sections_data.items():
            if isinstance(section_data, dict):
                # Debug scripts
                if 'scripts' in section_data:
                    print(f"🔍 DEBUG: {section_name} final scripts count: {len(section_data['scripts'])}")
                    if section_data['scripts']:
                        print(f"🔍 DEBUG: {section_name} first script: {section_data['scripts'][0]}")
                        if isinstance(section_data['scripts'][0], dict):
                            print(f"🔍 DEBUG: {section_name} first script keys: {list(section_data['scripts'][0].keys())}")
                            print(f"🔍 DEBUG: {section_name} first script has original_path: {'original_path' in section_data['scripts'][0]}")
                            print(f"🔍 DEBUG: {section_name} first script has path: {'path' in section_data['scripts'][0]}")
                            print(f"🔍 DEBUG: {section_name} first script has filename: {'filename' in section_data['scripts'][0]}")
                
                # Debug placeholder content management
                if 'placeholder_content_management' in section_data:
                    print(f"🔍 DEBUG: {section_name} final placeholder_content_management count: {len(section_data['placeholder_content_management'])}")
                    if section_data['placeholder_content_management']:
                        print(f"🔍 DEBUG: {section_name} first placeholder: {section_data['placeholder_content_management'][0]}")
        
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
            
            # Create template_config.json only
            template_config = self._create_template_config(processed_data)
            
            # Save template_config.json only
            questions_success = True  # Skip questions_config.json creation
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

    def _update_template_config_with_sections_1_7_paths(self, processed_data: Dict[str, Any], code_folder: str, raw_logs_folder: str):
        """Update template config with new file paths for sections 1-7 after copying files"""
        print(f"DEBUG: ===== UPDATE TEMPLATE CONFIG WITH SECTIONS 1-7 PATHS START =====")
        
        # Load the current template config
        template_config_path = os.path.join(self.test_case_folder, "configuration", "template_config.json")
        if not os.path.exists(template_config_path):
            print(f"⚠️ Template config not found at {template_config_path}")
            return
        
        try:
            with open(template_config_path, 'r', encoding='utf-8') as f:
                template_config = json.load(f)
        except Exception as e:
            print(f"❌ Error loading template config: {e}")
            return
        
        configuration = template_config.get('configuration', {})
        sections_1_7 = configuration.get('sections_1_7', {})
        
        # Update sections 1, 2, 3, 6, 7
        for section_key in ['section_1', 'section_2', 'section_3', 'section_6', 'section_7']:
            if section_key in sections_1_7 and isinstance(sections_1_7[section_key], dict):
                section_data = sections_1_7[section_key]
                
                # Update images
                if 'images' in section_data and isinstance(section_data['images'], list):
                    for image_info in section_data['images']:
                        if isinstance(image_info, dict) and 'path' in image_info:
                            # Check if this image was copied to raw_logs folder
                            filename = image_info.get('filename', '')
                            if filename:
                                # Look for the copied file in raw_logs folder
                                copied_files = [f for f in os.listdir(raw_logs_folder) if filename in f]
                                if copied_files:
                                    # Use the first matching file
                                    new_filename = copied_files[0]
                                    image_info['path'] = f"raw_logs/{new_filename}"
                                    image_info['filename'] = new_filename
                                    print(f"✅ Updated {section_key} image path: {new_filename}")
                
                # Update scripts
                if 'scripts' in section_data and isinstance(section_data['scripts'], list):
                    for script_info in section_data['scripts']:
                        if isinstance(script_info, dict) and 'path' in script_info:
                            # Check if this script was copied to code folder
                            filename = script_info.get('filename', '')
                            if filename:
                                # Look for the copied file in code folder
                                copied_files = [f for f in os.listdir(code_folder) if filename in f]
                                if copied_files:
                                    # Use the first matching file
                                    new_filename = copied_files[0]
                                    script_info['path'] = f"code/{new_filename}"
                                    script_info['filename'] = new_filename
                                    print(f"✅ Updated {section_key} script path: {new_filename}")
        
        # Update sections 4 and 5 (pairs)
        for section_key in ['section_4', 'section_5']:
            if section_key in sections_1_7 and isinstance(sections_1_7[section_key], dict):
                section_data = sections_1_7[section_key]
                if 'pairs' in section_data and isinstance(section_data['pairs'], list):
                    for pair in section_data['pairs']:
                        if isinstance(pair, dict):
                            # Update pair images
                            if 'images' in pair and isinstance(pair['images'], list):
                                for image_info in pair['images']:
                                    if isinstance(image_info, dict) and 'path' in image_info:
                                        filename = image_info.get('filename', '')
                                        if filename:
                                            copied_files = [f for f in os.listdir(raw_logs_folder) if filename in f]
                                            if copied_files:
                                                new_filename = copied_files[0]
                                                image_info['path'] = f"raw_logs/{new_filename}"
                                                image_info['filename'] = new_filename
                                                print(f"✅ Updated {section_key} pair image path: {new_filename}")
                            
                            # Update pair scripts
                            if 'scripts' in pair and isinstance(pair['scripts'], list):
                                for script_info in pair['scripts']:
                                    if isinstance(script_info, dict) and 'path' in script_info:
                                        filename = script_info.get('filename', '')
                                        if filename:
                                            copied_files = [f for f in os.listdir(code_folder) if filename in f]
                                            if copied_files:
                                                new_filename = copied_files[0]
                                                script_info['path'] = f"code/{new_filename}"
                                                script_info['filename'] = new_filename
                                                print(f"✅ Updated {section_key} pair script path: {new_filename}")
        
        # Save the updated template config
        try:
            with open(template_config_path, 'w', encoding='utf-8') as f:
                json.dump(template_config, f, indent=2, ensure_ascii=False)
            print(f"✅ Updated template config saved with new sections 1-7 paths")
        except Exception as e:
            print(f"❌ Error saving updated template config: {e}")
        
        print(f"DEBUG: ===== UPDATE TEMPLATE CONFIG WITH SECTIONS 1-7 PATHS COMPLETED =====")
    
    def _verify_section11_scripts_copied(self, code_folder: str) -> bool:
        """Verify that all Section 11 scripts from step_widgets are copied to the code folder"""
        try:
            print(f"🔍 Verifying Section 11 scripts are copied to {code_folder}")
            
            print(f"DEBUG: parent_app exists: {hasattr(self, 'parent_app')}")
            if hasattr(self, 'parent_app'):
                print(f"DEBUG: parent_app is not None: {self.parent_app is not None}")
                if self.parent_app:
                    print(f"DEBUG: parent_app has step_widgets: {hasattr(self.parent_app, 'step_widgets')}")
                    if hasattr(self.parent_app, 'step_widgets'):
                        print(f"DEBUG: step_widgets is not None/empty: {self.parent_app.step_widgets is not None and bool(self.parent_app.step_widgets)}")
                        if self.parent_app.step_widgets:
                            print(f"DEBUG: step_widgets keys: {list(self.parent_app.step_widgets.keys())}")
            
            if not hasattr(self, 'parent_app') or not self.parent_app or not hasattr(self.parent_app, 'step_widgets') or not self.parent_app.step_widgets:
                print("DEBUG: No parent step_widgets found for verification")
                return True
            
            expected_scripts = []
            for step_key, step_widget in self.parent_app.step_widgets.items():
                if 'upload_scripts_list' in step_widget and step_widget['upload_scripts_list']:
                    for script_info in step_widget['upload_scripts_list']:
                        filename = script_info.get('filename', '')
                        if filename:
                            expected_scripts.append(filename)
                            print(f"DEBUG: Expected Section 11 script: {filename}")
            
            if not expected_scripts:
                print("DEBUG: No Section 11 scripts expected")
                return True
            
            # Check which scripts are missing
            missing_scripts = []
            for script_name in expected_scripts:
                script_path = os.path.join(code_folder, script_name)
                if not os.path.exists(script_path):
                    print(f"❌ Missing Section 11 script: {script_name}")
                    missing_scripts.append(script_name)
                else:
                    print(f"✅ Section 11 script exists: {script_name}")
            
            if missing_scripts:
                print(f"⚠️ {len(missing_scripts)} Section 11 scripts are missing: {missing_scripts}")
                return False
            else:
                print(f"✅ All {len(expected_scripts)} Section 11 scripts verified successfully!")
                return True
                
        except Exception as e:
            print(f"❌ Error during Section 11 script verification: {e}")
            return False
