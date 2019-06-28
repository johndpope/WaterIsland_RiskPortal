$(document).ready(function () {
    $("#create_mna_deal_error_div").hide();
    $("#create_mna_deal_present_msg_div").hide();
    $('#deal_name').focusout(function() {
        var deal_name = $('#deal_name').val();
        if (deal_name) {
            $.ajax({
                'type': 'POST',
                'url': '../risk/check_if_deal_present',
                'data': {'deal_name': deal_name},
                success: function (response) {
                    if (response.msg == 'Success') {
                        if (response.ma_deal_present & response.formulae_present) {
                            $('#create_mna_deal_present_msg').addClass("alert alert-danger");
                            $('#create_mna_deal_present_msg').html("<strong>Error: " + deal_name + "</strong> is already present in " +
                                "both <strong>Formulae Downside</strong> and <strong>MA Deals</strong> page.");
                            $("#create_mna_deal_present_msg_div").show();
                        }
                        else if (response.ma_deal_present) {
                            $('#create_mna_deal_present_msg').addClass("alert alert-danger");
                            $('#create_mna_deal_present_msg').html("<strong>Note: " + deal_name + "</strong> is already present in " +
                                "<strong>MA Deals</strong> page. It will be saved to <strong>Formulae Downside</strong> Page Only.");
                            $("#create_mna_deal_present_msg_div").show();
                        }
                        else if (response.formulae_present) {
                            $('#create_mna_deal_present_msg').addClass("alert alert-danger");
                            $('#create_mna_deal_present_msg').html("<strong>Note: " + deal_name + "</strong> is already present in " +
                                "<strong>Formulae Downside</strong>. It will be saved to <strong>MA Deals</strong> Page Only.");
                            $("#create_mna_deal_present_msg_div").show();
                        }
                        else {
                            $("#create_mna_deal_present_msg_div").hide();
                        }
                    }
                    else {
                        $("#create_mna_deal_present_msg_div").hide();
                    }
                },
                error: function (err) {
                    alert(err);
                }
            })
        }
        $("#create_mna_deal_present_msg_div").hide();
    });

    $('#calculate_deal_value').on('click', function () {
        /* 
        Formula is 
            ((cash terms) + (acquirer ticker last price * share terms) + (target dividends) - (acquirer dividends) +
             (short rebate) + (stub/cvr value))
        */
        var acquirer_ticker = $('#acquirer_ticker').val();
        var deal_cash_terms = parseFloat($('#deal_cash_terms').val());
        var deal_share_terms = parseFloat($('#deal_share_terms').val());
        var target_dividends = parseFloat($('#target_dividends').val());
        var acquirer_dividends = parseFloat($('#acquirer_dividends').val());
        var short_rebate = parseFloat($('#short_rebate').val());
        var stub_cvr_value = parseFloat($('#stub_cvr_value').val());
        if (!deal_cash_terms) { deal_cash_terms = 0.0; }
        if (!deal_share_terms) { deal_share_terms = 0.0; }
        if (!target_dividends) { target_dividends = 0.0; }
        if (!acquirer_dividends) { acquirer_dividends = 0.0; }
        if (!short_rebate) { short_rebate = 0.0; }
        if (!stub_cvr_value) { stub_cvr_value = 0.0; }
        if (deal_share_terms > 0 &&  acquirer_ticker == "") {
            $('#create_mna_deal_error').addClass("alert alert-danger");
            $('#create_mna_deal_error').html("Error: Acquirer Ticker is required to calculate the Deal Value when Deal Share Terms > 0");
            $("#create_mna_deal_error_div").show();
        }
        else {
            $("#create_mna_deal_error_div").hide();
            $.ajax({
                'type': 'POST',
                'url': '../risk/calculate_mna_idea_deal_value',
                'data': {
                    'acquirer_ticker': acquirer_ticker,
                    'deal_cash_terms': deal_cash_terms,
                    'deal_share_terms': deal_share_terms,
                    'target_dividends': target_dividends,
                    'acquirer_dividends': acquirer_dividends,
                    'short_rebate': short_rebate,
                    'stub_cvr_value': stub_cvr_value
                },
                success: function (response) {
                    $('#deal_value').val(response);
                },
                error: function (err) {
                    alert(err);
                }
            })
        }
    });

    $('#action_id').focusout(function() {
        var action_id = $('#action_id').val();
        if (action_id) {
            $.ajax({
                'type': 'POST',
                'url': '../risk/fetch_bloomberg_data',
                'data': {'action_id': action_id},
                success: function (response) {
                    if (response.error == false) {
                        var target_ticker = response.CA052[0];
                        var acquirer_ticker = response.CA054[0];
                        var deal_cash_terms = parseFloat(response.CA072[0]);
                        var deal_share_terms = parseFloat(response.CA073[0]);
                        var origination_date = response.CA057[0];
                        var expected_close_date = response.CA835[0];
                        if (!deal_cash_terms) { deal_cash_terms = 0.0; }
                        if (!deal_share_terms) { deal_share_terms = 0.0; }
                        $('#target_ticker').val(target_ticker);
                        $('#acquirer_ticker').val(acquirer_ticker);
                        $('#deal_cash_terms').val(deal_cash_terms);
                        $('#deal_share_terms').val(deal_share_terms);
                        $('#origination_date').val(origination_date);
                        $('#expected_close_date').val(expected_close_date);
                        $('#target_ticker')[0].style.backgroundColor = 'yellow';
                        $('#acquirer_ticker')[0].style.backgroundColor = 'yellow';
                        $('#deal_cash_terms')[0].style.backgroundColor = 'yellow';
                        $('#deal_share_terms')[0].style.backgroundColor = 'yellow';
                        $('#origination_date')[0].style.backgroundColor = 'yellow';
                        $('#expected_close_date')[0].style.backgroundColor = 'yellow';
                    }
                    else {
                        console.log("Error in fetching data from bloomberg for given action id");
                    }
                },
                error: function (err) {
                    alert(err);
                }
            })
        }
        else {
            $('#target_ticker').val('');
            $('#acquirer_ticker').val('');
            $('#deal_cash_terms').val('');
            $('#deal_share_terms').val('');
            $('#origination_date').val('');
            $('#expected_close_date').val('');
            $('#target_ticker')[0].style.backgroundColor = '';
            $('#acquirer_ticker')[0].style.backgroundColor = '';
            $('#deal_cash_terms')[0].style.backgroundColor = '';
            $('#deal_share_terms')[0].style.backgroundColor = '';
            $('#origination_date')[0].style.backgroundColor = '';
            $('#expected_close_date')[0].style.backgroundColor = '';
        }
    });
});
