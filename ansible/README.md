# Overview

Ansible scripts for deploying cts project to a server.

# Description

These Ansible scripts should enable the re-creation of the URN resolver site for the
coptic scriptorium in a variety of environments. Initially, this targets Ubuntu
Long-Term-Support (LTS) version 14.4.

For debugging / testing purposes, these scripts can also be used to deploy to
a virtual machine running locally on a user's machine, inside VirtualBox (or VMWare,
although this documentation only contemplates VirtualBox).

As per Ansible recommended practice, the project uses roles for enabling
software on the server.

# Installing Ansible

First, install Ansible. See http://docs.ansible.com/intro_installation.html . If you're
using MacPorts on OS X, this will do the trick:

> sudo port install ansible

You'll also need to install "sshpass" if you connect to a machine using a password. Again,
for the Mac:

> sudo port install sshpass

# Setting up the Ubuntu Virtual Machine For Testing

If you're using VirtualBox, install a new Ubuntu Server (14.4 LTS). To match the
configuration of the production box, create the "ubuntu" user, and set the password to
something you won't forget.

For debugging purposes (instead of just testing, there are a number of additional
steps you'll want to take:
- install the VirtualBox Guest Additions (so you can share a folder)
- configure a shared folder - this should be the location where you've cloned the "cts.git"
  repository.
- mount the shared folder at /var/www/cts

For installing the VirtualBox Guest Additions, this should help:
http://askubuntu.com/questions/22743/how-do-i-install-guest-additions-in-a-virtualbox-vm,
specifically this answer: http://askubuntu.com/a/526203

# Invoking this Ansible playbook

Once you've got Ansible installed, invoking this playbook looks like this:

> ansible-playbook -c ssh -k -K --vault-password-file=~/.scriptorium-vault-password -i testing scriptorium.yml

Breaking that apart:
"-c ssh" - use native SSH support (just works better on the Mac)
"-k -K" - ask for a password to connect to the machine (not needed if using key files)
"-i testing" - use the testing profile for configuring the test machine
"scriptorium.yml" - the base script to create the scriptorium - a shell for invoking roles.

