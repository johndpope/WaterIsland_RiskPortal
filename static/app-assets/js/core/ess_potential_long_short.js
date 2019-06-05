$(document).ready(function () {
    $('#ess_ls').DataTable({
        "pageLength": 100,
        "columnDefs": [{
            "targets": [1, 2, 3, 6, 7, 8, 9, 10, 11],
            "render": $.fn.dataTable.render.number(',', '.', 2),

        }],
    });


});