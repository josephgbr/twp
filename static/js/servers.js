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
$(function(){

	// Send Mod Archive
	$(document).on("change", "#install-mod input[type='file']", function() {
		var $this = $(this);
		var $btn = $('#install-mod-button');
		var file = this.files[0];
	     
	    $btn.removeClass('btn-default').addClass('btn-success disabled');
	    $btn.html("<i class='fa fa-refresh fa-spin'></i> "+$BABEL_STR_INSTALLING+" '"+file.name+"'...");
	     
		bootbox.dialog({
			message: "<div class='text-center text-muted'><h1><i class='fa fa-circle-o-notch fa-spin'></i><br/>"+$BABEL_STR_PLEASE_WAIT+"</h1></div>",
			buttons: {}
		});
		
		$('#install-mod #url').val('');
	    $('#install-mod').submit();
	});
	
	// Send Map Archive
	$(document).on("change", "#upload-maps input[type='file']", function() {
		var $this = $(this);
		var $btn = $('#btn-upload-map');
		var srvid = $('#form-server-config #srvid').val();
		var file = this.files[0];
		var origHTML = $btn.html();
	     
	    $btn.removeClass('btn-default').addClass('btn-success disabled');
	    $btn.html("<i class='fa fa-refresh fa-spin'></i> "+$BABEL_STR_UPLOADING+" '"+file.name+"'...");
		
    	$.ajax({
    		url: '/_upload_maps/'+srvid,
			type: 'POST',
			data: new FormData($('#upload-maps')[0]),
            contentType: false,
            cache: false,
            processData: false,
            async: false,
			success: function(data){
				check_server_data(data);
				
				if (data['success'])
				{
					refresh_server_maps_list(srvid);
					
					if (".map" === file.name.substr(-4))
					{
						var $line = $("tr#row-"+file.name.substr(0, file.name.length-4));
						var $list = $("#maplist-container");
						$list.animate({
						    scrollTop: $line.offset.top - $list.offset.top + $list.scrollTop()
						});
					}
				}
			    $btn.removeClass('btn-default').removeClass('btn-success disabled').addClass('btn-default');
			    $btn.html(origHTML);
			},
			error: function(){
				check_server_data({'error':true, 'errormsg':$BABEL_STR_UNEXPECTED_ERROR});
			    $btn.removeClass('btn-default').removeClass('btn-success disabled').addClass('btn-default');
			    $btn.html(origHTML);
			}
    	});
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
	$(document).on("click", "a[data-target='#modal_new_server']", function() {
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
	    			$cfglist.append("<option value='"+data['configs'][i]+"'>"+data['configs'][i]+"</option>");
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
			    	label: $BABEL_STR_CANCEL,
			    	className: "btn-default"
			    }
			}
		});
	});
	
	// Open ECon Modal
	$(document).on("click", "a[data-target='#modal_external_console']", function() {
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
		
		$.post($SCRIPT_ROOT + '/_send_econ_command/'+$('#form-econ #srvid').val(), $('#form-econ').serialize(), function(data) {
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
		
		return false;
	});
	
	// Dialog Cofiguration can't close when click out
	$('#modal_instance_configuration').modal({'backdrop':'static', 'show':false});
	
	// Open Dialog Server Instance Configuration
	$(document).on("click", "a[data-target='#modal_instance_configuration']", function() {
	     var srvid = $(this).data('id');
	     $('#form-server-config #srvid').val(srvid);
	     $('#modal_instance_configuration .btn-success').css('visibility','hidden');
	     $('#modal_instance_configuration .btn-default').css('visibility','hidden');
	     $.post($SCRIPT_ROOT + '/_get_server_config/'+srvid, '', function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 $("#modal_instance_configuration #check_alsrv").prop('checked', data['alsrv']);
		    	 $("#modal_instance_configuration #srvcfg").val(data['srvcfg']);
		    	 $("#modal_instance_configuration .modal-title").text("Instance Configuration: "+data['fileconfig']);
	    	 }
	    	 else
	    	 {
		    	 $("#modal_instance_configuration #check_alsrv").prop('checked', false);
		    	 $("#modal_instance_configuration #srvcfg").val("");
		    	 $("#modal_instance_configuration .modal-title").text($BABEL_STR_INSTANCE_CONF);
	    	 }
	    	 
	    	 $('#modal_instance_configuration .btn-success').css('visibility','');
		     $('#modal_instance_configuration .btn-default').css('visibility','');
	     });
	});
	// Select map
	$(document).on("change", ".check_map", function() {
		update_advance_config_maps();
	});
	
	// Remove Map
	$(document).on("click", ".remove-map", function(){
		var map = $(this).data("map");
		var srvid = $('#form-server-config #srvid').val();
		
		$.post($SCRIPT_ROOT+'/_remove_map/'+srvid, 'map='+map, function(data){
			check_server_data(data);
			
			if (data['success'])
			{
				$("tr#row-"+map).remove();
				update_advance_config_maps();
			}
		});
	});
	
	// Change wizard value
	$(document).on("change", ".wizard-param", function() {
		var $this = $(this);
		var value = $this.val();
		var defval = $this.data('default')==='undefined'?undefined:$this.data('default'); // TODO: Not use 'undefined'
		if ($this.is("input") && "checkbox" === $this.prop("type"))
			value = $this.prop('checked')?1:0;
		update_config_textarea($("#modal_instance_configuration #srvcfg"), $this.attr("id"), value, defval);
	});
	
	// Select re-launch if offline
	$(document).on("change", "#check_alsrv", function() {
		$("#modal_instance_configuration #alsrv").val($(this).is(":checked"));
	});
	
	// Select Tab
	$("ul.nav-tabs > li > a").on("shown.bs.tab", function (e) {
        var id = $(e.target).attr("href").substr(1);
        var srvid = $('#form-server-config #srvid').val();
        
        if ("maps" === id)
        	refresh_server_maps_list(srvid);
        else if ("wizard" === id)
        	generate_wizard($('#wizard'), srvid);
    });
	
	// Press "OK" button in Server Instance Configuration
	$(document).on("click", "#modal_instance_configuration .btn-success", function() {
		var $this = $(this);

		$.post($SCRIPT_ROOT + '/_save_server_config/'+$("#form-server-config #srvid").val(), $('#form-server-config').serialize(), function(data) {
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

				if (data['register'] == 1)
					$flags.find('.tw-no-register').addClass('fa-eye').removeClass('fa-eye-slash text-muted').prop('title', $BABEL_STR_PUBLIC_SERVER);
				else
					$flags.find('.tw-no-register').addClass('fa-eye-slash text-muted').removeClass('fa-eye').prop('title', $BABEL_STR_PRIVATE_SERVER);
				
				if (data['password'])
					$flags.find('.tw-password').removeClass('text-muted').prop('title', $BABEL_STR_REGISTER_SERVER);
				else
					$flags.find('.tw-password').addClass('text-muted').prop('title', $BABEL_STR_NOT_REGISTER_SERVER);
				
				if (data['alaunch'] == 0)
					$flags.find('.tw-alaunch').addClass('text-muted').prop('title', $BABEL_STR_NOT_AUTOLAUNCH);
				else
					$flags.find('.tw-alaunch').removeClass('text-muted').prop('title', $BABEL_STR_AUTOLAUNCH);
				
				$('#modal_instance_configuration').modal('hide');
				
				if (data['status'])
				{
					bootbox.dialog({
						message: $BABEL_STR_SERVER_ONLINE_CONFIG,
						title: $BABEL_STR_TITLE_SERVER_ONLINE_CONFIG,
						buttons: {
						    success: {
						    	label: $BABEL_STR_RESTART,
						    	className: "btn-danger",
						    	callback: function() {
						    		$.post($SCRIPT_ROOT + '/_restart_server_instance/'+data['id'], '', function(data) {
						    			check_server_data(data);
						    			if (data['success'])
						    				window.location.href = '/servers';
						    		});
						    	}
						    },
						    main: {
						    	label: $BABEL_STR_OK,
						    	className: "btn-default"
						    }
						}
					});
				}
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
	    		 var row = "<tr id='row-"+data['maps'][i].name+"'>";
	    		 row += "<td><input type='checkbox' name='map_used' class='check_map' data-map='"+data['maps'][i].name+"' "+(mapSelected?'checked':'')+"/></td>";
	    		 row += "<td>"+data['maps'][i].name+"</td>";
	    		 row += "<td>"+data['maps'][i].size+"</td>";
	    		 row += "<td class='text-right'><button type='button' class='remove-map btn btn-link btn-xs btn-delete-row' data-map='"+data['maps'][i].name+"' title='"+$BABEL_STR_REMOVE_MAP+"'><i class='fa fa-remove'></i></button></td>";
	    		 row += "</tr>";
	    		 $("#maplist").append(row);
	    	 }
    	 }
    });
}

function generate_wizard($wizard, srvid)
{
	$.getJSON($SCRIPT_ROOT+'/static/json/base_conf.json', function(data){
		$.post($SCRIPT_ROOT+'/_get_mod_wizard_config/'+srvid, '', function(mdata){
			check_server_data(mdata);
			
			var mcfg = data;
			if (mdata['success'] && mdata['config'])
				$.extend(true, mcfg, data, $.parseJSON(mdata['config']));
				
			var html = "";
			
			// Create Menu
			html += "<ul id='simple-tabs' class='nav nav-pills nav-justified' role='tablist'>";
			$.each(mcfg, function(section, variables){
				html += "<li><a href='#"+section.replace(" ","_")+"' data-toggle='tab'>"+section+"</a></li>";
			});
			html += "</ul>";
			
			// Fill Panels
			html += "<div class='tab-content' style='margin-top:1.5em;'>";
			$.each(mcfg, function(section, variables){		  	
				html += "<div class='tab-pane' id='"+section.replace(" ","_")+"' style='overflow:auto; height:220px;'>";
				$.each(variables, function(key, val){
					var defval = val.default;
					var rval = get_config_value_textarea($("#modal_instance_configuration #srvcfg"), key);
					if (!rval)
						rval = defval;
					
					if ("select" === val.type)
					{					
						html += "<label for='"+key+"'>"+val.label+"</label>";
						html += "<select id='"+key+"' data-default='"+defval+"' class='form-control wizard-param' title='"+(val.tooltip?val.tooltip:'')+"'>";
						for (var i in val.values)
							html += "<option value='"+val.values[i]+"' "+(val.values[i]==rval?'selected':'')+">"+val.values[i]+"</option>";
						html += "</select>";
					}
					else if ("checkbox" === val.type)
					{
						html += "<input class='wizard-param' data-default='"+defval+"' id='"+key+"' type="+val.type+" title='"+(val.tooltip?val.tooltip:'')+"' "+(1==rval?'checked':'')+"/> <span style='font-weight:bold'>"+val.label+"</span><br/>";
					}
					else
					{
						html += "<label for='"+key+"'>"+val.label+"</label>";
						html += "<input id='"+key+"' data-default='"+defval+"' type="+val.type+" value='"+(rval?rval:'')+"' "+(val.range?"min='"+val.range[0]+"' max='"+val.range[1]+"'":'')+" class='form-control wizard-param' title='"+(val.tooltip?val.tooltip:'')+"' />";
					}
				});
				html += "</div>";
			});
			html += "</div>";
			
			$wizard.html(html);
			$('#simple-tabs a:first').tab('show');
		});
	});
}

function update_advance_config_maps()
{
	var maps = new Array();
	$("input[name=map_used]:checked").each(function(){ maps.push($(this).data('map')); });
	update_config_textarea($("#modal_instance_configuration #srvcfg"), "sv_map", (maps.length > 0)?maps[0]:undefined);
	update_config_textarea($("#modal_instance_configuration #srvcfg"), "sv_maprotation", (maps.length > 1)?maps.join(" "):undefined);	
}
