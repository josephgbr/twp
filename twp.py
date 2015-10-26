#!/usr/bin/env python
# -*- coding: utf-8 -*-
import twp
import subprocess, time, re, hashlib, sqlite3, os, json
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
from requests import get
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


# Configuration
config = configparser.SafeConfigParser()
config.readfp(open('twp.conf'))

SECRET_KEY = '\xb13\xb6\xfb+Z\xe8\xd1n\x80\x9c\xe7KM\x1c\xc1\xa7\xf8\xbeY\x9a\xfa<.'

TWP_INFO = {
    'version':'0.1.0',
    'refresh_time':config.getint('global', 'refresh_time')
}
DEBUG = config.getboolean('global', 'debug')
HOST = config.get('global', 'host')
PORT = config.getint('global', 'port')
DATABASE = config.get('database', 'file')


# Start Flask App
app = Flask(__name__)
app.config.from_object(__name__)


# SQLite
def connect_db():
    '''
    SQLite3 connect function
    '''

    return sqlite3.connect(app.config['DATABASE'])

def query_db(query, args=(), one=False):
    '''
    SQLite3 query function
    '''
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
          for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv


# App Callbacks
@app.before_request
def before_request():
    '''
    executes functions before all requests
    '''

    check_session_limit()
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    '''
    executes functions after all requests
    '''

    if hasattr(g, 'db'):
        g.db.close()
        

# Routes
@app.route("/")
@app.route("/overview")
def overview():
    return render_template('index.html', twp=TWP_INFO, dist=twp.get_linux_distribution(), ip=get_public_ip())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        app.logger.debug('A value for debugging')
        request_username = request.form['username']
        request_passwd = str_to_hash(request.form['password'])

        current_url = request.form['url']

        user = query_db('select username from users where username=? and password=?', [request_username, request_passwd], one=True)

        if user:
            session['logged_in'] = True
            session['last_activity'] = int(time.time())
            session['username'] = user['username']
            flash(u'You are logged in!', 'success')

            if current_url == url_for('login'):
                return redirect(url_for('overview'))
            return redirect(current_url)

        flash(u'Invalid username or password!', 'danger')
    return render_template('login.html', twp=TWP_INFO)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('last_activity', None)
    session.pop('name', None)
    flash(u'You are logged out!', 'success')
    return redirect(url_for('overview'))

@app.route('/about')
def about():
    return redirect(url_for('overview'))

@app.route('/servers')
def servers():
    servers = query_db('select * from servers')
    return render_template('servers.html', twp=TWP_INFO, gm_configs=twp.get_gametypes_configs(), servers=servers)

@app.route('/players')
def players():
    return render_template('index.html', twp=TWP_INFO)

@app.route('/maps')
def maps():
    return render_template('index.html', twp=TWP_INFO)


@app.route('/_refresh_cpu_host')
def refresh_cpu_host():
    return twp.host_cpu_percent()

@app.route('/_refresh_uptime_host')
def refresh_uptime_host():
    return jsonify(twp.host_uptime())

@app.route('/_refresh_disk_host')
def refresh_disk_host():
    return jsonify(twp.host_disk_usage(partition=config.get('overview', 'partition')))

@app.route('/_refresh_memory_host')
def refresh_memory_containers():
    return jsonify(twp.host_memory_usage())

@app.route('/_get_gametype_attrs/<gm>')
def get_gametype_attrs(gm):
    filename = '/configs/%s.json' % gm
    with open(filename) as f:
        return f.read()
    return []

@app.route('/_get_all_online_servers')
def get_all_online_servers():
    return jsonify(twp.get_tw_masterserver_list())
    

# Security Checks
def check_session_limit():
    if 'logged_in' in session and session.get('last_activity') is not None:
        now = int(time.time())
        limit = now - 60 * config.getint('session', 'time')
        last_activity = session.get('last_activity')
        if last_activity < limit:
            flash(u'Session timed out!', 'info')
            logout()
        else:
            session['last_activity'] = now
            
            
# Tools
def str_to_hash(strIn):
    return hashlib.sha512(strIn.encode()).hexdigest()

def get_public_ip():
    return get('https://api.ipify.org').text


# Init Module
if __name__ == "__main__":
    app.run(host=app.config['HOST'], port=app.config['PORT'])
