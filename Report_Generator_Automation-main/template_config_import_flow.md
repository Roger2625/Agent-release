# Template Config JSON Import Flow

## Complete Import Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEMPLATE_CONFIG.JSON IMPORT FLOW            │
└─────────────────────────────────────────────────────────────────┘

1. FILE SELECTION
   ├── User clicks "Import Template JSON"
   ├── QFileDialog opens for file selection
   └── User selects template_config.json file

2. FILE LOADING & VALIDATION
   ├── Load and parse JSON file
   ├── Validate JSON structure
   ├── Detect project directory for path resolution
   └── Store import_project_dir for later use

3. DATA CLEARING
   ├── Clear all existing form data
   ├── Reset UI components
   ├── Clear configuration fields
   └── Reset sections 1-7 tab creation flag

4. CORE IMPORT PROCESS
   │
   ├── 4.1 CONFIGURATION DATA IMPORT
   │   ├── Import basic fields (report title, number, paths)
   │   ├── Import DUT fields, hash sections, ITSAR fields
   │   ├── Import machine IP, target IP, SSH credentials
   │   └── Import screenshots and interfaces
   │
   ├── 4.2 SECTIONS 1-7 DATA IMPORT
   │   ├── Import all 7 sections with content, images, scripts
   │   ├── Create sections 1-7 tab if needed
   │   └── Load data into UI via Sections1_7Manager
   │
   ├── 4.3 TEST PLAN DATA IMPORT (Section 8)
   │   ├── Import test scenarios with keys and descriptions
   │   ├── Import test bed diagram heading and images
   │   ├── Import test bed scripts with metadata
   │   ├── Import tools required
   │   └── Import execution steps
   │
   ├── 4.4 SECTION 8 MEDIA IMPORT
   │   ├── Import Section 8 media data (scripts/images)
   │   ├── Handle placeholder management
   │   └── Update template_config.json with media info
   │
   ├── 4.5 TEST EXECUTION DATA IMPORT (Section 11)
   │   ├── Import test execution cases with metadata
   │   ├── Import step images and scripts
   │   ├── Handle placeholder management
   │   └── Preserve file paths and metadata
   │
   ├── 4.6 TEST CASE RESULTS IMPORT
   │   ├── Import test case results data
   │   └── Update test case results table
   │
   └── 4.7 UPLOADED FILES & PLACEHOLDERS IMPORT
       ├── Import automatic images (placeholders)
       ├── Import uploaded scripts and images
       ├── Handle file path resolution
       └── Add files to appropriate sections

5. DATA PROCESSING METHODS
   │
   ├── 5.1 FILE PATH RESOLUTION
   │   ├── Resolve relative paths to absolute paths
   │   ├── Handle different project directory structures
   │   └── Check multiple possible file locations
   │
   ├── 5.2 SCRIPT IMPORT
   │   ├── Copy script files to appropriate locations
   │   ├── Add scripts to section containers
   │   └── Handle script metadata and placeholders
   │
   └── 5.3 IMAGE IMPORT
       ├── Copy image files to appropriate locations
       ├── Add images to section containers
       └── Handle image metadata and placeholders

6. UI REPOPULATION
   │
   ├── 6.1 CONFIGURATION FIELDS
   │   ├── Repopulate DUT fields, hash sections, ITSAR fields
   │   ├── Update text inputs and dropdowns
   │   └── Restore field metadata and placeholders
   │
   ├── 6.2 SECTION WIDGETS
   │   ├── Recreate section tabs and layouts
   │   ├── Restore content, images, and scripts
   │   └── Rebuild placeholder displays
   │
   └── 6.3 TEST EXECUTION UI
       ├── Recreate test execution cases
       ├── Restore step widgets with images and scripts
       └── Rebuild execution step layouts

7. POST-IMPORT PROCESSING
   │
   ├── 7.1 VALIDATION
   │   ├── Validate imported file existence
   │   ├── Check for missing files and provide warnings
   │   └── Verify data integrity
   │
   ├── 7.2 UI UPDATES
   │   ├── Update preview displays
   │   ├── Force UI refresh
   │   └── Update status bar
   │
   └── 7.3 SUCCESS NOTIFICATION
       └── Show success message to user

8. KEY DATA STRUCTURES IN TEMPLATE_CONFIG.JSON
   │
   ├── Configuration
   │   ├── Basic settings (report title, number, paths)
   │   ├── DUT fields, hash sections, ITSAR fields
   │   ├── Machine IP, target IP, SSH credentials
   │   └── Screenshots and interfaces
   │
   ├── Sections 1-7
   │   ├── Complete section data with content
   │   ├── Images, scripts, placeholders
   │   └── Text content and metadata
   │
   ├── Test Plan (Section 8)
   │   ├── Test scenarios with keys and descriptions
   │   ├── Test bed diagram and images
   │   ├── Tools required
   │   └── Execution steps
   │
   ├── Test Execution (Section 11)
   │   ├── Test cases with metadata
   │   ├── Step images and scripts
   │   └── Placeholder management
   │
   ├── Media Files
   │   ├── All uploaded images with metadata
   │   ├── All uploaded scripts with metadata
   │   └── File path information
   │
   └── Placeholders
       ├── Automatic images
       └── Placeholder management data

9. ERROR HANDLING
   │
   ├── JSON parsing errors
   ├── File not found errors
   ├── Invalid data structure errors
   ├── Import validation failures
   └── UI update errors

┌─────────────────────────────────────────────────────────────────┐
│                    IMPORT COMPLETED SUCCESSFULLY               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Methods Involved

### Main Import Method
- `import_template_json()` - Entry point for template JSON import

### Data Import Methods
- `import_configuration_data()` - Import basic configuration
- `import_sections_1_7_data()` - Import sections 1-7 data
- `import_test_plan_data()` - Import test plan data (Section 8)
- `import_test_execution_data()` - Import test execution data (Section 11)
- `import_test_case_results()` - Import test case results
- `import_uploaded_files_and_placeholders()` - Import files and placeholders

### Processing Methods
- `resolve_import_path()` - Resolve file paths
- `_add_imported_script_to_section()` - Add scripts to sections
- `_add_imported_image_to_section()` - Add images to sections

### UI Management
- `clear_all_form_data()` - Clear existing data
- `update_preview()` - Update UI preview
- `Sections1_7Manager.load_sections_1_7_data()` - Load sections data

## File Structure Expected

```
project_directory/
├── configuration/
│   └── template_config.json
├── code/
│   └── script files
├── raw_logs/
│   └── image files
└── report/
    └── generated reports
```

This flow ensures complete restoration of all application state from the template_config.json file, including all UI elements, file references, and metadata.
