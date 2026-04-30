import nmap

# Configuration
host = '192.168.0.18'   
port_range = '1-1024'
nm = nmap.PortScanner(nmap_search_path=[r'C:\Program Files (x86)\Nmap\nmap.exe'])

print(f"Starting debug scan for {host}...")

try:
    # Perform the scan
    # Added -Pn because we know .165 might be hiding from pings
    result = nm.scan(host, port_range, '-sV -sC -T4 -Pn')

    # Check if the scan actually found TCP ports
    if host in result['scan'] and 'tcp' in result['scan'][host]:
        ports_found = result['scan'][host]['tcp']
        
        for port_num, port_data in ports_found.items():
            port_status = port_data.get('state')
            print(f"Port {port_num} status: {port_status}")
            if port_status == "open":
                name = port_data.get('name', 'Unknown')
                product = port_data.get('product', 'Unknown')
                version = port_data.get('version', 'Unknown')
                
                print(f"\n[+] Found Open Port: {port_num}")
                print(f"    Service: {name}")
                print(f"    Product: {product}")
                print(f"    Version: {version}")
    else:
        print(f"\n[!] Scan finished: No open TCP ports were found on {host}.")

except Exception as e:
    print(f"An error occurred during the scan: {e}")