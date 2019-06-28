$(document).ready(function () {

    $('#submit_long_short_as_of').on('click', function () {
        let as_of = $('#long_short_as_of').val();
        if (as_of) {
            window.location.href = "../portfolio_optimization/ess_potential_long_shorts?as_of=" + as_of;
        }
        else {
            swal('Error!', 'Select Date please!', 'error');
        }
    });

    var table = $('#ess_ls').DataTable({
        "pageLength": 100,
        "order":[[1, 'asc']],
        "columnDefs": [{
            "targets": [2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }],
        scrollY: "50vh",
        scrollX: true,
        fixedColumns: {
            leftColumns: 2
        },
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'csv',
                text: '<i class="fa fa-print"></i> Import as CSV',
                className: 'btn btn-default btn-xs',
            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        }
    });
});

document.onload = function () {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust()
        .fixedColumns().update()
};

$(window).resize(function(){
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust()
        .fixedColumns().relayout()
});
