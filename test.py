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
import twp
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
        twp.app.config['TESTING'] = True
        self.app = twp.app.test_client()

    #def tearDown(self):
        #os.close(self.db_fd)
        
    def test_login_logout(self):
        rv = self.login('admin', 'admin')
        assert 'You are logged in!' in rv.data
        rv = self.logout()

if __name__ == '__main__':
    unittest.main()