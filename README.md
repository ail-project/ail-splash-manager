# ail-splash-manager

AIL crawlers are using a splash crawler to fetch and render a domain.  
The purpose of this Flask server is to simplify the installation and manage them:
- Create, launch, relaunch splash dockers.
- handle proxies
- check crawler status

Installation
------------

```bash
git clone https://github.com/ail-project/ail-splash-manager.git
cd ail-splash-manager
./install.sh
```

Tor proxy
------------

### Installation

The tor proxy from the Ubuntu package is installed by default.

**This package is outdated**: Some v3 onion address are not resolved.

**/!\ Install the tor proxy provided by The [torproject](https://2019.www.torproject.org/docs/debian) to solve this issue./!\**

### Configuration

Once installed, we need to allow all splash dockers to reach this proxy. You can use the ``configure_tor`` script or configure it yourself.

- Script
```bash
cd ail-splash-manager
./configure_tor.sh
```

- Manual configuration:
  - Allow Tor to bind to any interface or to the docker interface (by default binds to 127.0.0.1 only) in ``/etc/tor/torrc``
       ``SOCKSPort 0.0.0.0:9050`` or
       ``SOCKSPort 172.17.0.1:9050``
  - Add the following line ``SOCKSPolicy accept 172.17.0.0/16`` in ``/etc/tor/torrc``
     (for a linux docker, the localhost IP is *172.17.0.1*; Should be adapted for other platform)
  - Restart the tor proxy: ``sudo service tor restart``


API
  ------------

`api/v1/ping`

`api/v1/version`

`api/v1/get/session_uuid`

`api/v1/get/proxies/all`

`api/v1/get/splash/name/all`

`api/v1/get/splash/proxy/all`

`api/v1/splash/restart`

`api/v1/splash/kill`

`api/v1/proxy/add`

`api/v1/proxy/edit`

`api/v1/proxy/delete`

`api/v1/splash/edit`

`api/v1/splash/delete`
