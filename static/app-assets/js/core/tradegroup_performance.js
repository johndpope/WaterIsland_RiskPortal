$(document).ready(function () {
    $('#submit_expoures_as_of').on('click', function () {
        // Get the Date
        let as_of = $('#exposures_as_of').val();
        window.location.replace('../exposures/exposures_snapshot?as_of=' + as_of);


    });

    let tradegroup_performance = $.parseJSON($('#tradegroup_performance_dollars').val());

    let tradegroup_performance_bips = $.parseJSON($('#tradegroup_performance_bips').val());
    Object.keys(tradegroup_performance).forEach(function (fund) {
        addFundMainTab(fund, 'fundtabs', 'fund-tab-content', 'Across', tradegroup_performance, tradegroup_performance_bips);

    });
    $(".loader-wrapper").remove();


});

function addFundMainTab(name, addToTab, addToContent, sleeve, tradegroup_performance, tradegroup_performance_bps) {
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

    // For each Fund, create a Datatable and iterate over the response for 2 tabs ($ Performance vs bps Performance)
    $('<ul class="nav nav-pills nav-fill" id="performance_metric_tabs' + name + '"></ul>').appendTo('#tab' + name);

    $('<li class="nav-item"><a class="nav-link active" href="#performance_metric_tabs_bips' + name + '" data-toggle="tab">' + "Performance(bps)" + '</a></li>').appendTo('#performance_metric_tabs' + name);
    $('<li class="nav-item"><a class="nav-link" href="#performance_metric_tabs_dollar' + name + '" data-toggle="tab">' + "Performance($)" + '</a></li>').appendTo('#performance_metric_tabs' + name);


    $('<div class="tab-content" id="performance_metric_tabs_dollar_and_bips' + name + '"></div>').appendTo('#tab' + name);


    let tradegroup_performances_in_dollar = JSON.parse(tradegroup_performance[name]);
    let tradegroup_performances_in_bps = JSON.parse(tradegroup_performance_bps[name]);

    // Do this Iteratively for each fund

    // Create Active Tab for ARB
    let data = tradegroup_performances_in_dollar;

    let bips_data = tradegroup_performances_in_bps;


    $('<div class="tab-pane active" id="performance_metric_tabs_bips' + name + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + 'bips' + '">' +
        '<tfoot><tr><td></td><td></td><td></td><td></td><td></td><td></td><td><td></td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>' +
        '').appendTo('#performance_metric_tabs_dollar_and_bips' + name);
    initializeDatatableSummary(bips_data, 'table' + name + 'bips', '_bps');


    $('<div class="tab-pane" id="performance_metric_tabs_dollar' + name + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + 'dollar' + '">' +
        '<tfoot><tr><td></td><td></td><td></td><td></td><td></td><td></td><td><td></td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table></div>' +
        '').appendTo('#performance_metric_tabs_dollar_and_bips' + name);
    initializeDatatableSummary(data, 'table' + name + 'dollar', '_Dollar');


}


function initializeDatatableSummary(data, table_id, column) {
    $('#' + table_id).DataTable({
        scrollY: "680px",
        scrollX: true,
        scrollCollapse: true,
        data: data,
        lengthChange: false,
        paginate: false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',

        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: 'TradeGroup Perf. Over Fund NAV',
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
        fixedHeader: {
            header: true,
            footer: true
        },
        columns: [
            {title: 'Date', data: 'Date'},
            {title: 'Sleeve', data: 'Sleeve'},
            {title: 'TradeGroup', data: 'TradeGroup'},
            {title: 'Catalyst', data: 'CatalystTypeWIC'},
            {title: 'Rating', data: 'CatalystRating'},
            {title: 'LongShort', data: 'LongShort'},
            {title: 'InceptionDate', data: 'InceptionDate'},
            {title: 'EndDate', data: 'EndDate'},
            {title: 'Status', data: 'Status'},
            {title: 'ITD', data: 'ITD' + column},
            {title: 'YTD', data: 'YTD' + column},
            {title: 'QTD', data: 'QTD' + column},
            {title: 'MTD', data: 'MTD' + column},
            {title: '30D', data: '30D' + column},
            {title: '5D', data: '5D' + column},
            {title: '1D', data: '1D' + column},
            {title: 'Story', data: 'story_url'},

        ],
        "columnDefs": [{
            "targets": [9, 10, 11, 12, 13, 14, 15],
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
            var j = 9;
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
    window.location.href = "../position_stats/get_tradegroup_performance_main_page?as_of=" + as_of;

});


$('#tradegroup_attributions').on('change', function () {
    let selected = $('#tradegroup_attributions').val();

    let as_of = $('#as_of').val();

    if (selected === "TRADEGROUP ATTRIBUTION OVER OWN CAPITAL") {
        window.location.href = "../position_stats/get_tradegroup_attribution_over_own_capital?as_of=" + as_of
    }

});