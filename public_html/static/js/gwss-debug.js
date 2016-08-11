/*
** gwss is WebSocket Server
** 
** (c) Copyleft - 2016 : https://github.com/modulix/gwss
**
*/

// Default values, could be overwritten in html file
var gwss_host = 'localhost';
var gwss_port = 80;
var gwss_retry = 5;
var gwss_debug = false;
var gwss_groups = [];

function openSocket()
	{
	var $debug = $('#gwss_debug');

	if (gwss_debug) {
		$debug.prepend('<li>Trying to open webSocket at ws://' + gwss_host + ':' + gwss_port + '/gwss');
		}
	var ws = new WebSocket('ws://' + gwss_host + ':' + gwss_port + '/gwss');

	ws.onopen = function(){
		if (typeof(retry) != 'undefined') {
			clearInterval(retry);
			}
		if (gwss_debug) {
			$debug.prepend('<li class="label-success"> Websocket:open');
			}
		// Calling web page script to subscribe to services
		gwss_open();
		};
	ws.onmessage = function(ev){
		var json = JSON.parse(ev.data);
		if (json.js_action == "error") {
			if (gwss_debug) {
				$debug.prepend('<li class="label-info">' + ev.data);
				}
			if (typeof gwss_error === "function") { 
				gwss_error();
				}
			}
		else {
			if (json.js_action == "ping") {
				if (gwss_debug) {
					$debug.prepend('<li class="label-info">' + ev.data);
					}
				if (typeof gwss_ping === "function") { 
					gwss_ping();
					}
				}
			else {
				if (gwss_debug)
					$debug.prepend('<li>' + json.service + ' : ' + ev.data);
				gwss_receive(json);
				}
			}
		};
	ws.onclose = function(ev){
		if (gwss_debug)
			$debug.prepend('<li class="label-warning">Websocket:closed');
		if (typeof gwss_close === "function") { 
			gwss_close();
			}
		if (typeof(retry) != 'undefined')
			{
			clearInterval(retry);
			}
		retry = setInterval("gwss = openSocket();", (gwss_retry * 1000));
		};

	ws.onerror = function(ev){
		if (gwss_debug)
			$debug.prepend('<li class="label-important">Websocket:' + ev.data);
		if (typeof gwss_close === "function") {
			gwss_error(ev.data);
			}
		};
	return(ws);
	}

