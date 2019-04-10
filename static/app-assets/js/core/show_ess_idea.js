let calculations_array_global = [];
$(document).ready(function () {
    // Step by Step calculations
    try {
        let regression_calcs_latest = $.parseJSON($('#regression_calcs_latest').val());
        let latest_calcs_array = [];
        latest_calcs_array = fill_calculations_dictionary(regression_calcs_latest);
        set_global_calculations_array(latest_calcs_array);
    }
    catch (e) {
        console.log(e);
    }


    $('#ess_idea_company_overview').summernote({'height': '250px'});
    $('#ess_idea_situation_overview').summernote({'height': '250px'});
    /***********************************************************
     *               New User - Page Visist Stats               *
     ***********************************************************/
    $('.premium-analysis').hide();
    $('.premium-analysis-table').hide();
    $('#show_ess_idea_news_items').DataTable();
    $('#show_ess_idea_notes_table').DataTable();
    var peer_valution_table = $('#peer_valuation_table').DataTable({
        "aoColumnDefs": [{
            "aTargets": [4, 5, 6, 7, 8, 9],
            "mRender": function (data) {
                return parseFloat(data).toFixed(2);
            }
        }, {
            "aTargets": [2],
            "mRender": function (data) {
                return "$" + Math.round(data).toString();
            },
            "fnCreatedCell": function (nTd) {
                var $currencyCell = $(nTd);
                var commaValue = $currencyCell.text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
                $currencyCell.text(commaValue);
            }
        },
            {
                "aTargets": [3],
                "mRender": function (data) {
                    return "$" + (Math.round(data / 1000000)).toString() + "M";
                },
                "fnCreatedCell": function (nTd) {
                    var $currencyCell = $(nTd);
                    var commaValue = $currencyCell.text().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1,");
                    $currencyCell.text(commaValue);
                }
            }]
    });


    (function () {
        Colors = {};
        Colors.names = {
            aqua: "#00ffff",
            beige: "#f5f5dc",
            cyan: "#00ffff",
            darkkhaki: "#bdb76b",
            fuchsia: "#ff00ff",
            gold: "#ffd700",
            green: "#008000",
            khaki: "#f0e68c",
            lightblue: "#add8e6",
            lightcyan: "#e0ffff",
            lightgreen: "#90ee90",
            lightgrey: "#d3d3d3",
            lightpink: "#ffb6c1",
            lightyellow: "#ffffe0",
            lime: "#00ff00",
            orange: "#ffa500",
            pink: "#ffc0cb",
            silver: "#c0c0c0",
            white: "#ffffff",
            yellow: "#ffff00"
        };

    })();

    Colors.random = function () {
        var result;
        var count = 4;
        for (var prop in this.names)
            if (Math.random() < 1 / ++count)
                result = prop;
        return this.names[result];
    };


    var stockEvents = [];
    /** Save Downside Changes **/
    var downside_changes = $('#ess_idea_downside_changes').val();
    try {
        downside_changes = $.parseJSON(downside_changes);

        for (var i = 0; i < downside_changes.length; i++) {
            stockEvents.push({
                "date": new Date(2018, 05, 05),
                "type": "text",
                "backgroundColor": "#85CDE6",
                "graph": "g1",
                "text": "Deal Revision Point",
                "description": "Upside Revised to:" + downside_changes[i]['pt_up'] + " & Downside Revised to:" + downside_changes[i]['pt_down']
            })
        }
    } catch (err) {
        console.log(err);
        stockEvents = [];
    }

    /** Peer Valuation Charts **/
    try {
        var peer_tickers = $('#peer_tickers').val().split(',');
        var ev_ebitda_chart_data_ltm = generateEvEbitdaChartData('#ev_ebitda_chart_ltm', 'ev_ebitda_value');
        var ev_ebitda_chart_data_1bf = generateEvEbitdaChartData('#ev_ebitda_chart_1bf', 'ev_ebitda_value');
        var ev_ebitda_chart_data_2bf = generateEvEbitdaChartData('#ev_ebitda_chart_2bf', 'ev_ebitda_value');

        var ev_sales_chart_data_ltm = generateEvEbitdaChartData('#ev_sales_chart_ltm', 'ev_sales_value');
        var ev_sales_chart_data_1bf = generateEvEbitdaChartData('#ev_sales_chart_1bf', 'ev_sales_value');
        var ev_sales_chart_data_2bf = generateEvEbitdaChartData('#ev_sales_chart_2bf', 'ev_sales_value');

        var p_eps_chart_data_ltm = generateEvEbitdaChartData('#p_eps_chart_ltm', 'pe_ratio');
        var p_eps_chart_data_1bf = generateEvEbitdaChartData('#p_eps_chart_1bf', 'pe_ratio');
        var p_eps_chart_data_2bf = generateEvEbitdaChartData('#p_eps_chart_2bf', 'pe_ratio');

        var p_fcf_chart_data = generateEvEbitdaChartData('#p_fcf_chart', 'p_fcf_value');


    } catch (err) {
        console.log(err);
    }


    $('#fperiod_override').on('change', function () {
        var selected_option = this.options[this.selectedIndex].value;
        if (selected_option === 'LTM') {
            //Set chart Data provider to LTM
            EV_EBITDA_CHART.dataProvider = ev_ebitda_chart_data_ltm[0];
            EV_EBITDA_CHART.graphs = ev_ebitda_chart_data_ltm[1];
            EV_EBITDA_CHART.validateData();
            P_EPS_CHART.dataProvider = p_eps_chart_data_ltm[0];
            P_EPS_CHART.graphs = p_eps_chart_data_ltm[1];
            P_EPS_CHART.validateData();

            EV_SALES_CHART.dataProvider = ev_sales_chart_data_ltm[0];
            EV_SALES_CHART.graphs = ev_sales_chart_data_ltm[1];
            EV_SALES_CHART.validateData();


        }
        else if (selected_option === '1BF') {
            EV_EBITDA_CHART.dataProvider = ev_ebitda_chart_data_1bf[0];
            EV_EBITDA_CHART.graphs = ev_ebitda_chart_data_1bf[1];
            EV_EBITDA_CHART.validateData();


            EV_SALES_CHART.dataProvider = ev_sales_chart_data_1bf[0];
            EV_SALES_CHART.graphs = ev_sales_chart_data_1bf[1];
            EV_SALES_CHART.validateData();

            P_EPS_CHART.dataProvider = p_eps_chart_data_1bf[0];
            P_EPS_CHART.graphs = p_eps_chart_data_1bf[1];
            P_EPS_CHART.validateData();
        }
        else {
            EV_EBITDA_CHART.dataProvider = ev_ebitda_chart_data_2bf[0];
            EV_EBITDA_CHART.graphs = ev_ebitda_chart_data_2bf[1];
            EV_EBITDA_CHART.validateData();

            EV_SALES_CHART.dataProvider = ev_sales_chart_data_2bf[0];
            EV_SALES_CHART.graphs = ev_sales_chart_data_2bf[1];
            EV_SALES_CHART.validateData();

            P_EPS_CHART.dataProvider = p_eps_chart_data_2bf[0];
            P_EPS_CHART.graphs = p_eps_chart_data_2bf[1];
            P_EPS_CHART.validateData();
        }

    });

    function generateEvEbitdaChartData(chart_id, field_name) {
        let all_ev_ebitda_chart_data = JSON.parse($(chart_id).val());
        let all_ebitda_json_parsed = [];
        all_ev_ebitda_chart_data.forEach(function (entry) {
            all_ebitda_json_parsed.push($.parseJSON(entry.toString().replace(/None/gi, '\"None\"').toString().replace(/nan/gi, '\"NaN\"').toString().replace(/'/g, "\"")));
        });
        if (all_ebitda_json_parsed.length == 0) {
            return [[], []]
        }
        let max_ev_ebitda_chart = all_ebitda_json_parsed[0];
        let chartData = [];
        let graphs = [];
        for (let i = 0; i < max_ev_ebitda_chart.length; i++) {
            let obj = {};
            if (max_ev_ebitda_chart[i].date.toString() === 'None') {
                continue;
            }

            obj['date'] = max_ev_ebitda_chart[i].date.toString();

            let counter = 0;
            while (counter < peer_tickers.length) {
                if (all_ebitda_json_parsed[counter][i] === "NaN") {
                    //Assign Null Value
                    obj[peer_tickers[counter] + "_ev_ebitda"] = null;
                }
                else {
                    obj[peer_tickers[counter] + "_ev_ebitda"] = parseFloat(all_ebitda_json_parsed[counter][i][field_name]).toFixed(2);
                }
                counter++;
            }

            chartData.push(obj);
        }


        for (let i = 0; i < peer_tickers.length; i++) {
            graphs.push({
                "valueAxis": "v1",
                "lineColor": Colors.random(),
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "connect": false,
                "title": peer_tickers[i],
                "valueField": peer_tickers[i] + "_ev_ebitda",

            });
        }


        return [chartData, graphs];

    }

    let EV_EBITDA_CHART = AmCharts.makeChart("ess_idea_ev_ebitda_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },
        "hideCredits": true,
        "dataProvider": ev_ebitda_chart_data_ltm[0],
        "dataDateFormat": "YYYY-MM-DD",
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "precision": 2,

        }],
        "graphs": ev_ebitda_chart_data_ltm[1],
        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "minPeriod": "dd",
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });


    // EV/SAles Chart
    let EV_SALES_CHART = AmCharts.makeChart("ess_idea_ev_sales_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },
        // "hideCredits":true,
        "dataProvider": ev_sales_chart_data_ltm[0],
        "dataDateFormat": "YYYY-MM-DD",
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",

        }],
        "graphs": ev_sales_chart_data_ltm[1],
        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "minPeriod": "dd",
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });


    /**  P/EPS Chart **/

    let P_EPS_CHART = AmCharts.makeChart("ess_idea_p_eps_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },

        // "hideCredits":true,
        "dataDateFormat": "YYYY-MM-DD",
        "dataProvider": p_eps_chart_data_ltm[0],
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",

        }],
        "graphs": p_eps_chart_data_ltm[1],
        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "minPeriod": "dd",
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });


    /**  P/FCF Chart **/

    let P_FCF_CHART = AmCharts.makeChart("ess_idea_p_fcf_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },

        // "hideCredits":true,
        "dataDateFormat": "YYYY-MM-DD",
        "dataProvider": p_fcf_chart_data[0],
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",

        }],
        "graphs": p_fcf_chart_data[1],
        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "minPeriod": "dd",
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });


    /** Peer Valuation Chart Ends **/

    let alpha_hedge_market_netural_chart_data = generateAHMChartData();
    let unaffected_date = $('#ess_idea_unaffected_date').val();
    let AHMchart = AmCharts.makeChart("ess_idea_alpha_chart", {
        "type": "stock",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },
        "dataDateFormat": "YYYY-MM-DD",


        "dataSets": [{
            "fieldMappings": [{
                "fromField": "px_last",
                "toField": "px_last"
            }, {
                "fromField": "hedges",
                "toField": "hedges"
            },
                {
                    "fromField": "market_neutral_val",
                    "toField": "market_neutral_val"
                }],
            "dataProvider": alpha_hedge_market_netural_chart_data,
            "categoryField": "date",
            // EVENTS
            "stockEvents": stockEvents,
            "fillAlpha": 0.3
        }],
        // "hideCredits":true,

        "panels": [{
            "stockGraphs": [{
                "useDataSetColors": false,
                "id": "g1",
                "valueField": "px_last",
                "valueAxis": "a1",
                "title": "Alpha Chart",
                "lineColor": "#ff0400",
                "fillAlphas": 0.1

            }, {
                "useDataSetColors": false,
                "id": "g2",
                "valueField": "hedges",
                "valueAxis": "a1",
                "title": "Hedge Index",
                "lineColor": "orange",
                "fillAlphas": 0.1
            },
                {
                    "useDataSetColors": false,
                    "id": "g3",
                    "valueField": "market_neutral_val",
                    "valueAxis": "a2",
                    "title": "Market Neutral Chart",
                    "lineColor": "#1dff00",
                    "fillAlphas": 0.1
                }], "valueAxes": [{
                "id": "a1",
                "axisColor": "#FF6600",
                "position": "left",
                "offset": 0
            }, {
                "id": "a2",
                "axisColor": "#FCD202",
                "position": "right",
                "offset": 0
            }],
            "stockLegend": {
                useGraphSettings: true
            },
            "guides": [{
                "date": new Date(unaffected_date),
                "lineColor": "#ffffff",
                "lineAlpha": 1,
                "dashLength": 2,
                "inside": true,
                "labelRotation": 90,
                "label": "Unaffected Date"
            }],
        }],


        "chartScrollbarSettings":
            {
                "graph":
                    "g1"
            }
        ,
        "categoryAxesSettings": {
            "minPeriod": "DD",
            "maxSeries": 0
        },
        "chartCursorSettings":
            {
                "valueBalloonsEnabled":
                    true,
                "graphBulletSize":
                    1,
                "valueLineBalloonEnabled":
                    true,
                "valueLineEnabled":
                    true,
                "valueLineAlpha":
                    0.5
            }
        ,
        "export":
            {
                "enabled":
                    true
            },

    });


// generate some random data, quite different range
    function generateAHMChartData() {
        let alpha_chart_data = JSON.parse($('#alpha_chart').val());
        let hedge_chart_data = JSON.parse($('#hedge_chart').val());

        let chartData = [];
        let market_neutral_chart_data = JSON.parse($('#market_neutral_chart').val());
        // Construct Chart Data
        if (hedge_chart_data.length == 0) {
            //Only process for Alpha Charts
            for (let i = 0; i < alpha_chart_data.length; i++) {
                chartData.push({
                    date: alpha_chart_data[i].date,
                    px_last: parseFloat(alpha_chart_data[i].px_last).toFixed(2),
                })
            }
            return chartData;
        }


        for (let i = 0; i < hedge_chart_data.length; i++) {
            chartData.push({
                date: alpha_chart_data[i]['date'],
                px_last: parseFloat(alpha_chart_data[i]['px_last']).toFixed(2),
                hedges: parseFloat(hedge_chart_data[i]['vol']).toFixed(2),
                market_neutral_val: parseFloat(market_neutral_chart_data[i]['market_netural_value']).toFixed(2)
            })
        }

        return chartData;

    }

    /** Implied Probability Chart **/

    let implied_probability_chart_data = generateIMPChartData();


    let IMPchart = AmCharts.makeChart("ess_idea_implied_probability_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },
        "hideCredits": true,
        "dataDateFormat": "YYYY-MM-DD",
        "dataProvider": implied_probability_chart_data,
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "unit": '%',
        }, {
            "id": "v2",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "type": "date",

        }],
        "graphs": [{
            "valueAxis": "v1",
            "lineColor": "#FF6600",
            "bullet": "round",
            "bulletBorderThickness": 1,
            "hideBulletsCount": 30,
            "title": "Implied Probability Chart",
            "valueField": "implied_probability",
            "balloonText": "[[implied_probability]]%",
            "fillAlphas": 0.1,
            "id": "g1"
        }],

        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",

        "categoryAxis": {
            "parseDates": true,
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "categoryAxesSettings": {
            "minPeriod": "DD",
            "maxSeries": 0
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });

    function generateIMPChartData() {
        let implied_chart_data = JSON.parse($('#implied_probability_chart').val());
        let chartData = [];
        for (let i = 0; i < implied_chart_data.length; i++) {
            chartData.push({
                date: implied_chart_data[i].date,
                implied_probability: parseFloat(implied_chart_data[i].implied_probability * 100).toFixed(2),
            })
        }
        return chartData;
    }

    let upside_downside_records_data = generateUpsideDownsideTrackRecordData();

    function generateUpsideDownsideTrackRecordData() {
        let upside_downside_records = JSON.parse($('#upside_downside_records_df').val());
        let chartData = [];
        $('#model-upside').html("Upside: "+parseFloat(upside_downside_records[upside_downside_records.length-1].pt_up).toFixed(2));
        $('#model-downside').html("Downside: "+parseFloat(upside_downside_records[upside_downside_records.length-1].pt_down).toFixed(2));
        $('#model-ptwic').html("PT WIC: "+parseFloat(upside_downside_records[upside_downside_records.length-1].pt_wic).toFixed(2));
        for (let i = 0; i < upside_downside_records.length; i++) {
            chartData.push({
                date: upside_downside_records[i].date_updated,
                pt_up: parseFloat(upside_downside_records[i].pt_up).toFixed(2),
                pt_down: parseFloat(upside_downside_records[i].pt_down).toFixed(2),
                pt_wic: parseFloat(upside_downside_records[i].pt_wic).toFixed(2),
            })
        }
        return chartData;
    }

    let UpsideDownsideTrackRecordChart = AmCharts.makeChart("ess_idea_upside_downside_track_record_chart", {
        "type": "serial",
        "theme": "black",
        "legend": {
            "useGraphSettings": true
        },
        // "hideCredits":true,
        "dataDateFormat": "YYYY-MM-DD",
        "dataProvider": upside_downside_records_data,
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
        }, {
            "id": "v2",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "type": "date",

        }],
        "graphs": [{
            "valueAxis": "v1",
            "lineColor": "#29a329",
            "bullet": "round",
            "bulletBorderThickness": 1,
            "hideBulletsCount": 30,
            "title": "Price Target (Up)",
            "valueField": "pt_up",
            "fillAlphas": 0.1,
            "id": "g1"
        },
            {
                "valueAxis": "v1",
                "lineColor": "#cc0000",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": "Price Target (Down)",
                "valueField": "pt_down",
                "fillAlphas": 0.1,
                "id": "g2"
            },
            {
                "valueAxis": "v1",
                "lineColor": "#FF6600",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": "Price Target (WIC)",
                "valueField": "pt_wic",
                "fillAlphas": 0.1,
                "id": "g3"
            }],

        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",

        "categoryAxis": {
            "parseDates": true,
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });


    /** ----------------------- **/


    /** Event Premium Chart Chart **/

    let event_premium_chart_data = generateEventPremiumChartData();
    let EventPremiumChart = AmCharts.makeChart("ess_idea_event_premium_chart", {
        "type": "serial",
        "theme": "black",
        "dataDateFormat": "YYYY-MM-DD",
        "hideCredits": true,
        "dataProvider": event_premium_chart_data,
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "unit": "%"
        }, {
            "id": "v2",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",
            "type": "date",

        }],
        "graphs": [{
            "lineColor": "#FF6600",
            "valueAxis": "v1",
            "bullet": "round",
            "bulletBorderThickness": 1,
            "hideBulletsCount": 30,
            "title": "Event Premium Chart",
            "valueField": "event_premium",
            "balloonText": "[[event_premium]]%",
            "fillAlphas": 0.1
        }],
        "chartScrollbar": {},
        "chartCursor": {
            "cursorPosition": "mouse"
        },
        "categoryField": "date",
        "categoryAxis": {
            "parseDates": true,
            "axisColor": "#DADADA",
            "minorGridEnabled": true,
            "equalSpacing": true
        },
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
        },
        "categoryAxesSettings": {
            "minPeriod": "DD",
            "maxSeries": 0
        },
        "export": {
            "enabled": true,
            "position": "bottom-right"
        }
    });

    function generateEventPremiumChartData() {
        let event_premium_chart_data = JSON.parse($('#event_premium_chart').val());
        let chartData = [];
        for (let i = 0; i < event_premium_chart_data.length; i++) {
            chartData.push({
                date: event_premium_chart_data[i].date,
                event_premium: parseFloat(event_premium_chart_data[i].event_premium * 100).toFixed(2),
            })
        }
        return chartData;

    }


    /** ------------------------- **/
// News Table Clickable Row Functionality

    $('.clickable-row-news').click(function () {
        $('#show_ess_idea_news_article').summernote({'height': 300});
        $('#show_ess_idea_news_article').summernote('code', $(this).data('value'));
        $('#show_ess_idea_go_to_url').val($(this).data("href"));
        $('#show_ess_idea_news_modal').modal('show');
    });

// Add Goto URL onClick Listener

    $('#show_ess_idea_go_to_url').on('click', function () {
        window.open($(this).val());
    });

// Handlers for Notes
    $('.clickable-row-notes').click(function () {
        $('#show_ess_idea_note_article').summernote({'height': 300});
        $('#show_ess_idea_note_article').summernote('code', $(this).data('value'));
        $('#show_ess_idea_notes_modal').modal('show');
        let notes_id = $(this).data('ids');
        // POST Ajax Request for Attachments
        $.ajax({
            url: "../notes/get_attachments/",
            type: 'POST',
            data: {'notes_id': notes_id},
            success: function (response) {
                let attachments = response['attachments'];
                if (attachments.length > 0) {
                    let files = "<br> Your attachments:<br><br>";
                    for (var i = 0; i < attachments.length; i++) {
                        files += "<a href=" + attachments[i].url + ">" + attachments[i].filename + "</a><br />";
                    }
                    $('#edit_notes_attachments').html(files);
                }
            },
            error: function (err) {
                console.log(err);
            }
        });


    });


    $('#ess_bull_thesis').summernote({toolbar: [], height: 120});
    $('#ess_bull_thesis').summernote('disable');
    $('#ess_bear_thesis').summernote({toolbar: [], height: 120});
    $('#ess_bear_thesis').summernote('disable');
    $('#ess_our_thesis').summernote({toolbar: [], height: 120});
    $('#ess_our_thesis').summernote('disable');


    $('#ess_bull_thesis').summernote('code', $('#bull_thesis_input').val());
    $('#ess_our_thesis').summernote('code', $('#our_thesis_input').val());
    $('#ess_bear_thesis').summernote('code', $('#bear_thesis_input').val());

    $('#ess_idea_situation_overview').summernote('code', $('#ess_idea_situation_overview').data('value'));
    $('#ess_idea_situation_overview').summernote('disable');

    $('#ess_idea_company_overview').summernote('code', $('#ess_idea_company_overview').data('value'));
    $('#ess_idea_company_overview').summernote('disable');

})
;


/** Section to Show Premium Analysis.... **/
$('#show_premium_analysis').on('click', function (e) {
    //Get Deal ID for calling the Premium Analysis Function
    //Disable the button
    toastr.info('Generating Realtime Upside/Downside(Please wait)', 'Running Premium Analysis!', {
        positionClass: 'toast-top-left',
        containerId: 'toast-top-left'
    });
    $('#show_premium_analysis').prop('disabled', true);

    let deal_id = $('#ess_idea_deal_id').val();
    // Pass this to Views

    $.ajax({
        'url': '../risk/ess_idea_premium_analysis',
        'type': 'POST',
        'data': {'deal_id': deal_id},
        'success': function (response) {
            let task_id = response['task_id'];
            let success_url = "../risk/get_premium_analysis_results_from_worker";
            let progress_url = "../../celeryprogressmonitor/get_celery_task_progress?task_id=" + task_id.toString();
            $('#premium_analysis_regression_breakdown_table tbody').empty();

            function get_premium_analysis_results() {
                $.ajax({
                    'url': success_url,
                    'type': 'POST',
                    'data': {'task_id': task_id},
                    'success': function (response) {
                        $('#progress-bar').hide();
                        let dynamic_upside_downside = response;
                        let regression_results = response['regression_results'];
                        let regression_calculations = response['regression_calculations'];
                        let cix_calculations = response['cix_calculations'];
                        let calculations_array = [];
                        // Fill Calculations Dictionary
                        calculations_array = fill_calculations_dictionary(regression_calculations);
                        set_global_calculations_array(calculations_array); // Calculations Array is Set here. Will respond to event listeners
                        // Create Required Modals dynamically 3 multiples
                        let multiples = Object.keys(regression_results);
                        for (var i = 0; i < multiples.length; i++) {
                            let multiple = multiples[i];
                            let id = '';
                            if (multiple === 'EV/EBITDA') {
                                id = 'ev_ebitda'
                            }
                            else if (multiple === 'P/E') {
                                id = 'p_e'
                            }
                            else if (multiple === 'EV/Sales') {
                                id = 'ev_sales'
                            }
                            else if (multiple === 'DVD Yield') {
                                id = 'dvd_yield'
                            }
                            else if (multiple === 'FCF Yield') {
                                id = 'fcf_yield'
                            }
                            // Append Multiple
                            let currernt_row = '<tr>';
                            let row_cell = currernt_row + '<td>' + multiple + '</td>';

                            let coefficients = regression_results[multiples[i]]['Coefficients'];
                            // Iterate throught coeffieicent and create a Table
                            let coefficients_table = '<table class=\"table table-striped\"><thead><tr><th>Peer/Intercept</th><th>Coefficients</th></tr></thead><tbody>';

                            for (var peer in coefficients) {
                                coefficients_table += '<tr><td>' + peer + '</td><td>' + parseFloat(coefficients[peer]).toFixed(4) +
                                    '</td></tr>'
                            }
                            coefficients_table += '</table>';
                            // Create a Bootstrap Modal
                            get_regression_analysis_modal(id + '_coefficients', coefficients_table, 'Regression Coefficients');

                            row_cell += '<td>' + get_modal_launch_button('id', id + '_coefficients', 'View Coefficients') +
                                '</td>';

                            let peer_multiples_at_price_target_date = regression_results[multiples[i]]['Peers Multiples @ Price Target Date'];
                            // Iterate throught Peer Multiples at PT Date
                            let peer_multiples_at_pt_table = '<table class=\"table table-striped\"><thead><tr><th>Peer</th><th>Multiples</th></tr></thead><tbody>';

                            for (var peer in peer_multiples_at_price_target_date) {
                                peer_multiples_at_pt_table += '<tr><td>' + peer + '</td><td>' + parseFloat(peer_multiples_at_price_target_date[peer]).toFixed(2) +
                                    '</td></tr>'
                            }
                            peer_multiples_at_pt_table += '</table>';

                            get_regression_analysis_modal(id + '_peer_multiples_at_pt', peer_multiples_at_pt_table, 'Peer Multiples at Price Target Date');

                            row_cell += '<td>' + get_modal_launch_button('id', id + '_peer_multiples_at_pt', 'Peers Multiple Drilldown') +
                                '</td>';

                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Implied Multiple @ Price Target Date']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bear Multiple @ Price Target Date']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha PT WIC Multiple @ Price Target Date']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bull Multiple @ Price Target Date']).toFixed(2) + '</td>';

                            // Repeat the Above for Now Section
                            let peer_multiples_at_now = regression_results[multiples[i]]['Peers Multiples @ Now'];
                            // Iterate throught Peer Multiples at PT Date
                            let peer_multiples_at_now_table = '<table class=\"table table-striped\"><thead><tr><th>Peer</th><th>Multiples</th></tr></thead><tbody>';

                            for (var peer in peer_multiples_at_now) {
                                peer_multiples_at_now_table += '<tr><td>' + peer + '</td><td>' + parseFloat(peer_multiples_at_now[peer]).toFixed(2) +
                                    '</td></tr>'
                            }
                            peer_multiples_at_now_table += '</table>';

                            get_regression_analysis_modal(id + '_peer_multiples_at_now', peer_multiples_at_now_table, 'Peer Multiples (Now)');

                            row_cell += '<td>' + get_modal_launch_button('id', id + '_peer_multiples_at_now', 'Peers Multiple Drilldown') +
                                '</td>';

                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Implied Multiple @ Now']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bear Multiple @ Now']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha PT WIC Multiple @ Now']).toFixed(2) + '</td>';
                            row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bull Multiple @ Now']).toFixed(2) + '</td>';
                            row_cell += '</tr>';
                            $('#premium_analysis_regression_breakdown_table tbody').append(row_cell);
                        }

                        $('#show_premium_analysis').prop('disabled', false);
                        //Show the table
                        $('.premium-analysis').show();
                        $('.premium-analysis-table').show();
                        $('.cix_down_price').html(dynamic_upside_downside['cix_down_price']);
                        $('.cix_up_price').html(dynamic_upside_downside['cix_up_price']);
                        $('.regression_down_price').html(dynamic_upside_downside['regression_down_price']);
                        $('.regression_up_price').html(dynamic_upside_downside['regression_up_price']);
                        $('.wic_price_cix').html(dynamic_upside_downside['wic_cix_price']);
                        $('.wic_price_regression').html(dynamic_upside_downside['wic_regression_price']);
                    },
                    'error': function (err) {
                        console.log(err);
                    }

                });
            }

            $(function () {
                CeleryProgressBar.initProgressBar(progress_url, {
                    onSuccess: get_premium_analysis_results,
                    pollInterval: 2000,

                })
            });


        },

    });

});

function set_global_calculations_array(calculations_array) {
    calculations_array_global = calculations_array;
}


function fill_calculations_dictionary(regression_calculations) {
    let bull_calculations = [];
    let bear_calculations = [];
    let wic_calculations = [];

    let multiples = Object.keys(regression_calculations);
    for (var i = 0; i < multiples.length; i++) {
        let current_multiple = multiples[i];
        if (current_multiple === 'Total') {
            continue;
        }
        // Populate Bull Case Parameters for Modal
        bull_calculations.push({
            [current_multiple]: {
                '1': regression_calculations[current_multiple]['Alpha Implied Multiple @ PTD'],
                '2': regression_calculations[current_multiple]['Bull Multiple @ PTD'],
                '3': regression_calculations[current_multiple]['Bull Premium @ PTD'],
                '4': regression_calculations[current_multiple]['Alpha Implied Multiple @ Now'],
                '5': regression_calculations[current_multiple]['Bull Multiple @ Now'],
                '6': regression_calculations[current_multiple]['Upside'],
                '7': regression_calculations[current_multiple]['Upside (Adj,weighted)'],
            }
        });

        wic_calculations.push({
            [current_multiple]: {
                '1': regression_calculations[current_multiple]['Alpha Implied Multiple @ PTD'],
                '2': regression_calculations[current_multiple]['PT WIC Multiple @ PTD'],
                '3': regression_calculations[current_multiple]['PT WIC Premium @ PTD'],
                '4': regression_calculations[current_multiple]['Alpha Implied Multiple @ Now'],
                '5': regression_calculations[current_multiple]['PT WIC Multiple @ Now'],
                '6': regression_calculations[current_multiple]['PT WIC'],
                '7': regression_calculations[current_multiple]['PT WIC (Adj,weighted)'],
            }
        });


        bear_calculations.push({
            [current_multiple]: {
                '1': regression_calculations[current_multiple]['Alpha Implied Multiple @ PTD'],
                '2': regression_calculations[current_multiple]['Bear Multiple @ PTD'],
                '3': regression_calculations[current_multiple]['Bear Premium @ PTD'],
                '4': regression_calculations[current_multiple]['Alpha Implied Multiple @ Now'],
                '5': regression_calculations[current_multiple]['Bear Multiple @ Now'],
                '6': regression_calculations[current_multiple]['Downside'],
                '7': regression_calculations[current_multiple]['Downside (Adj,weighted)'],
            }
        });
    }
    //Push the totals
    bull_calculations.push({
        'Final': {'1': regression_calculations['Total']['Up Price (Regression)']}
    });

    bear_calculations.push({
        'Final': {'1': regression_calculations['Total']['Down Price (Regression)']}
    });

    wic_calculations.push({
        'Final': {'1': regression_calculations['Total']['PT WIC Price (Regression)']}
    });


    return [bull_calculations, bear_calculations, wic_calculations]
}

/** Section to Show Premium Analysis.... **/
$('#ess_idea_view_balance_sheet').on('click', function (e) {
    //Get Deal ID for calling the Premium Analysis Function
    //Disable the button
    toastr.info('Retrieving Balance Sheet(Please wait)', 'Gathering Balance Sheet Information!', {
        positionClass: 'toast-top-left',
        containerId: 'toast-top-left'
    });
    $('#ess_idea_view_balance_sheet').prop('disabled', true);

    let deal_id = $('#ess_idea_deal_id').val();
    // Pass this to Views

    $.ajax({
        'url': '../risk/ess_idea_view_balance_sheet',
        'type': 'POST',
        'data': {'deal_id': deal_id},
        'success': function (response) {
            $('#ess_idea_view_balance_sheet').prop('disabled', false);
            //Show the modal
            let balance_sheet_bloomberg = $.parseJSON(response['balance_sheet']);
            let upside_balance_sheet_adjustments = $.parseJSON(response['upside_balance_sheet_adjustments']);
            let wic_balance_sheet_adjustments = $.parseJSON(response['wic_balance_sheet_adjustments']);
            let downside_balance_sheet_adjustments = $.parseJSON(response['downside_balance_sheet_adjustments']);
            let adjust_upside_with_bloomberg = response['adjust_upside_with_bloomberg'];
            let adjust_wic_with_bloomberg = response['adjust_wic_with_bloomberg'];
            let adjust_downside_with_bloomberg = response['adjust_downside_with_bloomberg'];

            if (adjust_upside_with_bloomberg === 'No') {
                $('#use_upside_without_bloomberg').prop('checked', true);
            }
            if (adjust_wic_with_bloomberg === 'No') {
                $('#use_wic_without_bloomberg').prop('checked', true);
            }
            if (adjust_downside_with_bloomberg === 'No') {
                $('#use_downside_without_bloomberg').prop('checked', true);
            }

            $('#upside_balance_sheet_px').val(decimal_places(balance_sheet_bloomberg[0]['PX'], 2));
            $('#upside_balance_sheet_best_eps').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EPS'], 2));
            $('#upside_balance_sheet_best_net_income').val(decimal_places(balance_sheet_bloomberg[0]['BEST_NET_INCOME'], 1));
            $('#upside_balance_sheet_best_opp').val(decimal_places(balance_sheet_bloomberg[0]['BEST_OPP'], 1));
            $('#upside_balance_sheet_best_sales').val(decimal_places(balance_sheet_bloomberg[0]['BEST_SALES'], 1));
            $('#upside_balance_sheet_cur_ev_component').val(decimal_places(balance_sheet_bloomberg[0]['CUR_EV_COMPONENT'], 1));
            $('#upside_balance_sheet_best_capex').val(decimal_places(balance_sheet_bloomberg[0]['BEST_CAPEX'], 1));
            $('#upside_balance_sheet_best_ebitda').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EBITDA'], 1));
            $('#upside_balance_sheet_eqy_sh_out').val(decimal_places(balance_sheet_bloomberg[0]['EQY_SH_OUT'], 1));

            // Populate for On WIC Balance Sheet
            $('#wic_balance_sheet_px').val(decimal_places(balance_sheet_bloomberg[0]['PX'], 2));
            $('#wic_balance_sheet_best_eps').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EPS'], 2));
            $('#wic_balance_sheet_best_net_income').val(decimal_places(balance_sheet_bloomberg[0]['BEST_NET_INCOME'], 1));
            $('#wic_balance_sheet_best_opp').val(decimal_places(balance_sheet_bloomberg[0]['BEST_OPP'], 1));
            $('#wic_balance_sheet_best_sales').val(decimal_places(balance_sheet_bloomberg[0]['BEST_SALES'], 1));
            $('#wic_balance_sheet_cur_ev_component').val(decimal_places(balance_sheet_bloomberg[0]['CUR_EV_COMPONENT'], 1));
            $('#wic_balance_sheet_best_capex').val(decimal_places(balance_sheet_bloomberg[0]['BEST_CAPEX'], 1));
            $('#wic_balance_sheet_best_ebitda').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EBITDA'], 1));
            $('#wic_balance_sheet_eqy_sh_out').val(decimal_places(balance_sheet_bloomberg[0]['EQY_SH_OUT'], 1));

            // Populate for On Downside Balance Sheet
            $('#downsides_balance_sheet_px').val(decimal_places(balance_sheet_bloomberg[0]['PX'], 2));
            $('#downsides_balance_sheet_best_eps').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EPS'], 2));
            $('#downsides_balance_sheet_best_net_income').val(decimal_places(balance_sheet_bloomberg[0]['BEST_NET_INCOME'], 1));
            $('#downsides_balance_sheet_best_opp').val(decimal_places(balance_sheet_bloomberg[0]['BEST_OPP'], 1));
            $('#downsides_balance_sheet_best_sales').val(decimal_places(balance_sheet_bloomberg[0]['BEST_SALES'], 1));
            $('#downsides_balance_sheet_cur_ev_component').val(decimal_places(balance_sheet_bloomberg[0]['CUR_EV_COMPONENT'], 1));
            $('#downsides_balance_sheet_best_capex').val(decimal_places(balance_sheet_bloomberg[0]['BEST_CAPEX'], 1));
            $('#downsides_balance_sheet_best_ebitda').val(decimal_places(balance_sheet_bloomberg[0]['BEST_EBITDA'], 1));
            $('#downsides_balance_sheet_eqy_sh_out').val(decimal_places(balance_sheet_bloomberg[0]['EQY_SH_OUT'], 1));


            // Populate the Adjustments balance Sheet
            if (upside_balance_sheet_adjustments.length > 0) {
                $('#upside_adjustment_balance_sheet_px').val(decimal_places(upside_balance_sheet_adjustments[0]['PX'], 2));
                $('#upside_adjustment_balance_sheet_best_eps').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_EPS'], 2));
                $('#upside_adjustment_balance_sheet_best_net_income').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_NET_INCOME'], 1));
                $('#upside_adjustment_balance_sheet_best_opp').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_OPP'], 1));
                $('#upside_adjustment_balance_sheet_best_sales').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_SALES'], 1));
                $('#upside_adjustment_balance_sheet_cur_ev_component').val(decimal_places(upside_balance_sheet_adjustments[0]['CUR_EV_COMPONENT'], 1));
                $('#upside_adjustment_balance_sheet_best_capex').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_CAPEX'], 1));
                $('#upside_adjustment_balance_sheet_best_ebitda').val(decimal_places(upside_balance_sheet_adjustments[0]['BEST_EBITDA'], 1));
                $('#upside_adjustment_balance_sheet_eqy_sh_out').val(decimal_places(upside_balance_sheet_adjustments[0]['EQY_SH_OUT'], 1));

            }
            // Populate the Adjustments for WIC

            if (wic_balance_sheet_adjustments.length > 0) {
                $('#wic_adjustment_balance_sheet_px').val(decimal_places(wic_balance_sheet_adjustments[0]['PX'], 2));
                $('#wic_adjustment_balance_sheet_best_eps').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_EPS'], 2));
                $('#wic_adjustment_balance_sheet_best_net_income').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_NET_INCOME'], 1));
                $('#wic_adjustment_balance_sheet_best_opp').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_OPP'], 1));
                $('#wic_adjustment_balance_sheet_best_sales').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_SALES'], 1));
                $('#wic_adjustment_balance_sheet_cur_ev_component').val(decimal_places(wic_balance_sheet_adjustments[0]['CUR_EV_COMPONENT'], 1));
                $('#wic_adjustment_balance_sheet_best_capex').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_CAPEX'], 1));
                $('#wic_adjustment_balance_sheet_best_ebitda').val(decimal_places(wic_balance_sheet_adjustments[0]['BEST_EBITDA'], 1));
                $('#wic_adjustment_balance_sheet_eqy_sh_out').val(decimal_places(wic_balance_sheet_adjustments[0]['EQY_SH_OUT'], 1));

            }

            // Populate the Adjustments for Downsides
            console.log(downside_balance_sheet_adjustments);


            if (downside_balance_sheet_adjustments.length > 0) {
                $('#downsides_adjustment_balance_sheet_px').val(decimal_places(downside_balance_sheet_adjustments[0]['PX'], 2));
                $('#downsides_adjustment_balance_sheet_best_eps').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_EPS'], 2));
                $('#downsides_adjustment_balance_sheet_best_net_income').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_NET_INCOME'], 1));
                $('#downsides_adjustment_balance_sheet_best_opp').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_OPP'], 1));
                $('#downsides_adjustment_balance_sheet_best_sales').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_SALES'], 1));
                $('#downsides_adjustment_balance_sheet_cur_ev_component').val(decimal_places(downside_balance_sheet_adjustments[0]['CUR_EV_COMPONENT'], 1));
                $('#downsides_adjustment_balance_sheet_best_capex').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_CAPEX'], 1));
                $('#downsides_adjustment_balance_sheet_best_ebitda').val(decimal_places(downside_balance_sheet_adjustments[0]['BEST_EBITDA'], 1));
                $('#downsides_adjustment_balance_sheet_eqy_sh_out').val(decimal_places(downside_balance_sheet_adjustments[0]['EQY_SH_OUT'], 1));

            }


            $('#balance_sheet_modal').modal('show');
            caclulateFinalBalanceSheet();  //Populate the Final Balance Sheet
        },
        'error': function (error) {
            console.log(error);
        }
    });

});

/** Save Balance Sheet **/

/** Section to Show Premium Analysis.... **/
$('#save_balance_sheet').on('click', function (e) {
    //Get Deal ID for calling the Premium Analysis Function
    //Disable the button
    $('#balance_sheet_modal').modal('hide');
    let deal_id = $('#ess_idea_deal_id').val();
    // Pass this to Views
    let upside_balance_sheet = {
        'PX': $('#upside_adjustment_balance_sheet_px').val(),
        'BEST_EPS': $('#upside_adjustment_balance_sheet_best_eps').val(),
        'BEST_NET_INCOME': $('#upside_adjustment_balance_sheet_best_net_income').val(),
        'BEST_OPP': $('#upside_adjustment_balance_sheet_best_opp').val(),
        'BEST_SALES': $('#upside_adjustment_balance_sheet_best_sales').val(),
        'CUR_EV_COMPONENT': $('#upside_adjustment_balance_sheet_cur_ev_component').val(),
        'BEST_CAPEX': $('#upside_adjustment_balance_sheet_best_capex').val(),
        'BEST_EBITDA': $('#upside_adjustment_balance_sheet_best_ebitda').val(),
        'EQY_SH_OUT': $('#upside_adjustment_balance_sheet_eqy_sh_out').val()
    };

    let wic_balance_sheet = {
        'PX': $('#wic_adjustment_balance_sheet_px').val(),
        'BEST_EPS': $('#wic_adjustment_balance_sheet_best_eps').val(),
        'BEST_NET_INCOME': $('#wic_adjustment_balance_sheet_best_net_income').val(),
        'BEST_OPP': $('#wic_adjustment_balance_sheet_best_opp').val(),
        'BEST_SALES': $('#wic_adjustment_balance_sheet_best_sales').val(),
        'CUR_EV_COMPONENT': $('#wic_adjustment_balance_sheet_cur_ev_component').val(),
        'BEST_CAPEX': $('#wic_adjustment_balance_sheet_best_capex').val(),
        'BEST_EBITDA': $('#wic_adjustment_balance_sheet_best_ebitda').val(),
        'EQY_SH_OUT': $('#wic_adjustment_balance_sheet_eqy_sh_out').val()
    };

    // Save the PT Date Balance Sheet.

    let downside_balance_sheet = {
        'PX': $('#downsides_adjustment_balance_sheet_px').val(),
        'BEST_EPS': $('#downsides_adjustment_balance_sheet_best_eps').val(),
        'BEST_NET_INCOME': $('#downsides_adjustment_balance_sheet_best_net_income').val(),
        'BEST_OPP': $('#downsides_adjustment_balance_sheet_best_opp').val(),
        'BEST_SALES': $('#downsides_adjustment_balance_sheet_best_sales').val(),
        'CUR_EV_COMPONENT': $('#downsides_adjustment_balance_sheet_cur_ev_component').val(),
        'BEST_CAPEX': $('#downsides_adjustment_balance_sheet_best_capex').val(),
        'BEST_EBITDA': $('#downsides_adjustment_balance_sheet_best_ebitda').val(),
        'EQY_SH_OUT': $('#downsides_adjustment_balance_sheet_eqy_sh_out').val()
    };

    let x = $('#use_upside_without_bloomberg').is(":checked");
    let y = $('#use_wic_without_bloomberg').is(":checked");
    let z = $('#use_downside_without_bloomberg').is(":checked");

    let upside_with_bloomberg = 'Yes';
    let wic_with_bloomberg = 'Yes';
    let downside_with_bloomberg = 'Yes';

    if (x) {
        upside_with_bloomberg = 'No'
    }
    if (y) {
        wic_with_bloomberg = 'No'
    }
    if (z) {
        downside_with_bloomberg = 'No'
    }


    $.ajax({
        'url': '../risk/ess_idea_save_balance_sheet',
        'type': 'POST',
        'data': {
            'deal_id': deal_id,
            'upside_balance_sheet': JSON.stringify(upside_balance_sheet),
            'wic_balance_sheet': JSON.stringify(wic_balance_sheet),
            'downside_balance_sheet': JSON.stringify(downside_balance_sheet),
            'upside_with_bloomberg': upside_with_bloomberg,
            'wic_with_bloomberg': wic_with_bloomberg,
            'downside_with_bloomberg': downside_with_bloomberg
        },
        'success': function (response) {
            if (response === 'Success') {
                toastr.success('Balance Sheet Updated!', 'Parameters Updated!');
            }
            else {
                toastr.error('Failed!', 'Please Try again or contact support!');
            }
        },
        'error': function (error) {
            console.log(error);
        }
    });

});


$('#ess_idea_todays_calculations').on('click', function () {
    let deal_id = $('#ess_idea_deal_id').val();
    $.ajax({
        url: '../risk/premium_analysis_get_latest_calculations',
        type: 'POST',
        data: {'deal_id': deal_id},
        success: function (response) {
            $('#premium_analysis_regression_breakdown_table tbody').empty();

            if (response === 'Failed') {
                // Show a sweet alert
            }
            else {
                // Process and Populate the Table...
                try {
                    let regression_results = $.parseJSON(response['regression_results']);
                    //let calculated_on = response['calculated_on'];
                    let multiples = Object.keys(regression_results);
                    for (var i = 0; i < multiples.length; i++) {
                        let multiple = multiples[i];
                        let id = '';
                        if (multiple === 'EV/EBITDA') {
                            id = 'ev_ebitda'
                        }
                        else if (multiple === 'P/E') {
                            id = 'p_e'
                        }
                        else if (multiple === 'EV/Sales') {
                            id = 'ev_sales'
                        }
                        else if (multiple === 'DVD Yield') {
                            id = 'dvd_yield'
                        }
                        else if (multiple === 'FCF Yield') {
                            id = 'fcf_yield'
                        }
                        // Append Multiple
                        let currernt_row = '<tr>';
                        let row_cell = currernt_row + '<td>' + multiple + '</td>';

                        let coefficients = regression_results[multiples[i]]['Coefficients'];
                        // Iterate throught coeffieicent and create a Table
                        let coefficients_table = '<table class=\"table table-striped\"><thead><tr><th>Peer/Intercept</th><th>Coefficients</th></tr></thead><tbody>';

                        for (var peer in coefficients) {
                            coefficients_table += '<tr><td>' + peer + '</td><td>' + parseFloat(coefficients[peer]).toFixed(4) +
                                '</td></tr>'
                        }
                        coefficients_table += '</table>';
                        // Create a Bootstrap Modal
                        get_regression_analysis_modal(id + '_coefficients', coefficients_table, 'Regression Coefficients');

                        row_cell += '<td>' + get_modal_launch_button('id', id + '_coefficients', 'View Coefficients') +
                            '</td>';

                        let peer_multiples_at_price_target_date = regression_results[multiples[i]]['Peers Multiples @ Price Target Date'];
                        // Iterate throught Peer Multiples at PT Date
                        let peer_multiples_at_pt_table = '<table class=\"table table-striped\"><thead><tr><th>Peer</th><th>Multiples</th></tr></thead><tbody>';

                        for (var peer in peer_multiples_at_price_target_date) {
                            peer_multiples_at_pt_table += '<tr><td>' + peer + '</td><td>' + parseFloat(peer_multiples_at_price_target_date[peer]).toFixed(2) +
                                '</td></tr>'
                        }
                        peer_multiples_at_pt_table += '</table>';

                        get_regression_analysis_modal(id + '_peer_multiples_at_pt', peer_multiples_at_pt_table, 'Peer Multiples at Price Target Date');

                        row_cell += '<td>' + get_modal_launch_button('id', id + '_peer_multiples_at_pt', 'Peers Multiple Drilldown') +
                            '</td>';

                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Implied Multiple @ Price Target Date']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bear Multiple @ Price Target Date']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha PT WIC Multiple @ Price Target Date']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bull Multiple @ Price Target Date']).toFixed(2) + '</td>';

                        // Repeat the Above for Now Section
                        let peer_multiples_at_now = regression_results[multiples[i]]['Peers Multiples @ Now'];
                        // Iterate throught Peer Multiples at PT Date
                        let peer_multiples_at_now_table = '<table class=\"table table-striped\"><thead><tr><th>Peer</th><th>Multiples</th></tr></thead><tbody>';

                        for (var peer in peer_multiples_at_now) {
                            peer_multiples_at_now_table += '<tr><td>' + peer + '</td><td>' + parseFloat(peer_multiples_at_now[peer]).toFixed(2) +
                                '</td></tr>'
                        }
                        peer_multiples_at_now_table += '</table>';

                        get_regression_analysis_modal(id + '_peer_multiples_at_now', peer_multiples_at_now_table, 'Peer Multiples (Now)');

                        row_cell += '<td>' + get_modal_launch_button('id', id + '_peer_multiples_at_now', 'Peers Multiple Drilldown') +
                            '</td>';

                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Implied Multiple @ Now']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bear Multiple @ Now']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha PT WIC Multiple @ Now']).toFixed(2) + '</td>';
                        row_cell += '<td class="text-info">' + parseFloat(regression_results[multiples[i]]['Alpha Bull Multiple @ Now']).toFixed(2) + '</td>';
                        row_cell += '</tr>';
                        $('#premium_analysis_regression_breakdown_table tbody').append(row_cell);

                    }
                    $('.premium-analysis-table').show();
                }
                catch (e) {
                    swal("Error!", "No latest adjustment info found. Please run Live Analysis", "error");
                    return;
                }


            }
        },
        error: function (err) {
            console.log(err);
            swal("Error!", err.toString(), "error");
        }
    })
});


/** Version Drop Down Change **/
$('#ess_idea_version_number_select').on('change', function () {
    let deal_id = $('#ess_idea_deal_id').val();
    let linkHref = '../risk/show_ess_idea?ess_idea_id=' + deal_id + '&version=' + $(this).val();
    window.location.href = linkHref;

});
$('#calculate_balance_sheet').on('click', function () {
    caclulateFinalBalanceSheet();
});


function caclulateFinalBalanceSheet() {
    $('#upside_final_balance_sheet_best_capex').val(decimal_places(eval($('#upside_balance_sheet_best_capex').val() + "+" + $('#upside_adjustment_balance_sheet_best_capex').val()), 1));
    $('#upside_final_balance_sheet_px').val(decimal_places(eval($('#upside_balance_sheet_px').val() + "+" + $('#upside_adjustment_balance_sheet_px').val()), 2));
    $('#upside_final_balance_sheet_best_eps').val(decimal_places(eval($('#upside_balance_sheet_best_eps').val() + "+" + $('#upside_adjustment_balance_sheet_best_eps').val()), 2));
    $('#upside_final_balance_sheet_best_net_income').val(decimal_places(eval($('#upside_balance_sheet_best_net_income').val() + "+" + $('#upside_adjustment_balance_sheet_best_net_income').val()), 1));
    $('#upside_final_balance_sheet_best_opp').val(decimal_places(eval($('#upside_balance_sheet_best_opp').val() + "+" + $('#upside_adjustment_balance_sheet_best_opp').val()), 1));
    $('#upside_final_balance_sheet_best_sales').val(decimal_places(eval($('#upside_balance_sheet_best_sales').val() + "+" + $('#upside_adjustment_balance_sheet_best_sales').val()), 1));
    $('#upside_final_balance_sheet_cur_ev_component').val(decimal_places(eval($('#upside_balance_sheet_cur_ev_component').val() + "+" + $('#upside_adjustment_balance_sheet_cur_ev_component').val()), 1));
    $('#upside_final_balance_sheet_best_ebitda').val(decimal_places(eval($('#upside_balance_sheet_best_ebitda').val() + "+" + $('#upside_adjustment_balance_sheet_best_ebitda').val()), 1));
    $('#upside_final_balance_sheet_eqy_sh_out').val(decimal_places(eval($('#upside_balance_sheet_eqy_sh_out').val() + "+" + $('#upside_adjustment_balance_sheet_eqy_sh_out').val()), 1));


    // Calculate Balance Sheet for WIC
    $('#wic_final_balance_sheet_best_capex').val(decimal_places(eval($('#wic_balance_sheet_best_capex').val() + "+" + $('#wic_adjustment_balance_sheet_best_capex').val()), 1));
    $('#wic_final_balance_sheet_px').val(decimal_places(eval($('#wic_balance_sheet_px').val() + "+" + $('#wic_adjustment_balance_sheet_px').val()), 2));
    $('#wic_final_balance_sheet_best_eps').val(decimal_places(eval($('#wic_balance_sheet_best_eps').val() + "+" + $('#wic_adjustment_balance_sheet_best_eps').val()), 2));
    $('#wic_final_balance_sheet_best_net_income').val(decimal_places(eval($('#wic_balance_sheet_best_net_income').val() + "+" + $('#wic_adjustment_balance_sheet_best_net_income').val()), 1));
    $('#wic_final_balance_sheet_best_opp').val(decimal_places(eval($('#wic_balance_sheet_best_opp').val() + "+" + $('#wic_adjustment_balance_sheet_best_opp').val()), 1));
    $('#wic_final_balance_sheet_best_sales').val(decimal_places(eval($('#wic_balance_sheet_best_sales').val() + "+" + $('#wic_adjustment_balance_sheet_best_sales').val()), 1));
    $('#wic_final_balance_sheet_cur_ev_component').val(decimal_places(eval($('#wic_balance_sheet_cur_ev_component').val() + "+" + $('#wic_adjustment_balance_sheet_cur_ev_component').val()), 1));
    $('#wic_final_balance_sheet_best_ebitda').val(decimal_places(eval($('#wic_balance_sheet_best_ebitda').val() + "+" + $('#wic_adjustment_balance_sheet_best_ebitda').val()), 1));
    $('#wic_final_balance_sheet_eqy_sh_out').val(decimal_places(eval($('#wic_balance_sheet_eqy_sh_out').val() + "+" + $('#wic_adjustment_balance_sheet_eqy_sh_out').val()), 1));


    // Calculate Balance Sheet for Downsides
    $('#downsides_final_balance_sheet_best_capex').val(decimal_places(eval($('#downsides_balance_sheet_best_capex').val() + "+" + $('#downsides_adjustment_balance_sheet_best_capex').val()), 1));
    $('#downsides_final_balance_sheet_px').val(decimal_places(eval($('#downsides_balance_sheet_px').val() + "+" + $('#downsides_adjustment_balance_sheet_px').val()), 2));
    $('#downsides_final_balance_sheet_best_eps').val(decimal_places(eval($('#downsides_balance_sheet_best_eps').val() + "+" + $('#downsides_adjustment_balance_sheet_best_eps').val()), 2));
    $('#downsides_final_balance_sheet_best_net_income').val(decimal_places(eval($('#downsides_balance_sheet_best_net_income').val() + "+" + $('#downsides_adjustment_balance_sheet_best_net_income').val()), 1));
    $('#downsides_final_balance_sheet_best_opp').val(decimal_places(eval($('#downsides_balance_sheet_best_opp').val() + "+" + $('#downsides_adjustment_balance_sheet_best_opp').val()), 1));
    $('#downsides_final_balance_sheet_best_sales').val(decimal_places(eval($('#downsides_balance_sheet_best_sales').val() + "+" + $('#downsides_adjustment_balance_sheet_best_sales').val()), 1));
    $('#downsides_final_balance_sheet_cur_ev_component').val(decimal_places(eval($('#downsides_balance_sheet_cur_ev_component').val() + "+" + $('#downsides_adjustment_balance_sheet_cur_ev_component').val()), 1));
    $('#downsides_final_balance_sheet_best_ebitda').val(decimal_places(eval($('#downsides_balance_sheet_best_ebitda').val() + "+" + $('#downsides_adjustment_balance_sheet_best_ebitda').val()), 1));
    $('#downsides_final_balance_sheet_eqy_sh_out').val(decimal_places(eval($('#downsides_balance_sheet_eqy_sh_out').val() + "+" + $('#downsides_adjustment_balance_sheet_eqy_sh_out').val()), 1));


}

function decimal_places(value, decimal) {
    return Number(value).toFixed(decimal);
}


/* Copy Function: To Copy Current Balance Sheet Adjustments to Price Target Date Adjustments */
$('#copy_from_upside_adjustments').on('click', function () {
    // Set Downsides and WIC from Upside Adjustments
    $('#wic_adjustment_balance_sheet_best_capex').val(decimal_places($('#upside_adjustment_balance_sheet_best_capex').val(), 1));
    $('#wic_adjustment_balance_sheet_px').val(decimal_places($('#upside_adjustment_balance_sheet_px').val(), 2));
    $('#wic_adjustment_balance_sheet_best_eps').val(decimal_places($('#upside_adjustment_balance_sheet_best_eps').val(), 2));
    $('#wic_adjustment_balance_sheet_best_net_income').val(decimal_places($('#upside_adjustment_balance_sheet_best_net_income').val(), 1));
    $('#wic_adjustment_balance_sheet_best_opp').val(decimal_places($('#upside_adjustment_balance_sheet_best_opp').val(), 1));
    $('#wic_adjustment_balance_sheet_best_sales').val(decimal_places($('#upside_adjustment_balance_sheet_best_sales').val(), 1));
    $('#wic_adjustment_balance_sheet_cur_ev_component').val(decimal_places($('#upside_adjustment_balance_sheet_cur_ev_component').val(), 1));
    $('#wic_adjustment_balance_sheet_best_ebitda').val(decimal_places($('#upside_adjustment_balance_sheet_best_ebitda').val(), 1));
    $('#wic_adjustment_balance_sheet_eqy_sh_out').val(decimal_places($('#upside_adjustment_balance_sheet_eqy_sh_out').val(), 1));


    $('#downsides_adjustment_balance_sheet_best_capex').val(decimal_places($('#upside_adjustment_balance_sheet_best_capex').val(), 1));
    $('#downsides_adjustment_balance_sheet_px').val(decimal_places($('#upside_adjustment_balance_sheet_px').val(), 2));
    $('#downsides_adjustment_balance_sheet_best_eps').val(decimal_places($('#upside_adjustment_balance_sheet_best_eps').val(), 2));
    $('#downsides_adjustment_balance_sheet_best_net_income').val(decimal_places($('#upside_adjustment_balance_sheet_best_net_income').val(), 1));
    $('#downsides_adjustment_balance_sheet_best_opp').val(decimal_places($('#upside_adjustment_balance_sheet_best_opp').val(), 1));
    $('#downsides_adjustment_balance_sheet_best_sales').val(decimal_places($('#upside_adjustment_balance_sheet_best_sales').val(), 1));
    $('#downsides_adjustment_balance_sheet_cur_ev_component').val(decimal_places($('#upside_adjustment_balance_sheet_cur_ev_component').val(), 1));
    $('#downsides_adjustment_balance_sheet_best_ebitda').val(decimal_places($('#upside_adjustment_balance_sheet_best_ebitda').val(), 1));
    $('#downsides_adjustment_balance_sheet_eqy_sh_out').val(decimal_places($('#upside_adjustment_balance_sheet_eqy_sh_out').val(), 1));

});

function get_regression_analysis_modal(id, content, modal_title) {
    let modal = "<div class=\"modal fade\" id=\"" + id + "\" tabindex=\"-1\" role=\"dialog\" aria-hidden=\"true\">" +
        "<div class=\"modal-dialog modal-dialog-centered\" role=\"document\">" +
        "<div class=\"modal-content\">" +
        "<div class=\"modal-header\">" +
        "<h5 class=\"modal-title\">" + modal_title + "</h5>" +
        "<button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"Close\">" +
        " <span aria-hidden=\"true\">&times;</span>" +
        "</button>" +
        "</div>" +
        "<div class=\"modal-body\">" +
        content +
        "</div>" +
        "<div class=\"modal-footer\">" +
        " <button type=\"button\" class=\"btn btn-secondary\" data-dismiss=\"modal\">Close</button>" +
        "</div>" +
        "</div>" +
        "</div>" +
        "</div>"

    $('body').append(modal);
}

function get_modal_launch_button(id, datatarget, label) {
    return "<button type=\"button\" class=\"btn btn-info\" data-toggle=\"modal\" data-target=\"#" + datatarget + "\">" +
        label +
        "</button>"
}


// Detatiled Calculations Event Listeners

$('#upside_calculations').on('click', function () {
    $('#step_by_step_content').empty();
    let upside_data = '';
    if (calculations_array_global.length > 0) {
        for (var i = 0; i < calculations_array_global[0].length; i++) {
            let current_multiple = Object.keys(calculations_array_global[0][i])[0];
            upside_data += '<h5><strong>' + current_multiple + '</strong></h5><br>';
            var current_keys = Object.keys(calculations_array_global[0][i][current_multiple]);
            for (var j = 0; j < current_keys.length; j++) {
                upside_data += '<p>' + calculations_array_global[0][i][current_multiple][j + 1] + '</p><br>'
            }
        }
    }
    $('#step_by_step_content').append(upside_data);
    $('#ess_idea_calculations_modal').modal('show');

});

$('#wic_calculations').on('click', function () {
    $('#step_by_step_content').empty();
    let wic_data = '';
    if (calculations_array_global.length > 0) {
        for (var i = 0; i < calculations_array_global[2].length; i++) {
            let current_multiple = Object.keys(calculations_array_global[2][i])[0];
            wic_data += '<h5><strong>' + current_multiple + '</strong></h5><br>';
            var current_keys = Object.keys(calculations_array_global[2][i][current_multiple]);
            for (var j = 0; j < current_keys.length; j++) {
                wic_data += '<p>' + calculations_array_global[2][i][current_multiple][j + 1] + '</p><br>'
            }
        }
    }
    $('#step_by_step_content').append(wic_data);
    $('#ess_idea_calculations_modal').modal('show');
});

$('#downside_calculations').on('click', function () {
    $('#step_by_step_content').empty();
    let downside_data = '';
    if (calculations_array_global.length > 0) {
        for (var i = 0; i < calculations_array_global[1].length; i++) {
            let current_multiple = Object.keys(calculations_array_global[1][i])[0];
            downside_data += '<h5><strong>' + current_multiple + '</strong></h5><br>';
            var current_keys = Object.keys(calculations_array_global[1][i][current_multiple]);
            for (var j = 0; j < current_keys.length; j++) {
                downside_data += '<p>' + calculations_array_global[1][i][current_multiple][j + 1] + '</p><br>'
            }
        }
    }
    $('#step_by_step_content').append(downside_data);
    $('#ess_idea_calculations_modal').modal('show');
});
