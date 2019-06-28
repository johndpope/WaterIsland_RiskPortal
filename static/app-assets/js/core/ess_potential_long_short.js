$(document).ready(function () {

    var table = $('#ess_ls').DataTable({
        "pageLength": 100,
        "order":[[1, 'asc']],
        "columnDefs": [{
            "targets": [2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }],
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'csv',
                text: '<i class="fa fa-print"></i> Import as CSV',
                className: 'btn btn-default btn-xs',
                customize: function (csv) {
                    var csvRows = csv.split('\n');
                    csvRows[0] = 'As Of, Alpha Ticker, PX, Model Up, Model WIC, Model Down, Catalyst, Rating, Deal Type,' +
                                 'Hedges?, Implied Prob, Return/Risk, Gross IRR, Days To Close, Ann. IRR, Adj. Ann IRR,' +
                                 'Long Prob, Long IRR, Short Prob, Short IRR, Potential Long, Potential Short'
                    return csvRows.join('\n');
                }
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
        initComplete: function () {
            this.api().columns([0]).every( function () {
                var column = this;
                var select = $('<br><select class="form-control"><option value=""></option></select>')
                    .appendTo( $(column.header()) )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );
                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );
 
                    column.cells('', column[0]).render('display').sort().unique().each( function ( d, j ) {
                    select.append('<option value="' + d + '">' + d.substr(0,30) + '</option>')
                } );
            } );
        }
    });
});