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
		if (confirm("Really like delete server instance?"))
		{
			$.getJSON($SCRIPT_ROOT + '/_remove_server/'+srvid, function(data) {
				if (data['success'])
				{
					window.location.reload();
				}
			});
		}
	});
});
