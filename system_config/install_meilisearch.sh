#!/bin/bash

echo "Downloading and Installing MeiliSearch"

# Install MeiliSearch latest version from the script
sudo curl -L https://install.meilisearch.com | sh

# Move MeiliSearch to the user bin
sudo mv ./meilisearch /usr/bin/

# Create data and configuration directories
sudo mkdir -p /var/lib/meilisearch/data
sudo mkdir -p /var/lib/meilisearch/dumps
sudo mkdir -p /var/lib/meilisearch/snapshots
sudo mkdir -p /etc/meilisearch

# Create the configuration file
sudo tee /etc/meilisearch/config.toml > /dev/null << EOF
# MeiliSearch Configuration File

# Database path
db_path = "/var/lib/meilisearch/data"

# Environment (development or production)
env = "production"

# HTTP server address and port
http_addr = "0.0.0.0:7700"

# Master key for API security
master_key = "e5ef239d483405d9bb0dfbe3d900f47fadb6e6a3"

# Directories for dumps and snapshots
dump_dir = "/var/lib/meilisearch/dumps"
snapshot_dir = "/var/lib/meilisearch/snapshots"

# Log level: OFF, ERROR, WARN, INFO, DEBUG, TRACE
log_level = "INFO"

# Maximum indexing memory (adjust based on your server resources)
max_indexing_memory = "1 GiB"

# Maximum indexing threads
max_indexing_threads = 4

# HTTP payload size limit
http_payload_size_limit = "100 MB"

# Disable analytics (optional)
# no_analytics = true

# Schedule snapshots (set to false to disable or provide interval in seconds)
schedule_snapshot = 86400  # Daily snapshots
EOF

# Create the service file
sudo tee /etc/systemd/system/meilisearch.service > /dev/null << EOF
[Unit]
Description=MeiliSearch
After=systemd-user-sessions.service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/meilisearch --config-file-path /etc/meilisearch/config.toml
Restart=on-failure
RestartSec=5
LimitNOFILE=65535

# Security settings
CapabilityBoundingSet=
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectSystem=full
ReadWritePaths=/var/lib/meilisearch

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions
sudo chown -R nobody:nobody /var/lib/meilisearch

# Enable the meilisearch service
sudo systemctl enable meilisearch

# Start the meilisearch service
sudo systemctl start meilisearch

# Reload the systemd configuration
sudo systemctl daemon-reload

echo "MeiliSearch installation complete!"
echo "The service is running on http://0.0.0.0:7700"
echo "Configuration file is located at /etc/meilisearch/config.toml"
