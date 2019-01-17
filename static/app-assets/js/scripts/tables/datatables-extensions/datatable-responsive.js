/*=========================================================================================
    File Name: datatables-responsive.js
    Description: Datatable Population Functionality for M&A IDEA Database
    ----------------------------------------------------------------------------------------
    Author: Kshitij Gorde
==========================================================================================*/

$(document).ready(function() {

    var mna_idea_table = $('#mna_idea_table').DataTable({});

    // Submit a New Deal on Modal Click Event
    $('#submit_mna_idea_new_deal_request').click(function (e) {
        //Get the selector values and submit an ajax request
        var alpha_ticker = $('#mna_idea_new_deal_ticker').val();
        $.ajax({
        type: "POST",
        url: "../risk/add_new_mna_idea_deal",
        data:{'ticker':alpha_ticker, 'csrfmiddlewaretoken':$('#mna_idea_csrf_token').val()},
        success: function(response) {
        $('#mna_idea_new_deal_modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
        if(response == 'failed'){
            swal("Error!", "Adding Deal Failed!", "error");
        }
        else{
            //Append the New Row to Existing Table
            var newRow = '<tr id="row_'+response+'"><td>'+alpha_ticker+'</td><td></td><td></td><td></td><td></td><td></td>' +
                '<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>' +
                '<td><div class="btn-group">' +
                '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                '<i class="ft-settings"></i>' +
                '</button>' +
                '<ul class="dropdown-menu">' +
                '<li><a id="edit_'+response+'" data-value="{{ row.DealKey }}" class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                '<li><a id="delete_'+response+'" data-value="{{ row.DealKey }}" class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                '<li><a id="view_'+response+'" data-value="{{ row.DealKey }}" class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
                '</ul>' +
                '</div></td></tr>';

            //Re-initialize Datatable again
            mna_idea_table.row.add($(newRow)).draw();
        }
    },
    error: function(err) {
      console.log(err);
    }
    }).then(function() {
    //setTimeout(setTweets, 8000); //Todo: Check how to do this async (dynamic adding of points)
    });

    });



    // Event Delegation for Dynamically added elements

    $('.table-responsive').on("click","#mna_idea_table tr td li a", function(){

        var current_deal = this.id.toString();

        // Handle Selected Logic Here
        if(current_deal.search('edit_')!=-1){
            //Logic for Editing a Deal
            console.log('Editing Deal');
        }
        else if(current_deal.search('delete_')!=-1){
            //Logic for Deleting a deal
            //First Popup sweetAlert to Confirm Deletion

            deal_key_to_delete = current_deal.split('_')[1];

            // Send this Deal key to Django View to Delete and Wait for Response. If Response is successful, then Delete the row from DataTable

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Deal!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
                }).then((willDelete) => {
                    if (willDelete) {
                        //Handle Ajax request to Delete
                        $.ajax({
                            type:'POST',
                            url:'../risk/delete_mna_deal',
                            data:{'DealKey':deal_key_to_delete,'csrfmiddlewaretoken':$('#mna_idea_csrf_token').val()},
                            success:function(response){
                                if(response==="deal_key_delete_success"){
                                    //Delete Row from DataTable
                                    swal("Success! The Deal has been deleted!", {icon: "success"});
                                    //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                    mna_idea_table.row($("#row_"+deal_key_to_delete)).remove().draw();

                                }
                                else{
                                    //show a sweet alert
                                    swal("Error!", "Deleting Deal Failed!", "error");
                                    console.log('Deletion failed');
                                }
                            },
                            error:function (error) {
                                swal("Error!", "Deleting Deal Failed!", "error");
                                console.log(error);
                            }
                        });

                    }
                });
        }
        else{
            //Logic to View the Deal
            console.log('Viewing Deal');

        }



    });



});