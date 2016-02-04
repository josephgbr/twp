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
var $LOG_SEEK = 0;
var $LOG_FILTER_TYPE = 0; // All
var $LOG_FILTER_ORDER = 0; // Desc
var $ISSUES_PAGINATION = [0, 0] // cur. page, num. pages
var $LOG_PAGINATION = [moment(new Date()).format("DD-MM-YYYY"),0] // cur. page

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
		//window.setInterval('get_server_instance_log()', 2000);
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
			  labels: [$BABEL_STR_PLAYERS],
			  resize: true,
			  dateFormat: function (x) { return moment(x).format("DD/MM/YYYY"); }
		});
		
		var chartColors = ['#F7464A', '#46BFBD', '#FDB45C', '#A7464A', '#37464A'];
		// Top Clans
		var chartTopClanData = [];
		for (var i in data['labels']['topclan'])
		{
			var clanName = data['labels']['topclan'][i];
			if (!clanName || !clanName[0])
				clanName = $BABEL_STR_UNKNOWN;
			
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
				countryName = $BABEL_STR_UNKNOWN;
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
	
	
	// Filter
	$("#filter-type").val($LOG_FILTER_TYPE).change(function(){
		$LOG_FILTER_TYPE = $(this).val();
		$LOG_SEEK = 0;
		$('#server-log').html("");
		get_server_instance_log();
	});
	$("#filter-order").val($LOG_FILTER_ORDER).change(function(){
		$LOG_FILTER_ORDER = $(this).val();
		$LOG_SEEK = 0;
		$('#server-log').html("");
		get_server_instance_log();
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
	
	window.setInterval('refresh_issues_count()', $REFRESH_TIME);
	refresh_issues_count();
	
});

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