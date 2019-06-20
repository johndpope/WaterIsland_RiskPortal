$(document).ready(function () {
    let tradegroup_drawdowns = $.parseJSON($('#tradegroup_drawdowns').val());
    let sleeve_drawdowns = $.parseJSON($('#sleeve_drawdowns').val());
    let bucket_drawdowns = $.parseJSON($('#bucket_drawdowns').val());

    $('#tradegroup_drawdown_table').DataTable({
        data: tradegroup_drawdowns,
        scrollY: "50vh",
        scrollX: true,
        scrollCollapse: false,
        paging: false,
        fixedColumns: {
            leftColumns: 2,
        },
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
        columns: [
            {data: 'Date'},
            {data: 'Fund'},
            {data: 'TradeGroup'},
            {data: 'Last_Date'},
            {data: 'NAV_Max_bps'},
             {data: 'NAV_Min_bps'},
            {data: 'NAV_Last_bps'},
            {data: 'NAV_MaxToMin_Drawdown_bps'},
            {data: 'NAV_MaxToLast_Drawdown_bps'},
            {data: 'NAV_Max_Date'},
            {data: 'NAV_Min_Date'},
            {data: 'ROC_Max_bps'},
            {data: 'ROC_Min_bps'},
            {data: 'ROC_Last_bps'},
            {data: 'ROC_MaxToMin_Drawdown_Pct'},
            {data: 'ROC_MaxToLast_Drawdown_Pct'},
            {data: 'ROC_Max_Date'},
            {data: 'ROC_Min_Date'},
            {data: 'ROMC_Max_bps'},
            {data: 'ROMC_Min_bps'},
            {data: 'ROMC_Last_bps'},
            {data: 'ROMC_MaxToMin_Drawdown_Pct'},
            {data: 'ROMC_MaxToLast_Drawdown_Pct'},
            {data: 'ROMC_Max_Date'},
            {data: 'ROMC_Min_Date'},
        ],

    });

    // Sleeve Drawdowns
    $('#sleeve_drawdown_table').DataTable({
        data: sleeve_drawdowns,
        scrollY: "50vh",
        scrollX: true,
        scrollCollapse: true,
        paging: false,
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
        columns: [
            {data: 'Date'},
            {data: 'Fund'},
            {data: 'Sleeve'},
            {data: 'Last_Date'},
            {data: 'NAV_Max_bps'},
            {data: 'NAV_Min_bps'},
            {data: 'NAV_Last_bps'},
            {data: 'NAV_MaxToMin_Drawdown_bps'},
            {data: 'NAV_MaxToLast_Drawdown_bps'},
            {data: 'NAV_Max_Date'},
            {data: 'NAV_Min_Date'},
            {data: 'ROC_Max_bps'},
            {data: 'ROC_Min_bps'},
            {data: 'ROC_Last_bps'},
            {data: 'ROC_MaxToMin_Drawdown_Pct'},
            {data: 'ROC_MaxToLast_Drawdown_Pct'},
            {data: 'ROC_Max_Date'},
            {data: 'ROC_Min_Date'},
            {data: 'ROMC_Max_bps'},
            {data: 'ROMC_Min_bps'},
            {data: 'ROMC_Last_bps'},
            {data: 'ROMC_MaxToMin_Drawdown_Pct'},
            {data: 'ROMC_MaxToLast_Drawdown_Pct'},
            {data: 'ROMC_Max_Date'},
            {data: 'ROMC_Min_Date'},
        ],
    });

    // Bucket Drawdowns
    $('#bucket_drawdown_table').DataTable({
        data: bucket_drawdowns,
        scrollY: "50vh",
        scrollX: true,
        scrollCollapse: true,
        paging: false,
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
        columns: [
            {data: 'Date'},
            {data: 'Fund'},
            {data: 'Bucket'},
            {data: 'Last_Date'},
            {data: 'NAV_Max_bps'},
            {data: 'NAV_Min_bps'},
            {data: 'NAV_Last_bps'},
            {data: 'NAV_MaxToMin_Drawdown_bps'},
            {data: 'NAV_MaxToLast_Drawdown_bps'},
            {data: 'NAV_Max_Date'},
            {data: 'NAV_Min_Date'},
            {data: 'ROC_Max_bps'},
            {data: 'ROC_Min_bps'},
            {data: 'ROC_Last_bps'},
            {data: 'ROC_MaxToMin_Drawdown_Pct'},
            {data: 'ROC_MaxToLast_Drawdown_Pct'},
            {data: 'ROC_Max_Date'},
            {data: 'ROC_Min_Date'},
            {data: 'ROMC_Max_bps'},
            {data: 'ROMC_Min_bps'},
            {data: 'ROMC_Last_bps'},
            {data: 'ROMC_MaxToMin_Drawdown_Pct'},
            {data: 'ROMC_MaxToLast_Drawdown_Pct'},
            {data: 'ROMC_Max_Date'},
            {data: 'ROMC_Min_Date'},
        ],

    });


});
$('body').on('shown.bs.tab', 'a[data-toggle="tab"]', function (e) {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust()
        .fixedColumns().update();
});
