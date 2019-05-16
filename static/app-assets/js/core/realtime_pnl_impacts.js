$(document).ready(function () {

    let last_synced_on = null;
    let realtime_pnl_table = $('#realtime_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Total YTD", "data"));
    let realtime_daily_pnl_table = $('#realtime_daily_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Daily", "daily_pnl"));
    let position_level_pnl = null;
    let final_position_level_ytd_pnl = null;
    let fund_level_pnl = null;
    let fund_drilldown_details = null;
    // Now create the Dynamic Fund Tabs for Fund level P&L
    createFundPnLTables();

    // Column Alignment for the Tab Clicks
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust();
    });


    $('#realtime_pnl_table tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = realtime_pnl_table.row(tr);

        if (row.child.isShown()) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child(format(row.data(), true)).show();
            tr.addClass('shown');
        }
    });

    $('#realtime_daily_pnl_table tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = realtime_daily_pnl_table.row(tr);

        if (row.child.isShown()) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child(format(row.data(), false)).show();
            tr.addClass('shown');
        }
    });


    // let funds_list = ['ARB', 'MACO', 'MALT', 'LEV', 'AED', 'CAM', 'LG', 'WED', 'TAQ', 'TACO'];
    // for (var fund in funds_list) {
    //     $('#fund-tab-content').find('#tabARB table tbody').on('click', 'td.details-control', function () {
    //         var tr = $(this).closest('tr');
    //         console.log(tr);
    //         // var row = realtime_daily_pnl_table.row(tr);
    //         //
    //         // if (row.child.isShown()) {
    //         //     // This row is already open - close it
    //         //     row.child.hide();
    //         //     tr.removeClass('shown');
    //         // }
    //         // else {
    //         //     // Open this row
    //         //     row.child(format(row.data(), false)).show();
    //         //     tr.addClass('shown');
    //         // }
    //     })
    // }


    later.setInterval(refreshPnL, later.parse.text('every 10 mins on Mon, Tue, Weds, Thurs and Fri'));

    function refreshPnL() {
        realtime_pnl_table.ajax.reload(null, true);
        realtime_daily_pnl_table.ajax.reload(null, true);
        createFundPnLTables()
        console.log('Requesting Updated P&L..');
        $('#last_sycned').text(last_synced_on);
    }

    function createFundPnLTables() {
        // Fires Ajax and Retrieves the Fund Level JSON
        $('#fundtabs').empty();
        $('#fund-tab-content').empty();
        $.ajax({
            type: 'POST',
            url: '../realtime_pnl_impacts/fund_level_pnl',
            success: function (response) {
                fund_level_pnl = response['fund_details'];
                Object.keys(fund_level_pnl).forEach(function (fund) {
                    addFundTab(fund, 'fundtabs', 'fund-tab-content', fund_level_pnl);

                });
            },
            error: function (err) {
                console.log(err);
            }
        });


    }

    function addFundTab(name, addToTab, addToContent, fund_level_pnl) {
        // create the tab
        if (name === 'ARB') {
            $('<li class="nav-item"><a class="nav-link active" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
            $('<div class="tab-pane active" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
        }
        else {
            $('<li class="nav-item"><a class="nav-link" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
            $('<div class="tab-pane" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
        }


        $('<div class="tab-content" id="fund_pnl' + name + '"></div>').appendTo('#tab' + name);

        let fund_pnl = JSON.parse(fund_level_pnl[name]);

        // Do this Iteratively for each fund
        // Crete Active Tab for ARB
        let data = fund_pnl;
        $('<div class="tab-pane active" id="tabTable' + name + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + '">' +
            '<tfoot><tr><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th></tr></tfoot></table><br><br><br>' +
            '</div>' +
            '').appendTo('#fund_pnl' + name);
        initializeDatatableSummary(data, 'table' + name, name);


    }

    function initializeDatatableSummary(data, table_id, fundName) {
        $('#' + table_id).DataTable({
            data: data,
            responsive: true,
            scrollY: "580px",
            scrollX: true,
            paging: false,
            columns: [
                {
                    "className": 'details-control',
                    "orderable": false,
                    "data": null,
                    "defaultContent": ''
                },
                {title: 'TradeGroup', data: 'TradeGroup'},
                {title: 'Start MktVal', data: 'START_MKTVAL'},
                {title: 'End MktVal', data: 'END_MKTVAL'},
                {title: 'MktVal Change', data: 'MKTVAL_CHG_USD'},
                {title: 'Capital($)', data: 'Capital($)_x'},
                {title: 'Capital(%)', data: 'Capital(%)_x'},
                {title: 'AUM', data: 'aum'},
                {title: 'Return on Capital', data: 'ROC'},
                {title: 'Contribution to NAV', data: 'Contribution_to_NAV'},

            ],
            "columnDefs": [{
                "targets": [2, 3, 4, 5, 6, 7, 8, 9],
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
                var api = this.api(), data;

                // Remove the formatting to get integer data for summation
                var intVal = function (i) {
                    return typeof i === 'string' ?
                        i.replace(/[\$,]/g, '') * 1 :
                        typeof i === 'number' ?
                            i : 0;
                };
                // Iterate through Each column

                $.each([ 2, 3, 4, 5], function (index, value) {
                    let pageTotal = api
                        .column([value], {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return intVal(a) + intVal(b);
                        }, 0);

                    // Update footer
                    $(api.column([value]).footer()).html(
                        '$ ' + pageTotal.toLocaleString()
                    );
                });

                $.each([6], function (index, value) {
                    let pageTotal = api
                        .column([value], {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return intVal(a) + intVal(b);
                        }, 0);

                    // Update footer
                    $(api.column([value]).footer()).html(
                        pageTotal.toLocaleString() + '%'
                    );
                });


                $.each([8, 9], function (index, value) {
                    let pageTotal = api
                        .column([value], {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return intVal(a) + intVal(b);
                        }, 0);

                    // Update footer
                    $(api.column([value]).footer()).html(
                        pageTotal.toLocaleString() + ' (bips)'
                    );
                });


            },
            "initComplete": function (settings, json) {
                var api = this.api();

                $(this).on('click', 'td.details-control', function(){
                    var tr = $(this).closest('tr');
                    var row = api.row(tr);

                    if (row.child.isShown()) {
                        // This row is already open - close it
                        row.child.hide();
                        tr.removeClass('shown');
                    }
                    else {
                        // Open this row
                        row.child(format(row.data(), false, true, fundName)).show();
                        tr.addClass('shown');
                    }
                })
            }
        })
    }

    function get_pnl_table_initialization_configuration(url, total_or_daily_string, json_response_tag) {

        return {
            scrollY: "580px",
            scrollX: true,
            responsive: false,
            scrollCollapse: true,
            dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
                '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
                '<"row"<"col-sm-5"i><"col-sm-7"p>>',

            buttons: {
                buttons: [{
                    extend: 'print',
                    text: '<i class="fa fa-print"></i> Print',
                    title: 'Realtime P&L',
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
            "lengthChange": false,
            "paging": false,
            "language": {
                "processing": "Refreshing PnL"
            },

            "processing": true,
            "searching": true,
            "ajax": {
                "url": [url],
                "type": "POST",
                dataSrc: function (json) {
                    let obj = JSON.parse(json[[json_response_tag]]);
                    position_level_pnl = JSON.parse(json[['position_level_pnl']]);
                    final_position_level_ytd_pnl = JSON.parse(json[['final_position_level_ytd_pnl']]);
                    fund_drilldown_details = JSON.parse(json[['fund_drilldown_details']]);
                    last_synced_on = json[['last_synced_on']];
                    return obj;
                }
            },
            "columns": [
                {
                    "className": 'details-control',
                    "orderable": false,
                    "data": null,
                    "defaultContent": ''
                },
                {"data": "TradeGroup_"},
                {"data": "Sleeve_"},
                {"data": "Catalyst_"},
                {"data": [total_or_daily_string] + " PnL_ARB"},
                {"data": [total_or_daily_string] + " PnL_MACO"},
                {"data": [total_or_daily_string] + " PnL_MALT"},
                {"data": [total_or_daily_string] + " PnL_LEV"},
                {"data": [total_or_daily_string] + " PnL_AED"},
                {"data": [total_or_daily_string] + " PnL_CAM"},
                {"data": [total_or_daily_string] + " PnL_LG"},
                {"data": [total_or_daily_string] + " PnL_WED"},
                {"data": [total_or_daily_string] + " PnL_TAQ"},
                {"data": [total_or_daily_string] + " PnL_TACO"},

            ],
            "columnDefs": [{
                "targets": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                "width": "1%",
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
            },
                {
                    "targets": [0],
                    "width": "2%",
                },
                {
                    "targets": [1],
                    "width": "5%",
                },
                {
                    "targets": [2, 3],
                    "width": "3%",
                }],
            initComplete: function () {
                this.api().columns([2, 3]).every(function () {
                    var column = this;
                    $(column.header()).append("<br>");
                    var select = $('<select class="custom-select" ><option value=""></option></select>')
                        .appendTo($(column.header()))
                        .on('change', function () {
                            var val = $.fn.dataTable.util.escapeRegex(
                                $(this).val()
                            );

                            column
                                .search(val ? '^' + val + '$' : '', true, false)
                                .draw();
                        });

                    column.data().unique().sort().each(function (d, j) {
                        select.append('<option value="' + d + '">' + d + '</option>')
                    });
                });

            },
            "footerCallback": function (row, data, start, end, display) {
                var api = this.api(), data;

                // Remove the formatting to get integer data for summation
                var intVal = function (i) {
                    return typeof i === 'string' ?
                        i.replace(/[\$,]/g, '') * 1 :
                        typeof i === 'number' ?
                            i : 0;
                };
                // Iterate through Each column

                $.each([4, 5, 6, 7, 8, 9, 10, 11, 12, 13], function (index, value) {
                    let pageTotal = api
                        .column([value], {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return intVal(a) + intVal(b);
                        }, 0);

                    // Update footer
                    $(api.column([value]).footer()).html(
                        '$ ' + pageTotal.toLocaleString()
                    );
                });


            }

        }
    }

    function format(data, is_ytd, fund_drilldown = false, current_fund = null) {
        let tradegroup = data['TradeGroup_'];

        let return_rows = '';
        let dataframe = null;
        if (is_ytd) {
            dataframe = final_position_level_ytd_pnl;
        }
        else {
            dataframe = position_level_pnl;
        }

        if (fund_drilldown) {
            // Return Fund Specifics
            tradegroup = data['TradeGroup'];
            dataframe = fund_drilldown_details;

            let fund = current_fund;
            for (var i = 0; i < dataframe.length; i++) {
                let dataframe_row = dataframe[i];
                if (dataframe_row['TradeGroup'] === tradegroup && dataframe_row['Group'] === fund) {
                    return_rows += '<tr>' +
                        '<td>' + dataframe_row['Group'] + '</td>' +
                        '<td>' + dataframe_row['TradeGroup'] + '</td>' +
                        '<td>' + dataframe_row['Sleeve'] + '</td>' +
                        '<td>' + dataframe_row['Bucket'] + '</td>' +
                        '<td><strong>' + dataframe_row['TICKER_x'] + '</strong></td>' +
                        '<td>' + dataframe_row['AlphaHedge'] + '</td>' +
                        '<td>' + dataframe_row['LongShort'] + '</td>' +
                        dataframe_row['Qty_x'] +
                        dataframe_row['START_ADJ_PX'] +
                        dataframe_row['END_ADJ_PX'] +
                        dataframe_row['PX_CHG_PCT'] +
                        dataframe_row['START_MKTVAL'] +
                        dataframe_row['END_MKTVAL'] +
                        dataframe_row['MKTVAL_CHG_USD'] +
                        '</tr>'
                }

            }

            return '<div class="table-responsive" style="padding-left:3%"> <table class="table table-striped table-bordered" border="0">' +
                '<thead>' +
                '<tr>' +
                '<th>Fund</th>' + '<th>TradeGroup</th>' +'<th>Sleeve</th>' +'<th>Bucket</th>' + '<th>Ticker</th>' +'<th>AlphaHedge</th>' +'<th>LongShort</th>'
                + '<th>Qty</th>' + '<th>Start PX</th>' + '<th>End PX</th>' + '<th>PX Change(%)</th>' +
                '<th>Start MktVal</th>' +'<th>EndMktVal</th>' +'<th>MktVal Change</th>' +
                '</tr>' +
                '</thead>' + '<tbody>' + return_rows +
                '</tbody>' +
                '</table></div>';
        }


        // Get Equivalent Row from Positions Impacts
        for (var i = 0; i < dataframe.length; i++) {
            let dataframe_row = dataframe[i];
            if (dataframe_row['TradeGroup_'] === tradegroup) {
                // Return corresponding rows
                return_rows += '<tr>' +
                    '<td></td>' +
                    '<td>' + dataframe_row['TradeGroup_'] + '</td>' +
                    '<td>' + dataframe_row['TICKER_x_'] + '</td>' +
                    dataframe_row['START_ADJ_PX_'] +
                    dataframe_row['END_ADJ_PX_'] +
                    dataframe_row['MKTVAL_CHG_USD_ARB'] +
                    dataframe_row['MKTVAL_CHG_USD_MACO'] +
                    dataframe_row['MKTVAL_CHG_USD_MALT'] +
                    dataframe_row['MKTVAL_CHG_USD_LEV'] +
                    dataframe_row['MKTVAL_CHG_USD_AED'] +
                    dataframe_row['MKTVAL_CHG_USD_CAM'] +
                    dataframe_row['MKTVAL_CHG_USD_LG'] +
                    dataframe_row['MKTVAL_CHG_USD_WED'] +
                    dataframe_row['MKTVAL_CHG_USD_TAQ'] +
                    dataframe_row['MKTVAL_CHG_USD_TACO'] +
                    '</tr>'
            }
        }

        return '<div class="table-responsive" style="padding-left:3%"> <table class="table table-striped table-bordered" border="0">' +
            '<thead>' +
            '<tr>' +
            '<th></th><th>TradeGroup</th>' + '<th>Ticker</th>' + '<th>Start PX</th>' + '<th>End PX</th>' + '<th>P&L ARB</th>' + '<th>P&L MACO</th>' +
            '<th>P&L MALT</th>' + '<th>P&L LEV</th>' + '<th>P&L AED</th>' + '<th>P&L CAM</th>' + '<th>P&L LG</th>' + '<th>P&L WED</th>'
            + '<th>P&L TAQ</th>' +
            '<th>P&L TACO</th>' +
            '</tr>' +
            '</thead>' + '<tbody>' + return_rows +
            '</tbody>' +

            '</table></div>';


    }


});

$('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust();
});
