import nmap
import json
import ipaddress
import re


network = '192.168.0.0/24'
port_range = '1-2000'
nm = nmap.PortScanner(nmap_search_path=[r'C:\Program Files (x86)\Nmap\nmap.exe'])  #Specify path to nmap.exe
router_ip = '192.168.0.1'


def active_ip_addresses(network):
    nm.scan(hosts=network, arguments='-sn')  # -sn is for ping scan (no port scan)
    live_hosts = nm.all_hosts()
    print(f"Live hosts in the network {network}: {live_hosts}")
    return live_hosts

host_list = active_ip_addresses(network)

def scanner(host_list, port_range=port_range, router_ip=router_ip):
    services = {} #stores services
    for host in host_list:
        print(f"Scanning host: {host}")
        if host == router_ip:
            print(f"Skipping router IP: {host}")
            continue
        try:
            result = nm.scan(host, port_range, '-sV -sC -T4')     #the scan function decides what gets scanned
            if host in result['scan'] and 'tcp' in result['scan'][host]: 
                mac = result['scan'][host].get('addresses', {}).get('mac', 'Unknown')
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
                        services.setdefault(host, {'mac': mac, 'ports': {}})
                        services[host]['ports'][port] = {
                            'cpe': cpe,
                            'name': name,
                            'product': product,
                            'version': version,
                            'extrainfo': extrainfo
                        }
        except Exception as e:
            print(f"Cannot scan port {port}. Error: {e}")
    return services

if __name__ == "__main__":
    services_to_lookup = scanner()
    print(json.dumps(services_to_lookup, indent=4))