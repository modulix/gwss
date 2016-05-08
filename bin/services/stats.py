#!/usr/bin/env python
import datetime
import json

import pygal
import base64
import random
from geoip import geolite2

def stats(service, gwss):
	"""
	This service broadcast some statistics depending on events
	event --.-> all_clients
		|-> client (on subscribe)
	This service also send some stats periodicaly (timer)
	timer ----> all_clients
	"""
	gwss.logger.debug("%s:%s" % (service.name, "Init/setup"))
	# Create service persistent var
	service.heartbeat = 5
	service.stat1 = []
	for idx in range(120):
		service.stat1.append(0)
	service.stat2 = {}
	service.timer_count = 0

def receive(gwss, service, action, client, data):
	"""
	"""
	gwss.logger.debug("%s:%s(%s)" % (service.name, id(client), data))
	service.send_all(data)

def event(gwss, service, client, event):
	"""
	This is event broadcasting worker:
	evt -> service:send_all()
	Tracked events are:
		add_client
		del_client
		timer
		client_start_work
		client_progress
		client_end_work
		client_event
	"""
	gwss.logger.debug("%s:event:%s" % (service.name, event))
	message = "error:stats:event:%s" % event
	if event == "timer":
		#There are some stats we send evry 5 sec
		if service.timer_count < (5 * (1/service.heartbeat)):
			service.timer_count += 1
			message = ""
		else:
			service.timer_count = 0
			message = '{"service": "stats", "action": "set", "data":{"id":"gwss_stat1","type": "base64", "value": "%s"}}' % stat1(gwss,service,client)
	if event == "svc_add_client":
		# On new subscription we send some the stats (multiple sends) but only to this client
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_lst_services","value": %s}}' % list_all_services(gwss)
		service.send_client(client, message)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_lst_clients","value": %s}}' % list_all_clients(gwss)
		service.send_client(client, message)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_clients_count","value": "%s"}}' % len(gwss.clients)
		service.send_client(client, message)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_stat1","type": "base64", "value": "%s"}}' % stat1(gwss,service,client)
		service.send_client(client, message)
		# At last, the message with new clients count is sended to all subscribed clients (including this new one)
		# (same as others events)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_stats_clients_count","value": "%s"}}' % len(service.clients)

	# On other events, we broadcast messages to all subscribed clients
	# Total of clients connected to this server
	if event == "add_client":
		geo = geolite2.lookup(service.track[id(client)]['ip'])
		if geo:
			try:
				service.stat2[geo.country.lower()] += 1
			except:
				service.stat2[geo.country.lower()] = 1
			service.track[id(client)]['country'] = geo.country.lower()
		else:
			service.track[id(client)]['country'] = "N/A"
	if event == "del_client":
		state = service.track[id(client)]['country']
		service.stat2[state] -= 1

	if event == "add_client" or event == "del_client":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_lst_clients","value": %s}}' % list_all_clients(gwss)
		service.send_all(message)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_stat2","type": "attr", "name": "src", "value": "%s"}}' % stat2(gwss,service,client)
		service.send_all(message)
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_clients_count","value": "%s"}}' % len(gwss.clients)
	# Total of clients connected to this service
	if event == "add_svc_client" or event == "del_svc_client":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_stats_clients_count","value": "%s"}}' % len(service.clients)
	# All running services list
	if event == "update_services":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_lst_services","value": %s}}' % list_all_services(gwss)

	if event == "client_start":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_client_start","value": "%s"}}' % datetime.datetime.now().strftime("%x %X")
	if event == "client_end":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_client_end","value": "%s"}}' % datetime.datetime.now().strftime("%x %X")
	if event == "client_event":
		message = '{"service": "stats", "action": "set", "data":{"id":"gwss_client_event","value": "%s"}}' % datetime.datetime.now().strftime("%x %X")

	if message:
		service.send_all(message)

def api(gwss, service, action, data):
	if action == "set":
		#data = {"service": "stats", "action": "set", "data": data}
		id = data["id"]
		value = data["value"]
		data = {"service": "stats", "action": "set", "data": {"id": id, "value": value}}
		#msg = json.dumps(data)
		#gwss.send_all(msg)
		service.events.append({"event": id, "client": service.clients, "data": {"id": id, "value": value}})
	if action == "get":
		id = data["id"]
		value = data["value"]
		data = {"service": "stats", "action": "set", "data": {"id": id, "value": value}}
		service.send_all(msg)

def list_all_services(gwss):
	# List of all running services on this server
	lst = []
	for svc in gwss.services:
		lst.append(svc.name)
	lst_services = json.dumps(lst)
	return(lst_services)

def list_all_clients(gwss):
	# List of all connected clients on this server
	lst = []
	for cli in gwss.clients:
		#lst.append("%s : %s" % (id(cli), gwss.track[id(cli)]))
		lst.append(id(cli))
	lst_clients = json.dumps(lst)
	return(lst_clients)

def stat1(gwss,service,client):
	gwss.logger.debug("%s:%s" % (service.name,"stat1"))
	bar_chart = pygal.StackedBar()
	if len(service.stat1) >= 120:
		del service.stat1[0]
	service.stat1.append(len(gwss.clients))
	bar_chart.add('Users', service.stat1)
	return(base64.b64encode(bar_chart.render()))

def stat2(gwss,service,client):
	gwss.logger.debug("%s:%s%s" % (service.name,"stat2",service.stat2))
	worldmap_chart = pygal.maps.world.World()
	worldmap_chart.title = 'Clients countries'
	worldmap_chart.add('gwss', service.stat2)
	worldmap_chart.render_to_file("/usr/share/nginx/html/static/img/stat2.svg")
	return("/static/img/stat2.svg")
	#return(base64.b64encode(worldmap_chart.render()))