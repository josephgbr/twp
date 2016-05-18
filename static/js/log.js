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
var $LOG_PAGINATION = [moment(new Date()).format("DD-MM-YYYY"),0] // cur. page

$(function(){
	
	if ($('#server-log').length)
	{
		// Refresh log
		get_server_instance_log();
	}
	
	$(document).on('click', '#log .pagination li>a', function(ev){
		var $this = $(this);
		var page = $this.data('page');
		
		if ('prev' == page)
		{
			if ($LOG_PAGINATION[0] > 0)
				--$LOG_PAGINATION[0];
		} else if ('next' == page)
		{
			if ($LOG_PAGINATION[0] < $LOG_PAGINATION[1])
				++$LOG_PAGINATION[0];
		}
		else
			$LOG_PAGINATION[0] = page;
		
		get_server_instance_log();
		ev.preventDefault();
	});
	
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
	$.post($SCRIPT_ROOT + '/_get_server_instance_log/'+$SRVID+'/'+$LOG_PAGINATION[0], '', function(data) {
		check_server_data(data);

		if (data['success'] && data['content'])
		{
			$('#server-log').html("");
			
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
			
			if (data['pages'])
			{
				var datepages = Object.keys(data['pages']).reverse();
				var curIndex = datepages.indexOf($LOG_PAGINATION[0]);
				$LOG_PAGINATION[1] = datepages.length-1;
				$('#server-log').prop('scrollTop', $('#server-log').prop('scrollHeight'));
				
				var html = "<li class='"+(0==curIndex?'disabled':'')+"'><a href='#' data-page='prev' aria-label='Previous'><span aria-hidden='true'>&laquo;</span></a></li>";
				var start_page = Math.max(0, curIndex-3);
				var end_page = Math.min(curIndex+3, $LOG_PAGINATION[1]);
				if (end_page < 7 && $LOG_PAGINATION[1] >= 7)
					end_page = 6;
				for (var i=start_page;i<=end_page;i++)
					html += "<li class='"+(i==curIndex?'active':'')+"'><a data-page='"+datepages[i]+"' href='#'>"+datepages[i]+"</a></li>";
				html += "<li class='"+(curIndex==$LOG_PAGINATION[1]?'disabled':'')+"'><a href='#' data-page='next' aria-label='Next'><span aria-hidden='true'>&raquo;</span></a></li>";
				$('#log .pagination').html(html);
			}
		}
	});
}