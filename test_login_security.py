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
import unittest
import tempfile

class TWPTestCase(unittest.TestCase):

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
    
    def setUp(self):
        self.db_fd, twp.app.config['DATABASE'] = tempfile.mkstemp()
        twp.app.config['TESTING'] = True
        twp.SERVERS_BASEPATH = tempfile.mkdtemp()
        self.app = twp.app.test_client()
        twp.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        
    def test_login_security(self):
        rv = self.login('1234', '1234')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('12345', '12345')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('123456', '123456')
        assert 'Invalid username or password!' in rv.data
        rv = self.login('1234567', '1234567')
        assert 'Banned' in rv.data


if __name__ == '__main__':
    unittest.main()