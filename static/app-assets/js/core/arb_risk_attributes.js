$(document).ready(function () {

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
                title: '',
                autoPrint: true,
                exportOptions: {
                    columns: ':visible',
                    stripHtml: false
                }
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
                return obj;
            }
        },
        "columns": [
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
            "targets": [1, 3, 4, 5, 7, 10, 11, 12],
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
                "targets": [6, 7, 8, 13, 14, 15],
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
                "targets": [9, 16],
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
        ]


    });


    setInterval(function () {
        nav_impacts_table.ajax.reload(null, true);
        console.log('Requesting Updated P&L..');
    }, 3600000); // Every Hour


});