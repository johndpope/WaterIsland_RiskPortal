$(document).ready(function(){
    // On Clicking Save Changes, POST and Ajax Request and Refresh the current page.
    // Show toast on Success or Failure

    /*  RISK FACTORS SAVE CHANGES */
    $('#submit_mna_idea_risk_form').on('click', function () {

       for(var i=0;i<9;i++){
           $('.loader-inner').append('<div></div>');
       }

        $('.loader-inner').loaders();
        // Gather Data and POST Asynchronously
        let data = {};
        data['deal_id'] = $('#deal_id').val();
        data['definiteness'] = $('#definiteness').val();
        data['hostile_friendly'] = $('#hostile_friendly').val();
        data['strategic_pe'] = $('#strategic_pe').val();
        data['deal_rationale'] = $('#deal_rationale').val();
        data['premium_percentage'] = $('#premium').val();
        data['stock_cash'] = $('#stock_cash').val();
        data['financing_percent_of_deal_value'] = $('#financing_percent_deal_value').val();
        data['proforma_leverage'] = $('#proforma_leverage').val();
        data['estimated_close'] = $('#estimated_closing_date').val();
        data['go_shop'] = $('#go_shop').val();
        data['divestitures_required'] = $('#divestitures_required').val();
        data['termination_fee_acquirer'] = $('#termination_fee_acquirer').val();
        data['termination_fee_target'] = $('#termination_fee_target').val();
        data['fair_valuation'] = $('#fair_valuation').val();
        data['cyclical_industry'] = $('#cyclical_industry').val();
        data['sec_required'] = $('#sec_required').val();
        data['sec_expected'] = $('#expected_sec').val();
        data['sec_actual'] = $('#actual_sec').val();
        data['hsr_required'] = $('#hsr_required').val();
        data['hsr_expected'] = $('#expected_hsr').val();
        data['hsr_actual'] = $('#actual_hsr').val();
        data['mofcom_required'] = $('#mofcom_required').val();
        data['mofcom_expected'] = $('#expected_mofcom').val();
        data['mofcom_actual'] = $('#actual_mofcom').val();
        data['cfius_required'] = $('#cfius_required').val();
        data['cfius_expected'] = $('#expected_cfius').val();
        data['cfius_actual'] = $('#actual_cfius').val();
        data['ec_required'] = $('#ec_required').val();
        data['ec_expected'] = $('#expected_ec').val();
        data['ec_actual'] = $('#actual_ec').val();
        data['accc_required'] = $('#accc_required').val();
        data['accc_expected'] = $('#expected_accc').val();
        data['accc_actual'] = $('#actual_accc').val();
        data['canada_required'] = $('#canada_required').val();
        data['canada_expected'] = $('#expected_canada').val();
        data['canada_actual'] = $('#actual_canada').val();
        data['cade_required'] = $('#cade_required').val();
        data['cade_expected'] = $('#expected_cade').val();
        data['cade_actual'] = $('#actual_cade').val();
        data['other_country_one'] = $('#other_country_one').val();
        data['other_country_two'] = $('#other_country_two').val();
        data['acquirer_sh_vote_required'] = $('#sh_vote_required').val();
        data['target_sh_vote_required'] = $('#target_sh_vote_required').val();
        data['acquirer_becomes_target'] = $('#acquirer_becomes_target').val();
        data['potential_bidding_war'] = $('#potential_bidding_war').val();
        data['commodity_risk'] = $('#commodity_risk').val();
        data['estimated_market_share_acquirer'] = $('#estimated_market_share_acquirer').val();
        data['estimated_market_share_target'] = $('#estimated_market_share_target').val();


        $.ajax({
            'url': '../risk/update_or_create_arb_risk_factors',
            'type': 'POST',
            'data': data,
            success: function (response) {
                console.log(response);
                $('.loader-inner').empty();
                if (response === 'Failed') {
                    toastr.error('Failed', 'Failed adding/updating Risk factors', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {

                    toastr.success('Risk Factors have been updated for this deal', 'Update Successful', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            },
            error: function (response) {

            }
        })


    });


    /* RISK FACTORS POPULATE */


});