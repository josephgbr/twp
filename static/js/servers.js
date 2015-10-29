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

	$(document).on("click", "a[data-target=#modal_new_server]", function() {
	     var gametype = $(this).data('gm');
	     $('#modal_new_server #gamemode').val(gametype);
	     $(".modal-body #cfgfile").val($SERVERS_BASEPATH+'/'+gametype+'/server.cfg');
	});
	
	$(document).on("click", "#modal_new_server .btn-success", function() {
		var gametype = $('#modal_new_server #gamemode').val();
		var configfile = $(".modal-body #cfgfile").val();
		$.getJSON($SCRIPT_ROOT + '/_create_server_instance/'+gametype+'?fileconfig='+configfile, function(data) {
			check_auth(data);

			if (data['success'])
			{
				$('#modal_new_server').modal('hide');
				window.location.reload();
			}
		});
	});
	
	$(document).on("click", ".remove-server-instance", function() {
		var srvid = $(this).data('id');
		var srvgm = $(this).data('gm');
		
		bootbox.dialog({
			message: "Are you sure?",
			title: "Delete "+srvgm+" Server Instance",
			buttons: {
			    success: {
			    	label: "Delete",
			    	className: "btn-danger",
			    	callback: function() {
						$.getJSON($SCRIPT_ROOT + '/_remove_server/'+srvid, function(data) {
							check_auth(data);
							
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
		$this = $(this);
		$parent_ul = $this.parent().parent();
		var srvid = $parent_ul.data('id');
		var srvbin = $this.text().trim();
		
		$.getJSON($SCRIPT_ROOT + '/_set_server_binary/'+srvid+'/'+srvbin, function(data) {
			check_auth(data);
		
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
	    	 check_auth(data);
	    	 
	    	 if (data['success'])
	    	 {
		    	 $("#modal_instance_configuration #alsrv").prop('checked', data['alsrv']);
		    	 $("#modal_instance_configuration #srvcfg").text(data['srvcfg']);
	    	 }
	     });
	});
	
	$(document).on("click", "#modal_instance_configuration .btn-primary", function() {
		$this = $(this);

		$.post('/_save_server_config', $('#form-server-config').serialize(), function(data) {
			check_auth(data);
		});
		
		$('#modal_instance_configuration').modal('hide');
	});
	
});
