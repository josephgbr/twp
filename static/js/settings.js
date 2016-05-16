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
	
	$(document).on('click', "#form-settings-change-pass a[id='btn-submit']", function(e){
		var passOld = $('#pass-old').val();
		var passNew = $('#pass-new').val();
		var passNewRepeat = $('#pass-new-repeat').val();
		
		// Validate Form
		$('#pass-old,#pass-new,#pass-new-repeat').tooltip('hide');
		if (!passOld)
		{
			$('#pass-old').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#pass-old').tooltip('show');
			return;
		}
		if (!passNew)
		{
			$('#pass-new').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#pass-new').tooltip('show');
			return;
		}
		if (!passNewRepeat)
		{
			$('#pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#pass-new-repeat').tooltip('show');
			return;
		}
		if (passNew !== passNewRepeat)
		{
			$('#pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_PASSWORD_DOESNT_MATCH});
			$('#pass-new-repeat').tooltip('show');
			return;
		}
		//
		
		var hashObj = new jsSHA("SHA-512", "TEXT");
		hashObj.update(passNew);
		passNew = hashObj.getHash("HEX");
		
		$.post($SCRIPT_ROOT + '/_set_user_password', 'pass_old='+passOld+'&pass_new='+passNew, function(data){
			check_server_data(data);
			
			if (data['success'])
			{
				$('#admin-pass-old,#admin-pass-new,#admin-pass-new-repeat').val('');
				bootbox.dialog({
					message: "<p class='text-center' style='color:#008000;'><i class='fa fa-check'></i> "+$BABEL_STR_PASSWORD_CHANGED_SUCCESSFULLY+"</p>",
					title: $BABEL_STR_CONFIGURATION_CHANGED,
					buttons: {
						success: {
							label: $BABEL_STR_OK,
							className: "btn-default",
							callback: function() {
								window.location.reload();
							}
						}
					}
				});
			}
		});
	});
	
	// Create User Slot
	$(document).on("click", "#create_user_slot", function(){
		$.post($SCRIPT_ROOT + '/_create_user_slot', '', function(data){
			check_server_data(data);
			
			if (data['success'] && data['user'])
			{
				var createDate = moment(data['user']['create_date']).utc().format("YYYY-MM-DD HH:mm:ss");
				var row = "<tr id='user-"+data['user']['id']+"'>"+
							"<td><i>User Slot '"+data['user']['token'].slice(0,10)+"...'</i></td>"+
							"<td>"+createDate+"</td>"+
							"<td>"+$BABEL_STR_NEVER+"</td>"+
							"<td class='text-right'>"+
							"<button type='button' data-uid='"+data['user']['id']+"' class='btn btn-xs btn-success copy-link-user btn-clipboard' data-clipboard-text='http://"+window.location.host+"/user_reg/"+data['user']['token']+"'>"+
							"<i class='fa fa-link'></i> "+$BABEL_STR_COPY_LINK+
							"</button> "+
							"<button type='button' data-uid='"+data['user']['id']+"' class='btn btn-xs btn-default' data-toggle='modal' data-target='#modal_user_permissions'>"+
							"<i class='fa fa-cog'></i> "+$BABEL_STR_PERMISSIONS+
							"</button> "+
							"<button type='button' class='remove-user btn btn-link btn-xs btn-delete-row' data-uid='"+data['user']['id']+"' href='#' title='Cancel User Slot'><i class='fa fa-remove'></i></button>"+
							"</td>";
				$('#tbody-users').append(row);
			}
		});
	});
	
	// Open Dialog Create Permission Level
	$(document).on("click", "button[data-target='#modal_create_permission_level']", function(){
		$('#form-create-permission-level #name').val('');
		$("#form-create-permission-level input[type='checkbox']").each(function(){ $(this).prop('checked', false); });
	});
	
	// Press "OK" button in Create Permission Level Dialog
	$(document).on("click", "#modal_create_permission_level .btn-success", function(){
		$.post($SCRIPT_ROOT + '/_create_permission_level', $('#form-create-permission-level').serialize(), function(data) {
			check_server_data(data);
			
			if (data['success'] && data['perm'])
			{
				var row = "<tr id='permission-"+data['perm']['id']+"'>"+
							"<td>"+data['perm']['name']+"</td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='start' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['start']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['start']?'fa-check':'fa-minus')+"'></i></button></td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='stop' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['stop']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['stop']?'fa-check success':'fa-minus')+"'></i></button></td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='config' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['config']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['config']?'fa-check success':'fa-minus')+"'></i></button></td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='econ' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['econ']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['econ']?'fa-check success':'fa-minus')+"'></i></button></td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='issues' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['issues']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['issues']?'fa-check success':'fa-minus')+"'></i></button></td>"+
							"<td class='text-center'><button type='button' data-id='"+data['perm']['id']+"' data-perm='log' class='btn btn-link btn-xs btn-perm' style='color:"+(data['perm']['log']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['log']?'fa-check success':'fa-minus')+"'></i></button></td>"+
							"<td class='text-right'>"+
							"<button type='button' class='remove-permission-level btn btn-link btn-xs btn-delete-row' data-id='"+data['perm']['id']+"' href='#' title='"+$BABEL_STR_REMOVE_PERMISSION_LEVEL+"'><i class='fa fa-remove'></i></button>"+
							"</td>"+
							"</tr>";
				$('#tbody-permission-levels').append(row);
				$('#modal_create_permission_level').modal('hide');
				$('#modal_user_permissions select').append("<option value='"+data['perm']['id']+"'>"+data['perm']['name']+"</option>");
			}
		});
	});
	
	
	// Change Permission inline
	$(document).on('click', '.btn-perm', function(){
		var $this = $(this);
		var id = $this.data('id');
		var perm = $this.data('perm');
		
		toggle_perm_icon($this.children('i'));
		$.post($SCRIPT_ROOT + '/_change_permission_level', 'id='+id+'&perm='+perm, function(data){
			check_server_data(data);

			if (!data['success'])
				toggle_perm_icon($this.children('i'));
		});
	});
	
	// Remove Permission Level
	$(document).on("click", ".remove-permission-level", function(){
		var permid = $(this).data('id');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE,
			title: $BABEL_STR_DELETE+" "+$BABEL_STR_PERMISSION_LEVEL,
			buttons: {
			    success: {
			    	label: $BABEL_STR_DELETE,
			    	className: "btn-danger",
			    	callback: function() {		    		
						$.post($SCRIPT_ROOT + '/_remove_permission_level/'+permid, '', function(data){
							check_server_data(data);
							
							if (data['success'])
							{
								$('#permission-'+permid).remove();
								$('#modal_user_permissions select').children("option[value='"+permid+"']").remove();
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
	
	// Remove User
	$(document).on("click", ".remove-user", function(){
		var uid = $(this).data('uid');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE,
			title: $BABEL_STR_DELETE+" "+$BABEL_STR_USER,
			buttons: {
			    success: {
			    	label: $BABEL_STR_DELETE,
			    	className: "btn-danger",
			    	callback: function() {		    		
						$.post($SCRIPT_ROOT + '/_remove_user/'+uid, '', function(data){
							check_server_data(data);
							
							if (data['success'])
								$('#user-'+uid).remove();
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
	
	// Open Dialog User Permissions
	$(document).on("click", "button[data-target='#modal_user_permissions']", function(){
		var uid = $(this).data('uid');

		$('#modal_user_permissions #uid').val(uid);
		
		$.post($SCRIPT_ROOT + '/_get_user_servers_level/'+uid, '', function(data){
			check_server_data(data);
			
			$("#modal_user_permissions select").each(function(){
				$(this).children("option")[0].selected = true;
			});
			
			if (data['success'])
			{
				for (var i in data['perms'])
					$('#modal_user_permissions #perm-'+data['perms'][i][0]+' option[value='+data['perms'][i][1]+']')[0].selected = true;
			}
			else
				$('#modal_user_permissions').modal('hide');
		});
	});
	
	// Change User Server Perm
	$(document).on('change', '#modal_user_permissions select', function(){
		var uid = $('#modal_user_permissions #uid').val();
		var $this = $(this);
		var select_id = $this.attr('id');
		var select_val = $this.val();
		var srvid = $this.data('srvid');
		
		$.post($SCRIPT_ROOT + '/_set_user_server_level/'+uid+'/'+srvid, 'perm_id='+select_val, function(data){
			check_server_data(data);
		});
	});
	
});

function toggle_perm_icon(elm)
{
	if (elm.hasClass('fa-check'))
		elm.removeClass('fa-check').addClass('fa-minus').css('color','#800000');
	else
		elm.removeClass('fa-minus').addClass('fa-check').css('color','#008000');
}
