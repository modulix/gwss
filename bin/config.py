#!/usr/bin/env python
# This file contain gwss tunables variables

pidfile = "/var/run/gwss/gwss.pid"
sockname = "/var/run/gwss/gwss.sock"
logfile = "/var/log/nginx/gwss.log"
server = "0.0.0.0"
port = 8888
api_url = "/api"
max_clients = 1000
#html_dir = "~/public_html"
#html_dir = "/usr/share/nginx/html"
html_dir = "/var/www/public_html"
services_dir = "/var/www/bin/services"