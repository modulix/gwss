
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
		console.log(msg)
		var fn = window["action_"+msg.js_action];
		if(typeof fn === 'function') {
			fn(msg.data);
		}
	}
	return(ws);
	}
function action_display(line){
	message = "<li>"+line.key+"</li>"
	$("#debug").append(message)
}
