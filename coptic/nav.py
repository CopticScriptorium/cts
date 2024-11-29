#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Script to retrieve current nav and footer from copticscriptorium.org
"""


import requests, re, io, os, sys

script_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep


def get_menu():
    head = "https://copticscriptorium.org/header.html"
    try:
        header = requests.get(head).text
    except Exception as e:
        sys.stderr.write(str(e))
        header = ""
    foot = "https://copticscriptorium.org/footer.html"
    try:
        footer = requests.get(foot).text
    except Exception as e:
        sys.stderr.write(str(e))
        footer = ""
    header = header.replace('href="/', 'href="https://copticscriptorium.org/')
    header = header.replace('src="./', 'src="https://copticscriptorium.org/')
    header = header.replace('src="/', 'src="https://copticscriptorium.org/')
    footer = footer.replace('src="./', 'src="https://copticscriptorium.org/')
    footer = footer.replace('src="/', 'src="https://copticscriptorium.org/')
    footer = re.sub(
        r'<p id="lastupdate">.*?</p>.*<script>.*lastupdate.*?</script>',
        "",
        footer,
        flags=re.DOTALL,
    )

    return header, footer


nav, footer = get_menu()

with io.open(script_dir + "templates" + os.sep + "nav.html", "w", encoding="utf8") as f:
    if len(nav) > 0:
        f.write(unicode(nav))

with io.open(
    script_dir + "templates" + os.sep + "footer.html", "w", encoding="utf8"
) as f:
    if len(footer) > 0:
        f.write(unicode(footer))
