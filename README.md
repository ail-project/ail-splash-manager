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

Usage
------------

#### Launching AIL Splash Manager
```bash
./LAUNCH.sh -l
```
#### killing AIL Splash Manager and all Splash dockers
```bash
./LAUNCH.sh -k
```

#### Launching AIL Splash Manager Tests
```bash
./LAUNCH.sh -t
```

Tor proxy
------------

### Installation

The tor proxy from the Ubuntu package is installed by default.

**This package is outdated**: Some v3 onion address are not resolved.

**/!\ Install the tor proxy provided by The [torproject](https://2019.www.torproject.org/docs/debian) to solve this issue./!\**

*Note: Ubuntu Install, add torrc in apt sources:*

```bash
sudo sh -c 'echo "deb https://deb.torproject.org/torproject.org $(lsb_release -sc) main" >> /etc/apt/sources.list.d/tor-project.list'
```

Once installed, we need to allow all splash dockers to reach this proxy. You can use the ``configure_tor`` script or configure it yourself.

- Install Script
```bash
cd ail-splash-manager
./configure_tor.sh
```

- Manual configuration:
  - Allow Tor to bind to any interface or to the docker interface (by default binds to 127.0.0.1 only) in ``/etc/tor/torrc``
       ``SocksPort 0.0.0.0:9050`` or
       ``SocksPort 172.17.0.1:9050``
  - Add the following line ``SocksPolicy accept 172.17.0.0/16`` in ``/etc/tor/torrc``
     (for a linux docker, the localhost IP is *172.17.0.1*; Should be adapted for other platform)
  - Restart the tor proxy: ``sudo service tor restart``


Configuration
------------

##### [AIL framework crawlers configuration](https://github.com/ail-project/ail-framework/blob/master/HOWTO.md#configuration) :  
  - Splash-Manager API key
  - Splash-Manager URL
  - Number of crawlers to launch
  - https://github.com/ail-project/ail-framework/blob/master/HOWTO.md#configuration

##### Proxies:

Edit ``config/proxies_profiles.cfg``:

- ``[section_name]:`` proxy name, each section describe a proxy.
- ``host:`` proxy host  
(for a linux docker, the localhost IP is 172.17.0.1; Should be adapted for other platform)
- ``port:`` proxy port
- ``type:`` proxy type, `SOCKS5` or `HTTP`
- ``description:`` proxy description
- ``crawler_type:`` crawler type (tor or web)

```bash
[default_tor] # section name: proxy name
host=172.17.0.1
port=9050
type=SOCKS5
description=tor default proxy
crawler_type=tor
```


##### Splash Dockers:

Edit ``config/containers.cfg``:

- ``[section_name name]:`` splash name, each section describe a splash container.
- ``proxy_name:`` proxy name (defined in proxies_profiles.cfg)
- ``port:``  single port or port range (ex: 8050 or 8050-8052),  
A port range is used to launch multiple Splash Dockers
- ``cpu:`` max number of cpu allocated
- ``memory:``max RAM (Go) allocated
- ``description:`` Splash description

```bash
[default_splash_tor] # section name: splash name
proxy_name=default_tor
port=8050-8052
cpu=1
memory=1
maxrss=2000
description= default splash tor
```

Web proxy
------------

#### SQUID

- Edit ``/etc/squid/squid.conf``:

  ```bash
  acl localnet src 172.17.0.0/16 # Docker IP range
  http_access allow localnet
  ```

- Add a new proxy in ``config/proxies_profiles.cfg``:

  ```bash
  [squid_proxy]
  host=172.17.0.1
  port=3128
  type=HTTP
  description=squid web proxy
  crawler_type=web
  ```

- Bind this proxy to a Splash docker in ``config/containers.cfg``

API
------------

`api/v1/ping`

`api/v1/version`

`api/v1/get/session_uuid`

`api/v1/get/proxies/all`

`api/v1/get/splash/all`

`api/v1/splash/restart`

`api/v1/splash/kill`
