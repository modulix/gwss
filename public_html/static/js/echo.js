
function openSocket(gwss_host, gwss_port)
	{
	var ws = new WebSocket('ws://' + gwss_host + ':' + gwss_port + '/gwss');

	ws.onopen = function(){
		if (typeof(retry) != 'undefined') {
			clearInterval(retry);
			}
		};
	ws.onmessage = function(ev){
		var msg = JSON.parse(ev.data)
		console.log(msg.service)
		service = window[msg.service]
		if (!service) return;
		var fn = service["action_"+msg.action];
		if(typeof fn === 'function') {
			fn(msg.data);
		}
	}
				// Virtual service used to give 'internal' messages
	return(ws);
	}
echo = {
	action_display : function(line){
		message = "<li>"+line+"</li>"
		$("#debug").append(message)
	}
}

