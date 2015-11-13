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
	var ctxChartPlayers7d = document.getElementById('chart-players-7d').getContext('2d');
	var ctxChartActiveClan = document.getElementById('chart-active-clan').getContext('2d');
	var ctxChartActiveCountry = document.getElementById('chart-active-country').getContext('2d');
	$.post($SCRIPT_ROOT + '/_get_chart_values/server/'+$SRVID, '', function(data) {
		var chartData = {
		    labels: data['labels']['players7d'],
		    datasets: [
		        {
		            label: "Players Count",
		            fillColor: "rgba(220,220,220,0.2)",
		            strokeColor: "rgba(220,220,220,1)",
		            pointColor: "rgba(220,220,220,1)",
		            pointStrokeColor: "#fff",
		            pointHighlightFill: "#fff",
		            pointHighlightStroke: "rgba(220,220,220,1)",
		            data: data['values']['players7d']
		        }
		    ]
		};
		
		var chartColors = [['#F7464A','#FF5A5E'], ['#46BFBD','#5AD3D1'], ['#FDB45C','#FFC870'], ['#A7464A','#AF5A5E'], ['#37464A','#3F5A5E']];
		var chartTopClanData = [];
		var chartTopCountryData = [];
		for (i in data['labels']['topclan'])
		{
			chartTopClanData.push({
				value: data['values']['topclan'][i],
				color: chartColors[i][0],
				highlight: chartColors[i][1],
				label: data['labels']['topclan'][i]
			});
		}
		for (i in data['labels']['topcountry'])
		{
			countryName = undefined;
			if (data['labels']['topcountry'][i] != -1)
				countryName = $.grep($COUNTRIES, function(e){ return e.codenum == data['labels']['topcountry'][i]; });
			
			if (!countryName || !countryName[0])
				countryName = "Unknown";
			else
				countryName = countryName[0].name;
				
			chartTopCountryData.push({
				value: data['values']['topcountry'][i],
				color: chartColors[i][0],
				highlight: chartColors[i][1],
				label: countryName
			});
		}
		
		var chartOptions = {
			responsive: true,
		    scaleShowGridLines : true,
		    scaleGridLineColor : "rgba(0,0,0,.05)",
		    scaleGridLineWidth : 1,
		    scaleShowHorizontalLines: true,
		    scaleShowVerticalLines: true,
		    bezierCurve : true,
		    bezierCurveTension : 0.4,
		    pointDot : true,
		    pointDotRadius : 4,
		    pointDotStrokeWidth : 1,
		    pointHitDetectionRadius : 20,
		    datasetStroke : true,
		    datasetStrokeWidth : 2,
		    datasetFill : true,
		};
		var chartPlayers7d = new Chart(ctxChartPlayers7d).Line(chartData, chartOptions);
		var chartActiveClan = new Chart(ctxChartActiveClan).Doughnut(chartTopClanData, {responsive: true});
		var chartActiveCountry = new Chart(ctxChartActiveCountry).Doughnut(chartTopCountryData, {responsive: true});
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