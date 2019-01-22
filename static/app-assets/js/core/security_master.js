$(document).ready(function () {

    let security_master_table = $('#wic_security_master_table').DataTable();

    /*
    Function to Submit a new Deal request
     */
    $('#submit_security_master_new_deal').on('click', function () {
        // Gather the Inputs
        let deal_name = $('#security_master_deal_name').val();
        let cash_terms = $('#security_master_cash_terms').val();
        let stock_terms = $('#security_master_stock_terms').val();
        let number_of_target_dividends = $('#security_master_number_of_target_dividends').val();
        let number_of_acquirer_dividends = $('#security_master_number_of_acquirer_dividends').val();
        let target_dividend_rate = $('#security_master_target_dividend_rate').val();
        let acquirer_dividend_rate = $('#security_master_acquirer_dividend_rate').val();
        let closing_date = $('#security_master_closing_date').val();

        let data = {};
        data['deal_name'] = deal_name;
        data['cash_terms'] = cash_terms;
        data['stock_terms'] = stock_terms;
        data['number_of_target_dividends'] = number_of_target_dividends;
        data['number_of_acquirer_dividends'] = number_of_acquirer_dividends;
        data['target_dividend_rate'] = target_dividend_rate;
        data['acquirer_dividend_rate'] = acquirer_dividend_rate;
        data['closing_date'] = closing_date;

        // Open an Ajax Request and on Success Reload the Page...
        $.ajax({
            url:'../securities/add_new_deal_to_security_master',
            type:'POST',
            data:data,
            success:function(response){
                if(response === 'Success'){
                    toastr.success('Added New Deal', 'Refreshing Page', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                    location.reload();
                }
                else{
                    toastr.error('Failed to Add', 'Something went wrong', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }

            },
            error:function(){
                alert('Something went wrong')
            }
        })

    });




    /** HANDLE Edits FOR A GIVEN DEAL **/
    $('.table-responsive').on("click", "#wic_security_master_table tr td li a", function () {
        let current_deal = this.id.toString();

        // Handle Selected Logic Here
        if (current_deal.search('edit_') != -1) {
            //Logic for Editing a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            let deal_id_to_edit = current_deal.split('_')[1]; //Get the I
            $.ajax({
                url: "../securities/add_new_deal_to_security_master",
                method: "POST",
                data: {
                    'deal_id': deal_id_to_edit,
                    'prepopulation_request': true,
                },
                success: function (response) {
                    let deal_object = response['deal_object'];

                    $('#security_master_deal_name').val(deal_object[0][1]);
                    $('#security_master_cash_terms').val(deal_object[0][2]);
                    $('#security_master_stock_terms').val(deal_object[0][3]);
                    $('#security_master_number_of_target_dividends').val(deal_object[0][4]);
                    $('#security_master_number_of_acquirer_dividends').val(deal_object[0][5]);
                    $('#security_master_target_dividend_rate').val(deal_object[0][6]);
                    $('#security_master_acquirer_dividend_rate').val(deal_object[0][7]);
                    $('#security_master_closing_date').val(deal_object[0][8]);

                    // Fill Values in the Modal and Then OPEN the modal
                    $('#security_master_new_deal_modal').modal('show');

                },
                error: function () {
                    swal("Error!", "Editing Deal Failed!. Please check the inputs", "error");
                }
            });
        }
    });

});