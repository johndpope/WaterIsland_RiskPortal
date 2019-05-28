$(document).ready(function () {
    let etf_performances = $.parseJSON($('#etf_performance').val());
    let etf_cum_pnl = $.parseJSON($('#etf_cum_pnl').val());
    let tradegroups_pnl = $.parseJSON($('#tradegroups_pnl').val());

    console.log(etf_cum_pnl);
    populateETFCharts(etf_cum_pnl, false, 'etf1_performance');
    populateEtfTradegroupsPnl(tradegroups_pnl);


    function populateEtfTradegroupsPnl(tradegroups_pnl) {
        let etf1_tg = JSON.parse(tradegroups_pnl['ETF1']);
        let etf2_tg = JSON.parse(tradegroups_pnl['ETF2']);
        let etf3_tg = JSON.parse(tradegroups_pnl['ETF3']);

        initializeDatatables(etf1_tg, '#etf_1_tg_perf');
        initializeDatatables(etf2_tg, '#etf_2_tg_perf');
        initializeDatatables(etf3_tg, '#etf_3_tg_perf');


    }

    function populateETFCharts(etf_cum_pnl, tradegroup_level=true, chart_div_id) {


        if(tradegroup_level === false){
            let etf1_data = JSON.parse(etf_cum_pnl['ETF1']);
            let etf2_data = JSON.parse(etf_cum_pnl['ETF2']);
            let etf3_data = JSON.parse(etf_cum_pnl['ETF3']);
            var chartData = [];

            for (var i = 0; i < etf1_data.length; i++) {
                let etf1_value = etf1_data[i]['cum_pnl'];
                let etf2_value = null;
                let etf3_value = null;

                if(etf2_data[i] === undefined){
                    etf2_value = null
                }
                else{
                    etf2_value = etf2_data[i]['cum_pnl']
                }
                if(etf3_data[i] === undefined){
                    etf3_value = null
                }
                else{
                    etf3_value = etf3_data[i]['cum_pnl']
                }

                chartData.push({
                    date: etf1_data[i]['DATE'],
                    etf1_cum_pnl: etf1_value,
                    etf2_cum_pnl: etf2_value,
                    etf3_cum_pnl: etf3_value,
                })
            }
            var graphs = [];
            graphs.push({
                "valueAxis": "v1",
                "lineColor": "green",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": 'ETF1',
                "valueField": "etf1_cum_pnl",
                "fillAlphas": 0.1
            });
            graphs.push({
                "valueAxis": "v1",
                "lineColor": "red",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": 'ETF2',
                "valueField": "etf2_cum_pnl",
                "fillAlphas": 0.1
            });

            graphs.push({
                "valueAxis": "v1",
                "lineColor": "blue",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": 'ETF3',
                "valueField": "etf3_cum_pnl",
                "fillAlphas": 0.1
            });


        }
        else{
            chartData = [];
            for (var i = 0; i < etf_cum_pnl.length; i++) {
                chartData.push({
                    date: etf_cum_pnl[i]['date'],
                    pnl: etf_cum_pnl[i]['pnl'],
                    cum_pnl: etf_cum_pnl[i]['cum_pnl'],
                })
            }
            var graphs = [];
            graphs.push({
                "valueAxis": "v1",
                "lineColor": "green",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": 'Cumulative P&L',
                "valueField": "cum_pnl",
                "fillAlphas": 0.1
            });
            graphs.push({
                "valueAxis": "v1",
                "lineColor": "black",
                "bullet": "round",
                "bulletBorderThickness": 1,
                "hideBulletsCount": 30,
                "title": 'Daily P&L',
                "valueField": "pnl",
                "fillAlphas": 0.1
            });



        }

        AmCharts.makeChart(chart_div_id, {
            "type": "serial",
            "legend": {
                "useGraphSettings": true
            },

            "hideCredits": true,
            "dataDateFormat": "YYYY-MM-DD",
            "dataProvider": chartData,
            "synchronizeGrid": true,
            "valueAxes": [{
                "id": "v1",
                "axisColor": "#FF6600",
                "axisThickness": 2,
                "axisAlpha": 1,
                "position": "left",

            }],
            "graphs": graphs,
            "chartScrollbar": {},
            "chartCursor": {
                "cursorPosition": "mouse"
            },
            "categoryField": "date",
            "categoryAxis": {
                "parseDates": true,
                "minPeriod": "dd",
                "equalSpacing": true,
                "axisColor": "#DADADA",
                "minorGridEnabled": true

            },
            "export": {
                "enabled": true,
                "position": "bottom-right"
            }
        });
    }


    function initializeDatatables(data, table_id) {
        return $(table_id).DataTable({
            "data": data,
            "columns": [
                {"data": "Date"},
                {"data": "Fund"},
                {"data": "TradeGroup"},
                {"data": "pct_of_assets"},
                {"data": "pnl"},
                {"data": "cum_pnl"},
                {"data": "pnl_chart_url"},

            ],
        })
    }


    $('.table').on('click', 'button', function() {
        let url = $(this).data('url');
        $.ajax({
            url: url,
            type: 'GET',
            success: function(response){
                let data = $.parseJSON(response);
                //$('.loader-wrapper').remove();

                console.log(data);
                // Populate the Charts..
                populateETFCharts(data, true, 'etf_tradegroup_performance');

            },
            error: function (err) {
                console.log(err)
            }
        })
    })


    $('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
        });

});