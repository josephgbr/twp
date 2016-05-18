"use strict";
/*
 ********************************************************************************************
 **    TWP v0.3.0 - Teeworlds Web Panel
 **    Copyright (C) 2016  Alexandre Díaz
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
var $ISSUES_PAGINATION = [0, 0] // cur. page, num. pages
var $COUNTRIES = [];
// Countries
$.getJSON($SCRIPT_ROOT+'/static/json/countries.json', function(data){ $COUNTRIES = data; });

$(function(){
	
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
		if (data['labels'] && data['labels']['players7d'] && data['labels']['players7d'].length > 0)
			createAnimatedChartLine('#chart-players-7d', data, 'players7d');
		else
			$('#chart-players-7d').html("<h1 class='text-center text-muted'>"+$BABEL_STR_NO_DATA+"<br/><i class='fa fa-meh-o'></i></h1>");

		// Top Clans
		if (data['labels'] && data['labels']['topclan'] && data['labels']['topclan'].length > 0)
			createAnimatedChartDonut('#chart-active-clan', data, 'topclan');
		else
			$('#chart-active-clan').html("<h1 class='text-center text-muted'>"+$BABEL_STR_NO_DATA+"<br/><i class='fa fa-meh-o'></i></h1>");
		
		// Top Countries
		if (data['labels'] && data['labels']['topcountry'] && data['labels']['topcountry'].length > 0)
		{
			for (var i in data['labels']['topcountry'])
			{
				var countryName = undefined;
				if (data['labels']['topcountry'][i] != -1)
					countryName = $.grep($COUNTRIES, function(e){ return e.codenum == data['labels']['topcountry'][i]; });
				
				if (!countryName || !countryName[0])
					countryName = $BABEL_STR_UNKNOWN;
				else
					countryName = countryName[0].name;
					
				data['labels']['topcountry'][i] = countryName;
			}
			createAnimatedChartDonut('#chart-active-country', data, 'topcountry');
		}
		else
			$('#chart-active-country').html("<h1 class='text-center text-muted'>"+$BABEL_STR_NO_DATA+"<br/><i class='fa fa-meh-o'></i></h1>");
	});
	
	// ColorPicker Modal
	$('#share-url').val($('#server-banner').prop('src'));
	$(document).on("click", "#generate-banner", function(event) {
		var colorTitle = $('#color-title').data('colorpicker').color.toHex().substr(1);
		var colorDetail = $('#color-detail').data('colorpicker').color.toHex().substr(1);
		var colorAddress = $('#color-address').data('colorpicker').color.toHex().substr(1);
		var colorGradStart = $('#color-grad-start').data('colorpicker').color.toHex().substr(1);
		var colorGradEnd = $('#color-grad-end').data('colorpicker').color.toHex().substr(1);
		var params = "title="+colorTitle+"&detail="+colorDetail+"&address="+colorAddress+"&grads="+colorGradStart+"&grade="+colorGradEnd;
		
		var $banner = $('#server-banner');
		$banner.prop('src','/server/1/banner?'+params);
		$('#share-url').val($banner.prop('src'));
	});
	
	// Issues
	$(document).on('shown.bs.modal', '#modal_instance_issues', function(ev){
		refresh_issues();
	});
	$(document).on('click', '#modal_instance_issues .pagination li>a', function(ev){
		var $this = $(this);
		var page = $this.data('page');
		
		if ('prev' == page)
		{
			if ($ISSUES_PAGINATION[0] > 0)
				--$ISSUES_PAGINATION[0];
		} else if ('next' == page)
		{
			if ($ISSUES_PAGINATION[0] < $ISSUES_PAGINATION[1])
				++$ISSUES_PAGINATION[0];
		}
		else
			$ISSUES_PAGINATION[0] = page;
		
		refresh_issues();
		ev.preventDefault();
	});
	
	refresh_uptime();
	window.setInterval('refresh_uptime()', 900);
	window.setInterval('refresh_issues_count()', $REFRESH_TIME);
	refresh_issues_count();
	
});

function refresh_uptime()
{
	var a = moment(new Date($SRV_LAUNCH_DATE)).utc();
	var dur = moment.duration(moment().utc().diff(a), 'milliseconds');
	
	var hstr = "";
	if (dur.years() > 0) hstr += dur.years()+" "+$BABEL_STR_YEARS+", ";
	if (dur.months() > 0) hstr += dur.months()+" "+$BABEL_STR_MONTHS+", ";
	if (dur.days() > 0) hstr += dur.days()+" "+$BABEL_STR_DAYS+", ";
	if (dur.hours() > 0) hstr += dur.hours()+" "+$BABEL_STR_HOURS+", ";
	if (dur.minutes() > 0) hstr += dur.minutes()+" "+$BABEL_STR_MINUTES+", ";
	hstr += dur.seconds()+" "+$BABEL_STR_SECONDS;
	$('#uptime').text(hstr);
}

function refresh_issues()
{
	$.post($SCRIPT_ROOT + '/_get_server_issues/'+$SRVID+'/'+$ISSUES_PAGINATION[0], '', function(data){
		check_server_data(data);
		
		if (data['success'])
		{
			$ISSUES_PAGINATION[1] = +data['pages'];
			$('#modal_instance_issues #issues-list').html('');
			for (var i in data['issues'])
			{
				var row = data['issues'][i];
				var html = "<tr>";
				html += "<td class='col-md-4'>"+moment(new Date(row[0])).format("DD-MM-YYYY HH:mm")+"</td>";
				html += "<td class='col-md-8'>"+row[1]+"</td>";
				html += "</tr>";
				$('#modal_instance_issues #issues-list').append(html);
			}
			
			var html = "<li class='"+(0==$ISSUES_PAGINATION[0]?'disabled':'')+"'><a href='#' data-page='prev' aria-label='Previous'><span aria-hidden='true'>&laquo;</span></a></li>";
			var start_page = Math.max(0, $ISSUES_PAGINATION[0]-3);
			var end_page = Math.min($ISSUES_PAGINATION[0]+3, $ISSUES_PAGINATION[1]);
			if (end_page < 7 && $ISSUES_PAGINATION[1] >= 7)
				end_page = 6;
			for (var i=start_page;i<=end_page;i++)
				html += "<li class='"+(i==$ISSUES_PAGINATION[0]?'active':'')+"'><a data-page='"+i+"' href='#'>"+i+"</a></li>";
			html += "<li class='"+($ISSUES_PAGINATION[1]==$ISSUES_PAGINATION[0]?'disabled':'')+"'><a href='#' data-page='next' aria-label='Next'><span aria-hidden='true'>&raquo;</span></a></li>";
			$('#modal_instance_issues .pagination').html(html);
		}
	});
}

function refresh_issues_count()
{
	$.post($SCRIPT_ROOT + '/_get_server_issues_count/'+$SRVID, '', function(data){
		$('#issues_count').text(data['success']?data['issues_count']:'0');
	});
}