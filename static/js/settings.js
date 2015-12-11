"use strict";
/*
 ********************************************************************************************
 **    TWP v0.1.0 - Teeworlds Web Panel
 **    Copyright (C) 2015  Alexandre Díaz
 **
 **    This program is free software: you can redistribute it and/or modify
 **    it under the terms of the GNU Affero General Public License as
 **    published by the Free Software Foundation, either version 3 of the
 **    License.
 **
 **    This program is distributed in the hope that it will be useful,
 **    but WITHOUT ANY WARRANTY; without even the implied warranty of
 **    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 **    GNU Affero General Public License for more details.
 **
 **    You should have received a copy of the GNU Affero General Public License
 **    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 ********************************************************************************************
 */
$(function(){
	
	$(document).on('click', "#form-settings-admin-pass a[id='btn-submit']", function(e){
		var passOld = $('#admin-pass-old').val();
		var passNew = $('#admin-pass-new').val();
		var passNewRepeat = $('#admin-pass-new-repeat').val();
		
		// Validate Form
		$('#admin-pass-old,#admin-pass-new,#admin-pass-new-repeat').tooltip('hide');
		if (!passOld)
		{
			$('#admin-pass-old').tooltip({trigger:'manual', placement:'bottom', title:"Can't be empty"});
			$('#admin-pass-old').tooltip('show');
			return;
		}
		if (!passNew)
		{
			$('#admin-pass-new').tooltip({trigger:'manual', placement:'bottom', title:"Can't be empty"});
			$('#admin-pass-new').tooltip('show');
			return;
		}
		if (!passNewRepeat)
		{
			$('#admin-pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:"Can't be empty"});
			$('#admin-pass-new-repeat').tooltip('show');
			return;
		}
		if (passNew !== passNewRepeat)
		{
			$('#admin-pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:'Passwords not match!'});
			$('#admin-pass-new-repeat').tooltip('show');
			return;
		}
		//
		
		hashObj = new jsSHA("SHA-512", "TEXT");
		hashObj.update(passNew);
		passNew = hashObj.getHash("HEX");
		
		$.post($SCRIPT_ROOT + '/_set_user_password/1', 'pass_old='+passOld+'&pass_new='+passNew, function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				$('#admin-pass-old,#admin-pass-new,#admin-pass-new-repeat').val('');
				alert("Password changed successfully :)");
			}
		});
	});
	
});
