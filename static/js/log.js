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
var $LOG_FILTER_TYPE = 0; // All
var $LOG_FILTER_ORDER = 0; // Desc

$(function(){
	
	// Prevent Enter Submit
	$(document).on("keypress", ".deny-enter :input:not(textarea)", function(ev) {
	    if (ev.keyCode == 13) {
	        ev.preventDefault();
	    }
	});
	
	if ($('#server-log').length)
	{
		// Refresh log
		get_server_instance_log();
	}
	
	// Filter
	$("#filter-type").val($LOG_FILTER_TYPE).change(function(){
		$LOG_FILTER_TYPE = $(this).val();
		$('#server-log').html("");
		get_server_instance_log();
	});
	$("#filter-order").val($LOG_FILTER_ORDER).change(function(){
		$LOG_FILTER_ORDER = $(this).val();
		$('#server-log').html("");
		get_server_instance_log();
	});
});

function get_server_instance_log()
{
	console.log("SSS");
	
	$.post($SCRIPT_ROOT + '/_get_server_instance_log/'+$SRVID+'/'+$SRVLOGCODE+'/'+$SRVLOGNAME, '', function(data) {
		check_server_data(data);

		if (data['success'] && data['content'])
		{
			var curtext = $('#server-log').val();
			
			for (var i in data['content']) {
				var table_row = "<tr class='"+data['content'][i]['type']+"'><td>"+data['content'][i]['date']+"</td><td>"+data['content'][i]['section']+"</td><td>"+data['content'][i]['message']+"</td></tr>";
				if ($LOG_FILTER_TYPE == 0 
					|| ($LOG_FILTER_TYPE == 1 && data['content'][i]['type'] == 'danger')
					|| ($LOG_FILTER_TYPE == 2 && data['content'][i]['type'] == 'warning')
					|| ($LOG_FILTER_TYPE == 3 && data['content'][i]['type'] == 'success'))
					{
						if ($LOG_FILTER_ORDER == 0)
							$('#server-log').prepend(table_row);
						else
							$('#server-log').append(table_row);
					}
			}

			$('#server-log').prop('scrollTop', $('#server-log').prop('scrollHeight'));
		}
	});
}