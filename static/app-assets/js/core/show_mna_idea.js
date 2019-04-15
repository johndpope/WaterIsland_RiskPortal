$(document).ready(function () {

    // Section for Tradegroup Stories
    // Main TradeGroup Story

    $.ajax({
        'type': 'GET',
        'url': '../position_stats/get_tradegroup_story?TradeGroup=' + $('#tradegroup_name').val() + '&Fund=ARB',
        success: function (response) {
            let exposures_and_pnl = JSON.parse(response['exposures_and_pnl_df']);
            let fund_name = 'ARB';
            let tradegroup_name = $('#tradegroup_name').val();
            let unique_tickers = response['unique_tickers'];
            let fieldMappingsArray = [];
            let tradegroup_level_dictionary = {};

            fieldMappingsArray = ["AlphaHedge_Exposure", "Alpha_Exposure", "Capital_Percent_of_NAV", "GrossExp_Percent_of_NAV",
                "Hedge_Exposure", "NetExp_Percent_of_NAV", "Spread_as_Percent", "Cumulative_pnl_bps",
                "Cumulative_options_pnl_bps"];

            tradegroup_level_dictionary["Cumulative_pnl_bps"] = 'Contribution in bps';
            tradegroup_level_dictionary["Spread_as_Percent"] = "Spread (%)";
            tradegroup_level_dictionary["Cumulative_options_pnl_bps"] = "Options";
            tradegroup_level_dictionary["AlphaHedge_Exposure"] = "AlphaHedge Exposure";
            tradegroup_level_dictionary["Alpha_Exposure"] = "Alpha Exposure";
            tradegroup_level_dictionary["Capital_Percent_of_NAV"] = "Capital as (%) of NAV";
            tradegroup_level_dictionary["GrossExp_Percent_of_NAV"] = "Gross Exp (%) of NAV";
            tradegroup_level_dictionary["Hedge_Exposure"] = "Hedge Exp";
            tradegroup_level_dictionary["NetExp_Percent_of_NAV"] = "Net Exp (%) of NAV";
            let tickerFieldMappings = 'Ticker_PnL_bps_';
            let datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, true, tickerFieldMappings);
            let graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, true, tickerFieldMappings, true);


            let title = "TIMELINE OF " + tradegroup_name + " in " + fund_name + "\n" + "P&L CONTRIBUTION, SPREAD (LEFT) v/s EXPOSURES(RIGHT)";
            let tradegroup_story_chart = AmCharts.makeChart("mna_idea_tradegroup_story", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '$$', 'light'));

        },
        error: function (err) {
            console.log(err);
        }
    });


    //Fill the Peers Table
    let related_peers = JSON.parse($('#mna_idea_related_peers').val());
    if (related_peers.length > 0) {
        for (var i = 0; i < related_peers.length; i++) {
            $('#ticker_hedge_' + (i + 1) + '_ticker').val(related_peers[i][0]);
        }
    }

    //Initialize summernote
    $('#mna_idea_lawyer_report').summernote({'height': '300px'});
    $('#mna_idea_lawyer_reports_table').DataTable();
    $('#mna_idea_historical_downside_estimates_table').DataTable({
        scrollY: '300px', scrollCollapse: true,
        paging: false
    });
    var unaffected_date = $('#unaffected_date').val();
    var overlay_weekly_downside_date_updated = $('#overlay_weekly_downside_date_updated').val();
    var overlay_weekly_downside_estimate = $('#overlay_weekly_downside_estimates').val();

    var ev_ebitda_ltm_valuation_multiple_datasets = [];
    var ev_ebitda_onebf_valuation_multiple_datasets = [];
    var ev_ebitda_twobf_valuation_multiple_datasets = [];

    var ev_sales_ltm_valuation_multiple_datasets = [];
    var ev_sales_onebf_valuation_multiple_datasets = [];
    var ev_sales_twobf_valuation_multiple_datasets = [];

    var pe_ratio_ltm_valuation_multiple_datasets = [];
    var pe_ratio_onebf_valuation_multiple_datasets = [];
    var pe_ratio_twobf_valuation_multiple_datasets = [];

    try {
        var mna_idea_weekly_downside_estimates_table = $('#mna_idea_weekly_downside_estimates_table').DataTable({'sorting': false});
    } catch (e) {
        console.log(e);
    }

    //Show week numbers
    // Show Week Numbers
    $('.showweeknumbers').daterangepicker({
        showWeekNumbers: true,
    });

    let analyst_comments = $('#mna_idea_analyst_comments').summernote({
        'height': '460px',
    });
    let downside_comments = $('#mna_idea_weekly_downside_estimate_comment').summernote({'height': '300px'});
    var ebitda_charts = null;
    var ev_sales_charts = null;
    var pe_ratio_charts = null;

    analyst_comments.summernote('code', $('#deal_comments').val());

    //Fill Analysis tables if present
    let target_acquier_charts = null;
    let valuationMultipleDatasets = [];
    //Populate Peer Charts
    let peer_chart_data = $.parseJSON($('#peer_valuation_charts').val());


    createPeerCharts(peer_chart_data);

    var deal_break_analysis = $('#deal_break_analysis').DataTable({
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },

        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
                autoPrint: false
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        }, "bLengthChange": false, "searching": false,
        "ordering": false, "columnDefs": [{
            "targets": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out
                if (cellData < 0) {
                    $(td).css('color', 'red')
                }
                else if (cellData > 5 && (rowIndex == 4 || rowIndex == 5)) {
                    $(td).css('color', 'red')
                }
                else {
                    $(td).css('color', 'green')
                }
            }
        }]
    });

    var deal_break_analysis_55_45 = $('#deal_break_analysis_55_45').DataTable({
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
                autoPrint: false
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        }, "bLengthChange": false, "searching": false,
        "ordering": false, "columnDefs": [{
            "targets": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out
                if (cellData < 0) {
                    $(td).css('color', 'red')
                }
                else if (cellData > 5 && (rowIndex == 4 || rowIndex == 5)) {
                    $(td).css('color', 'red')
                }
                else {
                    $(td).css('color', 'green')
                }
            }
        }]
    });

    var seventy_twentyfive_analysis = $('#deal_break_analysis_75_25').DataTable({
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
                autoPrint: false
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                title: $('#target_ticker').val() + '--' + $('#acquirer_ticker').val(),
            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        }, "bLengthChange": false, "searching": false,
        "ordering": false, "columnDefs": [{
            "targets": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {
                if (cellData < 0) {
                    $(td).css('color', 'red')
                }
                else if (cellData > 5 && (rowIndex == 4 || rowIndex == 5)) {
                    $(td).css('color', 'red')
                }
                else {
                    $(td).css('color', 'green')
                }
            }
        }]
    });


    $('#mna_idea_merger_overview').summernote({'height': '150'});
    $('#mna_idea_company_overview').summernote({'height': '150px'});

    //Only fill if Scenario Analysis Object is not empty
    if ($('#scenario_analysis_object').val() != '') {
        fill_analysis_tables($('#break_change').val(), $('#scenario_change').val(), $('#scenario_change_55_45').val(), $.parseJSON($('#break_scenario').val()), $.parseJSON($('#scenario_75_25').val()), $.parseJSON($('#scenario_55_45').val()));
    }

    /**
     *  Routine for Populating the Target and Acquirer Charts
     */
    var historical_pxs = $('#historical_px_last').val();
    var historical_px = $.parseJSON(historical_pxs);
    var hist_prices_dates = historical_px['fields']['PX_LAST'];


    var dates = historical_px['fields']['date'];
    var target_ticker = $('#target_ticker').val();
    var acquirer_ticker = $('#acquirer_ticker').val();
    var acquirer_error_flag = 0;
    //Try to get Acquirer Data
    try {
        var acq_historical_pxs = $('#historical_px_last_acquirer').val();
        var acq_historical_px = $.parseJSON(acq_historical_pxs);
        var hist_prices_dates_acquirer = acq_historical_px['fields']['PX_LAST'];
        var hist_dates_acquirer = acq_historical_px['fields']['date'];
        if (hist_prices_dates_acquirer.length === 0) {
            acquirer_error_flag = 1;
        }
    }
    catch (err) {
        acquirer_error_flag = 1;
        console.log(err);
    }


    try {
        generateTargetPriceChart(hist_prices_dates, dates, hist_prices_dates_acquirer, 'mna_idea_targetAcquirer_chart', target_ticker, acquirer_ticker, acquirer_error_flag, hist_dates_acquirer);

    }
    catch (err) {
        target_acquier_charts = AmCharts.makeChart('mna_idea_targetAcquirer_chart',
            {
                "type": "serial",
                "legend": {
                    "useGraphSettings": true
                },
                "hideCredits": true,
                "dataProvider": [],
            }
        );
        console.log(err);
    }

    function get_acquirer_chart_data(val) {
        console.log(val);
        return val;

    }

    function generateTargetPriceChart(target_ticker_prices, target_ticker_dates, hist_prices_dates_acquirer, div_id, target_ticker, acquirer_ticker, acquirer_error_flag, hist_dates_acquirer) {
        var chartData = [];
        var stockEvents = [];
        var guides = [];
        var deal_risk_factors_list = $.parseJSON($('#deal_risk_factors_list').val());

        if (unaffected_date != null && unaffected_date !== 'None') {
            guides.push({
                'date': new Date(unaffected_date),
                "lineColor": "cyan",
                "lineAlpha": 1,
                "dashLength": 0,
                "inside": true,
                "labelRotation": 90,
                "label": 'Unaffected Date',
                "fontSize": 12,
            });
        }
        console.log(overlay_weekly_downside_estimate);
        if (overlay_weekly_downside_estimate != null && overlay_weekly_downside_estimate !== '') {

            guides.push({
                'date': new Date(overlay_weekly_downside_date_updated),
                "lineColor": "red",
                "lineAlpha": 4,
                "dashLength": 0,
                "inside": true,
                "labelRotation": 90,
                "label": 'Estimated Downside',
                "baloonText": 'Analyst Estimated Downside (on this day) -->' + overlay_weekly_downside_estimate.toString(),
                "fontSize": 12,
            });
        }
        if (deal_risk_factors_list != null) {
            for (var i = 0; i < deal_risk_factors_list.length; i++) {
                var deal_risk_factors_dict = deal_risk_factors_list[i];
                var deal_risk_factors_expected = deal_risk_factors_dict['expected'];
                var deal_risk_factors_requirement = deal_risk_factors_dict['requirement'];
                var deal_risk_factors_actual = deal_risk_factors_dict['actual'];
                var deal_risk_factors_regulatory = deal_risk_factors_dict['regulatory'];
                var balloonText = "";
                if (deal_risk_factors_requirement.toLowerCase() != 'not required' || deal_risk_factors_requirement != null) {
                    balloonText = deal_risk_factors_requirement;
                }
                else {
                    balloonText = "This is the " + deal_risk_factors_regulatory + " expected date";
                }
                balloonText += " (" + deal_risk_factors_expected + ")";
                var color = randomColor({luminosity: 'dark', hue: 'random',})
                if (deal_risk_factors_expected != null) {
                    guides.push({
                        'date': new Date(deal_risk_factors_expected),
                        'balloonText': balloonText,
                        "lineColor": color,
                        "lineAlpha": 1,
                        "dashLength": 5,
                        "inside": true,
                        "labelRotation": 90,
                        "label": deal_risk_factors_regulatory + ' Expected',
                        "fontSize": 15,
                    });
                }
                if (deal_risk_factors_actual != null) {
                    guides.push({
                        'date': new Date(deal_risk_factors_actual),
                        "lineColor": color,
                        "lineAlpha": 1,
                        "dashLength": 0,
                        "inside": true,
                        "labelRotation": 90,
                        "label": deal_risk_factors_regulatory + ' Approved',
                        "fontSize": 15,
                        "balloonText": "This is the " + deal_risk_factors_regulatory + " Approved date (" + deal_risk_factors_actual + ")",
                    });
                }
            }
        }

        if (acquirer_error_flag != 1) {
            // First process Acquirer
            for (var j = 0; j < hist_prices_dates_acquirer.length; j++) {
                chartData.push({
                    date: hist_dates_acquirer[j],
                    acq_px_last: hist_prices_dates_acquirer[j],
                });
            }

            for (var i = 0; i < target_ticker_dates.length; i++) {
                if (target_ticker_prices[i] != null) {
                    chartData[i]['px_last'] = target_ticker_prices[i];
                }

            }

        }

        else {
            for (var i = 0; i < target_ticker_prices.length; i++) {
                chartData.push({
                    date: target_ticker_dates[i],
                    px_last: target_ticker_prices[i],
                });
            }

        }


        target_acquier_charts = AmCharts.makeChart(div_id, {
            "type": "serial",
            "theme": "light",
            "dataProvider": chartData,
            "hideCredits": true,
            "legend": {
                "useGraphSettings": true
            },
            "graphs": [{
                "title": target_ticker,
                "balloonText": "[[px_last]]",
                "connect": true,
                "lineColor": "#b6d278",
                "lineThickness": 2,
                "valueField": "px_last"
            }, {
                "title": acquirer_ticker,
                "balloonText": "[[acq_px_last]]",
                "connect": true,
                "lineColor": "#E9962C",
                "lineThickness": 2,
                "valueField": "acq_px_last",

            }],
            "export": {
                "enabled": true
            },
            "balloon": {
                "fixedPosition": false,
            },
            "guides": guides,
            "chartCursor": {
                "pan": true,
                "valueLineEnabled": true,
                "valueLineBalloonEnabled": true,
                "cursorAlpha": 1,
                "cursorColor": "#258cbb",
                "limitToGraph": "g1",
                "valueLineAlpha": 0.2,
                "valueZoomable": true
            },
            "chartScrollbar": {
                "graph": "g1",
                "oppositeAxis": false,
                "offset": 30,
                "backgroundAlpha": 0,
                "selectedBackgroundAlpha": 0.1,
                "selectedBackgroundColor": "#888888",
                "graphFillAlpha": 0,
                "graphLineAlpha": 0.5,
                "selectedGraphFillAlpha": 0,
                "selectedGraphLineAlpha": 1,
                "autoGridCount": true,
                "color": "#AAAAAA"
            },
            "dataDateFormat": "YYYY-MM-DD",
            "categoryField": "date",
            "categoryAxis": {
                "minPeriod": "DD",
                "parseDates": true,
                "minorGridEnabled": true
            }

        });
    }

    /* Generate The CIX Price Chart and Spread Index Chart
     */
    try {
        let cix_prices = $.parseJSON($('#cix_index_json').val())['PX_LAST'];
        let cix_dates = $.parseJSON($('#cix_index_json').val())['date'];
        let cix_index = $('#mna_idea_cix_index').val();

        generateTargetPriceChart(cix_prices, cix_dates, [], 'mna_idea_cix_price_chart', cix_index, '', 1);

        // Generate the Spread Index Chart...

        let spread_index_prices = $.parseJSON($('#spread_index_json').val())['PX_LAST'];
        let spread_index_dates = $.parseJSON($('#spread_index_json').val())['date'];
        let spread_index = $('#mna_idea_spread_index').val();

        generateTargetPriceChart(spread_index_prices, spread_index_dates, [], 'mna_idea_spread_index_chart', spread_index, '', 1);
    } catch (err) {
        console.log(err);
        console.log('Could not populate Spread/CIX Charts...')
    }


// SECTION FOR SCENARIO ANALYSIS **************************
    $('#run_scenario_analysis').on('click', function () {
        //Get all the Required Inputs
        var category = $('#mna_idea_scenario_select').val();
        var cash_terms = $('#deal_cash_terms').val();
        var share_terms = $('#deal_share_terms').val();
        var aum = $('#fund_aum').val();
        var deal_upside = $('#deal_upside').val();
        var deal_downside = $('#deal_downside').val();
        var target_current_price = $('#target_current_price').val();
        var target_shares_outstanding = $('#target_shares_outstanding').val();
        var target_shares_float = $('#target_shares_float').val();
        var scenario_analysis_csrf_token = $('#scenario_analysis_csrf_token').val();
        var acquirer_upside = $('#deal_acquirer_upside').val();
        var target_last_price = $('#target_current_price').val();
        var deal_id = $('#deal_id').val();

        $.ajax({
            type: 'POST',
            url: '../risk/mna_idea_run_scenario_analysis',
            data: {
                'csrfmiddlewaretoken': scenario_analysis_csrf_token,
                'category': category,
                'cash_terms': cash_terms,
                'share_terms': share_terms,
                'aum': aum,
                'deal_upside': deal_upside,
                'deal_downside': deal_downside,
                'target_current_price': target_current_price,
                'target_shares_outstanding': target_shares_outstanding,
                'target_shares_float': target_shares_float,
                'acquirer_upside': acquirer_upside,
                'target_last_price': target_last_price,
                'deal_id': deal_id
            },
            success: function (response) {
                deal_break_analysis.clear().draw();
                seventy_twentyfive_analysis.clear().draw();
                deal_break_analysis_55_45.clear().draw();

                if (response == 'Failed') {
                    toastr.error('Failed Running Analysis!', 'Please check your Inputs!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }


                response = $.parseJSON(response);

                if (response == 'Failed') {
                    toastr.error('Failed Running Analysis!', 'Please check logs!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    fill_analysis_tables(response['break_change'], response['scenario_change'], response['scenario_change_55_45'], $.parseJSON(response['break_scenario']), $.parseJSON(response['scenario_75_25']), $.parseJSON(response['scenario_55_45']));
                    toastr.success('Analysis Complete!', 'You may export to Pdf!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        });
    });

// ************** END ******** SECTION FOR SCENARIO ANALYSIS

    // Save MnA IDEA Overviews
    $('#save_mna_idea_overviews').on('click', function () {

        //Get the code from Summernote
        var comments = analyst_comments.summernote('code');
        var comment_csrf_token = $('#comments_csrf_token').val();
        var deal_id = $('#deal_id_under_consideration').val();
        //Create an Ajax Request to send the new comment info
        $.ajax({
            url: "../risk/update_comments",
            method: "POST",
            data: {
                'deal_id': deal_id,
                'comments': comments,
                'csrfmiddlewaretoken': comment_csrf_token
            },
            success: function (response) {
                //Just show a toast of Comment Updated
                if (response == 'Success') {
                    toastr.success('Your Note was updated!', 'Changes saved!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    toastr.error('Failed to store the changes!', 'Please copy your edi and store it elsewhere!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }

            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }

        });


    });

    function fill_analysis_tables(break_change, scenario_change, scenario_change_55_45, break_scenario_df, scenario_75_25_df, scenario_55_45_df) {
        var shares_rows_data = [];
        var nav_break_data = [];
        var aum_data = [];
        var shares_out_row = [];
        var shares_float_row = [];


        shares_rows_data.push(break_change);
        nav_break_data.push('NAV Break');
        aum_data.push('% AUM');
        shares_out_row.push('% Shares Out.');
        shares_float_row.push('% Float');

        for (var i = 0; i < 11; i++) {
            shares_rows_data.push(break_scenario_df[i]['shares']);
            nav_break_data.push(break_scenario_df[i]['NAV break']);
            aum_data.push(break_scenario_df[i]['% nav']);
            shares_out_row.push(break_scenario_df[i]['% of S/O']);
            shares_float_row.push(break_scenario_df[i]['% of Float']);
        }

        deal_break_analysis.rows.add([shares_rows_data, nav_break_data, aum_data, shares_out_row, shares_float_row]).draw();

        // SECTION FOR 75/25 Probaility
        var shares_rows_75_25 = [scenario_change];
        var nav_break_75_25 = ['NAV 75/25'];
        var nav_break = ['NAV break'];
        var aum_data_75_25 = ['% AUM'];
        var shares_out_75_25 = ['% Shares Out.'];
        var shares_float_75_25 = ['% Float'];


        for (var i = 0; i < 11; i++) {
            shares_rows_75_25.push(scenario_75_25_df[i]['shares']);
            nav_break.push(scenario_75_25_df[i]['NAV break']);
            aum_data_75_25.push(scenario_75_25_df[i]['% nav']);
            shares_out_75_25.push(scenario_75_25_df[i]['% of S/O']);
            shares_float_75_25.push(scenario_75_25_df[i]['% of Float']);
            nav_break_75_25.push(scenario_75_25_df[i]['NAV 75/25']);

        }


        seventy_twentyfive_analysis.rows.add([shares_rows_75_25, nav_break_75_25, nav_break, aum_data_75_25, shares_out_75_25, shares_float_75_25]).draw();


        // Process for 55/45 Probability
        var shares_rows_55_45 = [scenario_change_55_45];
        var nav_break_55_45 = ['NAV 55/45'];
        var nav_break = ['NAV break'];
        var aum_data_55_45 = ['% AUM'];
        var shares_out_55_45 = ['% Shares Out.'];
        var shares_float_55_45 = ['% Float'];


        for (var i = 0; i < 11; i++) {
            shares_rows_55_45.push(scenario_55_45_df[i]['shares']);
            nav_break.push(scenario_55_45_df[i]['NAV break']);
            aum_data_55_45.push(scenario_55_45_df[i]['% nav']);
            shares_out_55_45.push(scenario_55_45_df[i]['% of S/O']);
            shares_float_55_45.push(scenario_55_45_df[i]['% of Float']);
            nav_break_55_45.push(scenario_55_45_df[i]['NAV 55/45']);

        }

        deal_break_analysis_55_45.rows.add([shares_rows_55_45, nav_break_55_45, nav_break, aum_data_55_45, shares_out_55_45, shares_float_55_45]).draw();

    }

    AmCharts.checkEmptyData = function (chart) {
        try {
            if (0 === chart.dataProvider.length) {
                var dataPoint = {
                    dummyValue: 0
                };
                dataPoint[chart.categoryField] = '';
                chart.dataProvider = [dataPoint];
                // add label
                chart.addLabel(0, '50%', 'No data could be gathered for this chart.', 'center', '20px', 'white');
                // set opacity of the chart div
                chart.chartDiv.style.opacity = 1.0;
                // redraw it
                chart.validateNow();
            }
        }
        catch (e) {
            console.log(e);
        }

    };

    AmCharts.checkEmptyData(target_acquier_charts);

    /**
     * Section for Handling Addition/Updation of Peer set. Realtime chart rendering included. Following routines are included with functionality...
     * 1. Gathering the required inputs
     * 2. Event-handler on form submit
     * 3. Submit an Ajax Request (also check if current data needs to be saved for later population)
     * 4. Get valid reponse from controller and populate the EV/EBITDA charts, PE ratio charts and FCF Yield Charts
     * **/

    $('#mna_idea_add_peers_form').on('submit', function (e) {
        e.preventDefault(); //Prevent default behavior
        // Get the required inputs
        let deal_id = $('#deal_id').val();
        var peer_set = [];
        var csrf_token = $('#mna_idea_peers_csrf_token').val();
        $('#mna_idea_peer_table tr').each(function () {
            var fields = $(this).find(':input');
            var ticker = fields.eq(0).val();
            if (!(ticker === undefined || ticker === "")) {  // Header Row might cause undefined values. Hence check here first
                peer_set.push(
                    ticker + " EQUITY",
                );
            }
        });

        // Check if Save to DB required
        let save_to_db_flag = "OFF";
        if ($('#save_peer_to_db_check').is(":checked")) {
            save_to_db_flag = "ON"
        }

        //Clear Modal
        $('#mna_idea_add_peers_modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        //Spawn a loader
        $('.loader-inner').loaders();

        //Spawn a notification/toastr
        toastr.info('Charts will be populated automatically', 'Attempting to retrieve charts from Bloomberg....', {
            positionClass: 'toast-top-right',
            containerId: 'toast-top-right'
        });


        //Save to DB denoted by ON or OFF
        $.ajax({
            url: "../risk/mna_idea_add_peers",
            type: "POST",
            data: {
                'peer_set': JSON.stringify(peer_set),
                'save_to_db_flag': save_to_db_flag,
                'csrfmiddlewaretoken': csrf_token,
                'deal_id': deal_id
            },
            success: function (response) {
                $('.loader-inner').empty();
                if (response === 'Failed') {
                    toastr.error('Failed to add!', 'Please try again!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });

                }
                else {
                    //Reset and Close the Modal. Show a Preloader in the Chart Box till the response gets processed!
                    response = $.parseJSON(response);
                    //For each peer in JSon response, parse the ev_ebitda charts as JSON and create an EV_EBITDA chart and validat
                    createPeerCharts(response);

                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong!", "error");
                $('.loader-inner').empty();
            }
        })
    });

    function createPeerCharts(response) {
        valuationMultipleDatasets = [];
        let ev_ebitda_chart_ltm = parsePeerMultiplesChartData(response, 'ev_ebitda_ltm');
        let ev_ebitda_chart_1bf = parsePeerMultiplesChartData(response, 'ev_ebitda_1bf');
        let ev_ebitda_chart_2bf = parsePeerMultiplesChartData(response, 'ev_ebitda_2bf');

        //let ev_sales_chart_ltm = parsePeerMultiplesChartData(response, 'ev_sales_ltm');
        let ev_sales_chart_1bf = parsePeerMultiplesChartData(response, 'ev_sales_1bf');
        let ev_sales_chart_2bf = parsePeerMultiplesChartData(response, 'ev_sales_2bf');

        let pe_ratio_chart_ltm = parsePeerMultiplesChartData(response, 'pe_ratio_ltm');
        let pe_ratio_chart_1bf = parsePeerMultiplesChartData(response, 'pe_ratio_1bf');
        let pe_ratio_chart_2bf = parsePeerMultiplesChartData(response, 'pe_ratio_2bf');

        let fcf_yield_chart = parsePeerMultiplesChartData(response, 'fcf_yield');


        //Call make Charts and supply the data
        //createDataset(ev_sales_chart_ltm, 'ev_sales_value', '(LTM)');
        createDataset(ev_sales_chart_1bf, 'ev_sales_value', '(1BF)');
        createDataset(ev_sales_chart_2bf, 'ev_sales_value', '(2BF)');


        ev_sales_charts = createMultipleLineChart('mna_idea_ev_sales_chart', ev_sales_ltm_valuation_multiple_datasets, 'EV/Sales', 'ev_sales_value');
        valuationMultipleDatasets = []; //Reset Global Dataset

        createDataset(ev_ebitda_chart_1bf, 'ev_ebitda_value', '(1BF)');
        createDataset(ev_ebitda_chart_2bf, 'ev_ebitda_value', '(2BF)');
        createDataset(ev_ebitda_chart_ltm, 'ev_ebitda_value', '(LTM)');

        ebitda_charts = createMultipleLineChart('mna_idea_ev_ebitda_chart', ev_ebitda_ltm_valuation_multiple_datasets, 'EV-EBITDA', 'ev_ebitda_value');
        valuationMultipleDatasets = []; //Reset Global Dataset
        //Populate PE Ratio Chart

        createDataset(pe_ratio_chart_1bf, 'pe_ratio', '(1BF)');
        createDataset(pe_ratio_chart_2bf, 'pe_ratio', '(2BF)');
        createDataset(pe_ratio_chart_ltm, 'pe_ratio', '(LTM)');

        pe_ratio_charts = createMultipleLineChart('mna_idea_pe_ratio_chart', pe_ratio_ltm_valuation_multiple_datasets, 'PE Ratio', 'pe_ratio');
        //Populate FCF Yield charts
        valuationMultipleDatasets = []; //Reset Global Dataset
        createDataset(fcf_yield_chart, 'p_fcf_value', '');
        var fcfYieldCharts = createMultipleLineChart('mna_idea_fcf_yield_chart', valuationMultipleDatasets, 'Free Cash Flow Yield', 'p_fcf_value');


    }

    function createDataset(inputDataProvider, valueField, override) {
        var stockEvents = [];
        if (unaffected_date != 'None') {
            //Create Stock Event
            stockEvents.push({
                'date': new Date(unaffected_date),
                'backgroundColor': 'cyan',
                "showOnAxis": true,
                "type": "pin",
                'id': 'g1',
                "text": "Unaffected Date",
                'description': 'This is the Unaffected Date for the Deal..'
            });
        }
        $.each(inputDataProvider, function (k, v) {

            var ev_ebitda_ltm_data_provider = [];
            for (var i = 0; i < v.length; i++) {
                ev_ebitda_ltm_data_provider.push({
                    'date': v[i].date,
                    [valueField]: v[i][valueField]
                })
            }

            if (override === '(LTM)' && valueField === 'ev_ebitda_value') {
                //Push into LTM dataset

                ev_ebitda_ltm_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }
            else if (override === '(1BF)' && valueField === 'ev_ebitda_value') {
                //Push into 1bf dataset..
                ev_ebitda_onebf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }
            else if (override === '(2BF)' && valueField === 'ev_ebitda_value') {
                //Push into 2 bf
                ev_ebitda_twobf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }


            else if (override === '(1BF)' && valueField === 'ev_sales_value') {
                //Push into 2 bf
                ev_sales_onebf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }

            else if (override === '(2BF)' && valueField === 'ev_sales_value') {
                //Push into 2 bf
                ev_sales_twobf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }

            else if (override === '(LTM)' && valueField === 'pe_ratio') {
                //Push into 2 bf
                pe_ratio_ltm_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }
            else if (override === '(1BF)' && valueField === 'pe_ratio') {
                //Push into 2 bf
                pe_ratio_onebf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }
            else if (override === '(2BF)' && valueField === 'pe_ratio') {
                //Push into 2 bf
                pe_ratio_twobf_valuation_multiple_datasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }
            else if (valueField === 'p_fcf_value') {
                //Only FCF Yield
                valuationMultipleDatasets.push({
                    "title": k + override,
                    "dataProvider": ev_ebitda_ltm_data_provider,
                    categoryField: "date",
                    fieldMappings: [{
                        fromField: [valueField],
                        toField: [valueField]
                    }],
                    "stockEvents": stockEvents,
                    "compared": true,
                });
            }


        });
    }


    function parsePeerMultiplesChartData(response, mneumonic) {
        var chartData = {};
        var innerChartData = {};

        $.each(response, function (peer_ticker, v) {
            $.each(response[peer_ticker], function (k, v) {
                try {
                    if (k.toString().indexOf(mneumonic) != -1) {
                        //Populate EvEbitda data
                        innerChartData = $.parseJSON(v);
                    }
                } catch (err) {
                    console.log('Json parse error for key ' + k);
                }
            });
            chartData[peer_ticker] = innerChartData;
        });


        return chartData;
    }


    function createMultipleLineChart(div_id, dataset, title, valueField) {

        var chart = AmCharts.makeChart(div_id, {
            "type": "stock",
            "theme": "light",
            "dataSets": dataset,
            "hideCredits": true,
            panels: [{
                recalculateToPercents: "never",
                title: [title],
                stockGraphs: [{
                    "id": 'g1',
                    "valueField": valueField,
                    "comparable": true,
                    connect: false

                }],

                stockLegend: {
                    useGraphSettings: true
                }
            }],
            "dataSetSelector": {
                "position": "left",
                "listHeight": 150
            },


        });

        return chart;
    }

    /**
     * Handle New Lawyer Report Add Request
     * **/

    $('#submit_mna_idea_new_lawyer_report_request').on('click', function () {
        // Collect the Required Inputs
        let lawyer_report_date = $('#mna_idea_lawyer_date').val();
        let analyst_by = $('#lawyer_analyst_by').val();
        let lawyer_report = $('#mna_idea_lawyer_report').summernote('code');
        let title = $('#mna_idea_note_title').val();
        let csrf_token = $('#mna_idea_lawyer_csrf_token').val();
        let deal_id = $('#deal_id').val();

        $.ajax({
            url: '../risk/add_new_mna_idea_lawyer_report',
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': csrf_token,
                'lawyer_report_date': lawyer_report_date,
                'analyst_by': analyst_by,
                'lawyer_report': lawyer_report,
                'title': title,
                'deal_id': deal_id
            },
            success: function (response) {
                $('#mna_idea_add_lawyer_report_modal').modal('hide');
                if (response === 'Success') {
                    toastr.success('Added!', 'Reloading the Page!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                    location.reload();
                } else {
                    toastr.error('Failed Adding Note!', 'Please check your Inputs!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        });
    });

    /**
     *Create Table Row listeners for Lawyer and Community Reports. Spawn a Modal for Edit Functionality!
     * Refers to the following view in the controller: update_mna_idea_lawyer_report & update_mna_idea__community_report
     **/

    $('.table-responsive').on("click", "#mna_idea_lawyer_reports_table tr ", function () {
        let $tds = $(this).find('td');
        let date = moment($tds.eq(0).text()).format("YYYY-MM-DD");
        let analyst = $tds.eq(1).text();
        let title = $tds.eq(2).text();
        let report = $tds.eq(2).attr('data-value');
        let report_id = $(this).data("id");
        //Populate the Modal with above values
        $('#mna_idea_lawyer_date').val(date);
        $('#lawyer_analyst_by').val(analyst).change();
        var lawyer_report_summernote = $('#mna_idea_lawyer_report').summernote();
        lawyer_report_summernote.summernote('code', report);
        $('#mna_idea_note_title').val(title);

        //Display the Modal
        $('#mna_idea_add_lawyer_report_modal').modal('show');

        //Get the Updated Summernote

        $('#mna_idea_update_lawyer_report_request').on('click', function () {
            report = lawyer_report_summernote.summernote('code');
            date = $('#mna_idea_lawyer_date').val();
            analyst = $('#lawyer_analyst_by').val();
            title = $('#mna_idea_note_title').val();
            $.ajax({
                url: '../risk/update_mna_idea_lawyer_report',
                type: 'POST',
                data: {
                    'id': report_id,
                    'date': date,
                    'analyst_by': analyst,
                    'title': title,
                    'report': report
                },
                success: function (response) {
                    if (response === 'Success') {
                        toastr.success('Report Updated!', 'Reloading the Page!', {
                            positionClass: 'toast-top-right',
                            containerId: 'toast-top-right'
                        });
                        location.reload();
                    }
                    else {
                        toastr.error('Failed Updating Laywer Report!', 'Please check your Inputs or contact support!', {
                            positionClass: 'toast-top-right',
                            containerId: 'toast-top-right'
                        });
                    }

                },
                error: function (err) {
                    console.log(err);
                    toastr.error('Failed Updating Laywer Report!', 'Please check your Inputs or contact support!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            })

        });

        $('#mna_idea_delete_lawyer_report_request').on('click', function () {
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Note!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        url: '../risk/delete_mna_idea_lawyer_report',
                        data: {'id': report_id},
                        type: 'POST',
                        success: function (response) {
                            if (response === 'Success') {
                                toastr.success('Note Deleted!', 'Reloading the Page!', {
                                    positionClass: 'toast-top-right',
                                    containerId: 'toast-top-right'
                                });
                                location.reload();
                            }
                            else {
                                toastr.error('Failed Deleting Note!', 'Please check your Inputs or contact support!', {
                                    positionClass: 'toast-top-right',
                                    containerId: 'toast-top-right'
                                });
                            }

                        },
                        error: function (err) {
                            console.log(err);
                            toastr.error('Failed Updating Note!', 'Please check your Inputs or contact support!', {
                                positionClass: 'toast-top-right',
                                containerId: 'toast-top-right'
                            });
                        }
                    })

                }
            });
        });
    });


    /**
     * Handle MnA Idea Weekly Downside Estimates
     * Parmas: From Modal
     * Ajax :  View- add_or_update_mna_idea_weekly_downside_estimates
     * Security: CSRF Token set through Ajax Instance on Page Load....
     * Note: The Week number, Start Date and End Date will be filled at the backend..
     */

    $('#submit_mna_idea_weekly_downside_request').on('click', function () {
        // Get all the required params
        let downside_estimate = $('#mna_idea_weekly_downside_estimate').val();
        let downside_analyst = $('#mna_idea_weekly_downside_analyst').val();
        let downside_comment = downside_comments.summernote('code');
        let deal_id = $('#deal_id_under_consideration').val();
        // Got all Params....Submit an Ajax Request to the risk app Controller...
        $.ajax({
            url: "../risk/add_or_update_mna_idea_weekly_downside_estimates",
            type: "POST",
            data: {
                'downside_estimate': downside_estimate,
                'downside_analyst': downside_analyst,
                'downside_comment': downside_comment,
                'deal_id': deal_id
            },
            success: function (response) {
                if (response === 'Success') {
                    // Spawn Success Toastr. Reload the Page
                    toastr.success('Thanks!. Your Downside Estimate is recorded...', 'Reloading the Page!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                    location.reload();
                }
                else {
                    //Spawn Error Toastr
                    toastr.error('Failed to add/update your downside estimate', 'Please check your Inputs or contact support!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        });


    });

    /**
     * Following Event Handler for Dynamic population of Comment modal for each Analyst
     * Handled with Event-Delegation for Dynamically added historical estimates....
     */
    $('#mna_idea_weekly_downside_estimates_table').on('click', 'tr td a', function (e) {
        e.preventDefault();
        let $this = $(this);
        let comment = $this.data('comment');
        $('#mna_idea_weekly_downside_estimate_click_comment').summernote('code', comment);
        let modal = $this.attr('href');
        $(modal).modal('show');
    });


    /* Function to Populate Unaffected Date, CIX Index and Spread Index.... */

    $('#submit_mna_idea_unaffected_date_request').on('click', function () {

        // Get the required inputs
        let deal_id = $('#deal_id').val();
        let unaffected_date = $('#mna_idea_unaffected_date_input').val();

        //Clear Modal
        $('#mna_idea_add_unaffected_date_modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        $.ajax({
            url: "../risk/mna_idea_add_unaffected_date",
            type: "POST",
            data: {
                'unaffected_date': unaffected_date,
                'deal_id': deal_id
            },
            success: function (response) {
                if (response === 'Failed') {
                    toastr.error('Failed to add!', 'Please try again!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                    location.reload();

                }
                else {
                    toastr.info('Unaffected Date Updated...', 'Refreshing the page....', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });


                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        })
    });


    $('#submit_mna_idea_new_cix_request').on('click', function () {
        // Get the required inputs
        let deal_id = $('#deal_id').val();
        let cix = $('#mna_idea_cix_input').val();

        //Clear Modal
        $('#mna_idea_add_cix_modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        //Spawn a loader
        $('.loader-inner').loaders();

        //Spawn a notification/toastr
        toastr.info('Populating chart (Please Check Tab)', 'Attempting to retrieve charts from Bloomberg....', {
            positionClass: 'toast-top-right',
            containerId: 'toast-top-right'
        });

        //Save to DB denoted by ON or OFF
        $.ajax({
            'url': '../risk/retrieve_cix_index',
            'type': 'POST',
            data: {'cix': cix, 'deal_id': deal_id},
            success: function (response) {
                $('.loader-inner').empty();
                if (response === 'Failed') {
                    toastr.error('Failed updating CIX!', 'Please try again!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    response = $.parseJSON(response);
                    let ticker_prices = response['PX_LAST'];
                    let ticker_dates = response['date'];

                    generateTargetPriceChart(ticker_prices, ticker_dates, hist_prices_dates_acquirer, 'mna_idea_cix_price_chart', cix, '', 1);

                }


            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        })
    });

    $('#mna_idea_add_spread_index_form').on('submit', function (e) {
        e.preventDefault(); //Prevent default behavior
        // Get the required inputs
        let deal_id = $('#deal_id').val();
        let spread_index = $('#mna_idea_spread_index_input').val();
        //Clear Modal
        $('#mna_idea_add_spread_index_modal').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        //Spawn a loader
        $('.loader-inner').loaders();

        //Spawn a notification/toastr
        toastr.info('Populating chart (Please Check Tab)', 'Attempting to retrieve charts from Bloomberg....', {
            positionClass: 'toast-top-right',
            containerId: 'toast-top-right'
        });

        //Save to DB denoted by ON or OFF
        $.ajax({
            url: "../risk/retrieve_spread_index",
            type: "POST",
            data: {
                'spread_index': spread_index,
                'deal_id': deal_id
            },
            success: function (response) {
                $('.loader-inner').empty();
                if (response === 'Failed') {
                    toastr.error('Failed to add!', 'Please try again!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });

                }
                else {
                    response = $.parseJSON(response);
                    let ticker_prices = response['PX_LAST'];
                    let ticker_dates = response['date'];
                    generateTargetPriceChart(ticker_prices, ticker_dates, hist_prices_dates_acquirer, 'mna_idea_spread_index_chart', spread_index, '', 1);
                }
            },
            error: function (e) {
                swal("Error!", "Something went wrong - ", "error");
            }
        })
    });


    /* Button Click to change Datasets to 1BF, 2BF, LTM (Peer multiples) */
    $('.show_ltm_dataset').on('click', function () {
        ebitda_charts.dataSets = [];
        pe_ratio_charts.dataSets = [];
        ev_sales_charts.dataSets = [];
        for (var i = 0; i < ev_ebitda_ltm_valuation_multiple_datasets.length; i++) {
            ebitda_charts.dataSets.push(ev_ebitda_ltm_valuation_multiple_datasets[i]);
            ebitda_charts.mainDataSet = ev_ebitda_ltm_valuation_multiple_datasets[i];
            ev_sales_charts.dataSets.push(ev_sales_ltm_valuation_multiple_datasets[i]);
            ev_sales_charts.mainDataSet = ev_sales_ltm_valuation_multiple_datasets[i];
            pe_ratio_charts.dataSets.push(pe_ratio_ltm_valuation_multiple_datasets[i]);
            pe_ratio_charts.mainDataSet = pe_ratio_ltm_valuation_multiple_datasets[i];
        }
        ebitda_charts.validateData();
        ev_sales_charts.validateData();
        pe_ratio_charts.validateData();
        ebitda_charts.validateNow();
        pe_ratio_charts.validateNow();
        ev_sales_charts.validateNow();


    });

    $('.show_1bf_dataset').on('click', function () {

        ebitda_charts.dataSets = [];
        pe_ratio_charts.dataSets = [];
        ev_sales_charts.dataSets = [];

        for (var i = 0; i < ev_ebitda_onebf_valuation_multiple_datasets.length; i++) {
            ebitda_charts.dataSets.push(ev_ebitda_onebf_valuation_multiple_datasets[i]);
            ebitda_charts.mainDataSet = ev_ebitda_onebf_valuation_multiple_datasets[i];
            ev_sales_charts.dataSets.push(ev_sales_onebf_valuation_multiple_datasets[i]);
            ev_sales_charts.mainDataSet = ev_sales_onebf_valuation_multiple_datasets[i];
            pe_ratio_charts.dataSets.push(pe_ratio_onebf_valuation_multiple_datasets[i]);
            pe_ratio_charts.mainDataSet = pe_ratio_onebf_valuation_multiple_datasets[i];
        }
        ebitda_charts.validateData();
        ev_sales_charts.validateData();
        pe_ratio_charts.validateData();
        ebitda_charts.validateNow();
        pe_ratio_charts.validateNow();
        ev_sales_charts.validateNow();

    });

    $('.show_2bf_dataset').on('click', function () {
        ebitda_charts.dataSets = [];
        ev_sales_charts.dataSets = [];
        pe_ratio_charts.dataSets = [];

        for (var i = 0; i < ev_ebitda_twobf_valuation_multiple_datasets.length; i++) {
            ebitda_charts.dataSets.push(ev_ebitda_twobf_valuation_multiple_datasets[i]);
            ebitda_charts.mainDataSet = ev_ebitda_twobf_valuation_multiple_datasets[i];
            ev_sales_charts.dataSets.push(ev_sales_twobf_valuation_multiple_datasets[i]);
            ev_sales_charts.mainDataSet = ev_sales_twobf_valuation_multiple_datasets[i];
            pe_ratio_charts.dataSets.push(pe_ratio_twobf_valuation_multiple_datasets[i]);
            pe_ratio_charts.mainDataSet = pe_ratio_twobf_valuation_multiple_datasets[i];
        }
        ebitda_charts.validateData();
        ev_sales_charts.validateData();
        pe_ratio_charts.validateData();
        ebitda_charts.validateNow();
        pe_ratio_charts.validateNow();
        ev_sales_charts.validateNow();

    });


    $('.show_1bf_dataset').trigger('click'); // Show 1BF dataset by Default..

});