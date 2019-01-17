$(document).ready(function () {
    //Initialize the Database
    var credit_table = $('#credit_table').DataTable({
         paging: false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        columnDefs:[{targets:8, render:function(data){
            return moment(data).format('YYYY-MM-DD');
        }}],
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title:'',
                exportOptions: {
                    columns: [ 0,1,2,3,4,5,6,7,8,9,10]
                },
                customize: function ( win ) {
                    $(win.document.body)
                        .css( 'font-size', '10pt' )
                        .prepend(
                            '<p> Water Island Capital, Risk Portal</p>'
                        );

                    $(win.document.body).find( 'table' )
                        .addClass( 'compact' )
                        .css( 'font-size', 'inherit' );
                },
                autoPrint: true,
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                 exportOptions: {
                    columns: [ 0,1,2,3,4,5,6,7,8,9,10,11]
                },
            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        }
    });

    $('.table-responsive').on("click", "#credit_table tr td li a", function () {

        var current_deal = this.id.toString();
        // Handle Selected Logic Here
        if (current_deal.search('view_') != -1) {
            //Logic for Editing a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            var deal_id_to_view = current_deal.split('_')[1]; //Get the ID
            window.open("../risk/credit_show_deal?id=" + deal_id_to_view, '_blank');
        }

        else {
            //Logic for
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
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
                            url:'../risk/delete_credit_deal',
                            data:{'id':deal_id_to_edit},
                            success:function(response){
                                if(response==="Success"){
                                    //Delete Row from DataTable
                                    swal("Success! The Deal has been deleted!", {icon: "success"});
                                    //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                    credit_table.row($("#row_"+deal_id_to_edit)).remove().draw();

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


    });

    //New Deal Addition
    $('#submit_credit_new_deal_request').on('click', function () {

        //Get the Required Data
        var deal_name = $('#credit_deal_name').val();
        var deal_bucket = $('#credit_deal_bucket_select').val();
        var deal_strategy_type = $('#credit_deal_strategy_type').val();
        var catalyst =  $('#credit_catalyst_select').val();
        var catalyst_tier = $('#credit_catalyst_tier_select').val();
        var target_security_cusip = $('#credit_target_security_cusip').val();
        var coupon = $('#credit_coupon').val();
        var hedge_security_cusip = $('#credit_hedge_security_cusip').val();
        var estimated_closing_date = $('#credit_estimated_close_date').val();
        var upside_price = $('#credit_upside_price').val();
        var downside_price = $('#credit_downside_price').val();


        $.ajax({
            url: "../risk/add_new_credit_deal",
            type: "POST",
            data: {
                'deal_name': deal_name,
                'deal_bucket': deal_bucket,
                'deal_strategy_type': deal_strategy_type,
                'catalyst': catalyst,
                'catalyst_tier': catalyst_tier,
                'target_security_cusip': target_security_cusip,
                'coupon': coupon,
                'hedge_security_cusip': hedge_security_cusip,
                'estimated_closing_date':estimated_closing_date,
                'upside_price':upside_price,
                'downside_price':downside_price,
            },
            success: function (response) {

                $('#credit_new_deal_modal').modal('hide');
                location.reload();
                if (response === 'Failed') {
                    toastr.error('Adding Deal Failed', 'Please check your Inputs or contact support', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    toastr.success('Added New Deal', 'Please Refresh the page', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            }
        });
    });


});