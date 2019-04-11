$(document).ready(function () {
    $('#security_pnl_breakdown').DataTable({
        scrollY: "250px",
        scrollX: true,
        scrollCollapse: true,
        ordering:false,
        "lengthChange": false,
        "columnDefs": [{
            "targets": [1, 2],
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out
                if (cellData < 0) {
                    $(td).css('color', 'red')
                }
                else {
                    $(td).css('color', 'green')
                }
            },
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }],
        "footerCallback": function (row, data, start, end, display) {

            var api = this.api();
            nb_cols = api.columns().nodes().length;
            var j = 1;
            while (j < nb_cols) {
                var pageTotal = api
                    .column(j, {page: 'current'})
                    .data()
                    .reduce(function (a, b) {
                        return parseFloat(Number(a) + Number(b)).toFixed(2);
                    }, 0);
                // Update footer
                if (pageTotal < 0) {
                    $(api.column(j).footer()).html('<span class="red">' + pageTotal + '</span>');
                }
                else {
                    $(api.column(j).footer()).html('<span class="green">' + pageTotal + '</span>');
                }

                j++;
            }
        }

    });

    $('#position_summary').DataTable({
        ordering:false,
        "lengthChange": false,
        "columnDefs": [{
            "targets": [10, 11, 12, 13],
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out
                if (cellData < 0) {
                    $(td).css('color', 'red')
                }
                else {
                    $(td).css('color', 'green')
                }
            },
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }],
    });

    let unique_tickers = $('#unique_tickers').val();
    let fund_name = $('#fund_code').val();
    let exposures_and_pnl = JSON.parse($('#exposures_and_pnl').val());
    let tradegroup_name = $('#tradegroup_name').val();

    let fieldMappingsArray = [];
    fieldMappingsArray = ["Cumulative_pnl_dollar", "Daily_PnL_Dollar", "Cumulative_options_pnl_dollar"];
    let tradegroup_level_dictionary = {};
    tradegroup_level_dictionary["Cumulative_pnl_dollar"] = 'Contribution in ($)';
    tradegroup_level_dictionary["Daily_PnL_Dollar"] = "Daily P&L ($)";
    tradegroup_level_dictionary["Cumulative_options_pnl_dollar"] = "Options P&L ($)";
    let tickerFieldMappings = 'Ticker_PnL_Dollar_';
    let datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, true, tickerFieldMappings);
    let graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, true, tickerFieldMappings, false);
    let title = tradegroup_name + " in " + fund_name;
    // 1st Chart
    let tradegroup_story_chart = AmCharts.makeChart("pnl_dollar_performance", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '$$', 'black'));

    // Main TradeGroup Story
    fieldMappingsArray = [];
    fieldMappingsArray = ["AlphaHedge_Exposure", "Alpha_Exposure", "Capital_Percent_of_NAV", "GrossExp_Percent_of_NAV",
        "Hedge_Exposure", "NetExp_Percent_of_NAV", "Spread_as_Percent", "Cumulative_pnl_bps",
        "Cumulative_options_pnl_bps"];

    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary["Cumulative_pnl_bps"] = 'Contribution in bps';
    tradegroup_level_dictionary["Spread_as_Percent"] = "Spread (%)";
    tradegroup_level_dictionary["Cumulative_options_pnl_bps"] = "Options";
    tradegroup_level_dictionary["AlphaHedge_Exposure"] = "AlphaHedge Exposure";
    tradegroup_level_dictionary["Alpha_Exposure"] = "Alpha Exposure";
    tradegroup_level_dictionary["Capital_Percent_of_NAV"] = "Capital as (%) of NAV";
    tradegroup_level_dictionary["GrossExp_Percent_of_NAV"] = "Gross Exp (%) of NAV";
    tradegroup_level_dictionary["Hedge_Exposure"] = "Hedge Exp";
    tradegroup_level_dictionary["NetExp_Percent_of_NAV"] = "Net Exp (%) of NAV";

    tickerFieldMappings = 'Ticker_PnL_bps_';
    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, true, tickerFieldMappings);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, true, tickerFieldMappings, true);
    title = "TIMELINE OF "+tradegroup_name + " in " + fund_name + "\n" + "P&L CONTRIBUTION, SPREAD (LEFT) v/s EXPOSURES(RIGHT)";
    tradegroup_story_chart = AmCharts.makeChart("tradegroup_story_main", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '$$', 'light'));

    // Return on Capital Charts..
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary['Pnl_over_cap_percent'] = 'Cumulative P&L (%)';
    title = tradegroup_name + " RETURN ON CAPITAL IN " + fund_name;
    fieldMappingsArray = ['Pnl_over_cap_percent'];
    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, false, []);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, false, '', false);
    let tradegroup_roc_chart = AmCharts.makeChart("pnl_performance_over_capital", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '%', 'black'));

    // Rolling 30D Vol Chart
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary['Rolling_30D_PnL_Vol'] = 'Rolling 30D P&L Annualized Vol (%)';
    title = "VOLATILITY OF " + tradegroup_name + " RETURN ON CAPITAL IN " + fund_name;
    fieldMappingsArray = ['Rolling_30D_PnL_Vol'];

    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, false, []);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, false, '', false);

    let tradegroup_vol_chart = AmCharts.makeChart("volatility_of_roc", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '%', 'black'));

    // P&L Breakdown in BPS

    fieldMappingsArray = ["Cumulative_pnl_bps", "Daily_PnL_bps", "Cumulative_options_pnl_bps"];
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary["Cumulative_pnl_bps"] = 'Contribution in bps';
    tradegroup_level_dictionary["Daily_PnL_bps"] = "Daily P&L (bps)";
    tradegroup_level_dictionary["Cumulative_options_pnl_bps"] = "Options P&L (bps)";
    tickerFieldMappings = 'Ticker_PnL_bps_';
    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, true, tickerFieldMappings);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, true, tickerFieldMappings, false);
    title = "P&L (bps) breakdown \n" + tradegroup_name + " contribution to NAV in " + fund_name;
    let pnl_bps_breakdown = AmCharts.makeChart("pnl_bps_performance", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, 'bps', 'black'));

    // Historical Spread Chart
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary['Spread_as_Percent'] = 'Historical Spread   (%)';
    title = "SPREAD HISTORY " + tradegroup_name + " (%)";
    fieldMappingsArray = ['Spread_as_Percent'];

    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, false, []);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, false, '', false);

    let historical_spread = AmCharts.makeChart("spread_history", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '%', 'black'));

    // Exposure in % of NAV Breakdown Charts
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary['Capital_Percent_of_NAV'] = 'Capital % of NAV';
    tradegroup_level_dictionary['GrossExp_Percent_of_NAV'] = 'Gross Exposure % of NAV';
    tradegroup_level_dictionary['NetExp_Percent_of_NAV'] = 'Net Exposure % of NAV';
    title = "EXPOSURES\n " + tradegroup_name + " in " + fund_name;
    fieldMappingsArray = ['Capital_Percent_of_NAV', 'GrossExp_Percent_of_NAV', 'NetExp_Percent_of_NAV'];

    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, false, []);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, false, '', false);

    let exposures = AmCharts.makeChart("exposure", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '%', 'black'));

    // Exposures Breakdown
    tradegroup_level_dictionary = {};
    tradegroup_level_dictionary['Alpha_Exposure'] = 'Alpha Exposure';
    tradegroup_level_dictionary['Hedge_Exposure'] = 'Hedge Exposure';
    tradegroup_level_dictionary['AlphaHedge_Exposure'] = 'Alpha Hedge Exposure';
    title = "EXPOSURES\n " + tradegroup_name + " in " + fund_name;
    fieldMappingsArray = ['Alpha_Exposure', 'Hedge_Exposure', 'AlphaHedge_Exposure'];

    datasets = createDataSets(exposures_and_pnl, unique_tickers, fieldMappingsArray, false, []);
    graphs = createPnlGraphs(exposures_and_pnl, unique_tickers, tradegroup_name, tradegroup_level_dictionary, false, '', false);

    let exposures_breakdown = AmCharts.makeChart("exposure_breakdown_in_nav", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '%', 'black'));

});

// Below Function to adjust columns for dynamically created Tabs
$('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
});