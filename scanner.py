import nmap
import ipaddress
import re


network = '192.168.0.0/24'
ip_address = '192.168.0.118'
port_range = '7600-8000'
nm = nmap.PortScanner(nmap_search_path=[r'C:\Program Files (x86)\Nmap\nmap.exe'])  #Specify path to nmap.exe
router_ip = '192.168.0.1'

def active_ip_addresses(network):
    nm.scan(hosts=network, arguments='-sn')  # -sn is for ping scan (no port scan)
    live_hosts = nm.all_hosts()
    print(f"Live hosts in the network {network}: {live_hosts}")
    return live_hosts

#ip_address_obj = ipaddress.ip_address(ip_address)
host_list = active_ip_addresses(network)

for host in host_list:
    print(f"Scanning host: {host}")
    if host == router_ip:
        print(f"Skipping router IP: {host}")
        continue
    try:
        # The result is quite interesting to look at. You may want to inspect the dictionary it returns. 
        # It contains what was sent to the command line in addition to the port status we're after. 
        # For in nmap for port 80 and ip 10.0.0.2 you'd run: nma192.168.0.118p -oX - -p 89 -sV 10.0.0.2
        result = nm.scan(host, port_range, '-sV -sC -T4')     #the scan function decides what gets scanned
        # Uncomment following line and look at dictionary
        #print(result)
        if host in result['scan'] and 'tcp' in result['scan'][host] and host != '192.168.0.1':
        # We extract the port status from the returned object
            scanned_ports = result['scan'][host]['tcp']
            for port, port_data in scanned_ports.items():
                port_status = port_data.get('state')
                # port_data = result['scan'][host]['tcp'][port]
                if port_status == "open":
                    cpe = port_data.get('cpe', 'Unknown')  # Get the CPE information, if available
                    name = port_data.get('name', 'Unknown')  # Get the name of the host, if available
                    product = port_data.get('product', 'Unknown')  # Get the product information, if available
                    version = port_data.get('version', 'Unknown')  # Get the version information, if available
                    extrainfo = port_data.get('extrainfo', 'Unknown')  # Get any extra information, if available
                    print(f"Host {host} Port {port} is {port_status}")
                    print(f"Host {host}: Service running on port {port} is: cpe: {cpe}, name: {name}, product: {product}, version: {version}, extra info: {extrainfo}")
    except Exception as e:
        # We cannot scan some ports and this ensures the program doesn't crash when we try to scan them.
        print(f"Cannot scan port {port}. Error: {e}")
