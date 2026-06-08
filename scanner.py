import nmap
import json
from database_injection import save_error, conn


network = '192.168.0.183/32'
port_range = '1-65535'
nm = nmap.PortScanner(nmap_search_path=[r'C:\Program Files (x86)\Nmap\nmap.exe'])
router_ip = '192.168.0.0'


def active_ip_addresses(network):
    try:
        nm.scan(hosts=network, arguments='-sn')
        live_hosts = nm.all_hosts()
        print(f"Live hosts in the network {network}: {live_hosts}")
        return live_hosts
    except Exception as e:
        save_error(conn, 'active_ip_addresses', e, {'network': network})
        return []


def scanner(host_list, port_range=port_range, router_ip=router_ip):
    services = {} 
    for host in host_list:
        print(f"Scanning host: {host}")
        if host == router_ip:
            print(f"Skipping router IP: {host}")
            continue
        try:
            result = nm.scan(host, port_range, '-sV -sC -T4 -O')
            if host in result['scan'] and 'tcp' in result['scan'][host]:
                mac = result['scan'][host].get('addresses', {}).get('mac', 'Unknown')
                os_match = result['scan'][host].get('osmatch', [])
                if os_match:
                    os_name = os_match[0]['name']
                else:
                    os_name = 'Unknown'
                scanned_ports = result['scan'][host]['tcp']
                services.setdefault(host, {'mac': mac, 'os': os_name, 'ports': {}})
                services[host]['ports'][0] = {
                    'cpe': '',
                    'name': 'os',
                    'product': os_name,
                    'version': '',
                    'extrainfo': ''
                }
                for port, port_data in scanned_ports.items():
                    port_status = port_data.get('state')
                    if port_status == "open":
                        cpe = port_data.get('cpe', 'Unknown')
                        name = port_data.get('name', 'Unknown')
                        product = port_data.get('product', 'Unknown')
                        version = port_data.get('version', 'Unknown')
                        extrainfo = port_data.get('extrainfo', 'Unknown')
                        services[host]['ports'][port] = {
                            'cpe': cpe,
                            'name': name,
                            'product': product,
                            'version': version,
                            'extrainfo': extrainfo
                        }
        except Exception as e:
            save_error(conn, 'scanner', e, {'host': host})
    return services



if __name__ == "__main__":
    services_to_lookup = scanner(active_ip_addresses(network), )
    print(json.dumps(services_to_lookup, indent=4))