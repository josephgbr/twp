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
		window.setInterval('get_server_instance_log()', 2000);
	}
	
	// Kick Player
	$(document).on("click", ".kick-player", function() {
		var $this = $(this);
		var nickname = $(this).data('name');
		$this.addClass('disabled').html("<i class='fa fa-spinner fa-spin'></i>");
		$.post($SCRIPT_ROOT + '/_kick_player/'+$SRVID, 'nick='+encodeURIComponent(nickname), function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				$this.parent().parent().remove();
			}
		});
	});
	
	// Ban Player
	$(document).on("click", ".ban-player", function() {
		var $this = $(this);
		var nickname = $(this).data('name');
		$this.addClass('disabled').html("<i class='fa fa-spinner fa-spin'></i>");
		$.post($SCRIPT_ROOT + '/_ban_player/'+$SRVID, 'nick='+encodeURIComponent(nickname), function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				$('#pl-line-'+nickname).remove();
			}
		});
	});
	
	// Charts
	$.post($SCRIPT_ROOT + '/_get_chart_values/server/'+$SRVID, '', function(data) {
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
			  element: 'chart-players-7d',
			  data: chartData,
			  xkey: 'x',
			  ykeys: ['a'],
			  labels: ['Players'],
			  resize: true,
			  dateFormat: function (x) {
				  	var d = new Date(x);
					var curr_date = d.getDate();
					var curr_month = d.getMonth() + 1; //Months are zero based
					var curr_year = d.getFullYear();
					return curr_date + "-" + curr_month + "-" + curr_year; 
			  }
		});
		
		var chartColors = ['#F7464A', '#46BFBD', '#FDB45C', '#A7464A', '#37464A'];
		// Top Clans
		var chartTopClanData = [];
		for (var i in data['labels']['topclan'])
		{
			var clanName = data['labels']['topclan'][i];
			if (!clanName || !clanName[0])
				clanName = "Unknown";
			
			chartTopClanData.push({
				value: data['values']['topclan'][i],
				label: clanName
			});
		}
		Morris.Donut({
			element: 'chart-active-clan',
			data: chartTopClanData,
			colors: chartColors,
			resize: true
		});
		
		// Top Countries
		var chartTopCountryData = [];
		for (var i in data['labels']['topcountry'])
		{
			var countryName = undefined;
			if (data['labels']['topcountry'][i] != -1)
				countryName = $.grep($COUNTRIES, function(e){ return e.codenum == data['labels']['topcountry'][i]; });
			
			if (!countryName || !countryName[0])
				countryName = "Unknown";
			else
				countryName = countryName[0].name;
				
			chartTopCountryData.push({
				value: data['values']['topcountry'][i],
				label: countryName
			});
		}
		Morris.Donut({
			element: 'chart-active-country',
			data: chartTopCountryData,
			colors: chartColors,
			resize: true
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
			
			console.log(data['content']);
			for (i in data['content']) {
				$('#server-log').append("<tr class='"+data['content'][i]['type']+"'><td>"+data['content'][i]['date']+"</td><td>"+data['content'][i]['section']+"</td><td>"+data['content'][i]['message']+"</td></tr>");
			}
			$LOGSEEK = data['seek'];
			$('#server-log').prop('scrollTop', $('#server-log').prop('scrollHeight'));
		}
	});
}