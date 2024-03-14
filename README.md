# pfsense
Install openjdk pfsense 2.7

Enable  FreeBSD Reposotory

# ee /usr/local/etc/pkg/repos/pfSense.conf

Change 
FreeBSD: { enabled: yes }

Next edit file /usr/local/etc/pkg/repos/FreeBSD.con e change:

 FreeBSD: { enabled: yes }

# pgk update

Search foi package 

# pkg search ^openjdk

Afeter install package disable repo and file modified




