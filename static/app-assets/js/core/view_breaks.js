$(document).ready(function () {

    var breaks_table = $('#breaks_table').DataTable({
        paging: true,
        searching: true,
        ordering: false,
        sortable: true,
        pageLength: 25,
        aaSorting: [[3,'asc']],
        initComplete: function () {
            this.api().columns([1, 2, 7, 9]).every( function () {
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

    $(document).on("click", "a", function () {
        var button_id = this.id;
        if (button_id.includes("edit_break_")) {
            var position_rec_to_edit_id = button_id.split("_").pop();
            console.log(position_rec_to_edit_id);
            $('#position_rec_to_edit_id').val(position_rec_to_edit_id);
        }
    });

    $('#submit_position_rec_edit_form').on('submit', function (e) {
        e.preventDefault();
        var comments = $('#comments').val();
        var resolved = $('#resolved').val();
        var position_rec_to_edit_id = $('#position_rec_to_edit_id').val();
        $.ajax({
            type: 'POST',
            url: '../position_rec/edit_position_rec/',
            data: {'position_rec_to_edit_id': position_rec_to_edit_id, 'comments': comments, 'resolved': resolved},
            success: function (response) {
                console.log(response);
                if (response == 'Success') {
                    location.reload();
                }
                else {
                    swal("Error!", "Some error occurred", "error");
                    console.log('Error in updating action id', position_rec_to_edit_id);
                }
            },
            error: function (error) {
                swal("Error!", "The Position Rec Break could not be updated", "error");
                console.log(error, position_rec_to_edit_id);
            }
        });
        $('#edit_position_rec_modal').modal('hide');
    });

    const checkbox = document.getElementById('show_resolved_breaks_checkbox')
    checkbox.addEventListener('change', (event) => {
        if (event.target.checked) {
            console.log('checked');
            var url = window.location.href,
            url = url.replace("?resolved=true", "");
            url = url.replace("?resolved=false", "");
            url += "?resolved=true";
            window.location.href = url;
        } else {
            console.log('not checked');
            var url = window.location.href,
            url = url.replace("?resolved=true", "");
            url = url.replace("?resolved=false", "");
            url += "?resolved=false";
            window.location.href = url;
        }
    });
});