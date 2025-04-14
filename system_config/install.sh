# This will try to be a reproducible installation script for the system configuration
# Based on CentOS 8
sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-Linux-*
sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.epel.cloud|g' /etc/yum.repos.d/CentOS-Linux-*
dns update
dnf install python3.9 -y
python3 --version
# Python 3.9.6
dnf install python3-pip -y
pip3 install --upgrade pip
dnf install httpd -y
dnf install python39-mod_wsgi.x86_64 -y
dnf install git -y
git clone -b cleanup https://github.com/OriPekelman/cts.git /var/www/html/cts
cd /var/www/html/cts/coptic
pip3 install -r requirements.txt
touch coptic/settings/secrets.py # for the time being
gunicorn --bind unix:/run/gunicorn.sock coptic.wsgi:application
# ctrl-c to stop the server
echo """
[Unit]
Description=gunicorn daemon for Django Project
After=network.target

[Service]
User=apache
Group=apache
WorkingDirectory=/var/www/html/cts/coptic
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind unix:/run/gunicorn.sock coptic.wsgi:application

[Install]
WantedBy=multi-user.target""">/etc/systemd/system/gunicorn.service

systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn

echo """
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot /var/www/html/cts/coptic

    <Directory /var/www/html/cts/coptic>
        Require all granted
    </Directory>

    # Proxy configuration for Gunicorn
    ProxyPass / unix:/run/gunicorn.sock|uwsgi://localhost/

    ErrorLog /var/log/httpd/coptic_error.log
    CustomLog /var/log/httpd/coptic_access.log combined
</VirtualHost>""" > /etc/httpd/conf.d/coptic.conf 