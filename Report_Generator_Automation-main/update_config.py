import json
import time
import os
from pathlib import Path

def read_client_config():
    """Read token and base_url from client.conf.json"""
    try:
        # Try to find client.conf.json in parent directory
        config_path = Path('../client.conf.json')
        if not config_path.exists():
            config_path = Path('client.conf.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('token'), config.get('server_url')
    except FileNotFoundError:
        print("client.conf.json not found")
        return None, None
    except json.JSONDecodeError:
        print("Invalid JSON in client.conf.json")
        return None, None

def update_testcase_config(token, base_url):
    """Update 1.json with current token and base_url"""
    import os
    config_path = Path(os.path.expanduser('~/1.json'))
    
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update token and base_url
        config['token'] = token
        config['base_url'] = base_url
        
        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated {config_path} with new token and base_url")
        return True
        
    except FileNotFoundError:
        print(f"File {config_path} not found")
        return False
    except json.JSONDecodeError:
        print(f"Invalid JSON in {config_path}")
        return False

def main():
    """Main function to handle config updates"""
    print("Reading configuration from client.conf.json...")
    
    token, base_url = read_client_config()
    
    if token is None or base_url is None:
        print("Failed to read configuration")
        return
    
    print(f"Token: {token[:20]}...")
    print(f"Base URL: {base_url}")
    
    if update_testcase_config(token, base_url):
        print("Configuration updated successfully")
    else:
        print("Failed to update configuration")

if __name__ == "__main__":
    main()
