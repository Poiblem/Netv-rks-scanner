from scanner import scanner, active_ip_addresses
from vulnerability import get_vulnerabilities
import json

router_ip = '192.168.0.1'
network = '192.168.0.118/32' #'192.168.0.0/24' for hele netværket

result = scanner(host_list=active_ip_addresses(network), port_range='1-65535', router_ip=router_ip)



def main_loop(results):
    vuln_list = {}
    for ip, data in results.items():
        vuln_list.setdefault(ip, {})
        for port, service in data['ports'].items():
            cve = get_vulnerabilities(service)
            vuln_list[ip][port] = cve
    return vuln_list

test = main_loop(result)

print(json.dumps(test, indent=4))