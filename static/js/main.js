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
	
	$(document).on("keypress", ".deny-enter :input:not(textarea)", function(event) {
	    if (event.keyCode == 13) {
	        event.preventDefault();
	    }
	});

	refresh_main();
	window.setInterval('refresh_main()', $REFRESH_TIME);
	
	// Initialize colorpickers
	$('.colorpicker-input').colorpicker();
	
});

$.fn.extend({
	
	splitlines: function() {
		var lines = this.val().split(/\n/);
		var texts = [];
		for (var i=0; i < lines.length; i++)
		{
			if (/\S/.test(lines[i]))
				texts.push($.trim(lines[i]));
		}
		
		return texts;
	}
	
});

function refresh_main()
{
	get_server_instances_online();
	get_host_localtime();
}

function get_server_instances_online()
{
    $.post($SCRIPT_ROOT + '/_get_server_instances_online', '', function(data) {
      	 check_server_data(data);
      	 
      	 if (data['success'])
      	 {
      		 var num = data['num'];
      		 if (num == 0)
      			 $("#badge-num-server-instances").text("0").addClass('hidden');
      		 else
      			 $("#badge-num-server-instances").text(num).removeClass('hidden');
      	 }
    });
}

function check_server_data(data)
{
	if (!data || data == undefined)
		return;
	
	if (data['notauth'])
	{
		bootbox.dialog({
			message: "<p class='text-center' style='color:#800000;'><i class='fa fa-warning'></i> "+$BABEL_STR_SESSION_EXPIRED+" <i class='fa fa-warning'></i></p>",
			title: $BABEL_STR_TITLE_SESSION_EXPIRED,
			buttons: {
				success: {
					label: "Oh!",
					className: "btn-default",
					callback: function() {
						window.location.reload();
					}
				}
			}
		});
	}
	else if (data['error'])
	{
		var errormsg = data['errormsg']?data['errormsg']:$BABEL_STR_INTERNAL_ERROR;
		
		bootbox.dialog({
			message: "<p class='text-center' style='color:#800000;'>"+errormsg+"</p>",
			title: $BABEL_STR_ERROR_OOOPS+" <i class='fa fa-frown-o'></i>",
			buttons: {
				success: {
					label: $BABEL_STR_DAMN,
					className: "btn-default"
				}
			}
		});
	}
}

function get_host_localtime()
{
	$.post($SCRIPT_ROOT + '/_refresh_host_localtime', '', function(data) {
		$("#localtime").text(data['localtime']);
	});
}

function get_config_value_textarea($ta, param)
{
	var lines = $ta.splitlines();
	for (var i in lines)
	{
        var objMatch = lines[i].match(/^([^#\s]+)\s([^#\r\n]+)/);
        if (objMatch && param.toLowerCase() === objMatch[1].toLowerCase())
        	return objMatch[2];
	}
	
	return undefined;
}

function update_config_textarea($ta, param, new_value)
{
	var lines = $ta.splitlines();
	var nvalue = "";
	
	var replaced = false;
	for (var i in lines)
	{
        var objMatch = lines[i].match(/^([^#\s]+)\s([^#\r\n]+)/);
        if (objMatch && param.toLowerCase() === objMatch[1].toLowerCase())
        {
        	if (new_value)
        		nvalue += param+" "+new_value+"\n";
            replaced = true;
        }
        else
        	nvalue += lines[i]+"\n";
	}
	
    if (!replaced && new_value)
    	nvalue += param+" "+new_value+"\n";
    
    $ta.val(nvalue);
}

function generate_wizard($wizard)
{
	$.getJSON($SCRIPT_ROOT+'/static/js/base_conf.json', function(data){
		var html = "";
		$.each(data, function(key, val){			
			if ("select" === val.type)
			{
				html += "<label for='"+key+"'>"+val.label+"</label>";
				html += "<select id='"+key+"' class='form-control' title='"+(val.tooltip?val.tooltip:'')+"'>";
				for (var i in val.values)
					html += "<option value='"+val.values[i]+"' "+(val.values[i]==val.default?'selected':'')+">"+val.values[i]+"</option>";
				html += "</select>"
			}
			else if ("checkbox" === val.type)
				html += "<input id='"+key+"' type="+val.type+" title='"+(val.tooltip?val.tooltip:'')+"' "+(1===val.default?'checked':'')+"/> <span style='font-weight:bold'>"+val.label+"</span><br/>";
			else
			{
				html += "<label for='"+key+"'>"+val.label+"</label>";
				html += "<input id='"+key+"' type="+val.type+" value='"+(val.default?val.default:'')+"' "+(val.range?"min='"+val.range[0]+"' max='"+val.range[1]+"'":'')+" class='form-control' title='"+(val.tooltip?val.tooltip:'')+"' />";
			}
		});
		$wizard.html(html);
	});
}