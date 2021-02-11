#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import configparser
import json
import sys
import subprocess

from copy import deepcopy

CPU_LIMIT = 4
MEMORY_LIMIT = 8

docker_containers = {}
all_proxies = {}
all_proxies_ports = {}
all_containers_ports = {}
map_port_docker_id = {}
map_port_container_name = {}

#### PROXY ####
def load_default_proxies_profiles(current_dir):
    # clear docker proxies dir
    for root, dirs, files in os.walk(os.path.join(current_dir, 'dockers_proxies_profiles'), topdown=False):
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
        add_proxy(current_dir, proxy_name, proxy_host, proxy_port, proxy_type, crawler_type, proxy_description)

# # TODO: use os.path.realpath()
def add_proxy(current_dir, name, host, port, proxy_type, crawler_type, description):
    all_proxies[name] = {'host': host, 'port': port, 'type': proxy_type, 'description': description, 'crawler_type': crawler_type}
    # create proxy file
    proxy_dir = os.path.join(current_dir, 'dockers_proxies_profiles', name, 'etc/splash/proxy-profiles')
    if not os.path.isdir(proxy_dir):
        os.makedirs(proxy_dir)
    proxy_file = os.path.join(proxy_dir, 'default.ini')
    with open(proxy_file, 'w') as f:
        f.write('[proxy]\n')
        f.write('host={}\n'.format(host))
        f.write('port={}\n'.format(port))
        f.write('type={}\n'.format(proxy_type))

def get_all_proxy_profiles():
    return all_proxies

def get_all_docker_proxy_ports():
    return all_proxies_ports

# # TODO: refactor me, remove deepcopy , performance
def api_get_all_docker_proxy_ports():
    all_docker_proxy_ports = deepcopy(all_proxies_ports)
    for key in all_docker_proxy_ports:
        all_docker_proxy_ports[key] = list(all_docker_proxy_ports[key])
    return all_docker_proxy_ports

def get_splash_proxy_by_port(port):
    splash_id = get_splash_id_by_port(port)
    if splash_id:
        return docker_containers[splash_id]['proxy_name']

def get_proxy_dict(proxy_name, show_proxy_setting=False):
    proxy_dict = {'name': proxy_name}
    if proxy_name != 'None':
        proxy_dict['description'] = all_proxies[proxy_name]['description']
        proxy_dict['crawler_type'] = all_proxies[proxy_name]['crawler_type']
        if show_proxy_setting:
            proxy_dict['host'] = all_proxies[proxy_name]['host']
            proxy_dict['port'] = all_proxies[proxy_name]['port']
        return proxy_dict

def check_default_tor_proxy():
    pass

# # TODO: add check
def api_add_proxy(proxy_name, host, port, proxy_type, crawler_type, description=None, edit=False):
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

        res = {proxy_name:{'host': host, 'port': port, 'proxy_type': proxy_type, 'description': description, 'crawler_type': crawler_type}}
        return (res, 200)

def api_delete_proxy(proxy_name):
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
        res = {'name': proxy_name}
        return (res, 200)

#### ---- ####

def get_splash_id_by_port(port):
    return map_port_docker_id.get(port, None)

def get_containers_dict_by_name(splash_name):
    containers_dict = {}
    ports = list(all_containers_ports[splash_name])
    containers_dict['ports'] = ports
    containers_dict['description'] = get_splash_description_by_port(ports[0])
    containers_dict['proxy'] = get_proxy_dict(get_splash_proxy_by_port(ports[0]))
    return containers_dict

def get_splash_description_by_port(port):
    splash_id = get_splash_id_by_port(port)
    if splash_id:
        return docker_containers[splash_id].get('description', None)

def get_all_docker_containers():
    return all_docker_containers_ports

def get_all_containers_name_ports():
    all_containers_ports

def api_get_all_containers_name_ports():
    dict_containers_name = {}
    for key in all_containers_ports:
        dict_containers_name[key] = get_containers_dict_by_name(key)
    return dict_containers_name

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
        res = {'name': proxy_name}
        return (res, 200)

def launch_default_splash_dockers(proxy_dir):
    proxies_profiles = os.path.join('config', 'containers.cfg')
    if not os.path.exists(proxies_profiles):
        raise Exception('Config file: {}, not found'.format(proxies_profiles))
    cfg = configparser.ConfigParser()
    cfg.read(proxies_profiles)
    cfg_sections = cfg.sections()

    for section in cfg_sections:
        proxy_name = cfg.get(section, 'proxy_name')
        description = cfg.get(section, 'description')
        ports = cfg.get(section, 'port')
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

        for port in ports:
            if proxy_name not in get_all_proxy_profiles() and proxy_name != 'None':
                print('Error: Unknow proxy, {}'.format(proxy_name))
            else:
                launch_docker(section, port, proxy_dir, proxy_name, description=description, cpu=1, memory=2, maxrss=2000)
                #launch_docker(section, 8050, proxy_dir, proxy_name, description=description, cpu=1, memory=2, maxrss=2000)


def get_docker_id_from_output(b_stdout):
    docker_id = b_stdout.decode()
    return docker_id.replace('\n', '')

def get_docker_short_id(container_id):
    return container_id[:12]

def check_docker_install():
    cmd = ['docker', '--help']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        # # TODO: ADD LOG
        #print(p.stderr)
        return False
    else:
        return True

def check_docker_permission():
    cmd = ['docker', 'ps']
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if b'permission denied' in p.stderr:
        return False
    else:
        return True

def get_all_running_splash_docker():
    containers_id = []
    # get docker short id
    cmd_1 = ['docker', 'ps']
    cmd_2 = ['grep', 'scrapinghub/splash']
    p1 = subprocess.Popen(cmd_1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd_2, stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    output = p2.communicate()[0]
    if output:# If error
        lines = output.decode().split('\n')
        for line in lines:
            if line:
                container_id = line[:12]
                containers_id.append(container_id)
    return containers_id

def get_docker_port_cmd(container_id):
    cmd = ['docker', 'port', container_id]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stderr:
        print(p.stderr)
    else:
        container_port = p.stdout.decode()
        container_port = container_port.replace('\n', '').rsplit(':')[1]
        print(container_port)

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
        proxy_profile_dir = os.path.join(proxy_dir, proxy_name, 'etc/splash/proxy-profiles')
        cmd.append('-v')
        cmd.append('{}:/etc/splash/proxy-profiles/'.format(proxy_profile_dir))
        cmd.append('--net=bridge')
    # docker name
    cmd.append('scrapinghub/splash')
    # maxrss
    cmd.append('--maxrss')
    cmd.append(str(maxrss))
    return cmd

def launch_docker(container_name, port_number, proxy_dir, proxy_name, description=None, cpu=1, memory=2, maxrss=2000):
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
        docker_containers[new_docker_id] = {'port': port_number, 'proxy_name': proxy_name}
        if description:
            docker_containers[new_docker_id]['description'] = description
        map_port_docker_id[port_number] = new_docker_id

        # set proxy port
        if proxy_name not in all_proxies_ports:
            all_proxies_ports[proxy_name] = set()
        all_proxies_ports[proxy_name].add(port_number)

        # set container ports
        if container_name not in all_containers_ports:
            all_containers_ports[container_name] = set()
        all_containers_ports[container_name].add(port_number)

        map_port_container_name[port_number] = container_name

        return new_docker_id

def kill_all_splash_dockers():
    containers_id = get_all_running_splash_docker()
    for container_id in containers_id:
        kill_docker(container_id)

def kill_docker(docker_id):
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

        if docker_containers:
            proxy_name = docker_containers[new_docker_id]['proxy_name']
            docker_port = docker_containers[new_docker_id]['port']
            container_name = map_port_container_name[docker_port]
            docker_containers.pop(new_docker_id)
            map_port_docker_id.pop(docker_port)

            all_proxies_ports[proxy_name].remove(docker_port)
            all_containers_ports[container_name].remove(docker_port)
            map_port_container_name.remove(docker_port)

        return new_docker_id

def restart_docker(docker_id):
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

def api_restart_docker(docker_port):
    try:
        docker_port = int(docker_port)
    except Exception:
        return ({'status': 'error', 'reason': f'Invalid port number: {docker_port}'}, 400)
    docker_id = get_splash_id_by_port(docker_port)
    docker_id = restart_docker(docker_id)
    return ({'docker_id': docker_id, 'docker_port': docker_port}, 200)

def api_kill_docker(docker_port):
    try:
        docker_port = int(docker_port)
    except Exception:
        return ({'status': 'error', 'reason': f'Invalid port number: {docker_port}'}, 400)
    docker_id = get_splash_id_by_port(docker_port)
    docker_id = kill_docker(container_id)
    return ({'docker_id': docker_id, 'docker_port': docker_port}, 200)

def launch_init():
    print('Lauching all Splash dockers ...')
    print()

    if not check_docker_install():
        print('Error: docker install')
        sys.exit(0)
    if not check_docker_permission():
        print('Error: permission denied, please run this script with sudo (docker containers)\n')
        sys.exit(0)

    current_dir = os.path.dirname(os.path.realpath(__file__))
    proxy_dir = os.path.join(current_dir, 'dockers_proxies_profiles')

    kill_all_splash_dockers()
    load_default_proxies_profiles(current_dir)
    launch_default_splash_dockers(proxy_dir)

    print(docker_containers)
    print(all_proxies)
    print(all_proxies_ports)
    print(all_containers_ports)
    print(map_port_docker_id)

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

# # # # #  ------ # # # # #

if __name__ == '__main__':
    container_id = '09d64a7d152e'
    #container_id = '294f7089f41e'

    #get_docker_state(container_id)
    #print(get_docker_gateway(container_id))
    #print(get_docker_binding(container_id))
    #print(get_docker_mounted_binding(container_id))

    res = test_splash_docker(container_id)
    print(res)
