#!/usr/bin/env python3
# -*-coding:UTF-8 -*

import os
import sys
import ssl
import json
import random
import time

from flask import Flask, render_template, jsonify, request, Request, Response, session, redirect, url_for

# Import Blueprint
from api_blueprint import api

Flask_dir = os.path.dirname(os.path.realpath(__file__))

# CONFIG #
baseUrl = ''
# baseUrl = baseUrl.replace('/', '')
# if baseUrl != '':
#     baseUrl = '/'+baseUrl
#
# try:
#     FLASK_PORT = config_loader.get_config_int("Flask", "port")
# except Exception:
#     FLASK_PORT = 7000
FLASK_PORT = 7001

# =========  TLS  =========#
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_context.load_cert_chain(certfile=os.path.join(Flask_dir, 'server.crt'), keyfile=os.path.join(Flask_dir, 'server.key'))
# =========       =========#

app = Flask(__name__, static_url_path=baseUrl+'/static/')
app.config['MAX_CONTENT_LENGTH'] = 900 * 1024 * 1024

# =========  BLUEPRINT  =========#
app.register_blueprint(api, url_prefix=baseUrl)
# =========       =========#

# ========= session ========
app.secret_key = str(random.getrandbits(256))

# ========== ERROR HANDLER ============
@app.errorhandler(405)
def _handle_client_error(e):
    res_dict = {"status": "error", "reason": "Method Not Allowed: The method is not allowed for the requested URL"}
    return Response(json.dumps(res_dict, indent=2, sort_keys=True), mimetype='application/json'), 405

@app.errorhandler(404)
def error_page_not_found(e):
    return Response(json.dumps({"status": "error", "reason": "404 Not Found"}, indent=2, sort_keys=True), mimetype='application/json'), 404

# ============ MAIN ============
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=FLASK_PORT, threaded=True, ssl_context=ssl_context)
