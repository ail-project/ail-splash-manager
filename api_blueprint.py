#!/usr/bin/env python3
# -*-coding:UTF-8 -*

'''
    Flask functions and routes for the rest api
'''

import os
import re
import sys
import uuid
import json

from flask import Flask, render_template, jsonify, request, Blueprint, redirect, url_for, Response
from functools import wraps

import splash_manager
splash_manager.launch_init()

# used by AIL, check if proxy or splash are edited
session_uuid = str(uuid.uuid4())

# ============ VARIABLES ============
api = Blueprint('api', __name__, template_folder='templates')

# ============ AUTH FUNCTIONS ============

def check_token_format(strg, search=re.compile(r'[^a-zA-Z0-9_-]').search):
    return not bool(search(strg))

def generate_token(length=41, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"):
    random_bytes = os.urandom(length)
    len_charset = len(charset)
    indices = [int(len_charset * (byte / 256.0)) for byte in random_bytes]
    token = "".join([charset[index] for index in indices])

    current_dir = os.path.dirname(os.path.realpath(__file__))
    token_file = os.path.join(current_dir, 'token_admin.txt')
    with open(token_file, 'w') as f:
        f.write(token)

    admin_token = token
    return token

def get_admin_token():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    token_file = os.path.join(current_dir, 'token_admin.txt')
    try:
        with open(token_file, 'r') as f:
            token = f.read()
    except FileNotFoundError:
        token = generate_token()
    return token

admin_token = get_admin_token()

def verify_token(token):
    if len(token) != 41:
        return False

    if not check_token_format(token):
        return False

    return token == admin_token

def verify_user_role(role, token):
    if is_in_role(token, role):
        return True
    else:
        return False

def is_in_role(token, role):
    return True
    # if r_serv_db.sismember('user_role:{}'.format(role), user_id):
    #     return True
    # else:
    #     return False

# ============ DECORATOR ============

def token_required(user_role):
    def actual_decorator(funct):
        @wraps(funct)
        def api_token(*args, **kwargs):
            data = authErrors(user_role)
            if data:
                return Response(json.dumps(data[0], indent=2, sort_keys=True), mimetype='application/json'), data[1]
            else:
                return funct(*args, **kwargs)
        return api_token
    return actual_decorator

def get_auth_from_header():
    token = request.headers.get('Authorization').replace(' ', '') # remove space
    return token

def authErrors(user_role):
    # Check auth
    if not request.headers.get('Authorization'):
        return ({'status': 'error', 'reason': 'Authentication needed'}, 401)
    token = get_auth_from_header()
    data = None
    # verify token format

    # brute force protection
    current_ip = request.remote_addr
    # login_failed_ip = r_cache.get('failed_login_ip_api:{}'.format(current_ip))
    # brute force by ip
    # if login_failed_ip:
    #     login_failed_ip = int(login_failed_ip)
    #     if login_failed_ip >= 5:
    #         return ({'status': 'error', 'reason': 'Max Connection Attempts reached, Please wait {}s'.format(r_cache.ttl('failed_login_ip_api:{}'.format(current_ip)))}, 401)

    try:
        authenticated = False
        if verify_token(token):
            authenticated = True

            # check user role
            if not verify_user_role(user_role, token):
                data = ({'status': 'error', 'reason': 'Access Forbidden'}, 403)

        if not authenticated:
            #r_cache.incr('failed_login_ip_api:{}'.format(current_ip))
            #r_cache.expire('failed_login_ip_api:{}'.format(current_ip), 300)
            data = ({'status': 'error', 'reason': 'Authentication failed'}, 401)
    except Exception as e:
        print(e)
        data = ({'status': 'error', 'reason': 'Malformed Authentication String'}, 400)
    if data:
        return data
    else:
        return None

# ============ API CORE =============

def create_json_response(data_dict, response_code):
    return Response(json.dumps(data_dict, indent=2, sort_keys=True), mimetype='application/json'), int(response_code)

def get_mandatory_fields(json_data, required_fields):
    for field in required_fields:
        if field not in json_data:
            return {'status': 'error', 'reason': 'mandatory field: {} not provided'.format(field)}, 400
    return None

# ============ FUNCTIONS ============

# ============= ROUTES ==============

@api.route("api/v1/ping", methods=['GET'])
@token_required('admin')
def ping():
    return Response(json.dumps({'message':'pong'}, indent=2, sort_keys=True), mimetype='application/json'), 200

@api.route("api/v1/version", methods=['GET'])
@token_required('admin')
def get_version():
    return Response(json.dumps({'message':'v0.1'}, indent=2, sort_keys=True), mimetype='application/json'), 200

@api.route("api/v1/get/session_uuid", methods=['GET'])
@token_required('admin')
def get_session_uuid():
    return Response(json.dumps({'session_uuid':session_uuid}, indent=2, sort_keys=True), mimetype='application/json'), 200

@api.route("api/v1/get/proxies/all", methods=['GET'])
@token_required('admin')
def get_proxies_all():
    res = splash_manager.get_all_proxy_profiles()
    return Response(json.dumps(res, indent=2, sort_keys=True), mimetype='application/json'), 200

# get splash by container name
@api.route("api/v1/get/splash/name/all", methods=['GET'])
@token_required('admin')
def get_splash_all():
    res = splash_manager.api_get_all_containers_name_ports()
    return Response(json.dumps(res, indent=2, sort_keys=True), mimetype='application/json'), 200

# get splash by proxy
@api.route("api/v1/get/splash/proxy/all", methods=['GET'])
@token_required('admin')
def get_splash_all_proxy():
    res = splash_manager.api_get_all_docker_proxy_ports()
    return Response(json.dumps(res, indent=2, sort_keys=True), mimetype='application/json'), 200

# restart splash container
@api.route("api/v1/splash/restart", methods=['POST'])
@token_required('admin')
def restart_splash():
    data = request.get_json()
    docker_port = data.get('docker_port', None)
    res = splash_manager.api_restart_docker(docker_port)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# API - launch docker
# launch splash container

# kill splash container
@api.route("api/v1/splash/kill", methods=['POST'])
@token_required('admin')
def kill_splash():
    data = request.get_json()
    docker_port = data.get('docker_port', None)
    res = splash_manager.api_kill_docker(docker_port)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]


# add proxy
@api.route("api/v1/proxy/add", methods=['POST'])
@token_required('admin')
def add_proxy():
    data = request.get_json()
    name = data.get('name', None)
    host = data.get('host', None)
    port = data.get('port', None)
    type = data.get('type', None)
    crawler_type = data.get('crawler_type', None)
    description = data.get('crawler_type', description)
    res = splash_manager.api_add_proxy(proxy_name, host, port, proxy_type, crawler_type, description=None)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# add proxy
@api.route("api/v1/proxy/edit", methods=['POST'])
@token_required('admin')
def edit_proxy():
    data = request.get_json()
    name = data.get('name', None)
    host = data.get('host', None)
    port = data.get('port', None)
    type = data.get('type', None)
    crawler_type = data.get('crawler_type', None)
    description = data.get('crawler_type', description)
    res = splash_manager.api_add_proxy(proxy_name, host, port, proxy_type, crawler_type, description=None, edit=True)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# delete proxy
@api.route("api/v1/proxy/delete", methods=['POST'])
@token_required('admin')
def delete_proxy():
    data = request.get_json()
    name = data.get('name', None)
    res = splash_manager.api_delete_proxy(proxy_name)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

############################

# add splash docker
@api.route("api/v1/splash/add", methods=['POST'])
@token_required('admin')
def add_splash():
    data = request.get_json()
    splash_name = data.get('name', None)
    proxy_name = data.get('proxy_name', None)
    port = data.get('port', None)
    cpu = data.get('type', cpu)
    memory = data.get('memory', None)
    maxrss = data.get('maxrss', None)
    description = data.get('crawler_type', description)
    res = splash_manager.api_add_splash_docker(splash_name, proxy_name, port, cpu, memory, maxrss, description=description)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# edit splash docker
@api.route("api/v1/splash/edit", methods=['POST'])
@token_required('admin')
def edit_splash():
    data = request.get_json()
    splash_name = data.get('name', None)
    proxy_name = data.get('proxy_name', None)
    port = data.get('port', None)
    cpu = data.get('type', cpu)
    memory = data.get('memory', None)
    maxrss = data.get('maxrss', None)
    description = data.get('crawler_type', description)
    res = splash_manager.api_add_splash_docker(splash_name, proxy_name, port, cpu, memory, maxrss, description=description, edit=True)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# delete splash docker
@api.route("api/v1/splash/delete", methods=['POST'])
@token_required('admin')
def delete_splash():
    data = request.get_json()
    name = data.get('name', None)
    res = splash_manager.api_delete_splash_docker(proxy_name)
    return Response(json.dumps(res[0], indent=2, sort_keys=True), mimetype='application/json'), res[1]

# # TODO:

# test tor
# test regular

# add logger
