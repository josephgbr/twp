# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.3.0 - Teeworlds Web Panel
##    Copyright (C) 2015  Alexandre Díaz
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU Affero General Public License as
##    published by the Free Software Foundation, either version 3 of the
##    License.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU Affero General Public License for more details.
##
##    You should have received a copy of the GNU Affero General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.    
#########################################################################################
import twpl
from twp import twp, BANLIST, PUBLIC_IP, SUPERUSER_ID, flash_errors, get_session_user,\
                get_session_server_permission_level
import time
from datetime import datetime, timedelta
from mergedict import ConfigDict
from flask import request, session, redirect, url_for, abort, render_template, \
                  flash, jsonify, send_file, current_app
from flask.ext.babel import Babel, _, format_datetime
from sqlalchemy import or_, func, desc
from twpl import BannerGenerator
from twpl.models import *


#################################
# TOOLS
#################################
def get_login_tries():
    return int(session.get('login_try')) if 'login_try' in session else 0

#################################
# GET
#################################
@twp.route("/install", methods=['GET'])
def installation():
    app_config = AppWebConfig.query.get(1)
    if app_config.installed:
        abort(404)
    return render_template('pages/install.html', appconfig = app_config)

@twp.route("/", methods=['GET'])
def overview():
    session['prev_url'] = request.path;
    return render_template('pages/index.html', dist=twpl.get_linux_distribution(), ip=PUBLIC_IP)

@twp.route('/search', methods=['GET'])
def search():
    servers = list()
    players = list()
    searchword = request.args.get('r', '')

    sk = "%%%s%%" % searchword
    servers = ServerInstance.query.filter(or_(ServerInstance.name.like(sk), 
                                                          ServerInstance.base_folder.like(sk))).all()
    players = Player.query.filter(Player.name.like(sk)).all()
    return render_template('pages/search.html', search=searchword, servers=servers, players=players)

@twp.route('/players', methods=['GET'])
def players():
    session['prev_url'] = request.path;
    
    players = Player.query.order_by(desc(Player.last_seen_date)).order_by(desc(Player.name)).all()
    return render_template('pages/players.html', players=players)

@twp.route('/maps', methods=['GET'])
def maps():
    session['prev_url'] = request.path;
    return redirect(url_for('twp.overview'))

@twp.route('/servers', methods=['GET'])
def servers():
    session['prev_url'] = request.path;

    ServerInstance.query.update({ServerInstance.status:0})
    db.session.commit()
    
    from twpl.forms import InstallModForm
    install_mod_form = InstallModForm()

    netstat = twpl.netstat()
    for conn in netstat:
        if not conn[2]:
            continue
        (rest,base_folder,bin) = conn[2].rsplit('/', 2)
        srv = ServerInstance.query.filter(ServerInstance.port.ilike(conn[0]), 
                                                      ServerInstance.base_folder.ilike(base_folder), 
                                                      ServerInstance.bin.ilike(bin))
        if srv.count() > 0:
            srv = srv.one()
            net_server_info = twpl.get_server_net_info("127.0.0.1", [srv])[0]
            # FIXME: Check info integrity
            if net_server_info and net_server_info['netinfo'].gametype:
                srv.status = 1
                srv.name = net_server_info['netinfo'].name
                srv.gametype = net_server_info['netinfo'].gametype
                db_add_and_commit(srv)
                
    flash_errors(install_mod_form)
    return render_template('pages/servers.html', 
                           servers=twpl.get_local_servers(current_app.config['SERVERS_BASEPATH']),
                           install_mod_form=install_mod_form)
    
@twp.route('/server/<int:srvid>', methods=['GET'])
def server(srvid):
    session['prev_url'] = request.path;
    srv = ServerInstance.query.get(srvid)

    netinfo = None
    if srv:
        netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
    else:
        flash(_('Server not found!'), "danger")
        
    users_reg = ServerStaffRegistry.query.filter(ServerStaffRegistry.server_id==srvid)\
                                                .order_by(desc(ServerStaffRegistry.date)).all()
    return render_template('pages/server.html', ip=PUBLIC_IP, server=srv, netinfo=netinfo, 
                           uidperms=get_session_server_permission_level(srv.id),
                           users_reg=users_reg)

@twp.route('/server/<int:srvid>/banner', methods=['GET'])
def generate_server_banner(srvid):
    srv = ServerInstance.query.get(srvid)
    if srv:
        netinfo = twpl.get_server_net_info("127.0.0.1", [srv])[0]['netinfo']
        banner_image = BannerGenerator((600, 40), srv, netinfo)
        
        if 'title' in request.values:
            banner_image.titleColor = twpl.HTMLColorToRGBA(request.values.get('title'))
        if 'detail' in request.values:
            banner_image.detailColor = twpl.HTMLColorToRGBA(request.values.get('detail'))
        if 'address' in request.values:
            banner_image.addressColor = twpl.HTMLColorToRGBA(request.values.get('address'))
        if 'grads' in request.values:
            banner_image.gradStartColor = twpl.HTMLColorToRGBA(request.values.get('grads'))
        if 'grade' in request.values:
            banner_image.gradEndColor = twpl.HTMLColorToRGBA(request.values.get('grade'))
        
        return send_file(banner_image.generate(PUBLIC_IP), as_attachment=False)

@twp.route('/login', methods=['GET', 'POST'])
def login():
    if not BANLIST.find(request.remote_addr) and get_login_tries() >= current_app.config['LOGIN_MAX_TRIES']:
        BANLIST.add(request.remote_addr, current_app.config['LOGIN_BAN_TIME']);
        session['login_try'] = 0;
        abort(403)

    from twpl.forms import LoginForm
    login_form = LoginForm()
    
    if request.method == 'POST':
        if login_form.validate_on_submit():
            request_username = request.form['username']
            request_passwd = twpl.str_sha512_hex_encode(request.form['password'])
    
            current_url = session['prev_url'] if 'prev_url' in session else url_for('twp.overview')
    
            dbuser = User.query.filter(User.username.like(request_username), 
                                       User.password.like(request_passwd))
            if dbuser.count() > 0:
                dbuser = dbuser.one()
                session['logged_in'] = True
                session['uid'] = dbuser.id
                session['last_activity'] = int(time.time())
                session['username'] = dbuser.username
                session.pop('timezone', None)
                flash(_('You are logged in!'), 'success')
                
                dbuser.last_login_date = func.now()
                db_add_and_commit(dbuser)
    
                if current_url == url_for('twp.login'):
                    return redirect(url_for('twp.overview'))
                return redirect(current_url)
    
            session['login_try'] = get_login_tries()+1
            session['last_login_try'] = int(time.time())
            flash(_('Invalid username or password! ({0}/{1})').format(get_login_tries(),
                                                                      current_app.config['LOGIN_MAX_TRIES']), 'danger')
    flash_errors(login_form)
    return render_template('pages/login.html', login_form=login_form)

@twp.route('/logout', methods=['GET'])
def logout():
    current_url = session['prev_url'] if 'prev_url' in session else url_for('twp.overview')
    
    session.pop('logged_in', None)
    session.pop('last_activity', None)
    session.pop('name', None)
    session.pop('prev_url', None)
    session.pop('login_try', None)
    session.pop('last_login_try', None)
    session.pop('uid', None)
    session.pop('timezone', None)
    flash(_('You are logged out!'), 'success')
    return redirect(url_for('twp.overview'))

@twp.route('/user_reg/<string:token>', methods=['GET', 'POST'])
def user_reg(token):
    user = User.query.filter(User.token.like(token))
    if user.count() < 1:
        abort(403)
    user = user.one()
    from twpl.forms import UserRegistrationForm
    user_reg_form = UserRegistrationForm()

    if request.method == 'POST':
        if not user_reg_form.validate_on_submit():
            flash_errors(user_reg_form)
            return render_template('pages/user_register.html', user=user, reg_form=user_reg_form, last_page=True)
        user_count = User.query.filter(User.username.ilike(request.form['username'])).count()
        if user_count > 0:
            flash(_('Username already in use!'), 'danger')
            return render_template('pages/user_register.html', user=user, reg_form=user_reg_form, last_page=True)
        user.token = None
        user.password = twpl.str_sha512_hex_encode(request.form['userpass'])
        user.username = request.form['username']
        db_add_and_commit(user)
        return redirect(url_for('twp.login'))
    return render_template('pages/user_register.html', user=user, reg_form=user_reg_form)


#################################
# POST
#################################
@twp.route('/_finish_installation', methods=['POST'])
def finish_installation():
    app_config = AppWebConfig.query.get(1)
    if app_config.installed:
        abort(404)
        
    adminuser = request.form['adminuser'] if request.form.has_key('adminuser') else None
    adminpass = request.form['adminpass'] if request.form.has_key('adminpass') else None
    if not adminuser or not adminpass or User.query.count() != 0:
        return jsonify({ 'error':True, 'errormsg':_('Missed params!') })
    
    app_config.brand = request.form['brand'] if 'brand' in request.form else ''
    if 'brand-url' in request.form.keys():
        app_config.brand_url = request.form['brand-url']
    app_config.installed = True
    db_add_and_commit(app_config)
    admin_user = User(username=adminuser, password=twpl.str_sha512_hex_encode(adminpass))
    db_add_and_commit(admin_user)
    return jsonify({ 'success':True })

@twp.route('/_refresh_cpu_host', methods=['POST'])
def refresh_cpu_host():
    if 'logged_in' in session and session['logged_in']:
        return twpl.host_cpu_percent()
    return jsonify({})

@twp.route('/_refresh_uptime_host', methods=['POST'])
def refresh_uptime_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_uptime())
    return jsonify({})

@twp.route('/_refresh_disk_host', methods=['POST'])
def refresh_disk_host():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_disk_usage(partition=current_app.config['PARTITION']))
    return jsonify({})

@twp.route('/_refresh_memory_host', methods=['POST'])
def refresh_memory_containers():
    if 'logged_in' in session and session['logged_in']:
        return jsonify(twpl.host_memory_usage())
    return jsonify({})

@twp.route('/_refresh_host_localtime', methods=['POST'])
def refresh_host_localtime():
    dt = datetime.utcnow()
    #return jsonify(twpl.host_localtime())
    return jsonify({'localtime':format_datetime(dt, 'short'), 'localzone':format_datetime(dt, "z")})

@twp.route('/_get_all_online_servers', methods=['POST'])
def get_all_online_servers():
    return jsonify(twpl.get_tw_masterserver_list(PUBLIC_IP))

@twp.route('/_get_chart_values/<string:chart>', methods=['POST'])
@twp.route('/_get_chart_values/<string:chart>/<int:srvid>', methods=['POST'])
def get_chart_values(chart, srvid=None):
    today = datetime.now()
    startday = today - timedelta(days=6)
    allowed_dates = [(startday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, 7)]
    labels = dict()
    values = dict()
    
    if chart.lower() == 'server':
        labels['players7d'] = list()
        values['players7d'] = list()
        # TODO: Filter only from today-7 to today...
        players = PlayerServerInstance.query.filter(PlayerServerInstance.server_id==srvid,
                                                    PlayerServerInstance.date >= startday).all()
        if not players:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        chart_data = ConfigDict()
        for dbplayer in players:
            strdate = dbplayer.date.strftime("%Y-%m-%d")
            if not strdate in allowed_dates:
                continue
            if not strdate in chart_data.keys() or not dbplayer.name in chart_data[strdate]:
                chart_data.merge({strdate:[dbplayer.name]})
        for secc in allowed_dates:
            labels['players7d'].append(secc)
            values['players7d'].append(len(chart_data[secc]) if secc in chart_data else 0)
        
        query_data = db.session.execute("SELECT count(clan) as num, clan FROM \
                                        (SELECT DISTINCT name,clan,server_id FROM player_server_instance \
                                        WHERE clan IS NOT NULL) as tbl WHERE tbl.server_id=:id GROUP BY clan \
                                        ORDER BY num DESC LIMIT 5", {"id":srvid})
        if query_data:
            labels['topclan'] = list()
            values['topclan'] = list()
            for value in query_data:
                if not value.clan < 1:
                    labels['topclan'].append(value.clan)
                    values['topclan'].append(value.num)
                
        query_data = db.session.execute("SELECT count(country) as num, country FROM \
                                        (SELECT DISTINCT name,country,server_id FROM player_server_instance \
                                        WHERE country IS NOT NULL) as tbl WHERE tbl.server_id=:id GROUP BY country \
                                        ORDER BY num DESC LIMIT 5", {"id":srvid})
        if query_data:
            labels['topcountry'] = list()
            values['topcountry'] = list()
            for value in query_data:
                if not value.country < 1:
                    labels['topcountry'].append(value.country)
                    values['topcountry'].append(value.num)
            
        return jsonify({'success':True, 'series':values, 'labels':labels})
    elif chart.lower() == 'machine':
        labels['players7d'] = list()
        values['players7d'] = list()
        players = PlayerServerInstance.query.filter(PlayerServerInstance.date >= startday).all()
        if not players:
            return jsonify({'error':True, 'errormsg':_('Invalid Operation: Server not found!')})
        chart_data = ConfigDict()
        for dbplayer in players:
            strdate = dbplayer.date.strftime("%Y-%m-%d")
            if not strdate in allowed_dates:
                continue
            if not strdate in chart_data.keys() or not dbplayer.name in chart_data[strdate]:
                chart_data.merge({strdate:[dbplayer.name]})
        for secc in allowed_dates:
            labels['players7d'].append(secc)
            values['players7d'].append(len(chart_data[secc]) if secc in chart_data else 0)
        return jsonify({'success':True, 'series':values, 'labels':labels})
    return jsonify({'error':True, 'errormsg':_('Undefined Chart!')})

@twp.route('/_get_server_instances_online', methods=['POST'])
def get_server_instances_online():
    servers = ServerInstance.query.filter(ServerInstance.status==1)
    return jsonify({'success':True, 'num':servers.count()})

@twp.route('/_set_timezone', methods=['POST'])
def set_timezone():
    tzstr = request.form['tzstr'] if 'tzstr' in request.form else None
    if not tzstr:
        return jsonify({'error':True, 'errormsg':_('Invalid TimeZone!')})
    
    sess_user = get_session_user()
    if sess_user:
        sess_user.timezone = tzstr
        db_add_and_commit(sess_user)
    else:
        session['timezone'] = tzstr
    return jsonify({'success':True})