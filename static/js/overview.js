function refreshMemoryHost(){
	$.getJSON($SCRIPT_ROOT + '/_refresh_memory_host', function(data) {
		$('#memory-usage').text(data.used +' / '+ data.total +' MB').fadeIn();
		$('#memory-usage-bar').css({'width':data.percent+'%'});
		$('#memory-cache-usage-bar').css({'width':data.percent_cached+'%'});
	});
}
function refreshCPUHost(){
	$.get($SCRIPT_ROOT + '/_refresh_cpu_host', function(data) {
		$('#cpu-usage').text(data +'%').fadeIn();
		$('#cpu-usage-bar').css({'width':data +'%'});
	});
}
function refreshDiskHost(){
	$.getJSON($SCRIPT_ROOT + '/_refresh_disk_host', function(data) {
		$('#disk-usage').text(data.used +' ('+ data.free +' free)').fadeIn();
		$('#disk-usage-bar').css({'width':data.percent});
	});
}
function refreshUptimeHost(){
	$.getJSON($SCRIPT_ROOT + '/_refresh_uptime_host', function(data) {
		$('#uptime').text('Uptime: ' + data.day +' day(s) '+ data.time).fadeIn();
	});
}
function memory_color(value){
	if(value != 0)
		if ('0' <= value && value <= '512')
			 return 'success';
		else if ('512' <= value && value < '1024')
			return 'warning';
		else
			return 'important';
}
function mastersrv_servers(){
	$.getJSON($SCRIPT_ROOT + '/_get_all_online_servers', function(data) {
		$('#twmslist-load').hide();
		
		if (data['servers'].length > 0)
		{
			var $table = $('#twmslist tbody');
			var cont = 0;
			for (reg in data['servers']) {
				var row = "<tr>";
				row += "<td>"+reg+"</td>";
				row += "<td>"+data['servers'][reg].name+"</td>";
				row += "<td>"+data['servers'][reg].gametype+"</td>";
				row += "<td>"+data['servers'][reg].players+"/"+data['servers'][reg].max_players+"</td>";
				row += "<td>"+data['servers'][reg].map+"</td>";
				row += "<td class='text-right'>"+Math.round(data['servers'][reg].latency*1000)+"</td>";
				row += "</tr>";
				$table.append(row);
			}
			$('#twmslist').show();
		}
		else
		{
			$('#twmslist-empty').show();
		}
	});
}
function refresh(){
	refreshMemoryHost();
	refreshCPUHost();
	refreshDiskHost();
	refreshUptimeHost();
}
$(function() {
	$('#memory-usage').hide();
	$('#cpu-usage').hide();
	$('#disk-usage').hide();
	$('#uptime').hide();
	$('#twmslist').hide();
	$('#twmslist-empty').hide();
	
	refresh();
	mastersrv_servers();
	window.setInterval('refresh()', $REFRESH_TIME);
});