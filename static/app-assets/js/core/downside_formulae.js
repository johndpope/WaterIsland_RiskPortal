$(document).ready(function () {
    let formulae_table = $('#downside_formulae_table').DataTable({
        scrollY: "50vh",
        scrollX: true,
        scrollCollapse: true,
        paging: false,
        fixedColumns: {
            leftColumns: 2
        },
        order: [[4, 'desc']],
        columnDefs: [{
            targets: [4], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        }],

    });


    // Keep Acquirer Security Input disabled
    $('#formulae_acquirer_security').prop('disabled', true);

    // Event Handler for Datatable dropdown
    $('#downside_formulae_table tr td .BaseCaseDownsideType').on('change', function (e) {
        // Change value of other columns based on dropdown...
        //Reference Data Point (Row No): 11; ReferencePrice (Row No): 12
        let downside_type_selected = $(this).val();
        if (downside_type_selected === 'Fundamental Valuation') {
            $(this).parent().parent().find("td").eq(12).find("input").val("");
            $(this).parent().parent().find("td").eq(13).find("input").val(" ");
        } else if (downside_type_selected === 'Break Spread') {
            $(this).parent().parent().find("td").eq(12).find("input").val("Deal Value");
            $(this).parent().parent().find("td").eq(13).find("input").val($(this).parent().parent().find("td").eq(7).html());
        } else if (downside_type_selected === 'Peer Index') {
            $(this).parent().parent().find("td").eq(12).find("input").val($(this).parent().parent().find("td").eq(6).html());
            $(this).parent().parent().find("td").eq(13).find("input").val($(this).parent().parent().find("td").eq(6).html());
        } else if (downside_type_selected === 'Premium/Discount') {
            $(this).parent().parent().find("td").eq(12).find("input").val($(this).parent().parent().find("td").eq(1).html());
            $(this).parent().parent().find("td").eq(13).find("input").val($(this).parent().parent().find("td").eq(8).html());
        } else if (downside_type_selected === 'Last Price') {
            $(this).parent().parent().find("td").eq(12).find("input").val($(this).parent().parent().find("td").eq(1).html());
            $(this).parent().parent().find("td").eq(13).find("input").val($(this).parent().parent().find("td").eq(8).html());
            $(this).parent().parent().find("td").eq(16).find("input").val(eval($(this).parent().parent().find("td").eq(8).html()).toFixed(2)); //Reference Price
            //Also Set the Base Case right here for LastPX

        }
    });

    $('#downside_formulae_table tr td #basecasecustominput').focusout(function (e) {

        let downside_type_selected = $(this).parent().parent().find('td .BaseCaseDownsideType').val();
        // Calculate and Evaluate the Expression
        let expression = "";
        if (downside_type_selected === 'Fundamental Valuation') {
            expression = $(this).parent().parent().find("td").eq(15).find("input").val();
        } else if (downside_type_selected === 'Break Spread') {
            //Calculation for Break Spread: Reference Price [Operation] CustomInput
            expression = $(this).parent().parent().find("td").eq(13).find("input").val(); //Reference Price
            expression += $(this).parent().parent().find("td").eq(14).find("#basecaseoperator").val(); //Operator
            expression += $(this).parent().parent().find("td").eq(15).find("input").val(); //CustomInput

        } else if (downside_type_selected === 'Peer Index') {
            expression = "";
        } else if (downside_type_selected === 'Premium/Discount') {
            //ReferencePrice [Operation] CustomInput
            expression = $(this).parent().parent().find("td").eq(13).find("input").val(); //Reference Price
            expression += $(this).parent().parent().find("td").eq(14).find("#basecaseoperator").val(); //Operator
            expression += $(this).parent().parent().find("td").eq(15).find("input").val(); //CustomInput
        } else if (downside_type_selected === 'Last Price') {
            //Just take Last price
            expression = $(this).parent().parent().find("td").eq(13).val(); //Take the Last Price
        }
        console.log(expression);
        //Set it as the Base Case....
        $(this).parent().parent().find("td").eq(16).find("input").val(eval(expression).toFixed(2)); //Reference Price
    });


    // Repeat the Same for Outliers
    $('#downside_formulae_table tr td .OutlierDownsideType').on('change', function (e) {
        // Change value of other columns based on dropdown...
        //Reference Data Point (Row No): 11; ReferencePrice (Row No): 12
        let downside_type_selected = $(this).val();
        if (downside_type_selected === 'Fundamental Valuation') {
            $(this).parent().parent().find("td").eq(19).find("input").val("");
            $(this).parent().parent().find("td").eq(20).find("input").val(" ");
        } else if (downside_type_selected === 'Break Spread') {
            $(this).parent().parent().find("td").eq(19).find("input").val("Deal Value");
            $(this).parent().parent().find("td").eq(20).find("input").val($(this).parent().parent().find("td").eq(7).html());
        } else if (downside_type_selected === 'Peer Index') {
            $(this).parent().parent().find("td").eq(19).find("input").val($(this).parent().parent().find("td").eq(6).html());
            $(this).parent().parent().find("td").eq(20).find("input").val($(this).parent().parent().find("td").eq(6).html());
        } else if (downside_type_selected === 'Premium/Discount') {
            $(this).parent().parent().find("td").eq(19).find("input").val($(this).parent().parent().find("td").eq(1).html());
            $(this).parent().parent().find("td").eq(20).find("input").val($(this).parent().parent().find("td").eq(8).html());
        } else if (downside_type_selected === 'Last Price') {
            $(this).parent().parent().find("td").eq(19).find("input").val($(this).parent().parent().find("td").eq(1).html());
            $(this).parent().parent().find("td").eq(20).find("input").val($(this).parent().parent().find("td").eq(8).html());
            //Set the value of Outlier right here...
            $(this).parent().parent().find("td").eq(23).find("input").val(eval($(this).parent().parent().find("td").eq(8).html()).toFixed(2)); //Reference Price
        } else if(downside_type_selected === 'Match Base Case'){
            // Copy 19 - 23 from 12-16
            $(this).parent().parent().find("td").eq(19).find("input").val($(this).parent().parent().find("td").eq(12).find('input').val());
            $(this).parent().parent().find("td").eq(20).find("input").val($(this).parent().parent().find("td").eq(13).find('input').val());
            $(this).parent().parent().find("td").eq(21).find("select").val($(this).parent().parent().find("td").eq(14).find('option:selected').val());
            $(this).parent().parent().find("td").eq(22).find("input").val($(this).parent().parent().find("td").eq(15).find('input').val());
            $(this).parent().parent().find("td").eq(23).find("input").val($(this).parent().parent().find("td").eq(16).find('input').val());
        }
    });

    $('#downside_formulae_table tr td #outliercustominput').focusout(function (e) {

        let downside_type_selected = $(this).parent().parent().find('td .OutlierDownsideType').val();
        // Calculate and Evaluate the Expression
        let expression = "";
        if (downside_type_selected === 'Fundamental Valuation') {
            expression = $(this).parent().parent().find("td").eq(22).find("input").val();
        } else if (downside_type_selected === 'Break Spread') {
            //Calculation for Break Spread: Reference Price [Operation] CustomInput
            expression = $(this).parent().parent().find("td").eq(20).find("input").val(); //Reference Price
            expression += $(this).parent().parent().find("td").eq(21).find("#outlieroperator").val(); //Operator
            expression += $(this).parent().parent().find("td").eq(22).find("input").val(); //CustomInput

        } else if (downside_type_selected === 'Peer Index') {
            expression = "";
        } else if (downside_type_selected === 'Premium/Discount') {
            //ReferencePrice [Operation] CustomInput
            expression = $(this).parent().parent().find("td").eq(20).find("input").val(); //Reference Price
            expression += $(this).parent().parent().find("td").eq(21).find("#outlieroperator").val(); //Operator
            expression += $(this).parent().parent().find("td").eq(22).find("input").val(); //CustomInput
        }

        //Set it as the Outlier....
        $(this).parent().parent().find("td").eq(23).find("input").val(eval(expression).toFixed(2)); //Reference Price
    });
    
    // Event Handler for Button Click. Call Ajax with the row data...
    $('#downside_formulae_table tr td button').on('click', function (e) {
        var save_button_id = $(this).attr('id');
        if (save_button_id && save_button_id.includes("save_risk_limit_")) {
            let id = save_button_id.split("_").pop()
            if (!id) {
                id = $(this).parent().parent().attr('id');
            }
            let risk_limit = $(this).parent().parent().find("td").eq(10).find("input").val();
            let risk_limit_dictionary = {};
            risk_limit_dictionary['risk_limit'] = risk_limit;
            risk_limit_dictionary['id'] = id;
            risk_limit_dictionary['update_risk_limit'] = true;
            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/update_downside_formulae",
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
                                        url:  "../risk_reporting/update_risk_limit",
                                        data: {'id': id, 'risk_limit': risk_limit},
                                        success:function(response){
                                            if(response==="Success"){
                                                //Delete Row from DataTable
                                                swal("Success! The Risk Limit has been updated to " + risk_limit, {icon: "success"});
                                                // Update the risk limit values in other rows for same TradeGroup
                                                var tradegroup = $('#' + save_button_id).parent().parent().find('td').eq(0).text()
                                                var row_length = $('#downside_formulae_table').find('tr').length
                                                for (var i = 0; i < row_length; i++) {
                                                    var lookup_tradegroup = $('#downside_formulae_table').find('tr').eq(i).find('td').eq(0).text()
                                                    if (lookup_tradegroup === tradegroup) {
                                                        $('#downside_formulae_table').find('tr').eq(i).find('td').eq(10).find('input').val(risk_limit)
                                                    }
                                                }
                                            }
                                            else{
                                                //show a sweet alert
                                                swal("Error!", "Updating Risk Limit Failed!", "error");
                                            }
                                        },
                                        error:function (error) {
                                            swal("Error!", "Updating Risk Limit Failed!", "error");
                                            console.log(error);
                                        }
                                    });
            
                                }
                            });
                    }
                    else if (response === 'Risk Limit Same') {
                        toastr.error('Risk Limit is already same!!!!', 'Error!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                    }
                    else {
                        //Failed. Show error toastr
                        toastr.error('Failed updating BaseCase and Outlier for the deal..', 'Error!', {
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
        }
        else {
            let id = $(this).parent().parent().attr('id');
            //Only update necessary elements (backend - set lastupdate to now..
            let is_excluded = $(this).parent().parent().find("td").eq(9).find(".custom-select2").val();
            let base_case_downside_type = $(this).parent().parent().find("td").eq(11).find(".custom-select2").val();
            let base_case_reference_data_point = $(this).parent().parent().find("td").eq(12).find("input").val();
            let base_case_reference_price = $(this).parent().parent().find("td").eq(13).find("input").val();
            let base_case_operation = $(this).parent().parent().find("td").eq(14).find(".custom-select2").val();
            let base_case_custom_input = $(this).parent().parent().find("td").eq(15).find("input").val();
            let base_case = $(this).parent().parent().find("td").eq(16).find("input").val();
            let base_case_notes = $(this).parent().parent().find("td").eq(17).find("input").val();
            let cix_ticker = $(this).parent().parent().find("td").eq(6).find("input").val();
            // Get data for the Outlier
            let outlier_downside_type = $(this).parent().parent().find("td").eq(18).find(".custom-select2").val();
            let outlier_reference_data_point = $(this).parent().parent().find("td").eq(19).find("input").val();
            let outlier_reference_price = $(this).parent().parent().find("td").eq(20).find("input").val();
            let outlier_operation = $(this).parent().parent().find("td").eq(21).find(".custom-select2").val();
            let outlier_custom_input = $(this).parent().parent().find("td").eq(22).find("input").val();
            let outlier = $(this).parent().parent().find("td").eq(23).find("input").val();
            let outlier_notes = $(this).parent().parent().find("td").eq(24).find("input").val();

            //Got the Data..Create a Dictionary and make a POST request

            let downsides_data_dictionary = {};

            downsides_data_dictionary['id'] = id;
            downsides_data_dictionary['is_excluded'] = is_excluded;
            downsides_data_dictionary['base_case_downside_type'] = base_case_downside_type;
            downsides_data_dictionary['base_case_reference_data_point'] = base_case_reference_data_point;
            downsides_data_dictionary['base_case_reference_price'] = base_case_reference_price;
            downsides_data_dictionary['base_case_operation'] = base_case_operation;
            downsides_data_dictionary['base_case_custom_input'] = base_case_custom_input;
            downsides_data_dictionary['base_case'] = base_case;
            downsides_data_dictionary['base_case_notes'] = base_case_notes;
            downsides_data_dictionary['cix_ticker'] = cix_ticker;
            downsides_data_dictionary['outlier_downside_type'] = outlier_downside_type;
            downsides_data_dictionary['outlier_reference_data_point'] = outlier_reference_data_point;
            downsides_data_dictionary['outlier_reference_price'] = outlier_reference_price;
            downsides_data_dictionary['outlier_operation'] = outlier_operation;
            downsides_data_dictionary['outlier_custom_input'] = outlier_custom_input;
            downsides_data_dictionary['outlier'] = outlier;
            downsides_data_dictionary['outlier_notes'] = outlier_notes;
            downsides_data_dictionary['update_risk_limit'] = false;
            // Make an Ajax POST request...

            $.ajax({
                "type": "POST",
                "url": "../risk_reporting/update_downside_formulae",
                "data": downsides_data_dictionary,
                "success": function (response) {
                    if (response === 'Success') {
                        //Show success Toastr...
                        toastr.success('Updated BaseCase and Outlier for the deal..', 'Formula Updated!', {
                            "showMethod": "slideDown",
                            "hideMethod": "slideUp",
                            timeOut: 2800
                        });
                    }
                    else {
                        //Failed. Show error toastr
                        toastr.error('Failed updating BaseCase and Outlier for the deal..', 'Error!', {
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
        }
    });
});
