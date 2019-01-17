$(document).ready(function () {
    //Initialize the Database
    var mna_idea_table = $('#mna_idea_table').DataTable({
         paging: false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        columnDefs:[{targets:2, render:function(data){
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

    $('.table-responsive').on("click", "#mna_idea_table tr td li a", function () {

        var current_deal = this.id.toString();
        // Handle Selected Logic Here
        if (current_deal.search('view_') != -1) {
            //Logic for Opening a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            let deal_id_to_view = current_deal.split('_')[1]; //Get the ID
            window.open("../risk/show_mna_idea?mna_idea_id=" + deal_id_to_view, '_blank');
            return false;

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
                            url:'../risk/delete_mna_idea',
                            data:{'id':deal_id_to_edit},
                            success:function(response){
                                if(response==="Success"){
                                    //Delete Row from DataTable
                                    swal("Success! The IDEA has been deleted!", {icon: "success"});
                                    //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                    mna_idea_table.row($("#row_"+deal_id_to_edit)).remove().draw();

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

    //Deal Value Client-side Calculation
    $('#calculate_deal_value').on('click', function(){
      //Formula is ((cash terms)+(acquirer ticker last price*share terms)+(target dividends)-(acquirer dividends) + (short rebate)+(stub/cvr value))
        var acquirer_ticker = $('#mna_idea_simulate_acquirer_ticker').val();
        var deal_cash_terms = $('#mna_idea_simulate_cash_terms').val();
        var deal_stock_terms = $('#mna_idea_simulate_share_terms').val();
        var target_dividends = $('#mna_idea_simulate_target_dividends').val();
        var acquirer_dividends = $('#mna_idea_simulate_acquirer_dividends').val();
        var short_rebate = $('#mna_idea_simulate_short_rebate').val();
        var stub_cvr_value = $('#mna_idea_simulate_stub_cvr_value').val();

        //Get the Deal Value from Server....
        $.ajax({
            'type':'POST',
            'url':'../risk/calculate_mna_idea_deal_value',
            'data':{
                'acquirer_ticker':acquirer_ticker,
                'deal_cash_terms':deal_cash_terms,
                'deal_stock_terms':deal_stock_terms,
                'target_dividends':target_dividends,
                'acquirer_dividends':acquirer_dividends,
                'short_rebate':short_rebate,
                'stub_cvr_value':stub_cvr_value
            },
            success:function(response){
                console.log(response);
                //Set the Deal Value parameter....
                $('#mna_idea_simulate_deal_value').val(response); //To be Calculated Automatically
            },
            error: function(err){
                alert(err);
            }
        })



    });


    //New Deal Addition
    $('#submit_mna_idea_new_deal_request').on('click', function () {

        //Get the Required Data
        var deal_name = $('#mna_idea_simulate_dealname').val();
        var analyst = $('#mna_idea_simulate_analyst').val();
        var target_ticker = $('#mna_idea_simulate_target_ticker').val();
        var acquirer_ticker = $('#mna_idea_simulate_acquirer_ticker').val();
        var deal_cash_terms = $('#mna_idea_simulate_cash_terms').val();
        var deal_stock_terms = $('#mna_idea_simulate_share_terms').val();
        var deal_value = $('#mna_idea_simulate_deal_value').val(); //To be Calculated Automatically
        var csrf_token = $('#mna_idea_csrf_token').val();
        var expected_close = $('#mna_idea_simulate_expected_close').val();
        var target_dividends = $('#mna_idea_simulate_target_dividends').val();
        var acquirer_dividends = $('#mna_idea_simulate_acquirer_dividends').val();
        var short_rebate = $('#mna_idea_simulate_short_rebate').val();
        var fx_carry = $('#mna_idea_simulate_fx_carry_percentage').val();
        var stub_cvr_value = $('#mna_idea_simulate_stub_cvr_value').val();
        var target_downside = $('#mna_idea_simulate_target_downside').val();
        var acquirer_upside = $('#mna_idea_simulate_acquirer_upside').val();
        var loss_tolerance = $('#mna_idea_simulate_loss_tolerance').val();

        $.ajax({
            url: "../risk/add_new_mna_idea",
            type: "POST",
            data: {
                'deal_name': deal_name,
                'analyst': analyst,
                'target_ticker': target_ticker,
                'acquirer_ticker': acquirer_ticker,
                'deal_cash_terms': deal_cash_terms,
                'deal_stock_terms': deal_stock_terms,
                'deal_value': deal_value,
                'csrfmiddlewaretoken': csrf_token,
                'expected_close':expected_close,
                'target_dividends':target_dividends,
                'acquirer_dividends':acquirer_dividends,
                'short_rebate':short_rebate,
                'fx_carry':fx_carry,
                'stub_cvr_value':stub_cvr_value,
                'target_downside':target_downside,
                'acquirer_upside':acquirer_upside,
                'loss_tolerance':loss_tolerance
            },
            success: function (response) {
                $('#mna_idea_new_deal_modal').modal('hide');
                if (response === 'Failed') {
                    toastr.error('Adding IDEA Failed', 'Please check your Inputs or contact support', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    toastr.success('Added New IDEA', 'Please Refresh the page', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            }
        });
    });


});