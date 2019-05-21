$(document).ready(function () {

    var mna_idea_table_archived = $('#mna_idea_table_archived').DataTable({
        paging: false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        columnDefs: [{
            targets: [2,3,9], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        }],
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: '',
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
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
                },
                autoPrint: true,
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                },
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


    //Initialize the Database
    var mna_idea_table = $('#mna_idea_table').DataTable({
        paging: false,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        fixedHeader: {
            header: true
        },
        columnDefs: [{
            targets: [2,3,9], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        }],
        "aaSorting": [[3, 'desc']],
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: '',
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
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
                },
                autoPrint: true,
            }, {
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
                },
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

     $('.table-responsive').on("click", "#mna_idea_table_archived tr td li a", function () {
        var current_deal = this.id.toString();
        // Handle Selected Logic Here
        if (current_deal.search('view_') != -1) {
            //Logic for Opening a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            let deal_id_to_view = current_deal.split('_')[1]; //Get the ID
            window.open("../risk/show_mna_idea?mna_idea_id=" + deal_id_to_view, '_blank');
            return false;

        }

        else if (current_deal.search('restore_') != -1) {
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
            $.ajax({
                type: 'POST',
                url: '../risk/restore_merger_arb_idea',
                data: {'id': deal_id_to_edit},
                success: function (response) {
                    if (response === "Success") {
                        //Delete Row from DataTable
                        swal("Success! The IDEA has been Restored!", {icon: "success"});
                        //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                        mna_idea_table_archived.row($("#row_" + deal_id_to_edit)).remove().draw();

                    }
                    else {
                        //show a sweet alert
                        swal("Error!", "Restoration Failed!", "error");
                    }
                },
                error: function (error) {
                    swal("Error!", "Restoring Deal Failed!", "error");
                }
            });
        }


        else {
            //Logic for Delete
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Deal!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../risk/delete_mna_idea',
                        data: {'id': deal_id_to_edit},
                        success: function (response) {
                            if (response === "Success") {
                                //Delete Row from DataTable
                                swal("Success! The IDEA has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                mna_idea_table_archived.row($("#row_" + deal_id_to_edit)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Deal Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Deal Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }
     });


    $('.table-responsive').on("click", "#mna_idea_table tr td li a", function () {

        var current_deal = this.id.toString();
        // Handle Selected Logic Here
        if (current_deal.search('view_') != -1) {
            //Logic for Opening a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            let deal_id_to_view = current_deal.split('_')[1]; //Get the ID
            window.open("../risk/show_mna_idea?mna_idea_id=" + deal_id_to_view, '_blank');
            return false;

        }
        else if (current_deal.search('archive_') != -1) {
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
            $.ajax({
                type: 'POST',
                url: '../risk/archive_mna_idea',
                data: {'id': deal_id_to_edit},
                success: function (response) {
                    if (response === "Success") {
                        //Delete Row from DataTable
                        swal("Success! The IDEA has been archived!", {icon: "success"});
                        //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                        mna_idea_table.row($("#row_" + deal_id_to_edit)).remove().draw();

                    }
                    else {
                        //show a sweet alert
                        swal("Error!", "Archiving Failed!", "error");
                    }
                },
                error: function (error) {
                    swal("Error!", "Archiving Deal Failed!", "error");
                }
            });
        }

        else {
            //Logic for Delete
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Deal!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../risk/delete_mna_idea',
                        data: {'id': deal_id_to_edit},
                        success: function (response) {
                            if (response === "Success") {
                                //Delete Row from DataTable
                                swal("Success! The IDEA has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                mna_idea_table.row($("#row_" + deal_id_to_edit)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Deal Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Deal Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }


    });
});