$(document).ready(function () {
    let position_level_impacts = null;
    let ytd_performances = null;
    let nav_impacts_table = $('#arb_risk_attributes_table').DataTable({
        "language": {
            "processing": "Getting Real-time NAV Impacts"
        },
        'paging': false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',

        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: 'NAV Impacts (Synced on): ' + $('#sync').val(),
                exportOptions: {
                    stripHtml: false,
                    columns: [ 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17 ]
                },
                customize: function (win) {
                    $(win.document.body)
                        .css('font-size', '10pt')
                        .prepend(
                            '<p> Water Island Capital, Risk Portal</p>'
                        );

                    $(win.document.body).find('table')
                        .addClass('compact')
                        .css('font-size', 'inherit');

                    var css = '@page { size: landscape; }',
                        head = win.document.head || win.document.getElementsByTagName('head')[0],
                        style = win.document.createElement('style');

                    style.type = 'text/css';
                    style.media = 'print';

                    if (style.styleSheet) {
                        style.styleSheet.cssText = css;
                    }
                    else {
                        style.appendChild(win.document.createTextNode(css));
                    }

                    head.appendChild(style);
                },
                autoPrint: true,
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                exportOptions: {
                    columns: ':visible',
                    stripHtml: false
                }

            },
            ],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        },

        "processing": true,
        "searching": true,
        "ajax": {
            "url": "../risk_reporting/merger_arb_risk_attributes",
            "type": "POST",
            dataSrc: function (json) {
                let obj = JSON.parse(json["data"]);
                position_level_impacts = JSON.parse(json["positions"]);
                ytd_performances = JSON.parse(json["ytd_pnl"]);
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
            {"data": "TradeGroup"},
            {"data": "RiskLimit"},
            {"data": "LastUpdate"},
            {"data": "BASE_CASE_NAV_IMPACT_ARB"},
            {"data": "BASE_CASE_NAV_IMPACT_MACO"},
            {"data": "BASE_CASE_NAV_IMPACT_MALT"},
            {"data": "BASE_CASE_NAV_IMPACT_AED"},
            {"data": "BASE_CASE_NAV_IMPACT_CAM"},
            {"data": "BASE_CASE_NAV_IMPACT_LG"},
            {"data": "BASE_CASE_NAV_IMPACT_LEV"},
            {"data": "OUTLIER_NAV_IMPACT_ARB"},
            {"data": "OUTLIER_NAV_IMPACT_MACO"},
            {"data": "OUTLIER_NAV_IMPACT_MALT"},
            {"data": "OUTLIER_NAV_IMPACT_AED"},
            {"data": "OUTLIER_NAV_IMPACT_CAM"},
            {"data": "OUTLIER_NAV_IMPACT_LG"},
            {"data": "OUTLIER_NAV_IMPACT_LEV"},

        ],
        "columnDefs": [{
            "targets": [2, 4, 5, 6, 8, 11, 12, 13],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out

                if (Math.abs(cellData) >= Math.abs(rowData['RiskLimit']) && $.isNumeric(cellData)) {
                    $(td).css('color', 'red')
                }
                else if (!$.isNumeric(cellData)) {
                    $(td).css('color', 'black')
                }
                else {
                    $(td).css('color', 'green')
                }
            }
        },
            {   // Multi - Strats and Leveraged Fund (Risk is 2x and 3x respectively
                "targets": [7, 8, 9, 14, 15, 16],
                "render": $.fn.dataTable.render.number(',', '.', 2),
                "createdCell": function (td, cellData, rowData, rowIndex) {
                    //Check for % Float and %Shares Out
                    if (Math.abs(cellData) >= Math.abs(2 * rowData['RiskLimit']) && $.isNumeric(cellData)) {
                        $(td).css('color', 'red')
                    }
                    else if (!$.isNumeric(cellData)) {
                        $(td).css('color', 'black')
                    }
                    else {
                        $(td).css('color', 'green')
                    }
                }
            },
            { // Handle 3x Risk for Leveraged Fund
                "targets": [10, 17],
                "render": $.fn.dataTable.render.number(',', '.', 2),
                "createdCell": function (td, cellData, rowData, rowIndex) {
                    //Check for % Float and %Shares Out
                    if (Math.abs(cellData) >= Math.abs(3 * rowData['RiskLimit']) && $.isNumeric(cellData)) {
                        $(td).css('color', 'red')
                    }
                    else if (!$.isNumeric(cellData)) {
                        $(td).css('color', 'black')
                    }
                    else {
                        $(td).css('color', 'green')
                    }
                }
            }
        ],
        "initComplete": function (settings, json) {

        }


    });

    function format(d) {
        let tradegroup = d['TradeGroup'];

        let return_rows = '';
        // Get Equivalent Row from Positions Impacts
        for (var i = 0; i < position_level_impacts.length; i++) {
            if (position_level_impacts[i]['TradeGroup'] === tradegroup) {
                // Return corresponding rows
                return_rows += '<tr>' +
                    '<td>' + position_level_impacts[i]['TradeGroup'] + '</td>' +
                    '<td>' + position_level_impacts[i]['Ticker'] + '</td>' +
                    '<td>' + position_level_impacts[i]['LastPrice'] + '</td>' +
                    '<td>' + position_level_impacts[i]['PM_BASE_CASE'] + '</td>' +
                    '<td>' + position_level_impacts[i]['Outlier'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_ARB'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_MACO'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_MALT'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_AED'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_CAM'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_LG'] + '</td>' +
                    '<td>' + position_level_impacts[i]['BASE_CASE_NAV_IMPACT_LEV'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_ARB'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_MACO'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_MALT'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_AED'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_CAM'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_LG'] + '</td>' +
                    '<td>' + position_level_impacts[i]['OUTLIER_NAV_IMPACT_LEV'] + '</td>' +
                    '</tr>'
            }
        }

        for (var j=0;j<ytd_performances.length;j++){
            if (ytd_performances[j]['TradeGroup'] === tradegroup) {
                // Return corresponding rows
                return_rows += '<tr>' +
                    '<td class="bg-warning">' + ytd_performances[j]['TradeGroup'] + '</td>' +
                    '<td class="bg-warning">YTD P&L -></td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_ARB'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_MACO'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_MALT'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_AED'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_CAM'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_LG'] + '</td>' +
                    '<td>' + ytd_performances[j]['PnL_BPS_LEV'] + '</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '<td>-</td>' +
                    '</tr>'
            }
        }


        // `d` is the original data object for the row
        return '<div class="table-responsive" style="padding-left:6%"> <table class="table table-striped table-bordered" border="0">' +
            '<thead>' +
            '<tr>' +
            '<th>Strategy</th>' + '<th>Ticker</th>' + '<th>Last Price</th>' + '<th>BaseCase</th>' + '<th>Outlier</th>' + '<th>ARB(BCase)</th>' +
            '<th>MACO(Bcase)</th>' + '<th>MALT(BCase)</th>' + '<th>AED(BCase)</th>' + '<th>CAM(BCase)</th>' + '<th>LG(BCase)</th>' + '<th>LEV(BCase)</th>'
            + '<th>ARB(Outlier)</th>' +
            '<th>MACO(Outlier)</th>' + '<th>MALT(Outlier)</th>' + '<th>AED(Outlier)</th>' + '<th>CAM(Outlier)</th>' + '<th>LG(Outlier)</th>' + '<th>LEV(Outlier)</th>' +
            '</tr>' +
            '</thead>' + '<tbody>' + return_rows +
            '</tbody>' +

            '</table></div>';
    }

    setInterval(function () {
        window.location.reload();
    }, 1200000); // Every 20 Minutes

    $('#arb_risk_attributes_table tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = nav_impacts_table.row(tr);

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

});