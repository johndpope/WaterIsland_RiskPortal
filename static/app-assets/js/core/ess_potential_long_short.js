$(document).ready(function () {

    var table = $('#ess_ls').DataTable({
        "pageLength": 100,
        "order":[[1, 'asc']],
        "columnDefs": [{
            "targets": [2, 3, 4, 9, 10, 11, 13, 14, 15, 16, 17, 18],
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }],
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