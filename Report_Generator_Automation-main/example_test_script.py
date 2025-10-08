#!/usr/bin/env python3
"""
Example test script for vulnerability scanning
This script demonstrates a simple network service check
"""

import socket
import subprocess
import sys
import time

def check_port(host, port):
    """Check if a port is open on the specified host"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False

def scan_common_ports(host):
    """Scan common ports on the specified host"""
    common_ports = [22, 23, 25, 53, 80, 110, 143, 443, 993, 995]
    
    print(f"Scanning common ports on {host}...")
    print("=" * 50)
    
    open_ports = []
    for port in common_ports:
        if check_port(host, port):
            service_name = get_service_name(port)
            print(f"✓ Port {port} ({service_name}) is OPEN")
            open_ports.append(port)
        else:
            service_name = get_service_name(port)
            print(f"✗ Port {port} ({service_name}) is CLOSED")
    
    print("=" * 50)
    print(f"Found {len(open_ports)} open ports: {open_ports}")
    return open_ports

def get_service_name(port):
    """Get the service name for a port"""
    services = {
        22: "SSH",
        23: "Telnet", 
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        993: "IMAPS",
        995: "POP3S"
    }
    return services.get(port, "Unknown")

def main():
    """Main function"""
    print("Vulnerability Scanning Test Script")
    print("=" * 40)
    
    # Get target host from command line or use default
    if len(sys.argv) > 1:
        target_host = sys.argv[1]
    else:
        target_host = "127.0.0.1"  # Default to localhost
    
    print(f"Target host: {target_host}")
    print(f"Scan start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Perform port scan
    open_ports = scan_common_ports(target_host)
    
    # Generate report
    print("\n" + "=" * 50)
    print("SCAN SUMMARY")
    print("=" * 50)
    print(f"Target: {target_host}")
    print(f"Scan completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Open ports found: {len(open_ports)}")
    
    if open_ports:
        print("Security recommendations:")
        print("- Review and secure any unnecessary open ports")
        print("- Ensure all services are properly configured")
        print("- Consider implementing firewall rules")
    else:
        print("No open ports found - good security posture!")
    
    print("\nScript execution completed successfully!")

if __name__ == "__main__":
    main()
