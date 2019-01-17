$(document).ready(function () {

    function generateTargetPriceChart(target_ticker_prices, target_ticker_dates, div_id, instrument_type){
        var chartData = []
        for(var i=0;i<target_ticker_prices.length;i++){
            chartData.push({
                date:target_ticker_dates[i],
                px_last:target_ticker_prices[i],
            })
        }

     AmCharts.makeChart(div_id, {
    "type": "serial",
    "legend": {
        "useGraphSettings": true
    },

     "hideCredits":true,
    "dataDateFormat":"YYYY-MM-DD",
    "dataProvider": chartData,
    "synchronizeGrid":true,
    "valueAxes": [{
        "id":"v1",
        "axisColor": "#FF6600",
        "axisThickness": 2,
        "axisAlpha": 1,
        "position": "left",

    }],
    "graphs": [{
        "valueAxis": "v1",
        "lineColor": "#FF6600",
        "bullet": "round",
        "bulletBorderThickness": 1,
        "hideBulletsCount": 30,
        "title": instrument_type,
        "valueField": "px_last",
		"fillAlphas": 0.1
    }],
    "chartScrollbar": {},
    "chartCursor": {
        "cursorPosition": "mouse"
    },
    "categoryField": "date",
    "categoryAxis": {
        "parseDates": true,
        "minPeriod": "dd",
        "equalSpacing":true,
        "axisColor": "#DADADA",
        "minorGridEnabled": true

    },
    "legend":{
      "useGraphSettings":true,
      "valueText":""
    },
    "export": {
    	"enabled": true,
        "position": "bottom-right"
     }
});
    }

    $('#get_comparison_form').on('submit', function (e) {
        //Get target and Acquirer Tickers
        e.preventDefault();
        $('.loader-inner').loaders();
        var target_ticker = $('#target_ticker').val();
        var bond_ticker = $('#bond_ticker').val();
        var proposed_date = $('#bond_equity_compare_proposed_date').val();
        var csrf_token = $('#bond_equity_compare_csrf_token').val();
        //Create an ajax request and submit the form

        $.ajax({
            url: "compare_equity_bond",
            method: "POST",
            data: {
                'target_ticker': target_ticker,
                'bond_ticker':bond_ticker,
                'proposed_date':proposed_date,
                'csrfmiddlewaretoken': csrf_token
            },
            success: function (response) {
                //Create the Amcharts
                $('.loader-inner').empty();
                generateTargetPriceChart(response['target_ticker_prices'], response['target_ticker_dates'],target_price_chart, 'Equity');
                generateTargetPriceChart(response['bond_prices'], response['bond_dates'], bond_price_chart, 'Bond');
            },
            error: function () {
                    alert('Some error occured!');
      }
        });
    });

});