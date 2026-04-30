

--- Database Layout for Sårbarhedsdatabasen=
---=========================================    

CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    mac_address VARCHAR(17) NOT NULL UNIQUE,
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
    created_at timestamp DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
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