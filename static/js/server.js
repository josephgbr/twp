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
	//var ctxChartPlayers7d = $("#chart-players-7d").get(0).getContext("2d");
	var ctxChartPlayers7d = document.getElementById('chart-players-7d').getContext('2d');
	$.post($SCRIPT_ROOT + '/_get_chart_values/'+$SRVID+'/players-7d', '', function(data) {
		var chartData = {
		    labels: data['labels'],
		    datasets: [
		        {
		            label: "Players Count",
		            fillColor: "rgba(220,220,220,0.2)",
		            strokeColor: "rgba(220,220,220,1)",
		            pointColor: "rgba(220,220,220,1)",
		            pointStrokeColor: "#fff",
		            pointHighlightFill: "#fff",
		            pointHighlightStroke: "rgba(220,220,220,1)",
		            data: data['values']
		        }
		    ]
		};
		var chartOptions = {
		    ///Boolean - Whether grid lines are shown across the chart
		    scaleShowGridLines : true,
		    //String - Colour of the grid lines
		    scaleGridLineColor : "rgba(0,0,0,.05)",
		    //Number - Width of the grid lines
		    scaleGridLineWidth : 1,
		    //Boolean - Whether to show horizontal lines (except X axis)
		    scaleShowHorizontalLines: true,
		    //Boolean - Whether to show vertical lines (except Y axis)
		    scaleShowVerticalLines: true,
		    //Boolean - Whether the line is curved between points
		    bezierCurve : true,
		    //Number - Tension of the bezier curve between points
		    bezierCurveTension : 0.4,
		    //Boolean - Whether to show a dot for each point
		    pointDot : true,
		    //Number - Radius of each point dot in pixels
		    pointDotRadius : 4,
		    //Number - Pixel width of point dot stroke
		    pointDotStrokeWidth : 1,
		    //Number - amount extra to add to the radius to cater for hit detection outside the drawn point
		    pointHitDetectionRadius : 20,
		    //Boolean - Whether to show a stroke for datasets
		    datasetStroke : true,
		    //Number - Pixel width of dataset stroke
		    datasetStrokeWidth : 2,
		    //Boolean - Whether to fill the dataset with a colour
		    datasetFill : true,
		    //String - A legend template
		    legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].strokeColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"
		};
		var chartPlayers7d = new Chart(ctxChartPlayers7d).Line(chartData, chartOptions);
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