#!/usr/bin/env python3

# Try to understand what's happening with the method
import inspect

try:
    # Import the module
    from enhanced_document_generator import EnhancedDocumentGenerator

    # Check all methods in the class
    methods = [method for method in dir(EnhancedDocumentGenerator) if not method.startswith('_')]
    print("Available methods:")
    for method in methods:
        print(f"  - {method}")

    # Check if our method is in the list
    if 'resolve_steps_data_filenames' in methods:
        print("\n✓ resolve_steps_data_filenames found in methods list")
    else:
        print("\n✗ resolve_steps_data_filenames NOT found in methods list")

    # Try to get the method directly
    try:
        method = getattr(EnhancedDocumentGenerator, 'resolve_steps_data_filenames')
        print(f"✓ Method retrieved via getattr: {method}")
        print(f"✓ Method type: {type(method)}")
    except AttributeError as e:
        print(f"✗ getattr failed: {e}")

except Exception as e:
    print(f"✗ Import or execution error: {e}")
    import traceback
    traceback.print_exc()


