#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests, re

print("Content-type:text/html\r\n\r\n")

def get_menu():
	head = "http://copticscriptorium.org/header.html"
	try:
		header = requests.get(head).text
	except:
		header = ""
	foot = "http://copticscriptorium.org/footer.html"
	try:
		footer = requests.get(foot).text
	except:
		footer = ""
	header = header.replace('href="/','href="http://copticscriptorium.org/')
	footer = re.sub(r'<p id="lastupdate">.*?</p>.*<script>.*lastupdate.*?</script>','',footer,flags=re.DOTALL)

	return header

print(get_menu.encode("utf8"))