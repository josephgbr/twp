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
	
	$(document).on("click", ".kick-player", function() {
		var $this = $(this);
		var nickname = $(this).data('name');
		$this.addClass('disabled').html("<i class='fa fa-spinner fa-spin'></i>");
		$.post($SCRIPT_ROOT + '/_kick_player/'+$SRVID, 'nick='+encodeURIComponent(nickname), function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				window.location.reload();
			}
		});
	});
	
	$(document).on("click", ".ban-player", function() {
		var $this = $(this);
		var nickname = $(this).data('name');
		$this.addClass('disabled').html("<i class='fa fa-spinner fa-spin'></i>");
		$.post($SCRIPT_ROOT + '/_ban_player/'+$SRVID, 'nick='+encodeURIComponent(nickname), function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				window.location.reload();
			}
		});
	});
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