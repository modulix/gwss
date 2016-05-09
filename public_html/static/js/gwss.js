/*
** gwss is WebSocket Server
** 
** (c) Copyleft - 2016 : https://github.com/modulix/gwss
**
*/

// Default values, could be overwritten in html file
var gwss_host = 'localhost';
var gwss_port = 80;
var gwss_retry = 10;
var gwss_id = 0;

function openSocket()
	{
	var ws = new WebSocket('ws://' + gwss_host + ':' + gwss_port + '/gwss');

	ws.onopen = function(){
		if (typeof(retry) != 'undefined') {
			clearInterval(retry);
			}
		// Calling web page script to subscribe to services
		if (typeof gwss_open === "function") { 
			gwss_open();
			}
		};
	ws.onmessage = function(ev){
		if (ev.data.substring(0,5) == "error")
			{
			if (typeof gwss_error === "function") { 
				gwss_error();
				}
			}
		else {
			if (ev.data.substring(0,4) == "ping")
				{
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
						}
					}
				gwss_receive(json);
				}
			}
		};
	ws.onclose = function(ev){
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
		if (typeof gwss_close === "function") {
			gwss_error(ev.data);
			}
		};
	return(ws);
	}

function gwss_subscribe(ws, service, data)
	{
	ws.send('{"service":"' + service + '", "action":"subscribe", "data":' + data + '}');
	}
function gwss_unsubscribe(ws, service, data)
	{
	ws.send('{"service":"' + service + '", "action":"unsubscribe", "data":' + data + '}');
	}

