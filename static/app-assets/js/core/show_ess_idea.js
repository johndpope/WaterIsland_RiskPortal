$(document).ready(function () {

    $('#ess_idea_company_overview').summernote({'height':'250px'});
    $('#ess_idea_situation_overview').summernote({'height':'250px'});
    /***********************************************************
     *               New User - Page Visist Stats               *
     ***********************************************************/
    $('.premium-analysis').hide();
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
    try{
        downside_changes = $.parseJSON(downside_changes);
        console.log(downside_changes);
        for(var i=0;i<downside_changes.length;i++){
            stockEvents.push({
                "date":new Date(2018,05,05),
                "type":"text",
                "backgroundColor": "#85CDE6",
                "graph":"g1",
                "text":"Deal Revision Point",
                "description":"Upside Revised to:"+downside_changes[i]['pt_up']+" & Downside Revised to:"+downside_changes[i]['pt_down']
            })
        }
    }catch(err){
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
                    obj[peer_tickers[counter] + "_ev_ebitda"] = all_ebitda_json_parsed[counter][i][field_name];
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
        // "hideCredits":true,
        "dataProvider": ev_ebitda_chart_data_ltm[0],
        "dataDateFormat": "YYYY-MM-DD",
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left",

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
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
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
                "dataDateFormat": "YYYY-MM-DD",
                "categoryField": "date",
                "parseDates": true,
                // EVENTS
                "stockEvents": stockEvents,
                "fillAlpha":0.3
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
                }
        })
    ;

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
                    px_last: alpha_chart_data[i].px_last,
                })
            }
            return chartData;
        }


        for (let i = 0; i < hedge_chart_data.length; i++) {
            chartData.push({
                date: alpha_chart_data[i]['date'],
                px_last: alpha_chart_data[i]['px_last'],
                hedges: hedge_chart_data[i]['vol'],
                market_neutral_val: market_neutral_chart_data[i]['market_netural_value']
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
        // "hideCredits":true,
        "dataDateFormat": "YYYY-MM-DD",
        "dataProvider": implied_probability_chart_data,
        "synchronizeGrid": true,
        "valueAxes": [{
            "id": "v1",
            "axisColor": "#FF6600",
            "axisThickness": 2,
            "axisAlpha": 1,
            "position": "left"
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
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
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
                implied_probability: implied_chart_data[i].implied_probability*100,
            })
        }
        return chartData;
    }

    let upside_downside_records_data = generateUpsideDownsideTrackRecordData();

    function generateUpsideDownsideTrackRecordData(){
        let upside_downside_records = JSON.parse($('#upside_downside_records_df').val());
        let chartData = [];
        for (let i = 0; i < upside_downside_records.length; i++) {
            chartData.push({
                date: upside_downside_records[i].date_updated,
                pt_up: upside_downside_records[i].pt_up,
                pt_down: upside_downside_records[i].pt_down,
                pt_wic: upside_downside_records[i].pt_wic,
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
            "position": "left"
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
        "legend": {
            "useGraphSettings": true,
            "valueText": ""
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
        "legend": {
            "useGraphSettings": true
        },
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
                event_premium: event_premium_chart_data[i].event_premium*100,
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
            let dynamic_upside_downside = $.parseJSON(response);
            $('#show_premium_analysis').prop('disabled', false);
            //Show the table
            $('.premium-analysis').show();
            $('.cix_down_price').html(dynamic_upside_downside['cix_down_price']);
            $('.cix_up_price').html(dynamic_upside_downside['cix_up_price']);
            $('.regression_down_price').html(dynamic_upside_downside['regression_down_price']);
            $('.regression_up_price').html(dynamic_upside_downside['regression_up_price']);


        },
        'error': function (error) {
            console.log(error);
        }
    });

});


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
            let balance_sheet_adjustments = $.parseJSON(response['balance_sheet_adjustments']);

            $('#balance_sheet_date').val(balance_sheet_bloomberg[0]['Date']);
            $('#balance_sheet_px').val(balance_sheet_bloomberg[0]['PX']);
            $('#balance_sheet_best_eps').val(balance_sheet_bloomberg[0]['BEST_EPS']);
            $('#balance_sheet_best_net_income').val(balance_sheet_bloomberg[0]['BEST_NET_INCOME']);
            $('#balance_sheet_best_opp').val(balance_sheet_bloomberg[0]['BEST_OPP']);
            $('#balance_sheet_best_sales').val(balance_sheet_bloomberg[0]['BEST_SALES']);
            $('#balance_sheet_cur_ev_component').val(balance_sheet_bloomberg[0]['CUR_EV_COMPONENT']);
            $('#balance_sheet_cur_mkt_cap').val(balance_sheet_bloomberg[0]['CUR_MKT_CAP']);
            $('#balance_sheet_dvd_indicated_yield').val(balance_sheet_bloomberg[0]['DIVIDEND_INDICATED_YIELD']);
            $('#balance_sheet_best_capex').val(balance_sheet_bloomberg[0]['BEST_CAPEX']);
            $('#balance_sheet_best_ebitda').val(balance_sheet_bloomberg[0]['BEST_EBITDA']);
            $('#balance_sheet_eqy_sh_out').val(balance_sheet_bloomberg[0]['EQY_SH_OUT']);


            // Populate the Adjustments balance Sheet
            if(balance_sheet_adjustments.length >0 ){
                $('#adjustment_balance_sheet_date').val(balance_sheet_adjustments[0]['Date']);
                $('#adjustment_balance_sheet_px').val(balance_sheet_adjustments[0]['PX']);
                $('#adjustment_balance_sheet_best_eps').val(balance_sheet_adjustments[0]['BEST_EPS']);
                $('#adjustment_balance_sheet_best_net_income').val(balance_sheet_adjustments[0]['BEST_NET_INCOME']);
                $('#adjustment_balance_sheet_best_opp').val(balance_sheet_adjustments[0]['BEST_OPP']);
                $('#adjustment_balance_sheet_best_sales').val(balance_sheet_adjustments[0]['BEST_SALES']);
                $('#adjustment_balance_sheet_cur_ev_component').val(balance_sheet_adjustments[0]['CUR_EV_COMPONENT']);
                $('#adjustment_balance_sheet_cur_mkt_cap').val(balance_sheet_adjustments[0]['CUR_MKT_CAP']);
                $('#adjustment_balance_sheet_dvd_indicated_yield').val(balance_sheet_adjustments[0]['DIVIDEND_INDICATED_YIELD']);
                $('#adjustment_balance_sheet_best_capex').val(balance_sheet_adjustments[0]['BEST_CAPEX']);
                $('#adjustment_balance_sheet_best_ebitda').val(balance_sheet_adjustments[0]['BEST_EBITDA']);
                $('#adjustment_balance_sheet_eqy_sh_out').val(balance_sheet_adjustments[0]['EQY_SH_OUT']);

            }
            else{
                $('#adjustment_balance_sheet_date').val(balance_sheet_bloomberg[0]['Date']);
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
    var balance_sheet = {
        'Date': $('#adjustment_balance_sheet_date').val(),
        'PX': $('#adjustment_balance_sheet_px').val(),
        'BEST_EPS': $('#adjustment_balance_sheet_best_eps').val(),
        'BEST_NET_INCOME': $('#adjustment_balance_sheet_best_net_income').val(),
        'BEST_OPP': $('#adjustment_balance_sheet_best_opp').val(),
        'BEST_SALES': $('#adjustment_balance_sheet_best_sales').val(),
        'CUR_EV_COMPONENT': $('#adjustment_balance_sheet_cur_ev_component').val(),
        'CUR_MKT_CAP': $('#adjustment_balance_sheet_cur_mkt_cap').val(),
        'DIVIDEND_INDICATED_YIELD': $('#adjustment_balance_sheet_dvd_indicated_yield').val(),
        'BEST_CAPEX': $('#adjustment_balance_sheet_best_capex').val(),
        'BEST_EBITDA': $('#adjustment_balance_sheet_best_ebitda').val(),
        'EQY_SH_OUT': $('#adjustment_balance_sheet_eqy_sh_out').val()
    };

    $.ajax({
        'url': '../risk/ess_idea_save_balance_sheet',
        'type': 'POST',
        'data': {'deal_id': deal_id, 'balance_sheet': JSON.stringify(balance_sheet)},
        'success': function (response) {
            if (response == 'Success') {
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

/** Version Drop Down Change **/
$('#ess_idea_version_number_select').on('change', function () {
    let deal_id = $('#ess_idea_deal_id').val();


    let linkHref = '../risk/show_ess_idea?ess_idea_id='+deal_id+'&version='+$(this).val();
    window.location.href = linkHref;

});
$('#calculate_balance_sheet').on('click', function () {
    caclulateFinalBalanceSheet();
});


function caclulateFinalBalanceSheet(){
   $('#final_balance_sheet_best_capex').val(eval($('#balance_sheet_best_capex').val()+"+"+$('#adjustment_balance_sheet_best_capex').val()));
   $('#final_balance_sheet_px').val(eval($('#balance_sheet_px').val()+"+"+$('#adjustment_balance_sheet_px').val()));
   $('#final_balance_sheet_best_eps').val(eval($('#balance_sheet_best_eps').val()+"+"+$('#adjustment_balance_sheet_best_eps').val()));
   $('#final_balance_sheet_best_net_income').val(eval($('#balance_sheet_best_net_income').val()+"+"+$('#adjustment_balance_sheet_best_net_income').val()));
   $('#final_balance_sheet_best_opp').val(eval($('#balance_sheet_best_opp').val()+"+"+$('#adjustment_balance_sheet_best_opp').val()));
   $('#final_balance_sheet_best_sales').val(eval($('#balance_sheet_best_sales').val()+"+"+$('#adjustment_balance_sheet_best_sales').val()));
   $('#final_balance_sheet_cur_ev_component').val(eval($('#balance_sheet_cur_ev_component').val()+"+"+$('#adjustment_balance_sheet_cur_ev_component').val()));
   $('#final_balance_sheet_cur_mkt_cap').val(eval($('#balance_sheet_cur_mkt_cap').val()+"+"+$('#adjustment_balance_sheet_cur_mkt_cap').val()));
   $('#final_balance_sheet_dvd_indicated_yield').val(eval($('#balance_sheet_dvd_indicated_yield').val()+"+"+$('#adjustment_balance_sheet_dvd_indicated_yield').val()));
   $('#final_balance_sheet_best_ebitda').val(eval($('#balance_sheet_best_ebitda').val()+"+"+$('#adjustment_balance_sheet_best_ebitda').val()));
   $('#final_balance_sheet_eqy_sh_out').val(eval($('#balance_sheet_eqy_sh_out').val()+"+"+$('#adjustment_balance_sheet_eqy_sh_out').val()));
   $('#final_balance_sheet_date').val($('#balance_sheet_date').val());
}





