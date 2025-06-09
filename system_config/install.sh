# This will try to be a reproducible installation script for the system configuration
# Based on CentOS 8 allow using vault (unmaintained packages)
sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-Linux-*
sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.epel.cloud|g' /etc/yum.repos.d/CentOS-Linux-*
dnf update
dnf install python3.10 -y
python3 --version
# Python 3.10.x
dnf install python3-pip -y
pip3 install --upgrade pip
dnf install httpd -y
dnf install python310-mod_wsgi.x86_64 -y
dnf install git -y
git clone -b ft_search https://github.com/OriPekelman/cts.git /var/www/html/cts2
cd /var/www/html/cts2/coptic
uv venv
uv python 3.10
uv sync
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
WorkingDirectory=/var/www/html/cts2/coptic
ExecStart=uv run /usr/local/bin/gunicorn --workers 3 --bind unix:/run/cts2_gunicorn.sock coptic.wsgi:application

[Install]
WantedBy=multi-user.target""">/etc/systemd/system/gunicorn.service

systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn

echo """
<VirtualHost *:80>
    ServerName localhost
    DocumentRoot /var/www/html/cts2/coptic

    <Directory /var/www/html/cts2/coptic>
        Require all granted
    </Directory>

    # Proxy configuration for Gunicorn
    ProxyPass / unix:/run/cts2_gunicorn.sock|uwsgi://localhost/

    ErrorLog /var/log/httpd/cts2_coptic_error.log
    CustomLog /var/log/httpd/cts2_coptic_access.log combined
</VirtualHost>""" > /etc/httpd/conf.d/cts2_coptic.conf 
