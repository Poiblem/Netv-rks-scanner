

--- Database Layout for Sårbarhedsdatabasen=
---=========================================    
--- on Desktop to run: & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U server_admin -d server_cve -h 127.0.0.1 -f database_layout.sql
-- & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U server_admin -d server_cve -h 127.0.0.1 -c 
-- Clear database: & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U server_admin -d server_cve -h 127.0.0.1 -c "DROP TABLE IF EXISTS incidents, vulnerabilities, services, devices, error_log CASCADE;"
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255),
    os VARCHAR(255),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    mac_address VARCHAR(17),
    last_seen timestamp DEFAULT NOW(),
    created_at timestamp DEFAULT NOW()
);  

CREATE TABLE IF NOT EXISTS   services (
    id SERIAL PRIMARY KEY,
    device_id INT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    port INT NOT NULL,
    protocol VARCHAR(10) NOT NULL,
    created_at timestamp DEFAULT NOW(),
    UNIQUE (device_id, port, protocol)
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    CVE_id VARCHAR(20) UNIQUE,
    description TEXT,
    severity VARCHAR(50),
    cvss_score DECIMAL(3,1),
    published_date timestamp,
    last_modified_date timestamp
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    vulnerability_id INT NOT NULL REFERENCES vulnerabilities(id),
    device_id INT NOT NULL REFERENCES devices(id),
    service_id INT NOT NULL REFERENCES services(id),
    incident_date timestamp,
    status VARCHAR(50),
    resolution TEXT
);

CREATE TABLE IF NOT EXISTS error_log (
    id SERIAL PRIMARY KEY,
    function_name VARCHAR(255) NOT NULL,
    error_message TEXT,
    error_type VARCHAR(255),
    context TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

