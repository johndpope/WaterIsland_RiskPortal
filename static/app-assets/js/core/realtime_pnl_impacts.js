$(document).ready(function () {

    let realtime_pnl_table = $('#realtime_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Total YTD", "data"));
    let realtime_daily_pnl_table = $('#realtime_daily_pnl_table').DataTable(get_pnl_table_initialization_configuration("live_tradegroup_pnl", "Daily", "daily_pnl"));

    // Column Alignment for the Tab Clicks
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $($.fn.dataTable.tables(true)).DataTable()
            .columns.adjust()
            .fixedColumns().relayout();
    });

    setInterval(function () {
        realtime_pnl_table.ajax.reload(null, true);
        realtime_daily_pnl_table.ajax.reload(null, true);
        console.log('Requesting Updated P&L..');
    }, 3600000); // Every Hour

});


function get_pnl_table_initialization_configuration(url, total_or_daily_string, json_response_tag) {
    return {
        scrollY: "680px",
        scrollX: true,
        scrollCollapse: true,
        fixedColumns: {
            leftColumns: 1
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
                return obj;
            }
        },
        "columns": [
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
            "targets": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
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
            this.api().columns([1, 2]).every(function () {
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

            $.each([3, 4, 5, 6, 7, 8, 9, 10, 11, 12], function (index, value) {
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