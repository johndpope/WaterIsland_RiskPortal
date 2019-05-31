$(document).ready(function () {
    $('#etf_positions_table').DataTable({
        "pageLength": 100,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy to Clipboard',

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
        initComplete: function () {
            this.api().columns([0, 1]).every(function () {
                var column = this;
                $(column.header()).append("<br>");
                var select = $('<select class="form-control" ><option value=""></option></select>')
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
    });


    $('#submit_etf_positions_as_of').on('click', function () {
        // Get as of date
        let as_of = $('#etf_positions_as_of').val();
        let url = '../etf/get_etf_positions?as_of=' + as_of;
        window.location.href = url;
    });
});