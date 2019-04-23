var charts = {};
var funds_data = {};
var current_fund;
$(document).ready(function () {
    let tradegroup_performance = $.parseJSON($('#performance_over_own_capital').val());
    // VOl Distribution Charts
    let vol_distribution_charts = $.parseJSON($('#vol_distribution_charts').val());

    Object.keys(tradegroup_performance).forEach(function (fund) {
        addFundMainTab(fund, 'fundtabs', 'fund-tab-content', 'Across', tradegroup_performance, vol_distribution_charts);

    });

    $(".loader-wrapper").remove();
});


function addFundMainTab(name, addToTab, addToContent, sleeve, tradegroup_performance, vol_distribution_charts) {
    // create the tab
    // Tab content should actually be another Tab and Tab content, this time with Funds Sleeves

    // create the tab content
    if (name === 'ARB') {
        $('<li class="nav-item"><a class="nav-link active" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
        $('<div class="tab-pane active" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
    }
    else {
        $('<li class="nav-item"><a class="nav-link" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
        $('<div class="tab-pane" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
    }


    $('<div class="tab-content" id="performance_over_own_capital' + name + '"></div>').appendTo('#tab' + name);

    let tradegroup_performances = JSON.parse(tradegroup_performance[name]);

    // Do this Iteratively for each fund
    // Crete Active Tab for ARB
    let data = tradegroup_performances;
    $('<div class="tab-pane active" id="tabTable' + name + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + '">' +
        '<tfoot><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>' +
        '</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table><br><br><br>' +
        '<div style="background-color: #30303d; color: #fff; width:100%;height:500px" id="ColumnChart' + name + '"></div></div>' +
        '').appendTo('#performance_over_own_capital' + name);
    initializeDatatableSummary(data, 'table' + name);


    // Create the Vol Distribution Chart and Append to Current Pane
    let fund_vol_distribution_chart = vol_distribution_charts[name];

    createVolCharts(fund_vol_distribution_chart, 'ColumnChart' + name, name);


}


function createVolCharts(fund_data, chart_id, fund) {

    var chart = AmCharts.makeChart(chart_id, {
        "theme": "dark",
        "type": "serial",
        "dataProvider": fund_data,
        "hideCredits": true,
        "titles": [
            {
                "text": "VOL DISTRIBUTION\n" + fund,
                "size": 15
            }
        ],
        "valueAxes": [{
            "position": "left",
            "title": "% of Tradegroups in Vol cohort",
        }],
        "depth3D": 20,
        "angle": 30,
        "startDuration": 0.5,
        "graphs": [{
            "fillAlphas": 0.9,
            "lineAlpha": 0.2,
            "title": "Vol",
            "type": "column",
            "valueField": "value"
        }],
        "plotAreaFillAlphas": 0.1,

        "categoryField": "bucket",
        "categoryAxis": {
            "gridPosition": "start",
            "labelRotation": 60
        },
        "export": {
            "enabled": true
        }
    });
    charts[fund] = chart;
    funds_data[fund] = fund_data;

    // var chart;
    // var chartData = fund_data;
    // AmCharts.ready(function() {
    // // SERIAL CHART
    //     AmCharts.theme = 'dark';
    // chart = new AmCharts.AmSerialChart();
    // chart.dataProvider = chartData;
    // chart.categoryField = "bucket";
    // chart.startDuration = 1;
    // chart.depth3D = 10;
    // chart.angle = 3;
    // chart.theme = "dark";
    // // AXES
    // // category
    // var categoryAxis = chart.categoryAxis;
    // categoryAxis.labelRotation = 90;
    // categoryAxis.gridPosition = "start";
    //
    // // value
    // // in case you don't want to change default settings of value axis,
    // // you don't need to create it, as one value axis is created automatically.
    // // GRAPH
    // var graph = new AmCharts.AmGraph();
    // graph.valueField = "value";
    // graph.balloonText = "[[category]]: [[value]]";
    // graph.type = "column";
    // graph.lineAlpha = 0;
    // graph.fillAlphas = 0.8;
    // chart.addGraph(graph);
//

    chart.addListener("clickGraphItem", function (event) {
        // let's look if the clicked graph item had any subdata to drill-down into
        if (event.item.dataContext.subdata != undefined) {
            // wow it has!
            // let's set that as chart's dataProvider
            event.chart.dataProvider = event.item.dataContext.subdata;
            event.chart.addLabel(
                25, 25,
                "Back",
                "left",
                undefined,
                undefined,
                undefined,
                undefined,
                true,
                'javascript:resetChart();');


            // validate the new data and make the chart animate again
            event.chart.validateData();
            event.chart.animateAgain();

        }
    });

    //chart.write(chart_id);
//});
}

// function which resets the chart back to yearly data

function resetChart() {

    $.each(charts, function (key, value) {
        //key - ARB value- chart
        value.dataProvider = funds_data[key];
        // remove the "Go back" label
        value.allLabels = [];
        value.validateData();
        value.animateAgain();
    });

}

function initializeDatatableSummary(data, table_id) {
    $('#' + table_id).DataTable({
        scrollY: "680px",
        scrollX: true,
        scrollCollapse: true,
        data: data,
        lengthChange: false,
        paginate: false,
        responsive: true,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',

        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: 'TradeGroup Perf. Over Own Capital',
                customize: function (win) {
                    $(win.document.body)
                        .css('font-size', '10pt')
                        .prepend(
                            '<p> Water Island Capital, Risk Portal</p>'
                        );

                    $(win.document.body).find('table')
                        .addClass('compact')
                        .css('font-size', 'inherit');
                },
                autoPrint: true,
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',

            }, {
                extend: 'csv',
                text: '<i class="fa fa-book"></i> CSV',

            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        },
        "order": [[1, "asc"]],
        columns: [
            {title: 'Sleeve', data: 'Sleeve'},
            {title: 'TradeGroup', data: 'TradeGroup'},
            {title: 'LongShort', data: 'LongShort'},
            {title: 'InceptionDate', data: 'InceptionDate'},
            {title: 'EndDate', data: 'EndDate'},
            {title: 'Status', data: 'Status'},
            {title: 'ITD (bps)', data: 'ITD_bps'},
            {title: 'YTD (bps)', data: 'YTD_bps'},
            {title: 'ROMC YTD (bps)', data: 'ROMC_YTD_bps'},
            {title: 'MTD (bps)', data: 'MTD_bps'},
            {title: 'ROMC MTD (bps)', data: 'ROMC_MTD_bps'},
            {title: '5D (bps)', data: '5D_bps'},
            {title: '1D (bps)', data: '1D_bps'},
            {title: 'ITD ($)', data: 'ITD_Dollar'},
            {title: 'YTD ($)', data: 'YTD_Dollar'},
            {title: 'MTD ($)', data: 'MTD_Dollar'},
            {title: '5D ($)', data: '5D_Dollar'},
            {title: '1D ($)', data: '1D_Dollar'},
            {title: 'VOL 30D(%)', data: 'VOL_30D_Pct'},
            {title: 'CAPITAL 1D(%)', data: 'Cap_1D_Pct'},
            {title: 'Story', data: 'story_url'},

        ],
        "columnDefs": [{
            "targets": [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
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
            var j = 13;
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
    })
}

// Below Function to adjust columns for dynamically created Tabs
$('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust();
});

$('#submit_tg_performance_as_of').on('click', function () {
    let as_of = $('#tradegroup_performance_as_of').val();
    window.location.href = "../position_stats/get_tradegroup_attribution_over_own_capital?as_of=" + as_of;

});


$('#tradegroup_attributions').on('change', function () {
    let selected = $('#tradegroup_attributions').val();

    let as_of = $('#as_of').val();
    if (selected === "TRADEGROUP ATTRIBUTION TO FUND NAV") {
        window.location.href = "../position_stats/get_tradegroup_performance_main_page?as_of=" + as_of
    }

});