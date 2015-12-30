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

	// Send Mod Archive
	$(document).on("change", "#install-mod input[type='file']", function() {
		var $this = $(this);
		var $btn = $('#install-mod-button');
	    var filename =  $this.val().replace(/^.*[\\\/]/, '');
	     
	    $btn.removeClass('btn-default').addClass('btn-success disabled');
	    $btn.html("<i class='fa fa-refresh fa-spin'></i> Installing '"+filename+"'...");
	     
		bootbox.dialog({
			message: "<div class='text-center text-muted'><h1><i class='fa fa-circle-o-notch fa-spin'></i><br/>"+$BABEL_STR_PLEASE_WAIT+"</h1></div>",
			buttons: {}
		});
		
		$('#install-mod #url').val('');
	    $('#install-mod').submit();
	});
	
	// Open dialog for type external url mod package
	$(document).on("click", "#install-mod-url", function() {
		bootbox.prompt($BABEL_STR_URL_TO_PACKAGE, function(result) {                
			if (result !== null) {
	    		var $btn = $('#install-mod-button');
	    		$btn.removeClass('btn-default').addClass('btn-success disabled');
	    		$btn.html("<i class='fa fa-refresh fa-spin'></i> "+$BABEL_STR_INSTALLING);
	    		
	    		bootbox.dialog({
	    			message: "<div class='text-center text-muted'><h1><i class='fa fa-circle-o-notch fa-spin'></i><br/>"+$BABEL_STR_PLEASE_WAIT+"</h1></div>",
	    			buttons: {}
	    		});
	    		
	    		$('#install-mod #url').val(result);
	    		$('#install-mod').submit();
			}
		});
	});
	
	// Open Dialog Create New Server Instance
	$(document).on("click", "a[data-target=#modal_new_server]", function() {
	     var mod = $(this).data('mod');
	     $('#modal_new_server #mod').val(mod);
	     var $cfglist = $('#modal_new_server #configs');
	     $cfglist.children().remove();
	     $('#modal_new_server #cfgfile').val("");
	     
	     $.post($SCRIPT_ROOT + '/_get_mod_configs/'+mod, '', function(data) {
	    	if (data['configs'] && data['configs'].length > 0)
	    	{
	    		$('#modal_new_server #cfgfile').val(data['configs'][0]);
	    		for (i in data['configs'])
	    			$cfglist.append("<option value='"+data['configs'][i]+"'>"+data['configs'][i]+"</option>")
	    	}
	    });
	});
	
	// Press "OK" button in New Server Instance Dialog
	$(document).on("click", "#modal_new_server .btn-success", function() {
		var srvmod = $('#modal_new_server #mod').val();
		var configfile = $(".modal-body #cfgfile").val();
		if (!configfile)
			return;
		
		$.post($SCRIPT_ROOT + '/_create_server_instance/'+srvmod, 'fileconfig='+configfile, function(data) {
			check_server_data(data);

			if (data['success'])
			{
				$('#modal_new_server').modal('hide');
				window.location.reload();
			}
		});
	});
	
	// Remove Server Instance
	$(document).on("click", ".remove-server-instance", function() {
		var srvid = $(this).data('id');
		var srvmod = $(this).data('mod');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE+"<br/><input type='checkbox' name='delete-configfile'/>"+$BABEL_STR_DELETE_CONF,
			title: $BABEL_STR_DELETE+" '"+srvmod+"' "+$BABEL_STR_SERVER_INSTANCE,
			buttons: {
			    success: {
			    	label: $BABEL_STR_DELETE,
			    	className: "btn-danger",
			    	callback: function() {
			    		var delconfig = $("input[name='delete-configfile']:checked").val()==='on'?'1':'0';			    		
						$.post($SCRIPT_ROOT + '/_remove_server_instance/'+srvid+'/'+delconfig, '', function(data) {
							check_server_data(data);
							
							if (data['success'])
							{
								window.location.reload();
							}
						});
			    	}
			    },
			    main: {
			    	label: "Cancel",
			    	className: "btn-default"
			    }
			}
		});
	});
	
	// Open ECon Modal
	$(document).on("click", "a[data-target=#modal_external_console]", function() {
		var srvid = $(this).data('id');
		$("#modal_external_console #srvid").val(srvid);
		$("#modal_external_console #econ-log").val('');
		setTimeout("$('#modal_external_console #cmd').focus()", 150);
	});
	
	// Send ECon Command
	$(document).on("click", "#modal_external_console #send-econ-command", function() {
		var $this = $(this);
		var srvid = $this.data('id');
		
		if ($this.hasClass('disabled'))
			return;
		
		$this.addClass('disabled').html("<i class='fa fa-spinner fa-spin'></i> "+$BABEL_STR_SENDING);
		
		$.post($SCRIPT_ROOT + '/_send_econ_command', $('#form-econ').serialize(), function(data) {
			$this.removeClass('disabled').text("Send");
			check_server_data(data);
			
			if (data['success'])
			{
				$("#modal_external_console #cmd").val('');
				var $econlog = $("#modal_external_console #econ-log");
				var last_content = $econlog.val();
				$econlog.val(last_content+data['rcv']); // FIXME: idk why "append" not works :\
				$econlog.prop('scrollTop', $econlog.prop('scrollHeight'));
				$('#modal_external_console #cmd').focus();
			}
		});
	});
	
	// Select Server binary
	$(document).on("click", ".menu-item-server-bin", function() {
		var $this = $(this);
		var $parent_ul = $this.parent().parent();
		var srvid = $parent_ul.data('id');
		var srvbin = $this.text().trim();
		
		$.post($SCRIPT_ROOT + '/_set_server_binary/'+srvid+'/'+srvbin, '', function(data) {
			check_server_data(data);
		
			if (data['success'])
			{
				$parent_ul.find('li').removeClass('active');
				$this.parent().addClass('active');
				$('#btn-play-srv-'+srvid+' .start-instance').removeClass('disabled');
			}
		});
	});
	
	// Dialog Cofiguration can't close when click out
	$('#modal_instance_configuration').modal({'backdrop':'static', 'show':false});
	
	// Open Dialog Server Instance Configuration
	$(document).on("click", "a[data-target=#modal_instance_configuration]", function() {
	     var srvid = $(this).data('id');
	     $('#form-server-config #srvid').val(srvid);
	     $.post($SCRIPT_ROOT + '/_get_server_config/'+srvid, '', function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 $("#modal_instance_configuration #alsrv").prop('checked', data['alsrv']);
		    	 $("#modal_instance_configuration #srvcfg").val(data['srvcfg']);
		    	 $("#modal_instance_configuration .modal-title").text("Instance Configuration: "+data['fileconfig']);
	    	 }
	    	 else
	    	 {
		    	 $("#modal_instance_configuration #alsrv").prop('checked', false);
		    	 $("#modal_instance_configuration #srvcfg").val("");
		    	 $("#modal_instance_configuration .modal-title").text($BABEL_STR_INSTANCE_CONF);
	    	 }
	     });
	});
	// Select map
	$(document).on("change", ".check_map", function() {
		var maps = new Array();
		$("input[name=map_used]:checked").each(function(){ maps.push($(this).data('map')); });
		
		update_config_textarea($("#modal_instance_configuration #srvcfg"), "sv_map", (maps.length > 0)?maps[0]:undefined);
		update_config_textarea($("#modal_instance_configuration #srvcfg"), "sv_maprotation", (maps.length > 1)?maps.join(" "):undefined);
	});
	
	// Select Tab
	$("ul.nav-tabs > li > a").on("shown.bs.tab", function (e) {
        var id = $(e.target).attr("href").substr(1);
        var srvid = $('#form-server-config #srvid').val();
        
        if ("maps" === id)
        	refresh_server_maps_list(srvid);
    });
	
	// Press "OK" button in Server Instance Configuration
	$(document).on("click", "#modal_instance_configuration .btn-primary", function() {
		var $this = $(this);

		$.post($SCRIPT_ROOT + '/_save_server_config', $('#form-server-config').serialize(), function(data) {
			check_server_data(data);
			
			if (data['success'])
			{
				var srvline_id = '#srv-line-'+data['id'];
				var $port = $(srvline_id+' .srv-port');
				var $name = $(srvline_id+' .srv-name');
				var $gametype = $(srvline_id+' .srv-gametype');
				var $flags = $(srvline_id+' .srv-flags');
				
				$port.text(data['port']);
				$name.text(data['name']);
				$gametype.text(data['gametype']);
				
				if (data['register'] == 0)
					$flags.find('.tw-no-register').addClass('fa-eye-slash').removeClass('fa-eye').css('color','#BBB').prop('title', $BABEL_STR_PUBLIC_SERVER);
				else
					$flags.find('.tw-no-register').addClass('fa-eye').removeClass('fa-eye-slash').css('color','#333').prop('title', $BABEL_STR_PRIVATE_SERVER);
				
				if (data['password'] == 0)
					$flags.find('.tw-password').css('color','#BBB').prop('title', $BABEL_STR_NOT_REGISTER_SERVER);
				else
					$flags.find('.tw-password').css('color','#333').prop('title', $BABEL_STR_REGISTER_SERVER);
				
				$('#modal_instance_configuration').modal('hide');
			}
		});
	});
	
	// Start Server Instance
	$(document).on("click", ".start-instance", function() {
		var $this = $(this);
		var srvid = $this.data('id');
		var $listline =  $('#srv-line-'+srvid);
		var $btngroup =  $('#btn-play-srv-'+srvid);
		var $btnlist = $btngroup.find('.dropdown-toggle');
		
		$this.addClass('disabled btn-warning').removeClass('btn-success');
		$btnlist.addClass('disabled btn-warning').removeClass('btn-success');
		$listline.find("a[data-target='#modal_instance_configuration']").addClass('disabled hidden');
		$listline.find(".remove-server-instance").addClass('disabled');
		$this.html("<i class='fa fa-spinner fa-spin'></i> "+$BABEL_STR_STARTING);
		
		$.post($SCRIPT_ROOT + '/_start_server_instance/'+srvid, '', function(data) {
			if (data['error'])
			{
				$this.removeClass('disabled btn-warning').addClass('btn-success');
				$btnlist.removeClass('disabled btn-warning').addClass('btn-success');
				$listline.find("a[data-target='#modal_instance_configuration']").removeClass('disabled hidden');
				$listline.find(".remove-server-instance").removeClass('disabled');
				$this.html("<i class='fa fa-play'></i> "+$BABEL_STR_START);
			}
			
			check_server_data(data);
	    	 
			if (data['success'])
			{
				window.location.reload();
			}
		});
	});
	
	// Stop Server Instance
	$(document).on("click", ".stop-instance", function() {
		var srvid = $(this).data('id');
	     $.post($SCRIPT_ROOT + '/_stop_server_instance/'+srvid, '', function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 window.location.reload();
	    	 }
	     });
	});
	
	// Remove Mod
	$(document).on("click", ".remove-mod", function() {
		var mod_folder = $(this).data('mod');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE+"<br/><span class='text-danger'>"+$BABEL_STR_THIS_CANT_BE_CANCELED+"</span>",
			title: $BABEL_STR_REMOVE+" '"+mod_folder+"' Mod",
			buttons: {
			    success: {
			    	label: $BABEL_STR_REMOVE,
			    	className: "btn-danger",
			    	callback: function() {
				   	     $.post($SCRIPT_ROOT + '/_remove_mod', 'folder='+mod_folder, function(data) {
				   	    	 check_server_data(data);
				   	    	 
				   	    	 if (data['success'])
				   	    	 {
				   		    	 window.location.reload();
				   	    	 }
				   	     });
			    	}
			    },
			    main: {
			    	label: $BABEL_STR_CANCEL,
			    	className: "btn-default"
			    }
			}
		});
	});
	
});

function refresh_server_maps_list(srvid)
{
    var maps = new Array();
    var maps_str = get_config_value_textarea($("#modal_instance_configuration #srvcfg"), "sv_maprotation");
    if (maps_str)
    	maps = maps_str.split(" ");
    maps.push(get_config_value_textarea($("#modal_instance_configuration #srvcfg"), "sv_map"));
    
	    $.post($SCRIPT_ROOT + '/_get_server_maps/'+srvid, '', function(data) {
    	 check_server_data(data);
    	 
    	 if (data['success'])
    	 {
    		 $("#maplist").html("");
	    	 for (var i in data['maps'])
	    	 { 
	    		 var mapSelected = maps.indexOf(data['maps'][i].name)>=0;
	    		 var row = "<tr><td><input type='checkbox' name='map_used' class='check_map' data-map='"+data['maps'][i].name+"' "+(mapSelected?'checked':'')+"/></td><td>"+data['maps'][i].name+"</td><td>"+data['maps'][i].size+"</td></tr>";
	    		 $("#maplist").append(row);
	    	 }
    	 }
    });
}