$(document).ready(function () {
    later.date.localTime();
    let last_synced_on = null;
    let realtime_pnl_table = $('#realtime_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Total YTD", "data"));
    let realtime_daily_pnl_table = $('#realtime_daily_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Daily", "daily_pnl"));
    let position_level_pnl = null;
    // Column Alignment for the Tab Clicks
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust()
            .fixedColumns().relayout();
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
            row.child(format(row.data())).show();
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
            row.child(format(row.data())).show();
            tr.addClass('shown');
        }
    });

    later.setInterval(refreshPnL, later.parse.text('every 10 mins on Mon, Tue, Weds, Thurs and Fri'));

    function refreshPnL(){
        realtime_pnl_table.ajax.reload(null, true);
        realtime_daily_pnl_table.ajax.reload(null, true);
        console.log('Requesting Updated P&L..');
        $('#last_sycned').text(last_synced_on);
    }


    function get_pnl_table_initialization_configuration(url, total_or_daily_string, json_response_tag) {

        return {
            scrollY: "680px",
            scrollX: true,
            scrollCollapse: true,
            fixedColumns: {
                leftColumns: 2
            },
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
                "targets": [ 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
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
    function format(d) {
        console.log(d);
        let tradegroup = d['TradeGroup_'];
        let return_rows = '';
        // Get Equivalent Row from Positions Impacts
        for (var i = 0; i < position_level_pnl.length; i++) {
            if (position_level_pnl[i]['TradeGroup_'] === tradegroup) {
                // Return corresponding rows
                return_rows += '<tr>' +
                    '<td></td>' +
                    '<td>' + position_level_pnl[i]['TradeGroup_'] + '</td>' +
                    '<td>' + position_level_pnl[i]['TICKER_x_'] + '</td>' +
                    '<td>' + position_level_pnl[i]['START_ADJ_PX_'] + '</td>' +
                    '<td>' + position_level_pnl[i]['END_ADJ_PX_'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_ARB'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_MACO'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_MALT'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_LEV'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_AED'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_CAM'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_LG'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_WED'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_TAQ'] + '</td>' +
                    '<td>' + position_level_pnl[i]['MKTVAL_CHG_USD_TACO'] + '</td>' +
                    '</tr>'
            }
        }


        // `d` is the original data object for the row
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

