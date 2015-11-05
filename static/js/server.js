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
	
	$(document).on("keypress", ".deny-enter :input:not(textarea)", function(ev) {
	    if (ev.keyCode == 13) {
	        ev.preventDefault();
	    }
	});
	
	if ($('#server-log').length)
	{
		get_server_instance_log();
		window.setInterval('get_server_instance_log()', 2000);
	}
});

var $LOGSEEK = 0;
function get_server_instance_log()
{
	$.getJSON($SCRIPT_ROOT + '/_get_server_instance_log/'+$SRVID+'/'+$LOGSEEK, function(data) {
		check_server_data(data);

		if (data['success'])
		{
			var curtext = $('#server-log').val();
			$('#server-log').append(data['content'])
			$LOGSEEK = data['seek'];
			$('#server-log').prop('scrollTop', $('#server-log').prop('scrollHeight'));
		}
	});
}