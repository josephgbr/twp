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

	$(document).on("change", "#install-mod input[type='file']", function() {
	     var $this = $(this);
	     var $parent = $this.parent();
	     var filename =  $this.val().replace(/^.*[\\\/]/, '');
	     
	     $parent.removeClass('btn-default').addClass('btn-success disabled');
	     $parent.html("<i class='fa fa-refresh fa-spin'></i> Installing '"+filename+"'...");
	     $('#install-mod').submit();
	});
	
	$(document).on("click", "a[data-target=#modal_new_server]", function() {
	     var mod = $(this).data('mod');
	     $('#modal_new_server #mod').val(mod);
	     var $cfglist = $('#modal_new_server #configs');
	     $cfglist.children().remove();
	     
	     $.getJSON($SCRIPT_ROOT + '/_get_mod_configs/'+mod, function(data) {
    		 for (i in data['configs'])
    			 $cfglist.append("<option value='"+data['configs'][i]+"'>"+data['configs'][i]+"</option>");
	     });
	});
	
	$(document).on("click", "#modal_new_server .btn-success", function() {
		var srvmod = $('#modal_new_server #mod').val();
		var configfile = $(".modal-body #cfgfile").val();
		if (!configfile)
			return;
		
		$.getJSON($SCRIPT_ROOT + '/_create_server_instance/'+srvmod+'?fileconfig='+configfile, function(data) {
			check_server_data(data);

			if (data['success'])
			{
				$('#modal_new_server').modal('hide');
				window.location.reload();
			}
		});
	});
	
	$(document).on("click", ".remove-server-instance", function() {
		var srvid = $(this).data('id');
		var srvmod = $(this).data('mod');
		
		bootbox.dialog({
			message: "Are you sure?",
			title: "Delete '"+srvmod+"' Server Instance",
			buttons: {
			    success: {
			    	label: "Delete",
			    	className: "btn-danger",
			    	callback: function() {
						$.getJSON($SCRIPT_ROOT + '/_remove_server_instance/'+srvid, function(data) {
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
	
	$(document).on("click", ".menu-item-server-bin", function() {
		var $this = $(this);
		var $parent_ul = $this.parent().parent();
		var srvid = $parent_ul.data('id');
		var srvbin = $this.text().trim();
		
		$.getJSON($SCRIPT_ROOT + '/_set_server_binary/'+srvid+'/'+srvbin, function(data) {
			check_server_data(data);
		
			if (data['success'])
			{
				$parent_ul.find('li').removeClass('active');
				$this.parent().addClass('active');
				$('#btn-play-srv-'+srvid).removeClass('disabled');
			}
		});
	});
	
	$('#modal_instance_configuration').modal({'backdrop':'static', 'show':false});
	
	$(document).on("click", "a[data-target=#modal_instance_configuration]", function() {
	     var srvid = $(this).data('id');
	     $('#form-server-config #srvid').val(srvid);
	     $.getJSON($SCRIPT_ROOT + '/_get_server_config/'+srvid, function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 $("#modal_instance_configuration #alsrv").prop('checked', data['alsrv']);
		    	 $("#modal_instance_configuration #srvcfg").val(data['srvcfg']);
	    	 }
	    	 else
	    	 {
		    	 $("#modal_instance_configuration #alsrv").prop('checked', false);
		    	 $("#modal_instance_configuration #srvcfg").val("");
	    	 }
	     });
	});
	
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
				
				$port.text(data['port']);
				$name.text(data['name']);
				$gametype.text(data['gametype']);
				
				$('#modal_instance_configuration').modal('hide');
			}
		});
	});
	
	$(document).on("click", ".start-instance", function() {
		var srvid = $(this).data('id');
	     $.getJSON($SCRIPT_ROOT + '/_start_server_instance/'+srvid, function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 window.location.reload();
	    	 }
	     });
	});
	
	$(document).on("click", ".stop-instance", function() {
		var srvid = $(this).data('id');
	     $.getJSON($SCRIPT_ROOT + '/_stop_server_instance/'+srvid, function(data) {
	    	 check_server_data(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 window.location.reload();
	    	 }
	     });
	});
	
});
