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
	
	/** MAIN MENU **/
    //stick in the fixed 100% height behind the navbar but don't wrap it
    $('#slide-nav.navbar-inverse').after($('<div class="inverse" id="navbar-height-col"></div>'));
    $('#slide-nav.navbar-default').after($('<div id="navbar-height-col"></div>'));  

    // Enter your ids or classes
    var toggler = '.navbar-toggle';
    var pagewrapper = '#page-content';
    var navigationwrapper = '.navbar-header';
    var menuwidth = '100%'; // the menu inside the slide menu itself
    var slidewidth = '30%';
    var menuneg = '-100%';
    var slideneg = '-30%';

    $("#slide-nav").on("click", toggler, function(e){

        var selected = $(this).hasClass('slide-active');

        $('#slidemenu').stop().animate({
            left: selected ? menuneg : '0px'
        });

        $('#navbar-height-col').stop().animate({
            left: selected ? slideneg : '0px'
        });

        $(pagewrapper).stop().animate({
            left: selected ? '0px' : slidewidth
        });

        $(navigationwrapper).stop().animate({
            left: selected ? '0px' : slidewidth
        });

        $(this).toggleClass('slide-active', !selected);
        $('#slidemenu').toggleClass('slide-active');

        //$('#page-content, .navbar, body, .navbar-header').toggleClass('slide-active');
    });

    /*var selected = '#slidemenu, #page-content, body, .navbar, .navbar-header';
    $(window).on("resize", function(){
        if ($(window).width() > 767 && $('.navbar-toggle').is(':hidden'))
            $(selected).removeClass('slide-active');
    });*/
    /** END: MAIN MENU **/
	
    /** GENERAL **/
	$(document).on("keypress", ".deny-enter :input:not(textarea)", function(event) {
	    if (event.keyCode == 13) {
	        event.preventDefault();
	    }
	});

	refresh_main();
	window.setInterval('refresh_main()', $REFRESH_TIME);
	
	// Initialize colorpickers
	$('.colorpicker-input').colorpicker();
	/** END: GENERAL **/
	
	/** CSS INITIALIZATIONS **/
	$('.carrousel-fade').each(function(){ $(this).carrouselanim(); });
	var clipboard = new Clipboard('.btn-clipboard');
	clipboard.on('error', function(e) {
		var $trigger = $(e.trigger);
	    alert("Oops! your browser can't copy to clipboard...\nYou need to copy manually:\n\n"+$trigger.data('clipboard-text'));
	});
});

/** AJAX CONFIG **/
var csrftoken = $('meta[name=csrf-token]').attr('content');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
/** END: AJAX CONFIG **/

/** REST CALLS **/
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
/** END: REST CALLS **/


/** CONFIG TOOLS **/
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
/** END: CONFIG TOOLS **/


/** JQUERY EXTENSIONS **/
// Minimal Animated Carrousel
$.fn.extend({
	carrouselanim: function(option) {
		var $this = $(this);
		
		function selItem(index, noAnim)
		{
			var $items = $this.data('carrousel-items');
			var selected = +$this.data('carrousel-sel');
			
			if (noAnim)
			{
				$items[selected].css('display', 'none');
				$items[index].css({ display:'initial', opacity:1 });
			}
			else
			{
				$items[selected].animate({ opacity:'0' }, function(){
					$items[selected].css('display', 'none');
				});
				$items[index].css({ display:'initial', opacity:0 });
				$items[index].animate({ opacity:1 });
			}
			$this.data('carrousel-sel', index);
		};
		
		if (typeof(option) === "string")
		{
			switch(option)
			{
			case "next":
				var $items = $this.data('carrousel-items');
				var selected = +$this.data('carrousel-sel');
				if (selected < $items.length-1)
					selItem(selected+1);
				break;
			case "prev":
				var selected = +$this.data('carrousel-sel');
				if (selected > 0)
					selItem(selected-1);
				break;
			}
		}
		else if (typeof(option) === "integer")
		{
			selItem(option);
		}
		else
		{
			var $items = [];
			var count=0;
			var activedSel=-1;
			$this.children('.carrousel-fade-list').children('.item').each(function(){
				var $_this = $(this);
				$_this.css({ display:'none', position:'absolute', width: '100%', left: 0 });
				$items.push($_this);
				if ($_this.hasClass('active'))
					activedSel = count;
				++count;
			});
			$this.css({ position:'relative' });
			$this.data('carrousel-items', $items);
			$this.data('carrousel-sel', 0);
			$items[0].css('display', 'initial');
			
			$this.find('.next').each(function(){
				$(this).click(function(){
					$this.carrouselanim('next');
					return false;
				})
			});
			$this.find('.prev').each(function(){
				$(this).click(function(){
					$this.carrouselanim('prev');
					return false;
				})
			});
			
			if (activedSel != -1)
				selItem(activedSel, true);
		}
	}
});

// Split TextArea/Input form controls
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