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
});