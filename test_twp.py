# -*- coding: utf-8 -*-
#########################################################################################
##    TWP v0.1.0 - Teeworlds Web Panel
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
# UNIT TEST

import os
import shutil
import twp
from twpl.models import AppWebConfig, User
import unittest
import tempfile

class TWPTestCase(unittest.TestCase):

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def logout(self):
        return self.app.get('/logout', follow_redirects=True)
    
    def setUp(self):
        self.db_fd, dbfile = tempfile.mkstemp()
        twp.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % dbfile
        twp.app.config['TESTING'] = True
        twp.app.config['WTF_CSRF_ENABLED'] = False
        twp.app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        twp.app.config['SERVERS_BASEPATH'] = tempfile.mkdtemp()
        self.test_server_folder = r'%s/twsrv' % twp.app.config['SERVERS_BASEPATH']
        self.app = twp.app.test_client()
        twp.db_init()
        self.app.post('/_finish_installation', data=dict(
            adminuser='admin',
            adminpass='admin',
            brand='Testing',
        ), follow_redirects=True)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(twp.app.config['SQLALCHEMY_DATABASE_URI'])
        
    def test_login_logout(self):
        rv = self.login('admin', 'admin')
        assert 'You are logged in!' in rv.data
        self.logout()
        rv = self.login('1234', '1234')
        assert 'Invalid username or password!' in rv.data
        
    def test_servers(self):
        rv = self.app.get('/servers', follow_redirects=True)
        assert 'No servers found!' in rv.data
        os.mkdir(self.test_server_folder)
        
        ## CREATE SERVER INSTANCE
        # NO AUTH
        rv = self.app.post('/_create_server_instance/twsrv', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        self.login('admin', 'admin')
        rv = self.app.post('/_create_server_instance/twsrv', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'success' in rv.data
        self.logout()
        
        ## SET INSTANCE BINARY
        # NO AUTH
        rv = self.app.post('/_set_server_binary/1/teeworlds_srv', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        self.login('admin', 'admin')
        rv = self.app.post('/_set_server_binary/1/teeworlds_srv', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'invalidBinary' in rv.data
        with open(r'%s/teeworlds_srv' % self.test_server_folder, 'wb') as f:
            f.write(b"\x01\x02\x03");
        rv = self.app.post('/_set_server_binary/1/teeworlds_srv', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'success' in rv.data
        self.logout()
        
        
        ## SAVE SERVER CONFIG
        # NO AUTH
        rv = self.app.post('/_save_server_config', data=dict(
            srvid=1,
            alsrv=0,
            srvcfg=""
        ), follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        self.login('admin', 'admin')
        rv = self.app.post('/_save_server_config', data=dict(
            srvid=1,
            alsrv=0,
            srvcfg=u'sv_name test\nsv_port 8305'
        ), follow_redirects=True)
        assert 'success' in rv.data
        #- Special Characters
        self.login('admin', 'admin')
        rv = self.app.post('/_save_server_config', data=dict(
            srvid=1,
            alsrv=0,
            srvcfg=u'sv_name test\nsv_port 8305\nsv_motd éáçñèö'
        ), follow_redirects=True)
        assert 'success' in rv.data
        self.logout()
        
        ## GET SERVER CONFIG
        # NO AUTH
        rv = self.app.post('/_get_server_config/1', follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        self.login('admin', 'admin')
        rv = self.app.post('/_get_server_config/1', follow_redirects=True)
        assert 'sv_name test' in rv.data
        self.logout()
        
        ## START SERVER
        # NO AUTH
        rv = self.app.post('/_start_server_instance/1', follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        # TODO
        
        ## STOP SERVER
        # NO AUTH
        rv = self.app.post('/_stop_server_instance/1', follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        # TODO
        
        ## DELETE SERVER INSTANCE
        # NO AUTH
        rv = self.app.post('/_remove_server_instance/1/1', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'notauth' in rv.data
        # AUTH
        self.login('admin', 'admin')
        rv = self.app.post('/_remove_server_instance/1/1', data=dict(
            fileconfig='testsrv'
        ), follow_redirects=True)
        assert 'success' in rv.data
        self.logout()
        
    def test_players(self):
        rv = self.app.get('/players', follow_redirects=True)
        assert 'No players found!' in rv.data

class LoginSecurityTestCase(unittest.TestCase):

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def setUp(self):
        self.db_fd, dbfile = tempfile.mkstemp()
        twp.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % dbfile
        twp.app.config['TESTING'] = True
        twp.app.config['WTF_CSRF_ENABLED'] = False
        twp.app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        twp.app.config['SERVERS_BASEPATH'] = tempfile.mkdtemp()
        self.app = twp.app.test_client()
        twp.db_init()
        self.app.post('/_finish_installation', data=dict(
            adminuser='admin',
            adminpass='admin',
            brand='Testing',
        ), follow_redirects=True)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(twp.app.config['SQLALCHEMY_DATABASE_URI'])
        
    def test_login_security(self):
        rv = self.login('1234', '1234')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('12345', '12345')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('123456', '123456')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('1234567', '1234567')
        assert rv.status_code == 403
        
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TWPTestCase))
    suite.addTest(unittest.makeSuite(LoginSecurityTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')