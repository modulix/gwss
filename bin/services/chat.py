#!/usr/bin/env python
from datetime import datetime
import time
import json
import gevent

def chat(service, gwss):
	"""
	This service broadcast all received messages to all subscribed clients
	event -> worker -> send_all (same message)
	It is also possible to use groups :
	event -> worker -> send_group (same message)
	"""
	gwss.logger.debug("%s:%s" % (service.name, "Init/setup"))
	# Persistent variables of the service:
	service.last = datetime.now()

	# Enable "timer" event to send time evry 5 minutes
	service.heartbeat = 299
	
def action(gwss, service, action, client, data):
	"""
	This function is executed each time there is a new "event"
	This function is executed each time somebody send a message
	"""
	gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client),data))
	message = "%s:%s:error:unhandled action" % (service.name,action)
	if action == "subscribe":
		service.add_client(client)
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"],id(client))
	if action == "unsubscribe":
		service.del_client(client)
	if action == "add_group":
		new_group = data["value"]
		exist = False
		for grp in service.groups:
			if grp["name"] == new_group:
				message = '{"service": "chat", "action": "set", "data":{"id":"messages","attr": "class", "class": "label-default", "value": "You need to choose another room name, %s already exists..."}}' % new_group
				service.send_client(client, message)
				exist = True
				message = ""
		if not exist:
			service.add_group(new_group, client)
			message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
			service.send_all(message)
			message = '{"service": "chat", "action": "set", "data": {"id":"messages", "attr": "class", "class": "label-success", "value":"%s created new room : %s"}}' % (id(client), new_group)
	if action == "del_group":
		service.del_group(new_group, client)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
	if action == "set":
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s"}}' % (data["id"], data["value"])
	if action == "set" and data["id"] == "messages":
		try:
			username = service.track[id(client)]['username']
		except:
			username = id(client)
		message = '{"service": "chat", "action": "set", "data": {"id":"%s", "value":"%s:%s"}}' % (data["id"],username, data["value"])
	if action == "timer":
		sysdate = datetime.now()
		# Waiting for minute just before real 5 minutes
		while (sysdate.minute + 1)%5:
			gevent.sleep(60)
			sysdate = datetime.now()
		# Waiting for seconds to reach 0 (exact 5 min)
		while sysdate.second != 0:
			gevent.sleep(0.5)
			sysdate = datetime.now()
		message = '{"service": "chat", "action": "set", "data":{"id":"messages", "attr": "class", "class": "label-alert", "value": "%s"}}' % sysdate.strftime("%x %H:%M")
	if action == "user":
		service.track[id(client)]['username'] = data["value"]
		message = '{"service": "chat", "action": "user", "data":{"id":"gwss_chat_username","value": %s}}' % data["value"]
		service.send_client(client, message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_clients","value": %s}}' % lst_clients(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data": {"id":"messages", "attr": "class", "class": "label-info", "value":"%s is known as %s"}}' % (id(client), data["value"])
	if action == "add_client":
		message = ""
	if action == "del_client":
		message = ""
	if action == "add_svc_client":
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_clients_count","value": "%s"}}' % len(service.clients)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_clients","value": %s}}' % lst_clients(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"messages", "attr": "class", "class": "label-success", "value": "Welcome to new user %s !"}}' % id(client)
	if action == "del_svc_client":
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_groups","value": %s}}' % lst_groups(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_lst_clients","value": %s}}' % lst_clients(service)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"gwss_chat_clients_count","value": "%s"}}' % len(service.clients)
		service.send_all(message)
		message = '{"service": "chat", "action": "set", "data":{"id":"messages", "attr": "class", "class": "label-info", "value": "User %s is leaving... bye, bye !"}}' % id(client)

	if message:
		gwss.logger.debug("%s:%s:%s:%s" % (service.name, action, id(client),message))
		service.send_all(message)

def lst_clients(service):
	lst = []
	for cli in service.clients:
		try:
			username = "%s:%s" % (str(id(cli)), service.track[id(cli)]['username'])
		except:
			username = str(id(cli))
		lst.append(username)
	return(json.dumps(lst))

def lst_groups(service):
	lst = []
	for grp in service.groups:
		lst.append(grp["name"])
	return(json.dumps(lst))

def api(gwss, service, action, data):
	"""
	REST api to manage this service
	"""
	if action == "set":
		data = {"service": "chat", "action": "set", "data": data}
		msg = json.dumps(data)
		service.send_all(msg)
	if action == "get":
		id = data["id"]
		value = data["value"]
		data = {"service": "chat", "action": "set", "data": {"id": id, "value": value}}
		service.send_all(msg)
