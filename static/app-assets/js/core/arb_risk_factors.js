$(document).ready(function(){

    function checkDateFields(required_target, expected_target, actual_target) {
        if ($(required_target).val() == 'Not required') {
            $(expected_target).prop("disabled", true);
            $(actual_target).prop("disabled", true);
            $(expected_target).val("");
            $(actual_target).val("");
        }
        else {
            $(expected_target).prop("disabled", false);
            $(actual_target).prop("disabled", false);
        }
    }

    checkDateFields('#sec_required', '#expected_sec', '#actual_sec')
    checkDateFields('#hsr_required', '#expected_hsr', '#actual_hsr')
    checkDateFields('#mofcom_required', '#expected_mofcom', '#actual_mofcom')
    checkDateFields('#cfius_required', '#expected_cfius', '#actual_cfius')
    checkDateFields('#ec_required', '#expected_ec', '#actual_ec')
    checkDateFields('#accc_required', '#expected_accc', '#actual_accc')
    checkDateFields('#canada_required', '#expected_canada', '#actual_canada')
    checkDateFields('#cade_required', '#expected_cade', '#actual_cade')

    $('#sec_required').on('click', function () {
        checkDateFields('#sec_required', '#expected_sec', '#actual_sec')
    });

    $('#hsr_required').on('click', function () {
        checkDateFields('#hsr_required', '#expected_hsr', '#actual_hsr')
    });

    $('#mofcom_required').on('click', function () {
        checkDateFields('#mofcom_required', '#expected_mofcom', '#actual_mofcom')
    });

    $('#cfius_required').on('click', function () {
        checkDateFields('#cfius_required', '#expected_cfius', '#actual_cfius')
    });

    $('#ec_required').on('click', function () {
        checkDateFields('#ec_required', '#expected_ec', '#actual_ec')
    });

    $('#accc_required').on('click', function () {
        checkDateFields('#accc_required', '#expected_accc', '#actual_accc')
    });

    $('#canada_required').on('click', function () {
        checkDateFields('#canada_required', '#expected_canada', '#actual_canada')
    });

    $('#cade_required').on('click', function () {
        checkDateFields('#cade_required', '#expected_cade', '#actual_cade')
    });

    $(document).on("click", "button", function () {
        var button_id = this.id;
        if (button_id.includes("edit_action_id_")) {
            var deal_id = button_id.split("_").pop()
            var title = "Update Action ID";
            var text = "Enter the value for action ID for deal ID " + deal_id.toString();
            var success = "The action ID has been updated to "
            swal({
                title: title,
                text: text,
                content: 'input',
                buttons: ["Cancel",
                    {text: "Save", closeModal: false}],
            }).then((action_id) => {
                if (action_id) {
                    $.ajax({
                        type: 'POST',
                        url: '../risk/edit_mna_idea_action_id',
                        data: {'deal_id': deal_id, 'action_id': action_id},
                        success: function (response) {
                            console.log(response);
                            if (response.error == false) {
                                $("#action_id_value").html(action_id);
                                swal("Success! " + success + action_id + " for " + deal_id.toString(), {icon: "success"});
                                location.reload();
                            }
                            else if (response.type == 'ma_deal'){
                                swal("Error!", "The action ID could not be updated", "error");
                                console.log('Updation failed', deal_id, action_id);
                            }
                            else if (response.type == 'action_id'){
                                swal("Error!", "The action ID is updated but there was a problem fetching data from Bloomberg API", "warning");
                                console.log('Fetching Bloomberg data failed', deal_id, action_id);
                            }
                            else if (response.type == 'same_action_id'){
                                swal("Same Action ID!", "OOPS! You forgot to change the Action ID value", "error");
                                console.log('Same Action ID', deal_id, action_id);
                            }
                            else if (response.type == 'duplicate_action_id'){
                                swal("Duplicate Action ID!", "The action ID already exists in the database", "error");
                                console.log('Duplicate Action ID', deal_id, action_id);
                            }
                            else {
                                swal("Error!", "Some error occurred", "error");
                                console.log('Error in updating action id', deal_id, action_id);
                            }
                        },
                        error: function (error) {
                            swal("Error!", "The action ID could not be updated", "error");
                            console.log(error, deal_id, action_id);
                        }
                    });

                }
            });
        }
    });
});