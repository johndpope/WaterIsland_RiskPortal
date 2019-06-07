$(document).ready(function () {
    let credit_deals_upside_downside_table = $('#credit_deals_upside_downside_table').DataTable({
        scrollY: "680px",
        scrollX: true,
        scrollCollapse: true,
        paging: false,
        fixedColumns: {
            leftColumns: 2
        },
        order: [[4, 'desc'], [3, 'desc']],
        columnDefs: [
            {
                targets: [3], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        },
            {
                targets: [4], render: function (data) {
                return moment(data, 'MMM DD, YYYY, h:mm a').format('YYYY-MM-DD, hh:mm a');
            }
        }],

    });

    $('#credit_deals_upside_downside_table tr td .DownsideTypeChange').on('change', function (e) {
        let row_id = $(this).attr('id').split("_").pop();
        if (!row_id) {
            row_id = $(this).parent().attr('id').split("_").pop();
        }
        let downside_select_value = $(this).val();
        if (downside_select_value === 'Fundamental Valuation') {
            $('#calculated_downside_' + row_id).val("");
            $('#calculated_downside_' + row_id)[0].style.backgroundColor = 'yellow';
        } 
        else if (downside_select_value === 'Last Price') {
            let last_price = $('#last_price_' + row_id).text();
            $('#calculated_downside_' + row_id).val(last_price);
            $('#calculated_downside_' + row_id)[0].style.backgroundColor = 'yellow';
        }
        else if (downside_select_value === 'Match ARB') {
            var ticker = $('#ticker_' + row_id).text();
            let credit_deals_dict = {};
            credit_deals_dict['ticker'] = ticker;
            credit_deals_dict['id'] = row_id;
            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/get_details_from_arb",
                "data": credit_deals_dict,
                "success": function (response) {
                    if (response.msg === 'Not Found') {
                        swal({
                            title: "Not Found",
                            text: ticker + " not found in the Arb Downside Formulae Page",
                            icon: "warning",
                            dangerMode: true,
                        })
                    }
                    else if (response.msg == 'Failure') {
                        swal("Error!", "Retrieving values from ARB Failed!", "error");
                    }
                    else if (response.msg == 'Success') {
                        let deal_value = response.deal_value;
                        let outlier = response.outlier;
                        $('#deal_value_' + row_id).text(deal_value);
                        $('#deal_value_' + row_id)[0].style.backgroundColor = 'yellow';
                        $('#calculated_downside_' + row_id).val(outlier);
                        $('#calculated_downside_' + row_id)[0].style.backgroundColor = 'yellow';
                    }
                    else {
                        swal("Error!", "Retrieving values from ARB Failed!", "error");
                    }
                }
            });
        }
    });

    $('#credit_deals_upside_downside_table tr td .UpsideTypeChange').on('change', function (e) {
        let row_id = $(this).attr('id').split("_").pop();
        if (!row_id) {
            row_id = $(this).parent().attr('id').split("_").pop();
        }
        let upside_select_value = $(this).val();
        if (upside_select_value === 'Fundamental Valuation') {
            $('#calculated_upside_' + row_id).val("");
            $('#calculated_upside_' + row_id)[0].style.backgroundColor = 'yellow';
        }
        else if (upside_select_value === 'Last Price') {
            let last_price = $('#last_price_' + row_id).text();
            $('#calculated_upside_' + row_id).val(last_price);
            $('#calculated_upside_' + row_id)[0].style.backgroundColor = 'yellow';
        }
        else if (upside_select_value === 'Match ARB') {
            var ticker = $('#ticker_' + row_id).text();
            let credit_deals_dict = {};
            credit_deals_dict['ticker'] = ticker;
            credit_deals_dict['id'] = row_id;
            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/get_details_from_arb",
                "data": credit_deals_dict,
                "success": function (response) {
                    if (response.msg === 'Not Found') {
                        swal({
                            title: "Not Found",
                            text: ticker + " not found in the Arb Downside Formulae Page",
                            icon: "warning",
                            dangerMode: true,
                        })
                    }
                    else if (response.msg == 'Failure') {
                        swal("Error!", "Retrieving values from ARB Failed!", "error");
                    }
                    else if (response.msg == 'Success') {
                        let deal_value = response.deal_value;
                        let outlier = response.outlier;
                        $('#deal_value_' + row_id).text(deal_value);
                        $('#deal_value_' + row_id)[0].style.backgroundColor = 'yellow';
                        $('#calculated_upside_' + row_id).val(deal_value);
                        $('#calculated_upside_' + row_id)[0].style.backgroundColor = 'yellow';
                    }
                    else {
                        swal("Error!", "Retrieving values from ARB Failed!", "error");
                    }
                }
            });
        }
        else if (upside_select_value === 'Calculate from SIX') {
            let spread_index = $('#spread_index_' + row_id).val();
            if (!spread_index) {
                swal("Error!", "Please enter Spread Index first, then select this option", "error");
            }
            else {
                calculate_upside_value_from_spread(row_id, spread_index);
            }
        }
    });

    $('.spread_index_class').focusout(function() {
        let row_id = $(this).attr('id').split("_").pop();
        if (!row_id) {
            row_id = $(this).parent().attr('id').split("_").pop();
        }
        let upside_select_value = $('#upside_type_select_' + row_id).val();
        if (upside_select_value == 'Calculate from SIX') {
            let spread_index = $('#spread_index_' + row_id).val();
            calculate_upside_value_from_spread(row_id, spread_index);
            console.log(upside_select_value, row_id, spread_index);
        }
    });

    function calculate_upside_value_from_spread(row_id, spread_index) {
        let data_dict = {};
        data_dict['spread_index'] = spread_index;
        data_dict['id'] = row_id;
        $.ajax({
            "type": "POST",
            "url": "../risk_reporting/fetch_from_bloomberg_by_spread_index",
            "data": data_dict,
            "success": function (response) {
                if (response.msg == 'Success') {
                    let px_last = parseFloat(response.px_last);
                    let last_price = parseFloat($('#last_price_' + row_id).text());
                    let upside = px_last + last_price;
                    $('#calculated_upside_' + row_id).val(upside);
                    $('#calculated_upside_' + row_id)[0].style.backgroundColor = 'yellow';
                    //Show success Toastr...
                    toastr.success('Upside updated. PX_LAST is ' + px_last, 'Upside Updated!', {
                        "showMethod": "slideDown",
                        "hideMethod": "slideUp",
                        timeOut: 2800
                    });
                }
                else {
                    //Failed. Show error toastr
                    toastr.error('Failed updating Upside.', 'Error!',
                                 {"showMethod": "slideDown", "hideMethod": "slideUp", timeOut: 2800});
                }
            },
            "error": function (err) {
                console.log(err);
            }
        });
    }

    $('#credit_deals_upside_downside_table tr td button').on('click', function (e) {
        var save_button_id = $(this).attr('id');
        if (save_button_id && save_button_id.includes("save_risk_limit_")) {
            let credit_deal_id = save_button_id.split("_").pop();
            if (!credit_deal_id) {
                credit_deal_id = $(this).parent().parent().attr('id');
            }
            $('#save_risk_limit_' + credit_deal_id).attr("disabled", true);	
            let risk_limit_dictionary = {};
            let risk_limit = $('#risk_limit_' + credit_deal_id).val();
            risk_limit_dictionary['risk_limit'] = risk_limit;
            risk_limit_dictionary['id'] = credit_deal_id;
            risk_limit_dictionary['update_risk_limit'] = true;
            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/update_credit_deals_upside_downside",
                "data": risk_limit_dictionary,
                "success": function (response) {
                    if (response.msg === 'Risk Limit Different') {
                        swal({
                            title: "Are you sure?",
                            text: "Do you want to update Risk Limit from " + response.original_risk_limit + " to " + risk_limit,
                            icon: "warning",
                            buttons: [
                                'No, cancel it!',
                                'Yes, I am sure!'
                            ],
                            dangerMode: true,
                            }).then((willUpdate) => {
                                if (willUpdate) {
                                    //Handle Ajax request to Delete
                                    $.ajax({
                                        type: 'POST',
                                        url:  "../risk_reporting/update_credit_deal_risk_limit",
                                        data: {'id': credit_deal_id, 'risk_limit': risk_limit},
                                        success:function(response){
                                            if(response==="Success"){
                                                //Delete Row from DataTable
                                                swal("Success! The Risk Limit has been updated to " + risk_limit, {icon: "success"});
                                                // Update the risk limit in the table
                                                $('#risk_limit_' + credit_deal_id).val(risk_limit);
                                                $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);	
                                            }
                                            else{
                                                //show a sweet alert
                                                swal("Error!", "Updating Risk Limit Failed!", "error");
                                                $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);	
                                            }
                                        },
                                        error:function (error) {
                                            swal("Error!", "Updating Risk Limit Failed!", "error");
                                            $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);	
                                            console.log(error);
                                        }
                                    });
            
                                }
                            });
                            $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);
                    }
                    else if (response === 'Risk Limit Same') {
                        toastr.error('Risk Limit is already same!!!!', 'Error!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                        $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);
                    }
                    else {
                        //Failed. Show error toastr
                        toastr.error('Failed updating BaseCase and Outlier for the deal..', 'Error!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                        $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);
                    }
                },
                "error": function (err) {
                    console.log(err);
                    $('#save_risk_limit_' + credit_deal_id).attr("disabled", false);
                }
            });
        }
        else {
            let credit_deal_id = save_button_id.split("_").pop();
            if (!credit_deal_id) {
                credit_deal_id = String($(this).parent().parent().attr('id'));
            }
            else { credit_deal_id = String(credit_deal_id); }

            let credit_deals_dict = {};

            credit_deals_dict['id'] = credit_deal_id;
            credit_deals_dict['spread_index'] = $('#spread_index_' + credit_deal_id).val();
            credit_deals_dict['is_excluded'] = $('#is_excluded_select_' + credit_deal_id).val();
            credit_deals_dict['downside_type'] = $('#downside_type_select_' + credit_deal_id).val();
            credit_deals_dict['downside'] = $('#calculated_downside_' + credit_deal_id).val();
            credit_deals_dict['downside_notes'] = $('#downside_notes_' + credit_deal_id).val();
            credit_deals_dict['upside_type'] = $('#upside_type_select_' + credit_deal_id).val();
            credit_deals_dict['upside'] = $('#calculated_upside_' + credit_deal_id).val();
            credit_deals_dict['upside_notes'] = $('#upside_notes_' + credit_deal_id).val();
            credit_deals_dict['update_risk_limit'] = false;

            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/update_credit_deals_upside_downside",
                "data": credit_deals_dict,
                "success": function (response) {
                    if (response === 'Success') {
                        //Show success Toastr...
                        toastr.success('Updated Upside and Downside for the Credit Deal..', 'Upside/Downside Updated!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                    }
                    else {
                        //Failed. Show error toastr
                        toastr.error('Failed updating Upside and Downside for the Credit Deal..', 'Error!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                    }
                },
                "error": function (err) {
                    console.log(err);
                }
            });
            $('#deal_value_' + credit_deal_id)[0].style.backgroundColor = '';
            $('#calculated_downside_' + credit_deal_id)[0].style.backgroundColor = '';
            $('#calculated_upside_' + credit_deal_id)[0].style.backgroundColor = '';
        }
    });
});
