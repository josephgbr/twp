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
	
	$(document).on('click', "#form-settings-admin-pass a[id='btn-submit']", function(e){
		var passOld = $('#admin-pass-old').val();
		var passNew = $('#admin-pass-new').val();
		var passNewRepeat = $('#admin-pass-new-repeat').val();
		
		// Validate Form
		$('#admin-pass-old,#admin-pass-new,#admin-pass-new-repeat').tooltip('hide');
		if (!passOld)
		{
			$('#admin-pass-old').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#admin-pass-old').tooltip('show');
			return;
		}
		if (!passNew)
		{
			$('#admin-pass-new').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#admin-pass-new').tooltip('show');
			return;
		}
		if (!passNewRepeat)
		{
			$('#admin-pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_CANT_BE_EMPTY});
			$('#admin-pass-new-repeat').tooltip('show');
			return;
		}
		if (passNew !== passNewRepeat)
		{
			$('#admin-pass-new-repeat').tooltip({trigger:'manual', placement:'bottom', title:$BABEL_STR_PASSWORD_DOESNT_MATCH});
			$('#admin-pass-new-repeat').tooltip('show');
			return;
		}
		//
		
		var hashObj = new jsSHA("SHA-512", "TEXT");
		hashObj.update(passNew);
		passNew = hashObj.getHash("HEX");
		
		$.post($SCRIPT_ROOT + '/_set_user_password/1', 'pass_old='+passOld+'&pass_new='+passNew, function(data) {
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
							"<td class='text-center'><i class='fa "+(data['perm']['create']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['delete']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['start']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['stop']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['config']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['econ']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['issues']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-center'><i class='fa "+(data['perm']['log']?'fa-check':'fa-close')+"'></i></td>"+
							"<td class='text-right'>"+
							"<a class='remove-permission-level btn btn-xs' data-id='"+data['perm']['id']+"' href='#' title='"+$BABEL_STR_REMOVE_PERMISSION_LEVEL+"'><i class='fa fa-remove'></i></a>"+
							"</td>"+
							"</tr>";
				$('#tbody-permission-levels').append(row);
				$('#modal_create_permission_level').modal('hide');
			}
		});
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
	});
});
