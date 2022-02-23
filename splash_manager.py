#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import argparse
import os
import configparser
import json
import sys
import subprocess

from uuid import uuid4

# # # # # # # # # # # # #
# #     DOCKER CMD    # #
# # # # # # # # # # # # #

def get_docker_id_from_output(b_stdout):
    docker_id = b_stdout.decode()
    return docker_id.replace('\n', '')

def get_docker_short_id(container_id):
    return container_id[:12]

# docker --help
def check_docker_install():
    cmd = ['docker', '--help']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        # # TODO: ADD LOG
        #print(p.stderr)
        return False
    else:
        return True

# docker ps
def check_docker_permission():
    cmd = ['docker', 'ps']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if b'permission denied' in p.stderr:
        return False
    else:
        return True

# docker ps | grep scrapinghub/splash
def get_all_running_splash_docker(r_text=False):
    containers_id = []
    # get docker short id
    cmd_1 = ['docker', 'ps']
    cmd_2 = ['grep', 'scrapinghub/splash']
    p1 = subprocess.Popen(cmd_1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd_2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    if output:# If error
        if r_text:
            return output.decode()
        lines = output.decode().split('\n')
        for line in lines:
            if line:
                container_id = line[:12]
                containers_id.append(container_id)
    return containers_id

# docker port <ID>
def get_docker_port_cmd(container_id):     # # TODO:
    cmd = ['docker', 'port', container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        container_port = p.stdout.decode()
        container_port = container_port.replace('\n', '').rsplit(':')[1]
        print(container_port)

# docker inspect -f '{{.NetworkSettings.Gateway}}' <ID>
def get_docker_gateway(container_id):
    cmd = ["docker", "inspect", "-f", "'{{.NetworkSettings.Gateway}}'", container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
        return None
    else:
        container_gateway = p.stdout.decode()
        container_gateway = container_gateway.replace('\n', '').replace("'", "")
        return container_gateway

# docker inspect -f '{{.HostConfig.Binds}}' <ID>
def get_docker_binding(container_id):
    cmd = ["docker", "inspect", "-f", "'{{.HostConfig.Binds}}'", container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr) # # TODO: LOG
        return None
    else:
        container_binding = p.stdout.decode()
        container_binding = container_binding[2:-3]
        return container_binding

def get_docker_mounted_binding(container_id):
    dict_docker_mounted_binding = {}
    # Get mounted binding Source
    cmd = ["docker", "inspect", "-f", "'{{range.Mounts}}{{if eq .Type \"bind\"}}{{.Source}}{{end}}{{end}}'", container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr) # # TODO: LOGS
        source = None
    else:
        source = p.stdout.decode()
        source = source[1:-2]
    dict_docker_mounted_binding['source'] = source
    # Get mounted binding Destination
    cmd = ["docker", "inspect", "-f", "'{{range.Mounts}}{{if eq .Type \"bind\"}}{{.Destination}}{{end}}{{end}}'", container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr) # # TODO: LOGS
        destination = None
    else:
        destination = p.stdout.decode()
        destination = destination[1:-2]
    dict_docker_mounted_binding['destination'] = destination
    return dict_docker_mounted_binding

# docker inspect <ID>
def get_docker_state(container_id):
    cmd = ["docker", "inspect", container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr) # # TODO: LOGS
        return {}
    else:
        dict_docker = p.stdout.decode()
        dict_docker = json.loads(dict_docker)[0]
        return dict_docker['State']

# build cmd to launch a docker
# docker run -d -p <PORT NUMBER>:8050 --restart=always --cpus=<NUMBER OF CPU>
#           --memory=<MEMORY SIZE>G
#           {-v <PROXY PROFILE LOCATION>:/etc/splash/proxy-profiles/ --net=bridge}
#           scrapinghub/splash --maxrss <MAXRSS>
def build_docker_cmd(port_number, proxy_dir, proxy_name, cpu=1, memory=2, maxrss=3000):
    cmd = ['docker', 'run', '-d']
    # bind port number
    cmd.append('-p')
    cmd.append('{}:8050'.format(port_number))
    # force restart on crash / max memory reached
    cmd.append('--restart=always')
    # cpu and memory
    cmd.append('--cpus={}'.format(cpu))
    cmd.append('--memory={}G'.format(memory))
    # proxy binding
    if proxy_name and proxy_name != 'None':
        proxy_profile_dir = os.path.join(proxy_dir, 'etc/splash/proxy-profiles')
        cmd.append('-v')
        cmd.append('{}:/etc/splash/proxy-profiles/'.format(proxy_profile_dir))
        cmd.append('--net=bridge')
    # docker name
    cmd.append('scrapinghub/splash')
    # maxrss
    cmd.append('--maxrss')
    cmd.append(str(maxrss))
    return cmd

# docker run
def cmd_launch_docker(port_number, proxy_dir, proxy_name, cpu, memory, maxrss):
    cmd = build_docker_cmd(port_number, proxy_dir, proxy_name, cpu=cpu, memory=memory, maxrss=maxrss)
    #print(cmd)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        out_stderr = p.stderr.decode().split('\n')
        for line in out_stderr:
            if len(line) > 7:
                if line[:7] == 'WARNING':
                    # # TODO: warning logs
                    print(line)
                elif line[:7] == 'docker:':
                    # # TODO: errors logs
                    print('ERROR:')
                    print(line)
                    print()
    if p.stdout:
        new_docker_id = get_docker_id_from_output(p.stdout)
        new_docker_id = get_docker_short_id(new_docker_id)
        return new_docker_id

# docker restart <ID>
def cmd_restart_docker(docker_id): # # TODO: RENAME ME
    cmd = ['docker', 'restart', docker_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        new_docker_id = get_docker_id_from_output(p.stdout)
        if new_docker_id == docker_id:
            print('docker {} relaunched'.format(new_docker_id))
        else:
            print('ERROR: docker relaunch, id change')
        return new_docker_id

# docker kill <ID>
def cmd_kill_docker(docker_id):
    # # TODO: check if docker_id in list
    cmd = ['docker', 'kill', docker_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        new_docker_id = get_docker_id_from_output(p.stdout)
        if new_docker_id == docker_id:
            print('docker {} killed'.format(new_docker_id))
        else:
            print('ERROR: docker relaunch, id change')
            print(p.stdout.decode())
        return new_docker_id

# # # # # # # # # # # # #
# # # # # # # # # # # # #
# # # # # # # # # # # # #

# # # # # # # # # # #
# #     PROXY     # #
# # # # # # # # # # #

class Proxy(object):
    """Proxy."""

    def __init__(self, name, host, port, current_dir, proxy_type, crawler_type, description=None):
        self.name = name
        self.host = host
        self.port = port
        self.proxy_dir = os.path.join(current_dir, 'dockers_proxies_profiles', self.name)
        self.proxy_type = proxy_type
        self.description = description
        self.crawler_type = crawler_type
        self.splash_dockers = {}

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_proxy_dir(self):
        return self.proxy_dir

    def get_crawler_type(self):
        return self.crawler_type

    def get_all_containers_name(self):
        return self.splash_dockers.keys()

    def get_splash_container_by_name(self, name):
        return self.splash_dockers[container_name]

    def to_dict(self, proxy_setting=False):
        proxy_dict = {'name': self.get_name()}
        if self.name != 'None':
            proxy_dict['description'] = self.get_description()
            proxy_dict['crawler_type'] = self.crawler_type
            if proxy_setting:
                proxy_dict['host'] = self.host
                proxy_dict['port'] = self.port
                proxy_dict['type'] = self.proxy_type
        return proxy_dict

    def add_splash_docker(self, container_obj):
        self.splash_dockers[container_obj.get_name()] = container_obj

    def remove_splash_docker(self, container_obj):
        self.splash_dockers.remove(container_obj.get_name())

    def delete_proxy(self):
        for container_name in self.get_all_containers_name():
            res = self.splash_dockers[container_name].delete_container()

        # # TODO: DELETE FILE

    def test_proxy(self):
        pass

#### API ####

# # TODO: add check
def api_add_proxy(proxy_name, host, port, proxy_type, crawler_type, description=None, edit=False): ################################
    proxies_profiles = os.path.join('config', 'proxies_profiles.cfg')
    if not os.path.exists(proxies_profiles):
        raise Exception('Config file: {}, not found'.format(proxies_profiles))
    cfg = configparser.ConfigParser()
    cfg.read(proxies_profiles)
    if cfg.has_section(proxy_name) and not edit:
        return ({'status': 'error', 'reason': f'This proxy already exist: {proxy_name}'}, 400)
    else:
        cfg.set(proxy_name, 'host', host)
        cfg.set(proxy_name, 'port', port)
        cfg.set(proxy_name, 'proxy_type', proxy_type)
        if description:
            cfg.set(proxy_name, 'description', description)
        cfg.set(proxy_name, 'crawler_type', crawler_type)
        with open(proxies_profiles, 'w') as configfile:
            configfile.write(cfg)

        create_proxy(proxy_name, host, port, proxy_type, crawler_type, description)

        res = {proxy_name:{'host': host, 'port': port, 'proxy_type': proxy_type, 'description': description, 'crawler_type': crawler_type}}
        return (res, 200)

# # TODO: KILL DOCKER
def api_delete_proxy(proxy_name): ################################
    proxies_profiles = os.path.join('config', 'proxies_profiles.cfg')
    if not os.path.exists(proxies_profiles):
        raise Exception('Config file: {}, not found'.format(proxies_profiles))
    cfg = configparser.ConfigParser()
    cfg.read(proxies_profiles)
    if not cfg.has_section(proxy_name):
        return ({'status': 'error', 'reason': f'This proxy don\'t exist: {proxy_name}'}, 400)
    else:
        cfg.remove_section(proxy_name)
        with open(proxies_profiles, 'w') as configfile:
            configfile.write(cfg)

        # # TODO: KILL DOCKER
        del all_proxxiess[proxy_name]

        res = {'name': proxy_name}
        return (res, 200)


# # # # # # # # # # #
# #     SPLASH    # #
# # # # # # # # # # #

class SplashContainer(object):
    """SplashContainer."""

    def __init__(self, name, proxy, cpu, memory, maxrss, description=None): # proxy name?
        self.name = name
        self.description = description
        self.proxy = proxy
        self.cpu = cpu
        self.memory = memory
        self.maxrss = maxrss
        self.splash = {}

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def get_cpu_limit(self):
        return self.cpu

    def get_memory_limit(self):
        return self.memory

    def get_maxrss(self):
        return self.maxrss

    def get_all_ports(self): # # TODO: TEST ME
        return self.splash.keys()

    def get_proxy_name(self):
        return self.proxy.get_name()

    def get_proxy_dir(self):
        return self.proxy.get_proxy_dir()

    def get_all_splash(self):
        return self.splash

    def get_splash_by_port(self, port):
        return self.splash[port]

    def launch_splash(self, port): # CREATE SPLASH OBJECT
        new_docker_id = cmd_launch_docker(port, self.get_proxy_dir(), self.get_proxy_name(), self.cpu, self.memory, self.maxrss)
        # New Docker Launched
        if new_docker_id:
            self.splash[port] = Splash(new_docker_id, port, self)
        else: # # TODO: LOGS ERROR
            print('ERROR: Splash not launched')

    def remove_splash(self, port): # REMOVE + KILL SPLASH OBJECT
        docker_id = get_splash_by_port(self, port).kill()
        if docker_id:
            self.proxy.remove(port)
        return docker_id

    def delete_container(self):
        for port in self.get_all_ports():
            docker_id = get_splash_by_port(self, port).kill()
            if docker_id:
                break
        if not self.splash:
            self.proxy.remove_container()
            return True
        return False

        # # TODO: DELETE FILE

    def to_dict(self, proxy=False): # # TODO: GET SPLASH DICT (PORT + ID) ????
        dict_container = {}
        dict_container['name'] = self.get_name()
        dict_container['description'] = self.get_description()
        dict_container['cpu'] = self.get_cpu_limit()
        dict_container['memory'] = self.get_memory_limit()
        dict_container['maxrss'] = self.get_maxrss()
        #dict_container['proxy'] = self.proxy # # TODO: TO DICT ## CHECK FIELD TO RETURN
        dict_container['ports'] = list(self.get_all_ports())
        if proxy:
            dict_container['proxy'] = {}
            dict_container['proxy']['name'] = self.proxy.get_name()
            dict_container['proxy']['crawler_type'] = self.proxy.get_crawler_type()
        return dict_container

class Splash(object):
    """Splash."""

    def __init__(self, container_id, port, splash_container):
        self.splash_container = splash_container
        self.id = container_id
        self.port = port

    def get_id(self):
        return self.id

    def get_name(self):
        return self.splash_container.get_name()

    def get_description(self):
        return self.splash_container.get_description()

    def get_name(self):
        return self.splash_container.get_name()

    def get_proxy_dir(self):
        return self.splash_container.get_proxy_dir()

    def get_proxy_name(self):
        return self.splash_container.get_proxy_name()

    def get_cpu_limit(self):
        return self.splash_container.get_cpu_limit()

    def get_memory_limit(self):
        return self.splash_container.get_memory_limit()

    def get_maxrss(self):
        return self.splash_container.get_maxrss()

    def kill(self):
        docker_id = cmd_kill_docker(self.id)
        return docker_id

    def restart(self, soft=True):
        if soft:
            docker_id = cmd_restart_docker(self.id)
        else:
            docker_id = cmd_kill_docker(self.id)
            if docker_id:
                new_docker_id = cmd_launch_docker(self.port, self.get_proxy_dir(), self.get_proxy_name(),
                                                    self.get_cpu_limit(), self.get_memory_limit(), self.get_maxrss())
                if new_docker_id:
                    self.id = new_docker_id
        return self.id

######################################################
######################################################

# # TODO: add check
# check if proxy exist
def api_add_splash_docker(splash_name, proxy_name, port, cpu, memory, maxrss, description=None, edit=False):
    containers_profiles = os.path.join('config', 'containers.cfg')
    if not os.path.exists(containers_profiles):
        raise Exception('Config file: {}, not found'.format(containers_profiles))
    cfg = configparser.ConfigParser()
    cfg.read(containers_profiles)
    if cfg.has_section(splash_name) and not edit:
        print('error, splash docker already exist')
        return ({'status': 'error', 'reason': f'This Splash docker already exist: {splash_name}'}, 400)
    else:
        cfg.set(splash_name, 'proxy_name', proxy_name)
        cfg.set(splash_name, 'port', port)
        cfg.set(splash_name, 'cpu', cpu)
        cfg.set(splash_name, 'memory', memory)
        cfg.set(splash_name, 'maxrss', maxrss)
        if description:
            cfg.set(splash_name, 'description', description)
        with open(containers_profiles, 'w') as configfile:
            configfile.write(cfg)

        # # TODO: LAUNCH DOCKER

        res = {proxy_name:{'proxy_name': proxy_name, 'port': port, 'cpu': cpu, 'memory': memory, 'maxrss': maxrss, 'description':description}}
        return (res, 200)

def api_delete_splash_docker(splash_name):
    containers_profiles = os.path.join('config', 'containers.cfg')
    if not os.path.exists(containers_profiles):
        raise Exception('Config file: {}, not found'.format(containers_profiles))
    cfg = configparser.ConfigParser()
    cfg.read(containers_profiles)
    if not cfg.has_section(splash_name):
        return ({'status': 'error', 'reason': f'This Splash docker don\'t exist: {splash_name}'}, 400)
    else:
        cfg.remove_section(splash_name)
        with open(containers_profiles, 'w') as configfile:
            configfile.write(cfg)

        # # TODO: KILL DOCKER

        res = {'name': proxy_name}
        return (res, 200)

# # # # # # # # # # # # # # # # #
#              CORE             #
# # # # # # # # # # # # # # # # #

def kill_all_splash_dockers():
    containers_id = get_all_running_splash_docker()
    for container_id in containers_id:
        cmd_kill_docker(container_id)

# # TODO: add a mod to only query
class SplashManager(object):
    """docstring for SplashManager."""

    def __init__(self):
        # # TODO: use me + add in config
        #CPU_LIMIT = 4
        #MEMORY_LIMIT = 8 # RAM LIMIT (Go)

        self.current_dir = os.path.dirname(os.path.realpath(__file__))

        self.all_proxies = {}
        self.all_splash_containers = {}

        # used by AIL, check if proxy or splash are edited
        self.session_uuid = str(uuid4())
        self.version = 'v0.1'

        # LAUNCH SPLASH DOCKERS #
        print('Launching all Splash dockers ...')
        print()
        if not check_docker_install():
            print('Error: docker install')
            sys.exit(0)
        if not check_docker_permission():
            print('Error: permission denied, please run this script with sudo (docker containers)\n')
            sys.exit(0)

        self.kill_all_splash_dockers()
        self.load_all_proxies_profiles()
        self.launch_all_splash_dockers()

    def get_session_uuid(self):
        return self.session_uuid

    def get_version(self):
        return self.version

    # #     PROXY     # #

    def get_all_proxies_name(self):
        return self.all_proxies.keys()

    def get_proxy_by_name(self, proxy_name):
        return self.all_proxies[proxy_name]

    def get_all_proxies_dict(self):
        proxies_dict = {}
        for proxy_name in self.get_all_proxies_name():
            proxies_dict[proxy_name] = self.get_proxy_by_name(proxy_name).to_dict(proxy_setting=True)
        return proxies_dict

    # ADD a new proxy in memory and in config file
    # # TODO: use os.path.realpath()
    def create_proxy(self, proxy_name, host, port, proxy_type, crawler_type, description):
        self.all_proxies[proxy_name] = Proxy(proxy_name, host, port, self.current_dir, proxy_type, crawler_type, description=description)
        # create proxy profile
        proxy_dir = os.path.join(self.current_dir, 'dockers_proxies_profiles', proxy_name, 'etc/splash/proxy-profiles')
        if not os.path.isdir(proxy_dir):
            os.makedirs(proxy_dir)
        proxy_file = os.path.join(proxy_dir, 'default.ini')
        with open(proxy_file, 'w') as f:
            f.write('[proxy]\n')
            f.write('host={}\n'.format(host))
            f.write('port={}\n'.format(port))
            f.write('type={}\n'.format(proxy_type))

    def load_all_proxies_profiles(self):
        # clear docker proxies dir
        for root, dirs, files in os.walk(os.path.join(self.current_dir, 'dockers_proxies_profiles'), topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        proxies_profiles = os.path.join('config', 'proxies_profiles.cfg')
        if not os.path.exists(proxies_profiles):
            raise Exception('Config file: {}, not found'.format(proxies_profiles))
        cfg = configparser.ConfigParser()
        cfg.read(proxies_profiles)
        cfg_sections = cfg.sections()

        for section in cfg_sections:
            proxy_name = section
            proxy_name = proxy_name.replace('/', '')
            proxy_description = cfg.get(section, 'description')
            proxy_host = cfg.get(section, 'host')
            proxy_port = cfg.get(section, 'port')
            proxy_type = cfg.get(section, 'type')
            crawler_type = cfg.get(section, 'crawler_type')
            self.create_proxy(proxy_name, proxy_host, proxy_port, proxy_type, crawler_type, proxy_description)

    def test_all_proxies(self):
        for poxy_name in self.all_proxies:
            print(poxy_name)
            res = self.get_proxy_by_name(poxy_name).test_proxy()

    # #     SPLASH     # #

    def get_all_splash_container_names(self):
        return self.all_splash_containers.keys()

    def get_splash_container_by_name(self, container_name):
        return self.all_splash_containers[container_name]

    def get_all_splash_container_dict(self):
        dict_all_splash_container = {}
        for container_name in self.get_all_splash_container_names():
            dict_all_splash_container[container_name] = self.get_splash_container_by_name(container_name).to_dict(proxy=True)
        return dict_all_splash_container

    def get_all_splash(self):
        l_splash = []
        for container_name in self.get_all_splash_container_names():
            l_splash.append(self.get_splash_container_by_name(container_name).get_all_splash())
        return l_splash

    def launch_splash(self, container_name, port):
        self.get_splash_container_by_name(container_name).launch_splash(port)

    def add_splash_container(self, name, proxy_name, cpu, memory, maxrss, description=None):
        proxy = self.get_proxy_by_name(proxy_name)
        self.all_splash_containers[name] = SplashContainer(name, proxy, cpu, memory, maxrss, description=description)

    def remove_splash_container(self, container_name):
        pass # # TODO:

    def launch_all_splash_dockers(self):
        proxies_profiles = os.path.join('config', 'containers.cfg')
        if not os.path.exists(proxies_profiles):
            raise Exception('Config file: {}, not found'.format(proxies_profiles))
        cfg = configparser.ConfigParser()
        cfg.read(proxies_profiles)
        cfg_sections = cfg.sections()

        for container_name in cfg_sections:
            proxy_name = cfg.get(container_name, 'proxy_name')
            description = cfg.get(container_name, 'description')
            cpu = cfg.getint(container_name, 'cpu')
            memory = cfg.getint(container_name, 'memory')
            maxrss = cfg.getint(container_name, 'maxrss')
            ports = cfg.get(container_name, 'port')
            ports = ports.split('-')
            if len(ports) > 1:
                try:
                    start = int(ports[0])
                    stop = int(ports[1]) + 1
                    ports = range(start, stop)
                except:
                    print('Error: launch_default splash, Invalid port number: {}'.format(ports))
                    continue
            else:
                try:
                    ports[0] = int(ports[0])
                except:
                    print('Error: launch_default splash, Invalid port number: {}'.format(ports[0]))
                    continue

            self.add_splash_container(container_name, proxy_name, cpu, memory, maxrss, description=description)
            for port in ports:
                if proxy_name not in self.get_all_proxies_name() and proxy_name != 'None': # # TODO: add me in launch_splash?
                    print('Error: Unknown proxy, {}'.format(proxy_name)) # # TODO: handle error
                else:
                    self.launch_splash(container_name, port)

    def restart_docker(self, splash_name, port, soft=True):
        splash = self.get_splash_container_by_name(splash_name).get_splash_by_port(port)
        docker_id = splash.restart(soft=soft)
        return docker_id

    def api_restart_docker(self, port, splash_name, soft=True):
        try:
            port = int(port)
        except Exception:
            return ({'status': 'error', 'reason': f'Invalid port number: {port}'}, 400)

        # check if container exist
        #if splash_name:
        if not self.get_splash_container_by_name(splash_name):
            return ({'status': 'error', 'reason': f'Unknown Splash Container Name: {splash_name}'}, 400)
        #else:
            # # TODO: search port
        #    pass
        # check if port exist
        if not self.get_splash_container_by_name(splash_name).get_splash_by_port(port):
            return ({'status': 'error', 'reason': f'Port not found: {port}'}, 400)

        docker_id = self.restart_docker(splash_name, port, soft=soft)
        return ({'docker_id': docker_id, 'port': port, 'name': splash_name}, 200)

    # def kill_docker(docker_id):

    def kill_all_splash_dockers(self):
        kill_all_splash_dockers()

# # # # # # # # # # # # # #
#                         #
#   API SPLASH CRAWLER    #
#                         #
# # # # # # # # # # # # # #

def api_kill_docker(docker_port):
    try:
        docker_port = int(docker_port)
    except Exception:
        return ({'status': 'error', 'reason': f'Invalid port number: {docker_port}'}, 400)
    docker_id = get_splash_id_by_port(docker_port)
    docker_id = kill_docker(container_id)
    return ({'docker_id': docker_id, 'docker_port': docker_port}, 200)

# # # # # # # # # # # # # #
#                         #
#   TEST SPLASH CRAWLER   #
#                         #
# # # # # # # # # # # # # #

def check_splash_docker_state(container_id):
    docker_state = get_docker_state(container_id)
    if docker_state['Error']:
        print(f'ERROR Docker: {docker_state["Error"]}') ## TODO: LOGS

    # # TODO:  OOMKilled
    if docker_state['Paused']:
        print('ERROR: Docker paused') ## TODO: LOGS
        return False
    elif docker_state['Restarting']:
        print('ERROR: Docker restarting') ## TODO: LOGS
        return False
    elif docker_state['Status'] != 'running' or not docker_state['Running'] or docker_state['Dead']:
        print('ERROR: This Docker is not running') ## TODO: LOGS
        return False
    else:
        return True

def test_splash_docker(container_id):
    if not check_splash_docker_state(container_id):
        return False

    gateway = get_docker_gateway(container_id)
    mounted_bind = get_docker_mounted_binding(container_id)

    # proxy profiles
    mounted_bind['source'] = os.path.join(mounted_bind['source'], 'default.ini')
    if mounted_bind['destination'] != '/etc/splash/proxy-profiles':
        print(f'ERROR PROXY PROFILES, Invalid Directory: {mounted_bind["destination"]}') ## TODO: LOGS

    if not os.path.isfile(mounted_bind['source']):
        print('ERROR PROXY PROFILES NOT FOUND') ## TODO: LOGS
        return False
    # Check Proxy
    else:
        dict_proxy_src = {}
        cfg = configparser.ConfigParser()
        cfg.read(mounted_bind['source'])
        try:
            proxy_host = cfg.get('proxy', 'host')
            proxy_port = cfg.get('proxy', 'port')
            proxy_type = cfg.get('proxy', 'type')
        except configparser.NoOptionError as e:
            print(f'Error: Invalid Proxy profile, missing option: {e}') # # TODO: LOGS
            return False

    # Check Proxy Host
    if gateway != proxy_host:
        print(f'ERROR: The Proxy Host is Invalid: proxy_host={proxy_host} splash_gateway={gateway}') # # TODO: LOGS
        return False

    return True

def tests():
    print()
    print('Splash List:')
    print(get_all_running_splash_docker(r_text=True).encode(encoding="ascii",errors="ignore"))
    print()

    containers_id = get_all_running_splash_docker()
    for container_id in containers_id:
        print(f'Testing Splash Docker {container_id}:')
        res = test_splash_docker(container_id)
        if not res:
            print(f'ERROR: Splash Docker {container_id}') # # TODO: LOGS
        else:
            print('success')
            print()


# # # # #  ------ # # # # #
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Splash Manager Helper')
    parser.add_argument('-k', '--kill', help='Kill all Splash dockers', action="store_true", default=False)
    parser.add_argument('-t', '--test', help='Launch Tests', action="store_true", default=False)
    args = parser.parse_args()

    if not args.kill and not args.test:
        parser.print_help()
        sys.exit(0)

    if args.kill:
        kill_all_splash_dockers()

    if args.test:
        tests()

    ## DEBUG:
    #splashManager = SplashManager()
    #print(splashManager.get_all_proxies_name())
    #print(splashManager.get_all_splash_container_names())
    #print(splashManager.get_all_splash())

    #container_id = '09d64a7d152e'
    #container_id = '294f7089f41e'

    #get_docker_state(container_id)
    #print(get_docker_gateway(container_id))
    #print(get_docker_binding(container_id))
    #print(get_docker_mounted_binding(container_id))

    #res = test_splash_docker(container_id)
    #print(res)

    #splashManager.test_all_proxies()
