$(document).ready(function () {
    var credit_idea_table = $('#credit_idea_table').DataTable({
        "aaSorting": [[0,'desc']],
        "pageLength": 25,
    });

    $('#credit_idea_add_new_idea').on("click", function(){
        $('#modal_label').html('CREATE A NEW IDEA');
        $('#idea_id_to_edit').val("");
    });

    $('.table-responsive').on("click", "#credit_idea_table tr td li a", function () {

        var current_idea = this.id.toString();
        // Handle Selected Logic Here
        if (current_idea.search('edit_idea_') != -1) {
            var idea_id_to_edit = current_idea.split('_').pop(); //Get the ID
            $('#submit_idea_edit_form').trigger('reset');
            $('#modal_label').html('EDIT IDEA');
            var analyst = '';
            var deal_bucket = '';
            var deal_strategy_type = '';
            var catalyst = '';
            var catalyst_tier = '';
            var target_sec_cusip = '';
            var coupon = '';
            var hedge_sec_cusip = '';
            var estimated_closing_date = '';
            var upside_price = '';
            var downside_price = '';
            var comments = '';
            $.ajax({
                url: "../credit_idea/get_credit_idea_details/",
                type: 'GET',
                data: {'credit_idea_id': idea_id_to_edit},
                success: function (response) {
                    let credit_idea_details = response['credit_idea_details'];
                    analyst = credit_idea_details.analyst;
                    deal_bucket = credit_idea_details.deal_bucket;
                    deal_strategy_type = credit_idea_details.deal_strategy_type;
                    catalyst = credit_idea_details.catalyst;
                    catalyst_tier = credit_idea_details.catalyst_tier;
                    target_sec_cusip = credit_idea_details.target_sec_cusip;
                    coupon = credit_idea_details.coupon;
                    hedge_sec_cusip = credit_idea_details.hedge_sec_cusip;
                    estimated_closing_date = credit_idea_details.estimated_closing_date;
                    upside_price = credit_idea_details.upside_price;
                    downside_price = credit_idea_details.downside_price;
                    comments = credit_idea_details.comments;
                    $('#analyst').val(analyst);
                    $('#deal_bucket').val(deal_bucket);
                    $('#deal_strategy_type').val(deal_strategy_type);
                    $('#catalyst').val(catalyst);
                    $('#catalyst_tier').val(catalyst_tier);
                    $('#target_sec_cusip').val(target_sec_cusip);
                    $('#coupon').val(coupon);
                    $('#hedge_sec_cusip').val(hedge_sec_cusip);
                    $('#estimated_closing_date').val(estimated_closing_date);
                    $('#upside_price').val(upside_price);
                    $('#downside_price').val(downside_price);
                    // $('#comments').summernote({'height': "400px"});
                    $('#comments').val(comments);
                    $('#idea_id_to_edit').val(idea_id_to_edit);
                },
                error: function (err) {
                    console.log(err);
                }
            });
            $('#create_new_idea_modal').modal('show');
        }
        else if (current_idea.search('delete_idea_') != -1) {
            //First Popup sweetAlert to Confirm Deletion
            idea_id_to_edit = current_idea.split('_').pop();

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Credit Idea!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../credit_idea/delete_credit_idea/',
                        data: {'id': idea_id_to_edit},
                        success: function (response) {
                            if (response === "credit_idea_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The Credit Idea has been deleted!", {icon: "success"});
                                credit_idea_table.row($("#row_" + idea_id_to_edit)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting the Credit Idea Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting the Credit Idea Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }
        else if (current_idea.search('view_idea_') != -1) {
            idea_id_to_view = current_idea.split('_').pop();
            $.ajax({
                url: "../credit_idea/get_credit_idea_details/",
                type: 'GET',
                data: {'credit_idea_id': idea_id_to_view},
                success: function (response) {
                    let credit_idea_details = response['credit_idea_details'];
                    comments = credit_idea_details.comments;
                    $('#credit_idea_view_idea').summernote({'height': "400px"});
                    $('#credit_idea_view_idea').summernote('code', comments);
                    $('#idea_id_to_edit').val(idea_id_to_edit);
                },
                error: function (err) {
                    console.log(err);
                }
            });
            $('#view_idea_modal').modal('show');
        }
    });
});
