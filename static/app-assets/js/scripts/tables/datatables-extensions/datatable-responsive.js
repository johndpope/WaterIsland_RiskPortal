/*=========================================================================================
    File Name: datatables-responsive.js
    Description: Datatable Population Functionality for M&A IDEA Database
    ----------------------------------------------------------------------------------------
    Author: Kshitij Gorde
==========================================================================================*/

$(document).ready(function() {

    var mna_idea_table = $('#mna_idea_table').DataTable({});
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