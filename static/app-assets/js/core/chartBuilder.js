function createDataSets(tradegroupOverallDP, unique_tickers, fieldMappingsArray, processTickers, tickerFieldMappings) {
    let datasets = [];
    // First Push TradeGroup Overall Dataset
    let fieldMappings = [];

    $.each(fieldMappingsArray, function (index, val) {
        fieldMappings.push({
            "fromField": val,
            "toField": val
        })
    });

    if (processTickers) {
        $.each(JSON.parse(unique_tickers), function (index, value) {
            fieldMappings.push({
                "fromField": tickerFieldMappings + value.replace(' ', '_'),
                "toField": tickerFieldMappings + value.replace(' ', '_')
            });
        });
    }
    
    datasets.push({
            "title": "GG - NEM",
            "fieldMappings": fieldMappings,
            "dataProvider": tradegroupOverallDP,
            "categoryField": "Date",
            "fillAlpha": 0.3
        }
    );


    return datasets;
}

function createPnlGraphs(tradegroup_story, unique_tickers, tradegroup_name, tradegroup_mneumonics_dictionary, process_tickers, tickerFiledMappings, is_main_chart) {
    // First fill the story
    let graphs = [];
    let axis = 'a1';
    let counter = 1;
    let is_hidden = false;
    let fillAlphas = 0;
    $.each(tradegroup_mneumonics_dictionary, function (index, value) {
        if (is_main_chart === true) {
            is_hidden = true;
        }
        if (value.toString().indexOf("Exposure") >= 0) {
            axis = 'a2';
        }
        if (is_main_chart === true && (index.toString().indexOf('Cumulative_pnl_bps') >= 0 || index.toString().indexOf('Alpha_Exposure') >= 0)) {
            is_hidden = false;
        }

        if (is_main_chart === false && index.toString().indexOf('Spread_as_Percent') >= 0) {
            fillAlphas = "0.3";
        }
        else {
            fillAlphas = "0"
        }


        graphs.push({
            "useDataSetColors": false,
            "id": "g" + counter++,
            "hidden": is_hidden,
            "valueField": index.toString(),
            "valueAxis": axis,
            "title": value.toString(),
            "fillAlphas": fillAlphas,
            "lineThickness": 1.5,
            "lineColor": randomColor({
                luminosity: 'bright',
                hue: 'random',
            }),


        });

    });
    if (process_tickers) {
        $.each(JSON.parse(unique_tickers), function (index, value) {
            graphs.push({
                "useDataSetColors": false,
                "id": "g" + counter++,
                "valueField": tickerFiledMappings + value.replace(' ', '_'),
                "valueAxis": 'a1',
                "title": value,
                "hidden": true,
                "fillAlphas": fillAlphas,
                "lineThickness": 1.5,
                "lineColor": randomColor({
                    luminosity: 'bright',
                    hue: 'random'
                }),

            });
        });
    }

    return graphs
}


function createLineChartConfigs(tradegroupOverallDP, datasets, graphs, title, y_title, theme) {
    return {
        "type": "stock",
        "theme": theme,
        "legend": {
            "useGraphSettings": true
        },
        "dataDateFormat": "YYYY-MM-DD",
        "dataSets": datasets,
        "hideCredits": true,

        "panels": [{
            "title": y_title,
            "allLabels": [{
                "x": 0,
                "y": 0,
                "text": title,
                "align": "center",
                "size": 12
            }],
            "stockGraphs": graphs,
            "valueAxes": [{
                "id": "a1",
                "axisColor": "#FF6600",
                "position": "left",
                "offset": 0,
                "title": 'Spread Info'
            }, {
                "id": "a2",
                "axisColor": "#FFF",
                "position": "right",
                "offset": 0,
                "title": 'Exposures'
            }],
            "stockLegend": {
                useGraphSettings: true
            },
        }],


        "categoryAxesSettings": {
            "minPeriod": "DD",
            "maxSeries": 0,

        }, rangeSelector: {
            inputEnabled: false
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
            },

        "export":
            {
                "enabled":
                    true
            },

    }

}
