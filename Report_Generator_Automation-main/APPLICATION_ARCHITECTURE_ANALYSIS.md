# Security Assessment Report Generator - Complete Architecture Analysis

## Overview
This is a comprehensive PyQt6-based application for generating security assessment reports with automated test execution capabilities. The application follows a modular architecture with clear separation of concerns between UI, data processing, and document generation.

## Core Architecture Components

### 1. Main Application Structure

#### Primary Entry Point
- **File**: `security_report_generator.py`
- **Class**: `SecurityReportGenerator(QMainWindow)`
- **Purpose**: Main application window with tabbed interface for different sections

#### Key UI Components
- **Sidebar Navigation**: Sections 1-7, Section 8 (Test Plan), Section 11 (Test Execution)
- **Content Areas**: Dynamic forms for each section
- **Preview Panel**: Real-time document preview
- **Export/Import System**: Configuration management

### 2. Data Flow Architecture

#### Input Sources
1. **User Interface Forms**: Text inputs, dropdowns, file uploads
2. **Script Uploads**: Python automation scripts
3. **Image/Screenshot Uploads**: Evidence collection
4. **Configuration Files**: Pre-defined templates

#### Data Processing Pipeline
```
UI Input → Configuration Storage → Export/Import → Document Generation → Final Report
```

### 3. Configuration Management System

#### Configuration Files Structure

##### `template_config.json`
```json
{
  "export_timestamp": "timestamp",
  "test_case_name": "name",
  "configuration": {
    "sections_1_7": {
      "section_1": { "heading": "...", "content": "...", "images": [], "scripts": [], "placeholders": [] },
      "section_2": { ... },
      // ... sections 3-7
    },
    "test_plan_overview": "...",
    "test_scenarios": [],
    "test_bed_diagram": { "heading": "...", "images": [], "scripts": [], "placeholders": [] },
    "tools_required": [],
    "execution_steps": [],
    "test_execution_cases": [],
    "expected_results": [],
    "evidence_format": []
  }
}
```

##### `question_config.json`
```json
{
  "ui": { "title": "..." },
  "questions": [
    {
      "id": 1,
      "question": "Question text",
      "help_text": "Help text",
      "error_message": "Error message",
      "question_type": "command_execution|upload|yes_no|text_input",
      "script_name": "scripts/script_name.py",
      "icon_info": { "show_icon": false, "title": "", "content": "" },
      "screenshot_line_number": 45,
      "dir_way": "start|end|none",
      "placeholder": "placeholder_name"
    }
  ],
  "metadata": { "total_questions": 4, "description": "...", "version": "1.0" },
  "configuration": { "fields": [] },
  "dependencies": [],
  "Summary": { "result_1": "none", "remarks_1": "none" },
  "automatic_images": []
}
```

### 4. Question Generation System

#### Essential Questions
- **Source**: Sections 1-7 script uploads
- **Purpose**: Pre-execution verification questions
- **Storage**: `question_config.json` → `questions` array
- **Types**: `yes_no`, `text_input`, `command_execution`, `upload`

#### Execution Step Questions
- **Source**: Section 8 and Section 11 script uploads
- **Purpose**: Test execution automation
- **Storage**: `question_config.json` → `questions` array
- **Integration**: Linked to specific test steps

#### Question Creation Process
1. **Script Upload**: User uploads Python script via UI
2. **Automatic Mapping**: System creates corresponding question entry
3. **Configuration Update**: Question added to `question_config.json`
4. **Placeholder Assignment**: Unique placeholder name generated
5. **Execution Integration**: Script linked to automation system

### 5. Script Management System

#### Script Upload Workflow
```
File Selection → Validation → Storage → Configuration Update → Question Creation
```

#### Storage Structure
```
test_case_folder/
├── code/
│   └── script.py (uploaded scripts)
├── raw_logs/
│   └── images/ (screenshots, evidence)
├── configuration/
│   ├── question_config.json
│   └── template_config.json
└── report/
    └── security_report.docx
```

#### Script Execution
- **Executor**: `SafeScriptExecutor` class
- **Manager**: `ScriptManager` class
- **Integration**: `GENERAL/comman_files/automation.py`
- **Dynamic Generation**: Scripts compiled into `dynamic_exec_generated.py`

### 6. Raw Logs Processing

#### Image Processing
- **Upload**: Via UI file dialogs
- **Storage**: `raw_logs/` directory
- **Processing**: `_process_images_for_field()` method
- **Integration**: Linked to specific sections and steps

#### Data Structure
```json
{
  "path": "raw_logs/filename.jpg",
  "filename": "filename.jpg",
  "original_path": "/original/path",
  "description": "Image description",
  "original_filename": "original_name.jpg"
}
```

### 7. Document Generation System

#### Core Generator
- **File**: `enhanced_document_generator.py`
- **Class**: `EnhancedDocumentGenerator`
- **Manager**: `EnhancedDocumentManager`

#### Document Structure
1. **Header**: Title, DUT details, placeholders
2. **Sections 1-7**: ITSAR information, requirements, configuration
3. **Section 8**: Test plan, scenarios, execution steps
4. **Section 9**: Expected results
5. **Section 10**: Evidence format
6. **Section 11**: Test execution cases with results

#### Placeholder System
- **Dynamic Resolution**: Values from configuration files
- **Section Mapping**: Each section has specific placeholders
- **Image Integration**: Screenshots embedded in appropriate sections
- **Script Results**: Command outputs integrated into execution steps

### 8. Export/Import System

#### Enhanced Export/Import
- **File**: `enhanced_export_import.py`
- **Class**: `EnhancedExportImport`
- **Purpose**: Configuration persistence and project management

#### Export Process
1. **Data Collection**: Gather all UI form data
2. **File Processing**: Copy images, scripts to appropriate folders
3. **Configuration Generation**: Create `template_config.json` and `question_config.json`
4. **Project Structure**: Organize files in test case folder

#### Import Process
1. **Configuration Loading**: Read existing configuration files
2. **UI Population**: Restore form data from configuration
3. **File Restoration**: Relink images and scripts
4. **State Recovery**: Restore application state

### 9. Automation Integration

#### Automation System
- **File**: `GENERAL/comman_files/automation.py`
- **Purpose**: Execute uploaded scripts and collect results
- **Integration**: Works with `question_config.json`

#### Execution Flow
1. **Question Loading**: Read questions from configuration
2. **Script Execution**: Run corresponding Python scripts
3. **Result Collection**: Capture outputs and screenshots
4. **Report Update**: Update placeholders with results
5. **Document Generation**: Create final report with results

### 10. Data Flow Summary

#### Complete Workflow
```
1. User Input (UI Forms)
   ↓
2. Configuration Storage (template_config.json, question_config.json)
   ↓
3. Script Upload & Processing (code/ folder)
   ↓
4. Image/Evidence Collection (raw_logs/ folder)
   ↓
5. Automation Execution (GENERAL/comman_files/automation.py)
   ↓
6. Result Integration (updated placeholders)
   ↓
7. Document Generation (enhanced_document_generator.py)
   ↓
8. Final Report (security_report.docx)
```

#### Key Data Transformations
- **UI Data → JSON Configuration**: Form data serialized to configuration files
- **Scripts → Questions**: Uploaded scripts automatically generate question entries
- **Images → Evidence**: Screenshots linked to specific test steps
- **Results → Placeholders**: Execution results populate document placeholders
- **Configuration → Document**: JSON data transformed into Word document

### 11. File Organization

#### Project Structure
```
Report_Generator_Automation/
├── security_report_generator.py          # Main application
├── enhanced_document_generator.py        # Document generation
├── enhanced_export_import.py             # Configuration management
├── script_upload_widget.py               # Script upload UI
├── script_executor.py                    # Script execution
├── section8_media_handler.py             # Media processing
├── GENERAL/comman_files/
│   ├── automation.py                     # Automation system
│   ├── config_manager.py                 # Configuration management
│   └── network_utils.py                  # Network utilities
├── tmp/                                  # Temporary test cases
│   └── [test_case_id]/
│       ├── code/                         # Uploaded scripts
│       ├── raw_logs/                     # Images and evidence
│       ├── configuration/                # Configuration files
│       └── report/                       # Generated reports
└── [various test and utility files]
```

### 12. Key Features

#### Automation Capabilities
- **Script Upload**: Python scripts for automated testing
- **Question Generation**: Automatic question creation from scripts
- **Execution Management**: Safe script execution with error handling
- **Result Integration**: Automatic result incorporation into reports

#### Document Features
- **Template Support**: Custom document templates
- **Dynamic Content**: Placeholder-based content generation
- **Image Integration**: Screenshot and evidence embedding
- **Section Management**: Organized report sections

#### Configuration Management
- **Project Persistence**: Save/load complete project states
- **Export/Import**: Share configurations between instances
- **Version Control**: Timestamp-based configuration tracking

This architecture provides a comprehensive solution for security assessment report generation with strong automation capabilities and flexible configuration management.
