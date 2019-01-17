$(document).ready(function () {
    // Initialize Datatable
    $('#arb_risk_attributes_table').DataTable({
        'paging': false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },

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
        }, "columnDefs": [{
            "targets": [2, 3, 4, 5, 6, 7, 8, 9],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {
                //Check for % Float and %Shares Out
                if (cellData >= rowData[1] && $.isNumeric(cellData)) {
                    $(td).css('color', 'red')
                }
                else if (!$.isNumeric(cellData)) {
                    $(td).css('color', 'black')
                }
                else {
                    $(td).css('color', 'green')
                }
            }
        }]
    });

});