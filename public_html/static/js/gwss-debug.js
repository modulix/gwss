/*
** gwss is WebSocket Server
** 
** (c) Copyleft - 2016 : https://github.com/modulix/gwss
**
*/

// Default values, could be overwritten in html file
var gwss_host = 'gwss.modulix.net';
var gwss_port = 80;
var gwss_retry = 10;
var gwss_debug = false;
var gwss_id = 0;

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
		if (ev.data.substring(0,5) == "error")
			{
			if (gwss_debug) {
				$debug.prepend('<li class="label-warning">' + ev.data);
				}
			if (typeof gwss_error === "function") { 
				gwss_error();
				}
			}
		else {
			if (ev.data.substring(0,4) == "ping")
				{
				if (gwss_debug) {
					$debug.prepend('<li class="label-info">' + ev.data);
					}
				if (typeof gwss_ping === "function") { 
					gwss_ping();
					}
				}
			else {
				var json = JSON.parse(ev.data);
				// Virtual service used to give 'internal' messages
				if (json.service == "gwss") {
					if (json.action == "subscribe") {
						// Client unique identifier
						gwss_id = json.data.value;
						if (gwss_debug)
							$debug.prepend('<li class="label-info">ID : ' + json.data.value + " (" + json.data.id + ")");
						}
					}
				else {
					if (json.action == "subscribe") {
						if (gwss_debug)
							$debug.prepend('<li class="label-info">Subscription : ' + json.service + "=" + json.data.value);
						}
					else {
						if (gwss_debug)
							$debug.prepend('<li>' + json.service + ' : ' + ev.data);
						}
					}
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

