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
function refreshMemoryHost(){
	$.post($SCRIPT_ROOT + '/_refresh_memory_host', '', function(data) {
		check_server_data(data);
		
		$('#memory-usage').text(data.used +' / '+ data.total +' MB').fadeIn();
		$('#memory-usage-bar').css({'width':data.percent+'%'});
		$('#memory-cache-usage-bar').css({'width':data.percent_cached+'%'});
	});
}
function refreshCPUHost(){
	$.post($SCRIPT_ROOT + '/_refresh_cpu_host', '', function(data) {
		check_server_data(data);
		
		$('#cpu-usage').text(data +'%').fadeIn();
		$('#cpu-usage-bar').css({'width':data +'%'});
	});
}
function refreshDiskHost(){
	$.post($SCRIPT_ROOT + '/_refresh_disk_host', '', function(data) {
		check_server_data(data);
		
		$('#disk-usage').text(data.used+' ('+data.free+' '+$BABEL_STR_FREE+')').fadeIn();
		$('#disk-usage-bar').css({'width':data.percent});
	});
}
function refreshUptimeHost(){
	$.post($SCRIPT_ROOT + '/_refresh_uptime_host', '', function(data) {
		check_server_data(data);
		
		$('#uptime').text($BABEL_STR_UPTIME+' '+data.day+' '+$BABEL_STR_DAYS+' '+data.time).fadeIn();
	});
}
function memory_color(value){
	if(value != 0)
		if ('0' <= value && value <= '512')
			 return 'success';
		else if ('512' <= value && value < '1024')
			return 'warning';
		else
			return 'important';
}
function mastersrv_servers(){
	$.post($SCRIPT_ROOT + '/_get_all_online_servers', '', function(data) {
		check_server_data(data);
		$('#twmslist-load').hide();
		
		if (data['servers'].length > 0)
		{
			var $table = $('#twmslist tbody');
			var cont = 0;
			for (reg in data['servers']) {
				var row = "<tr>";
				row += "<td>"+reg+"</td>";
				row += "<td>"+data['servers'][reg].name+"</td>";
				row += "<td>"+data['servers'][reg].gametype+"</td>";
				row += "<td>"+data['servers'][reg].players+"/"+data['servers'][reg].max_players+"</td>";
				row += "<td>"+data['servers'][reg].map+"</td>";
				row += "<td class='text-right'>"+Math.round(data['servers'][reg].latency*1000)+"</td>";
				row += "</tr>";
				$table.append(row);
			}
			$('#twmslist').show();
		}
		else
		{
			$('#twmslist-empty').show();
		}
	});
}
function refresh(){
	refreshMemoryHost();
	refreshCPUHost();
	refreshDiskHost();
	refreshUptimeHost();
}
$(function() {
	$('#memory-usage').hide();
	$('#cpu-usage').hide();
	$('#disk-usage').hide();
	$('#uptime').hide();
	$('#twmslist').hide();
	$('#twmslist-empty').hide();
	
	refresh();
	mastersrv_servers();
	window.setInterval('refresh()', $REFRESH_TIME);
	
	$.post($SCRIPT_ROOT + '/_get_chart_values/machine', '', function(data) {
		// Players last 7days
		var chartData = [];
		for (var i in data['labels']['players7d'])
		{
			chartData.push({
				a: data['values']['players7d'][i],
				x: data['labels']['players7d'][i]
			});
		}
		Morris.Line({
			  element: 'chart-machine-players7d',
			  data: chartData,
			  xkey: 'x',
			  ykeys: ['a'],
			  labels: [$BABEL_STR_PLAYERS],
			  resize: true,
			  dateFormat: function (x) {
				  	var d = new Date(x);
					var curr_date = d.getDate();
					var curr_month = d.getMonth() + 1; //Months are zero based
					var curr_year = d.getFullYear();
					return curr_date + "-" + curr_month + "-" + curr_year; 
			  }
		});
	});
});