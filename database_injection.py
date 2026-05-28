import psycopg2

conn = psycopg2.connect(
    host = "127.0.0.1",
    database = "server_cve",
    user = "server_admin",
    password = "123"
)


def save_error(conn, function_name, error, context=None):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO error_log (function_name, error_message, error_type, context)
            VALUES (%s, %s, %s, %s)
            """,
            (function_name, str(error), type(error).__name__, str(context))
        )
        conn.commit()
    except Exception as e:
        print(f"Kunne ikke gemme fejl i databasen: {e}")

def parse_cve(cves):
    final_data = []
    for cve in cves['vulnerabilities']:
        try:
            cve_true = cve['cve']
            cve_id = cve_true['id']
            for desc in cve_true['descriptions']:
                if desc['lang'] == 'en':
                    cve_description = desc['value']
                    break
            if 'cvssMetricV31' in cve_true['metrics']:
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
        except Exception as e:
            save_error(conn, 'parse_cve', e, cve)

    return final_data


def save_device(conn, ip_address, mac_address, hostname, os_name=None):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO devices (name, ip_address, mac_address, os)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ip_address) DO UPDATE SET
                mac_address = EXCLUDED.mac_address,
                os = EXCLUDED.os,
                last_seen = NOW()
            RETURNING id
            """,
            (hostname, ip_address, mac_address, os_name)
        )
        device_id = cursor.fetchone()[0]
        conn.commit()
        return device_id
    except Exception as e:
        conn.rollback()
        save_error(conn, 'save_device', e, {'ip': ip_address, 'mac': mac_address})
        return None


def save_service(conn, device_id, name, version, port, protocol):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO services (device_id, name, version, port, protocol)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (device_id, port, protocol) DO UPDATE SET
                name = EXCLUDED.name,
                version = EXCLUDED.version
            RETURNING id
            """,
            (device_id, name, version, port, protocol)
        )
        service_id = cursor.fetchone()[0]
        conn.commit()
        return service_id
    except Exception as e:
        conn.rollback()
        save_error(conn, 'save_service', e, {'device_id': device_id, 'port': port})
        return None


def save_vulnerability(conn, cve_parsed):
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vulnerabilities (CVE_id, description, severity, cvss_score, published_date, last_modified_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (CVE_id) DO UPDATE SET
                description = EXCLUDED.description,
                severity = EXCLUDED.severity,
                cvss_score = EXCLUDED.cvss_score,
                last_modified_date = EXCLUDED.last_modified_date
            RETURNING id
            """,
            (cve_parsed['cve_id'], cve_parsed['description'], cve_parsed['severity'],
             cve_parsed['cvss_score'], cve_parsed['published_date'], cve_parsed['last_modified_date'])
        )
        cve_id = cursor.fetchone()[0]
        conn.commit()
        return cve_id
    except Exception as e:
        conn.rollback()
        save_error(conn, 'save_vulnerability', e, cve_parsed)
        return None


def save_incident(conn, vulnerability_id, device_id, service_id):
    try:
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
    except Exception as e:
        conn.rollback()
        save_error(conn, 'save_incident', e, {'vuln_id': vulnerability_id, 'device_id': device_id, 'service_id': service_id})
        return None

def save_all(conn, scan_results, vuln_results):
    try:
        for ip, data in scan_results.items():
            device_id = save_device(conn, ip, data['mac'], ip, data.get('os', 'Unknown'))
            if device_id is None:
                continue

            for port, service in data['ports'].items():
                protocol = 'os' if port == 0 else 'tcp'
                service_id = save_service(
                    conn, device_id,
                    service['product'],
                    service['version'],
                    port,
                    protocol
                )
                if service_id is None:
                    continue

                if ip in vuln_results and port in vuln_results[ip]:
                    raw = vuln_results[ip][port]
                    if raw is not None:
                        cves = parse_cve(raw)
                        for cve in cves:
                            vuln_id = save_vulnerability(conn, cve)
                            if vuln_id is None:
                                continue
                            save_incident(conn, vuln_id, device_id, service_id)
    except Exception as e:
        save_error(conn, 'save_all', e, {'ip': ip, 'port': str(port)})