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
	
	$(document).on("keypress", ".deny-enter :input:not(textarea)", function(event) {
	    if (event.keyCode == 13) {
	        event.preventDefault();
	    }
	});
	
});

function check_server_data(data)
{
	if (!data || data == undefined)
		return;
	
	if (data['notauth'])
	{
		bootbox.dialog({
			message: "<p class='text-center' style='color:#800000;'><i class='fa fa-warning'></i> The session has expired <i class='fa fa-warning'></i></p>",
			title: "Session Expired!",
			buttons: {
				success: {
					label: "Oh!",
					className: "btn-default",
					callback: function() {
						window.location.reload();
					}
				}
			}
		});
	}
	else if (data['error'])
	{
		var errormsg = data['errormsg']?data['errormsg']:"Interal error has ocurred!";
		
		bootbox.dialog({
			message: "<p class='text-center' style='color:#800000;'>"+errormsg+"</p>",
			title: "Error - Ooops! <i class='fa fa-frown-o'></i>",
			buttons: {
				success: {
					label: "Damn",
					className: "btn-default"
				}
			}
		});
	}
}