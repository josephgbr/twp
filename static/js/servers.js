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
			console.log(data);
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
			if (data['success'])
			{
				$parent_ul.find('i').each(function(e) { $(this).remove(); });
				$('#btn-play-srv-'+srvid).removeClass('disabled');
				$this.prepend("<i class='fa fa-check'> </i>");
			}
		});
	});
	
});
