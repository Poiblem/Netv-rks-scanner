from flask import Flask, render_template, redirect, url_for
import threading
from scanner import scanner, active_ip_addresses
from vulnerability import get_vulnerabilities
from database_injection import save_all, conn, parse_cve
import psycopg2

app = Flask(__name__)

# Status variabel så hjemmesiden ved om scanneren kører
scan_status = {'running': False, 'message': 'Ingen scanning kørt endnu'}

router_ip = '192.168.0.1'
network = '192.168.0.0/24'


def run_scan():
    scan_status['running'] = True
    scan_status['message'] = 'Scanner kører...'
    try:
        hosts = active_ip_addresses(network)
        result = scanner(host_list=hosts, port_range='1-65535', router_ip=router_ip)
        
        vuln_list = {}
        for ip, data in result.items():
            vuln_list.setdefault(ip, {})
            for port, service in data['ports'].items():
                cve = get_vulnerabilities(service)
                vuln_list[ip][port] = cve
        
        save_all(conn, result, vuln_list)
        scan_status['message'] = 'Scanning færdig!'
    except Exception as e:
        scan_status['message'] = f'Fejl: {e}'
    scan_status['running'] = False


@app.route('/')
def index():
    return render_template('index.html', status=scan_status)


@app.route('/scan')
def start_scan():
    if not scan_status['running']:
        thread = threading.Thread(target=run_scan)
        thread.start()
    return redirect(url_for('index'))


@app.route('/devices')
def devices():
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return render_template('table.html', title='Devices', columns=columns, rows=rows)


@app.route('/services')
def services():
    cur = conn.cursor()
    cur.execute("SELECT * FROM services")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return render_template('table.html', title='Services', columns=columns, rows=rows)


@app.route('/vulnerabilities')
def vulnerabilities():
    cur = conn.cursor()
    cur.execute("SELECT * FROM vulnerabilities")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return render_template('table.html', title='Vulnerabilities', columns=columns, rows=rows)


@app.route('/incidents')
def incidents():
    cur = conn.cursor()
    cur.execute("SELECT * FROM incidents")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return render_template('table.html', title='Incidents', columns=columns, rows=rows)


@app.route('/errors')
def errors():
    cur = conn.cursor()
    cur.execute("SELECT * FROM error_log")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    return render_template('table.html', title='Error Log', columns=columns, rows=rows)


if __name__ == '__main__':
    app.run(debug=True)