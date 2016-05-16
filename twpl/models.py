# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.3.0 - Teeworlds Web Panel
##    Copyright (C) 2016  Alexandre Díaz
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
from flask.ext.babel import Babel, _
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func, desc
from sqlalchemy.orm import Session
db = SQLAlchemy()

class JSONSERIALIZER(object):
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class AppWebConfig(db.Model):
    __tablename__ = 'app_web_config'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(16))
    brand_url = db.Column(db.String(512))
    installed = db.Column(db.Boolean, default=False)
    
class UserServerInstancePermission(db.Model, JSONSERIALIZER):
    __tablename__ = 'user_server_instance_permission'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    perm_id = db.Column(db.Integer, db.ForeignKey("permission_level.id"), nullable=False)

    server = db.relationship('ServerInstance', foreign_keys=server_id)
    user = db.relationship('User', foreign_keys=user_id)
    perm = db.relationship('PermissionLevel', foreign_keys=perm_id)
    
class PermissionLevel(db.Model, JSONSERIALIZER):
    __tablename__ = 'permission_level'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    start = db.Column(db.Boolean, default=False)
    stop = db.Column(db.Boolean, default=False)
    log = db.Column(db.Boolean, default=False)
    econ = db.Column(db.Boolean, default=False)
    config = db.Column(db.Boolean, default=False)
    issues = db.Column(db.Boolean, default=False)
        
    def sudo(self):
        self.start = True
        self.stop = True
        self.log = True
        self.econ = True
        self.config = True
        self.issues = True
        return self
    
class Issue(db.Model, JSONSERIALIZER):
    __tablename__ = 'issue'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    message = db.Column(db.String(512))
    
    server = db.relationship('ServerInstance', foreign_keys=server_id)
    
class PlayerServerInstance(db.Model, JSONSERIALIZER):
    __tablename__ = 'player_server_instance'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    name = db.Column(db.String(25), nullable=False)
    clan = db.Column(db.String(25))
    country = db.Column(db.Integer)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    
    server = db.relationship('ServerInstance', foreign_keys=server_id)
    
class Player(db.Model, JSONSERIALIZER):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=func.now())
    last_seen_date = db.Column(db.DateTime, nullable=False, default=func.now())
    status = db.Column(db.Integer, nullable=False)

class ServerJob(db.Model, JSONSERIALIZER):
    __tablename__ = 'server_job'
    id = db.Column(db.String(191), primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable = False)
    job_type = db.Column(db.Integer, nullable = False)
    job_exec = db.Column(db.String(4092))
    
    server = db.relationship('ServerInstance', foreign_keys=server_id)
    
class ServerStaffRegistry(db.Model, JSONSERIALIZER):
    __tablename__ = 'server_staff_registry'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=func.now())
    server_id = db.Column(db.Integer, db.ForeignKey("server_instance.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(1024), nullable=False)
    
    server = db.relationship('ServerInstance', foreign_keys=server_id)
    user = db.relationship('User', foreign_keys=user_id)
    
class ServerInstance(db.Model, JSONSERIALIZER):
    __tablename__ = 'server_instance'
    id = db.Column(db.Integer, primary_key=True)
    fileconfig = db.Column(db.String(128), nullable=False)
    base_folder = db.Column(db.String(512), nullable=False)
    bin = db.Column(db.String(128))
    alaunch = db.Column(db.Boolean, default=False)
    port = db.Column(db.String(4), default='8303')
    name = db.Column(db.String(128), default="Unnamed Server")
    status = db.Column(db.Integer, default=0)
    gametype = db.Column(db.String(16), default='DM')
    visible = db.Column(db.Boolean, default=True)
    public = db.Column(db.Boolean, default=True)
    logfile = db.Column(db.String(128))
    econ_port = db.Column(db.String(4))
    econ_password = db.Column(db.String(32))
    launch_date = db.Column(db.DateTime, nullable=True, default=func.now())
    
    perms = db.relationship("UserServerInstancePermission", cascade = "all,delete", backref=db.backref("server_instance"))
    srv_staff_reg = db.relationship("ServerStaffRegistry", cascade = "all,delete", backref=db.backref("server_instance"))
    srv_job = db.relationship("ServerJob", cascade = "all,delete", backref=db.backref("server_instance"))
    player_srv_inst = db.relationship("PlayerServerInstance", cascade = "all,delete", backref=db.backref("server_instance"))
    issues = db.relationship("Issue", cascade = "all,delete", backref=db.backref("server_instance"))
    
class User(db.Model, JSONSERIALIZER):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, nullable=False, default=func.now())
    last_login_date = db.Column(db.DateTime)
    username = db.Column(db.String(12), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    token = db.Column(db.String(128))
    
    perms = db.relationship("UserServerInstancePermission", cascade = "all,delete", backref=db.backref("users"))
    srv_staff_reg = db.relationship("ServerStaffRegistry", cascade = "all,delete", backref=db.backref("users"))
    