# Base image
FROM ubuntu:20.04

# Environment settings
ENV DEBIAN_FRONTEND=noninteractive

# Install key packages
RUN apt-get update && apt-get install -y \
    apache2 \
    apache2-dev \
    chromium-browser \
    git \
    libapache2-mod-wsgi-py3 \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-pip \
    redis-server \
    redis-tools \
    unzip \
    xvfb \
    && apt-get clean

# Install Python dependencies
COPY coptic/requirements.txt /var/www/cts/coptic/requirements.txt
RUN pip3 install -r /var/www/cts/coptic/requirements.txt
RUN pip3 install debugpy

# Copy application files
WORKDIR /var/www/cts/coptic
COPY ./coptic /var/www/cts/coptic
RUN mkdir -p /var/www/cts/coptic/scripts
COPY ./scripts/ /var/www/cts/coptic/scripts

# Apache configuration
COPY ./ansible/roles/scriptorium/files/scriptorium.conf /etc/apache2/sites-available/000-default.conf

EXPOSE 80
# Environment variables for Django
ENV DJANGO_SETTINGS_MODULE="coptic.settings.docker"
# Command to start Apache
CMD ["python3", "-m", "debugpy", "--listen", "0.0.0.0:5678", "manage.py", "runserver", "0.0.0.0:8000"]