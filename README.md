# gwss
(Copyleft) 2016 - AWI : Aquitaine Webmédia Indépendant


gwss is WebSocket Server

## Install

### Prerequisites

You need to have <b>python</b> 2.7 minimum, the code is python 3.x compatible.

Used python libs:

#### core

* optparse
* gevent
* requests

```bash
$ pip install gevent
$ pip install gevent-websocket
$ pip install requests
```

#### services
The <b>./service</b> directory contain some examples, to be able run them, you need also to download this modules :
* stats
	* [geoIP]()
	* [pygal](http://www.pygal.org/en/latest/index.html) (with [pygal_maps_world](http://www.pygal.org/en/latest/documentation/types/maps/pygal_maps_world.html))
```bash
$ pip install python-geoip
$ pip install python-geoip-geolite2
$ pip install pygal
$ pip install pygal-maps-world
```

* logger
	* CouchDB
```bash
$ pip install CouchDB
```

### Demo

Have a look on : http://gwss.modulix.net

### Download

The sources are available on : https://github.com/modulix/gwss

```bash
$ git clone https://github.com/modulix/gwss.git
```

### Setup
First you need to choice the front end you want to use:
* nginx
* apache2 (>= 2.4.5) wit [mod_proxy_wstunnel](https://httpd.apache.org/docs/2.4/mod/mod_proxy_wstunnel.html)
* standalone (do not use in production)

#### Front Office

#### Directories
When ou dowload this project, you get these files:
'''
~/gwss/bin
~/gwss/public_html
'''
Move <b>public_html</b> files in the directory served by your front server, should be something like:
* nginx -> /usr/share/nginx/html
* apache -> /var/www/htdocs
* standalone -> ~/public_html

### Start & stop
#### System V
```bash
# /etc/init.d/gwss start
# /etc/init.d/gwss stop
```
#### systemd
```bash
# systemctl start gwss
# systemctl stop gwss
```

## Documentation

* [Docs](https://github.com/modulix/gwss/wiki/Doc)
* [FAQ](https://github.com/modulix/gwss/wiki/FAQ)
* [Bugs](https://github.com/modulix/gwss/issues)


