$(document).ready(function () {
    $("#create_mna_deal_error_div").hide();
    $('#calculate_deal_value').on('click', function () {
        /* 
        Formula is 
            ((cash terms) + (acquirer ticker last price * share terms) + (target dividends) - (acquirer dividends) +
             (short rebate) + (stub/cvr value))
        */
        var acquirer_ticker = $('#acquirer_ticker').val();
        var deal_cash_terms = $('#deal_cash_terms').val();
        var deal_share_terms = $('#deal_share_terms').val();
        var target_dividends = $('#target_dividends').val();
        var acquirer_dividends = $('#acquirer_dividends').val();
        var short_rebate = $('#short_rebate').val();
        var stub_cvr_value = $('#stub_cvr_value').val();
        if (parseFloat(deal_share_terms) > 0 &&  acquirer_ticker == "") {
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
});
