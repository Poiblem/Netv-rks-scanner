import psycopg2

conn = psycopg2.connect(
    host = "127.0.0.1",
    database = "server_cve",
    user = "server_admin",
    password = "123"
)


def parse_cve(cves):
    final_data = []
    for cve in cves['vulnerabilities']:
        cve_true = cve['cve']
        cve_id = cve_true['id']
        for desc in cve_true['descriptions']:
            if desc['lang'] == 'en':
                cve_description = desc['value']
                break
        if  'cvssMetricV31' in cve_true['metrics']:
            cve_cvss = cve_true['metrics']['cvssMetricV31'][0]['cvssData']['baseScore']
            cve_severity = cve_true['metrics']['cvssMetricV31'][0]['cvssData']['baseSeverity']
        else: 
            cve_cvss = cve_true['metrics']['cvssMetricV2'][0]['cvssData']['baseScore']
            cve_severity = cve_true['metrics']['cvssMetricV2'][0]['baseSeverity']
        cve_published = cve_true['published']
        cve_last_modified = cve_true['lastModified']

        final_data.append({
            'cve_id': cve_id,
            'description': cve_description,
            'cvss_score': cve_cvss,
            'severity': cve_severity,
            'published_date': cve_published,
            'last_modified_date': cve_last_modified
        })

    return final_data

def save_device(conn, ip_address, mac_address, hostname):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO devices (name, ip_address, mac_address)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (hostname, ip_address, mac_address)
    )
    device_id = cursor.fetchone()[0]
    conn.commit()
    return device_id

def save_service(conn, device_id, name, version, port, protocol):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO services (device_id, name, version, port, protocol)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (device_id, name, version, port, protocol)
    )
    service_id = cursor.fetchone()[0]
    conn.commit()
    return service_id
    
def save_vulnerability(conn, cve_parsed):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vulnerabilities (CVE_id, description, severity, cvss_score, published_date, last_modified_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (cve_parsed['cve_id'],cve_parsed['description'],cve_parsed['severity'],cve_parsed['cvss_score'],cve_parsed['published_date'],cve_parsed['last_modified_date'])
    )
    cve_id = cursor.fetchone()[0]
    conn.commit()
    return cve_id


def save_incident(conn, vulnerability_id, device_id, service_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO incidents (vulnerability_id, device_id, service_id, incident_date, status)
        VALUES (%s, %s, %s, NOW(), %s)
        RETURNING id
        """,
        (vulnerability_id, device_id, service_id, 'open')
    )
    incident_id = cursor.fetchone()[0]
    conn.commit()
    return incident_id

def save_all(conn, scan_results, vuln_results):
    for ip, data in scan_results.items():
        device_id = save_device(conn, ip, data['mac'], ip)

        for port, service in data['ports'].items():
            service_id = save_service(
                conn, device_id,
                service['product'],
                service['version'],
                port,
                'tcp'
            )

            if ip in vuln_results and port in vuln_results[ip]:
                cves = parse_cve(vuln_results[ip][port])
                for cve in cves:
                    vuln_id = save_vulnerability(conn, cve)
                    save_incident(conn, vuln_id, device_id, service_id)