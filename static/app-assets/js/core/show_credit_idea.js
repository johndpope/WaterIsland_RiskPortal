$(document).ready(function(){
   $.ajax({
        'type': 'GET',
        'url': '../position_stats/get_tradegroup_story?TradeGroup=' + $('#tradegroup_name').val() + '&Fund='+$('#fund_name').val(),
        success: function (response) {
            let exposures_and_pnl = JSON.parse(response['exposures_and_pnl_df']);
            if (exposures_and_pnl.length > 0) {
                let fund_name = $('#fund_name').val();
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
                let tradegroup_story_chart = AmCharts.makeChart("credit_idea_tradegroup_story", createLineChartConfigs(exposures_and_pnl, datasets, graphs, title, '$$', 'light'));
            }
            else {
                AmCharts.makeChart("credit_idea_tradegroup_story", createLineChartConfigs(exposures_and_pnl, [], [], 'The chart contains no data', '', 'light', 0, '50%'));
            }
        },
        error: function (err) {
            console.log(err);
        }
    });


});