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
		
		$.post($SCRIPT_ROOT + '/_set_user_password', 'pass_old='+passOld+'&pass_new='+passNew, function(data) {
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
	$(document).on("click", "#create_user_slot", function() {
		$.post($SCRIPT_ROOT + '/_create_user_slot', '', function(data) {
			check_server_data(data);
			
			if (data['success'] && data['user'])
			{
				var row = "<tr id='user-"+data['user']['id']+"'>"+
							"<td><i>User Slot '"+data['user']['token'].slice(0,10)+"...'</i></td>"+
							"<td>"+data['user']['create_date']+"</td>"+
							"<td>"+data['user']['last_login_date']+"</td>"+
							"<td class='text-right'>"+
							"<a data-id='"+data['user']['id']+"' class='btn btn-xs btn-default' data-toggle='modal' data-target='#modal_user_permissions'>"+
							"<i class='fa fa-cog'></i> Permissions"+
							"</a>"+
							"<a class='remove-user btn btn-xs btn-delete-row' data-id='"+data['user']['id']+"' href='#' title='Cancel User Slot'><i class='fa fa-remove'></i></a>"+
							"</td>";
				$('#tbody-users').append(row);
			}
		});
		
		return false;
	});
	
	// Open Dialog Create Permission Level
	$(document).on("click", "a[data-target='#modal_create_permission_level']", function() {
		$('#form-create-permission-level #name').val('');
		$("#form-create-permission-level input[type='checkbox']").each(function(){ $(this).prop('checked', false); });
	});
	
	// Press "OK" button in Create Permission Level Dialog
	$(document).on("click", "#modal_create_permission_level .btn-success", function() {
		$.post($SCRIPT_ROOT + '/_create_permission_level', $('#form-create-permission-level').serialize(), function(data) {
			check_server_data(data);
			
			if (data['perm'])
			{
				var row = "<tr id='permission-"+data['perm']['id']+"'>"+
							"<td>"+data['perm']['name']+"</td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='start' class='btn btn-xs btn-perm' style='color:"+(data['perm']['start']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['start']?'fa-check':'fa-minus')+"'></i></a></td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='stop' class='btn btn-xs btn-perm' style='color:"+(data['perm']['stop']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['stop']?'fa-check success':'fa-minus')+"'></i></a></td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='config' class='btn btn-xs btn-perm' style='color:"+(data['perm']['config']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['config']?'fa-check success':'fa-minus')+"'></i></a></td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='econ' class='btn btn-xs btn-perm' style='color:"+(data['perm']['econ']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['econ']?'fa-check success':'fa-minus')+"'></i></a></td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='issues' class='btn btn-xs btn-perm' style='color:"+(data['perm']['issues']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['issues']?'fa-check success':'fa-minus')+"'></i></a></td>"+
							"<td class='text-center'><a data-id='"+data['perm']['id']+"' data-perm='log' class='btn btn-xs btn-perm' style='color:"+(data['perm']['log']?'#008000':'#800000')+"'><i class='fa "+(data['perm']['log']?'fa-check success':'fa-minus')+"'></i></a></td>"+
							"<td class='text-right'>"+
							"<a class='remove-permission-level btn btn-xs btn-delete-row' data-id='"+data['perm']['id']+"' href='#' title='"+$BABEL_STR_REMOVE_PERMISSION_LEVEL+"'><i class='fa fa-remove'></i></a>"+
							"</td>"+
							"</tr>";
				$('#tbody-permission-levels').append(row);
				$('#modal_create_permission_level').modal('hide');
			}
		});
	});
	
	
	// Change Permission inline
	$(document).on('click', '.btn-perm', function(){
		var $this = $(this);
		var id = $this.data('id');
		var perm = $this.data('perm');
		
		toggle_perm_icon($this.children('i'));
		$.post($SCRIPT_ROOT + '/_change_permission_level', 'id='+id+'&perm='+perm, function(data) {
			check_server_data(data);

			if (!data['success'])
				toggle_perm_icon($this.children('i'));
		});
		
		return false;
	});
	
	// Remove Permission Level
	$(document).on("click", ".remove-permission-level", function() {
		var permid = $(this).data('id');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE,
			title: $BABEL_STR_DELETE+" "+$BABEL_STR_PERMISSION_LEVEL,
			buttons: {
			    success: {
			    	label: $BABEL_STR_DELETE,
			    	className: "btn-danger",
			    	callback: function() {		    		
						$.post($SCRIPT_ROOT + '/_remove_permission_level/'+permid, '', function(data) {
							check_server_data(data);
							
							if (data['success'])
								$('#permission-'+permid).remove();
						});
			    	}
			    },
			    main: {
			    	label: "Cancel",
			    	className: "btn-default"
			    }
			}
		});
		
		return false;
	});
	
	// Remove User
	$(document).on("click", ".remove-user", function() {
		var uid = $(this).data('id');
		
		bootbox.dialog({
			message: $BABEL_STR_ARE_YOU_SURE,
			title: $BABEL_STR_DELETE+" "+$BABEL_STR_USER,
			buttons: {
			    success: {
			    	label: $BABEL_STR_DELETE,
			    	className: "btn-danger",
			    	callback: function() {		    		
						$.post($SCRIPT_ROOT + '/_remove_user/'+uid, '', function(data) {
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
		
		return false;
	});
	
});

function toggle_perm_icon(elm)
{
	if (elm.hasClass('fa-check'))
		elm.removeClass('fa-check').addClass('fa-minus').css('color','#800000');
	else
		elm.removeClass('fa-minus').addClass('fa-check').css('color','#008000');
}
