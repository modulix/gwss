#!/usr/bin/env python
from classes.DaemonService import DaemonService

class EchoService(DaemonService):
	"""
	This service broadcast all received messages to all connected clients
	event -> worker -> send_all (same message)
	"""
	def action_echo(self, client, data):
		self.send_client(client, "display", data)

def echo(logger):
	return EchoService("echo", logger)
