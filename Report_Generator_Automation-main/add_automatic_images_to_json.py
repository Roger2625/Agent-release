#!/usr/bin/env python3

import json
import os

def add_automatic_images_to_json():
    """Add automatic_images array to the existing JSON file"""
    
    json_file_path = "tmp/Unknown_Test_Case/code/questions_config.json"
    
    if not os.path.exists(json_file_path):
        print(f"❌ JSON file not found: {json_file_path}")
        return
    
    try:
        # Read the existing JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Read existing JSON with keys: {list(data.keys())}")
        
        # Add automatic_images if not present
        if 'automatic_images' not in data:
            data['automatic_images'] = [
                {
                    "placeholder": "amazon_screenshot",
                    "image_path": None
                },
                {
                    "placeholder": "test_bed_diagram",
                    "image_path": None
                }
            ]
            print("✅ Added automatic_images array")
        else:
            print("✅ automatic_images already exists")
        
        # Write back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated JSON file: {json_file_path}")
        
        # Verify the update
        with open(json_file_path, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        if 'automatic_images' in updated_data:
            print(f"✅ Verification successful: automatic_images has {len(updated_data['automatic_images'])} items")
            for item in updated_data['automatic_images']:
                print(f"  - {item['placeholder']}")
        else:
            print("❌ Verification failed: automatic_images not found in updated file")
            
    except Exception as e:
        print(f"❌ Error updating JSON: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_automatic_images_to_json()
