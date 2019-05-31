$(document).ready(function () {
    var accounts_table = $('#accounts_table').DataTable({
        columnDefs: [{
            targets: [0], render: function (data) {
                return moment(data, 'MMM DD, YYYY, h:mm a').format('YYYY-MM-DD, hh:mm a');
            }
        }],
        "aaSorting": [[0,'desc']],
        "pageLength": 25,
    });

    $('#position_rec_add_new_account').on("click", function(){
        $('#modal_label').html('Create a New Account');
        $('#account_id_to_edit').val("");
    });

    $('.table-responsive').on("click", "#accounts_table tr td li a", function () {

        var current_account = this.id.toString();
        // Handle Selected Logic Here
        if (current_account.search('edit_account_') != -1) {
            var account_id_to_edit = current_account.split('_').pop(); //Get the ID
            $('#submit_accounts_edit_form').trigger('reset');
            $('#modal_label').html('Edit Account');
            var third_party = '';
            var account_no = '';
            var mnemonic = '';
            var type = '';
            var fund = '';
            var excluded = '';
            $.ajax({
                url: "../position_rec/get_account_details/",
                type: 'POST',
                data: {'account_id': account_id_to_edit},
                success: function (response) {
                    let account_details = response['account_details'];
                    third_party = account_details.third_party;
                    account_no = account_details.account_no;
                    mnemonic = account_details.mnemonic;
                    type = account_details.type;
                    fund = account_details.fund;
                    excluded = account_details.excluded;
                    $('#third_party').val(third_party);
                    $('#account_no').val(account_no);
                    $('#mnemonic').val(mnemonic);
                    $('#type').val(type);
                    $('#fund').val(fund);
                    $('#excluded').val(excluded);
                    $('#account_id_to_edit').val(account_id_to_edit);
                },
                error: function (err) {
                    console.log(err);
                }
            });
            $('#create_new_account_modal').modal('show');
        }
        else if (current_account.search('delete_account_') != -1) {
            //First Popup sweetAlert to Confirm Deletion
            account_id_to_edit = current_account.split('_').pop();

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Account!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../position_rec/delete_account/',
                        data: {'id': account_id_to_edit},
                        success: function (response) {
                            if (response === "account_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The Position Rec Account has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                accounts_table.row($("#row_" + account_id_to_edit)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Position Rec Account Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Position Rec Account Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }
    });
});
