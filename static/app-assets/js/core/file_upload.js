$(document).ready(function () {
    var file_upload_table = $('#file_upload_table').DataTable({
        columnDefs: [{
            targets: [0], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        }],
        "aaSorting": [[0,'desc']],
        "pageLength": 25,
    });

    $('.table-responsive').on("click", "#file_upload_table tr td li a", function () {

        var current_file_row = this.id.toString();
        if (current_file_row.search('delete_file_data_') != -1) {
            //First Popup sweetAlert to Confirm Deletion
            file_id_to_delete = current_file_row.split('_').pop();

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this file!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../position_rec/delete_ops_file/',
                        data: {'id': file_id_to_delete},
                        success: function (response) {
                            if (response === "file_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The Position Rec File has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                file_upload_table.row($("#row_" + file_id_to_delete)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Position Rec File Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Position Rec File Failed!", "error");
                            console.log(error);
                        }
                    });
                }
            });
        }
    });
});