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
from flask_wtf import Form
from wtforms import StringField, SubmitField, PasswordField, HiddenField
from wtforms.validators import InputRequired, EqualTo, url
from wtforms.fields.html5 import URLField
from flask_wtf.file import FileField


class LoginForm(Form):
    username = StringField(_('Username'), validators=[InputRequired()])
    password = PasswordField(_('Password'), validators=[InputRequired()])
    submit = SubmitField(_('Submit'))
    
class UserRegistrationForm(Form):
    username = StringField(_('Username'), validators=[InputRequired()])
    userpass = PasswordField(_('Password'), validators=[InputRequired(), EqualTo('ruserpass',message=_('Passwords must match'))])
    ruserpass = PasswordField(_('Repeat Password'), validators=[InputRequired()])
    submit = SubmitField(_('Finish'))

class InstallModForm(Form):
    file = FileField(_('From File'))
    url = HiddenField(_('From URL'), validators=[url()])