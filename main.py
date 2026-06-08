from scanner import scanner, active_ip_addresses
from vulnerability import get_vulnerabilities
from database_injection import save_all, conn
import json

router_ip = '192.168.0.1'
network = '192.168.0.0/24'
result = scanner(host_list=active_ip_addresses(network), port_range='1-20000', router_ip=router_ip)


def main_loop(results):
    vuln_list = {}
    for ip, data in results.items():
        vuln_list.setdefault(ip, {})
        for port, service in data['ports'].items():
            cve = get_vulnerabilities(service)
            vuln_list[ip][port] = cve
    return vuln_list
vuln_results = main_loop(result)

save_all(conn, result, vuln_results)
json.dump(vuln_results, open('vuln.json', 'w'), indent=4)
print("Færdig! Data gemt i databasen.")