$(document).ready(function () {

    var remove_file_ids = {BULL: [], OUR: [], BEAR: []};
    $('#ess_idea_new_deal_situation_overview').summernote();
    $('#ess_idea_new_deal_company_overview').summernote();
    var ess_idea_table = $('#ess_idea_table').DataTable({
        scrollX: true,
        scrollCollapse: true,
        scrollY: "50vh",
        fixedColumns: {
            leftColumns: 2,
            heightMatch: 'auto'
        },
        "order": [[ 17, "desc" ]],
        "pageLength": 100,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        'rowCallback': function (row, data, index) {
            if ($(row).attr('data-value') === '1') {
                $(row).css('background-color', '#ff9999');
            }
        },
        initComplete: function () {
            this.api().columns([0, 1, 2, 3, 4, 5, 6, 19]).every(function () {
                var column = this;
                $(column.header()).append("<br>");
                var select = $('<select class="custom-select form-control" ><option value=""></option></select>')
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
        columnDefs: [{
            targets: [11, 12], render: function (data)
            {
                return moment(data).format('YYYY-MM-DD');
            }
        },
        {
            targets: [8, 9, 10], render: function (data)
            {
                return parseFloat(data).toFixed(2);
            }
        },
        {
            targets: [7], render: function(data)
            {
                return Number(data).toFixed(2);
            }
        },
         { "width": "10px", "targets": 5 },],
        buttons: {
            buttons: [{
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',
                exportOptions: {
                    columns: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17 ,18, 19]
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

    $('#ess_bull_thesis').summernote({dialogsInBody: true, height: 700});
    $('#ess_our_thesis').summernote({dialogsInBody: true, height: 700});
    $('#ess_bear_thesis').summernote({dialogsInBody: true, height: 700});


// ----------------- Auto Population of GICS Sector -------------------------

    $('#ess_idea_new_deal_ticker').on('focusout', function () {
        // Get GICS Sector from Server by Passing the Ticker
        $.ajax({
            type: 'POST',
            url: '../risk/get_gics_sector',
            data: {'ticker': $('#ess_idea_new_deal_ticker').val()},
            success: function (status) {
                //Just show a Toastr here with Status
                toastr.info('Fetching from Bloomberg...', 'Populating GICS Sector!', {
                    positionClass: 'toast-top-right',
                    containerId: 'toast-top-right'
                });
                if (status != 'Failed') {
                    //Set Value of GICS field
                    $('#ess_idea_gics_sector').val(status);
                }
            },
            error: function (response) {
                toastr.error('Failed adding GICS Sector', 'Please manually Populate!', {
                    positionClass: 'toast-top-right',
                    containerId: 'toast-top-right'
                });
            }
        });
    });

//-------------- FILE UPLOAD FOR BULL, BEAR, OUR THESIS ---------------------
    function readURL(input, target) {
        var text = "";

        if (input.files && input.files[0]) {
            for (var i = 0; i < input.files.length; i++) {
                text += input.files[i].name + "<br>";
            }
            $(target).html(text);
        }

    }


    $('#bull_thesis_model').change(function () {
        readURL(this, '#edit_selected_bull_attachments');
    });

    $('#our_thesis_model').change(function () {
        readURL(this, '#edit_selected_our_attachments');
    });

    $('#bear_thesis_model').change(function () {
        readURL(this, '#edit_selected_bear_attachments');
    });

    var wrapper = $(".display_attachments");
    $(wrapper).on("click", ".remove_file", function(e){
        var index = -1;
        var file_id = $(this).attr('data-id');
        var target = ''
        if (file_id.indexOf("bull") >= 0) {
            remove_file_ids.BULL[remove_file_ids.BULL.length] = file_id.split("_").pop();
            target = '#target_bull_thesis'
        }
        else if (file_id.indexOf("our") >= 0) {
            remove_file_ids.OUR[remove_file_ids.OUR.length] = file_id.split("_").pop();
            target = '#target_our_thesis'
        }
        else if (file_id.indexOf("bear") >= 0) {
            remove_file_ids.BEAR[remove_file_ids.BEAR.length] = file_id.split("_").pop();
            target = '#target_bear_thesis'
        }
        console.log("FILE", target, remove_file_ids);
        var fileList = $(target).html().split("<br>")
        for (var i = 0; i< fileList.length; i++) {
            if (fileList[i].includes(file_id)) {
                index = i;
                break;
            }
        }
        fileList.splice(index, 1);
        fileList = fileList.join("<br>")
        $(target).html(fileList);

    });

//---------------------------------------------------------------------------


    $('#ess_idea_add_new_deal').on('click', function () {
        // $('#ess_new_deal_form')[0].reset();
        // $('#ess_bull_thesis').summernote('code','');
        // $('#ess_our_thesis').summernote('code','');
        // $('#ess_bear_thesis').summernote('code','');
        $('#ess_idea_new_deal_update_id').val('');
    });
    $('#ess_new_deal_form').on('submit', function (e) {
        e.preventDefault();

        /* Steps: Get the Fields and make an Ajax Request to Add new Deal */
        var update_id = $('#ess_idea_new_deal_update_id').val();

        if (update_id === '' || typeof update_id === undefined) {
            update_id = false;
        }
        var ticker;
        if (update_id) {
            ticker = $('#ess_idea_new_deal_ticker').val();
        }
        else {
            //Check if Index is present in Ticker (If present, don't append Equity else Append Equity only if Equity isn't already present
            var value = $('#ess_idea_new_deal_ticker').val();

            if (value.search("Index") != -1 || value.search('index') != -1 || value.search('INDEX') != -1 || value.search('Equity') != -1 || value.search('EQUITY') != -1 || value.search('equity') != -1) {
                ticker = $('#ess_idea_new_deal_ticker').val()
            }
            else {
                ticker = $('#ess_idea_new_deal_ticker').val() + " EQUITY";
            }


        }
        var tradegroup = $('#ess_idea_new_deal_tradegroup').val();

        let pt_up_check = 'No';
        let pt_down_check = 'No';   //Set default adjustments to False
        let pt_wic_check = 'No';

        //Check if Prices are to be adjusted automatically
        if ($('#pt_up_check').is(':checked')) {
            pt_up_check = 'Yes';
        }
        if ($('#pt_down_check').is(':checked')) {
            pt_down_check = 'Yes';
        }
        if ($('#pt_wic_check').is(':checked')) {
            pt_wic_check = 'Yes';
        }


        var situation_overview = $('#ess_idea_new_deal_situation_overview').summernote('code');
        var company_overview = $('#ess_idea_new_deal_company_overview').summernote('code');
        var pt_up = $('#ess_idea_new_deal_pt_up').val();
        var pt_down = $('#ess_idea_new_deal_pt_down').val();
        var pt_wic = $('#ess_idea_new_deal_pt_wic').val();
        var unaffected_date = $('#ess_idea_new_deal_unaffected_date').val();
        var expected_close = $('#ess_idea_new_deal_expected_close').val();
        var cix_index = $('#ess_idea_new_deal_cix_index').val();
        var price_target_date = $('#ess_idea_new_deal_price_target_date').val();
        var category = $('#ess_category_select').val();
        var catalyst = $('#ess_catalyst_select').val();
        var deal_type = $('#ess_deal_type').val();
        var lead_analyst = $('#ess_idea_lead_analyst').val();

        // Hedge-Ticker is a table. Iterate through each element and save in an dictionary
        var ticker_hedge = []; //create an empty array
        var multiples = [];

        if (update_id) {
            $('#ess_hedge_ticker_table tr').each(function () {
                //do your stuff, you can use $(this) to get current cell
                var fields = $(this).find(':input');
                var ticker = fields.eq(0).val();
                var hedge_weight = fields.eq(1).val();
                if (!(ticker === undefined || ticker === "")) {
                    // Header Row might cause undefined values. Hence check here first
                    ticker_hedge.push({
                        ticker: ticker,
                        hedge: hedge_weight
                    });
                }

            });
            let multiples_dict = {};
            $('#ess_idea_multiples_table tr').each(function () {
                //do your stuff, you can use $(this) to get current cell
                var fields = $(this).find(':input');
                var multiple = fields.eq(0).val();
                var weight = fields.eq(1).val();
                if (!(multiple === undefined || multiple === "")) {
                    // Header Row might cause undefined values. Hence check here first
                    multiples_dict[multiple] = weight;
                }
                multiples.push(multiples_dict);

            });


        }

        else {
            $('#ess_hedge_ticker_table tr').each(function () {
                //do your stuff, you can use $(this) to get current cell
                var fields = $(this).find(':input');
                var ticker = fields.eq(0).val();
                var hedge_weight = fields.eq(1).val();
                if (!(ticker === undefined || ticker === "")) {
                    // Header Row might cause undefined values. Hence check here first
                    if (ticker.search("Index") != -1 || ticker.search('index') != -1 || ticker.search('INDEX') != -1 || ticker.search('Equity') != -1 || ticker.search('EQUITY') != -1 || ticker.search('equity') != -1) {
                        ticker = ticker
                    }
                    else {
                        ticker = ticker + " EQUITY"
                    }

                    ticker_hedge.push({
                        ticker: ticker,
                        hedge: hedge_weight
                    });
                }

            });

            let multiples_dict = {}

            $('#ess_idea_multiples_table tr').each(function () {
                //do your stuff, you can use $(this) to get current cell
                var fields = $(this).find(':input');
                var multiple = fields.eq(0).val();
                var weight = fields.eq(1).val();
                if (!(multiple === undefined || multiple === "")) {
                    // Header Row might cause undefined values. Hence check here first
                    multiples_dict[multiple] = weight;
                }
                multiples.push(multiples_dict);
            });

        }


        var multiples_length = multiples.length;
        var peers_length = ticker_hedge.length;
        // Get Summernote Data
        var bull_thesis = $('#ess_bull_thesis').summernote('code').toString();
        var our_thesis = $('#ess_our_thesis').summernote('code').toString();
        var bear_thesis = $('#ess_bear_thesis').summernote('code').toString();


        // Now get the MOSAIC Rating
        var m_value = $('#ess_M_select').val();
        var o_value = $('#ess_O_select').val();
        var s_value = $('#ess_S_select').val();
        var a_value = $('#ess_A_select').val();
        var i_value = $('#ess_I_select').val();
        var c_value = $('#ess_C_select').val();

        // MOSAIC Overview
        var m_overview = $('#ess_M_overview').val();
        var o_overview = $('#ess_O_overview').val();
        var s_overview = $('#ess_S_overview').val();
        var a_overview = $('#ess_A_overview').val();
        var i_overview = $('#ess_I_overview').val();
        var c_overview = $('#ess_C_overview').val();

        var catalyst_tier = $('#ess_catalyst_tier_select').val();
        var hedges = $('#ess_hedges_select').val();
        var gics_sector = $('#ess_idea_gics_sector').val();

        var data = new FormData();
        var bull_thesis_model_file = $('#bull_thesis_model')[0].files;
        var our_thesis_model_file = $('#our_thesis_model')[0].files;
        var bear_thesis_model_file = $('#bear_thesis_model')[0].files;

        for (var i = 0; i < bull_thesis_model_file.length; i++) {
            var file = bull_thesis_model_file[i];

            data.append('filesBullThesis[]', file, file.name);
        }

        for (var i = 0; i < our_thesis_model_file.length; i++) {
            var file = our_thesis_model_file[i];

            data.append('filesOurThesis[]', file, file.name);
        }

        for (var i = 0; i < bear_thesis_model_file.length; i++) {
            var file = bear_thesis_model_file[i];

            data.append('filesBearThesis[]', file, file.name);
        }


        var ess_idea_status = $('#ess_idea_status').val();

        let adjust_based_off = $('#select_based_off').val();
        let premium_format = $('#premium_format').val();

        // ------- Append All Data --------------------------------

        // data.append('bull_thesis_model_file', bull_thesis_model_file);
        // data.append('our_thesis_model_file', our_thesis_model_file);
        // data.append('bear_thesis_model_file', bear_thesis_model_file);
        data.append('update_id', update_id);
        data.append('tradegroup', tradegroup);
        data.append('ticker', ticker);
        data.append('situation_overview', situation_overview);
        data.append('company_overview', company_overview);
        data.append('pt_up', pt_up);
        data.append('pt_down', pt_down);
        data.append('pt_wic', pt_wic);
        data.append('unaffected_date', unaffected_date);
        data.append('expected_close', expected_close);
        data.append('bull_thesis', bull_thesis);
        data.append('our_thesis', our_thesis);
        data.append('bear_thesis', bear_thesis);
        data.append('ticker_hedge', JSON.stringify(ticker_hedge));
        data.append('cix_index', cix_index);
        data.append('price_target_date', price_target_date);
        data.append('multiples', JSON.stringify(multiples));
        data.append('m_value', m_value);
        data.append('o_value', o_value);
        data.append('s_value', s_value);
        data.append('a_value', a_value);
        data.append('i_value', i_value);
        data.append('c_value', c_value);
        data.append('i_value', i_value);
        data.append('m_overview', m_overview);
        data.append('o_overview', o_overview);
        data.append('s_overview', s_overview);
        data.append('a_overview', a_overview);
        data.append('i_overview', i_overview);
        data.append('c_overview', c_overview);
        data.append('peers_length', peers_length);
        data.append('multiples_length', multiples_length);
        data.append('category', category);
        data.append('catalyst', catalyst);
        data.append('deal_type', deal_type);
        data.append('lead_analyst', lead_analyst);
        data.append('catalyst_tier', catalyst_tier);
        data.append('hedges', hedges);
        data.append('gics_sector', gics_sector);
        data.append('ess_idea_status', ess_idea_status);
        data.append('pt_up_check', pt_up_check);
        data.append('pt_down_check', pt_down_check);
        data.append('pt_wic_check', pt_wic_check);
        data.append('adjust_based_off', adjust_based_off);
        data.append('premium_format', premium_format);
        data.append('remove_file_ids', JSON.stringify(remove_file_ids));
        // // Done getting all Fields. Now POST via AJAX and get Response. If response is success, inserting the row (from response) into the Existing DataTable and Redraw it

        $.ajax({
            type: 'POST',
            url: '../risk/add_new_ess_idea_deal',
            data: data,
            processData: false,
            contentType: false,
            success: function (response) {
                var block_ele = $('.content-body');
                $(block_ele).block({
                    message: '<div class="semibold"><span class="ft-refresh-cw icon-spin text-left"></span>&nbsp;Please wait while your deal calculation completes...Do not hit Refresh or press the Back button!!!</div>',
                    fadeIn: 1000,
                    fadeOut: 1000,
                    timeout: 180000, //unblock after 3 minutes
                    overlayCSS: {
                        backgroundColor: '#fff',
                        opacity: 0.8,
                        cursor: 'wait'
                    },
                    css: {
                        border: 0,
                        padding: '10px 15px',
                        color: '#fff',
                        width: 'auto',
                        backgroundColor: '#333'
                    }
                });

                let task_id = response['task_id'];
                if (task_id === 'Error') {
                    display_error_message()
                }
                else {
                    $('#ess_idea_new_deal_modal').modal('hide');
                    $('body').removeClass('modal-open');
                    $('.modal-backdrop').remove();
                }

                let progress_url = "../../celeryprogressmonitor/get_celery_task_progress?task_id=" + task_id.toString();

                function reload_page() {
                    $(block_ele).unblock(); // Release the Lock
                    swal("Success! The IDEA has been added!", {icon: "success"}).then((value) => {
                        location.reload();
                    });
                }

                function display_error_message() {
                    $(block_ele).unblock(); // Release the Lock
                    swal("Error!", "Adding Deal Failed!. Please check the inputs", "error");
                }


                $(function () {
                    CeleryProgressBar.initProgressBar(progress_url, {
                        onSuccess: reload_page,
                        onError: display_error_message,
                        pollInterval: 2000,

                    })
                });
            },

            error: function (response) {
                swal("Error!", "Adding Deal Failed!. Please check the inputs", "error");
            }
        });


    });


    function get_celery_status(task_id) {
        $.ajax({
            type: 'POST',
            url: '../risk/get_ess_idea_celery_status',
            data: {'id': task_id},
            success: function (status) {
                //Just show a Toastr here with Status

                if (status === 'FAILURE') {
                    toastr.error('Could not add IDEA. Please re-check parameters!', 'IDEA Failed!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });

                }
                else if (status === 'SUCCESS') {
                    toastr.success('Please refresh the page to view!', 'New Deal Successfully Added!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    toastr.warning('Please refresh the page in a while!', 'New Deal Still being added!', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }


            },

            error: function (response) {
                swal("Error!", "Adding Deal Failed!. Please check the inputs", "error");
            }
        });


        return task_id;
    }

    /** HANDLE DELETION FOR A GIVEN DEAL **/
    $('.table-responsive').on("click", "#ess_idea_table tr td li a", function () {

        var current_deal = this.id.toString();
        var csrfmiddlewaretoken = $('#ess_idea_csrf_token').val();
        // Handle Selected Logic Here
        if (current_deal.search('edit_') != -1) {

            remove_file_ids = {BULL: [], OUR: [], BEAR: []};
            $('#edit_selected_bull_attachments').empty();
            $('#target_bull_thesis').empty();
            $('#edit_selected_our_attachments').empty();
            $('#target_our_thesis').empty();
            $('#edit_selected_bear_attachments').empty();
            $('#target_bear_thesis').empty();
            //Logic for Editing a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            var deal_id_to_edit = current_deal.split('_')[1]; //Get the ID
            
            $.ajax({
                url:"../risk/get_attachments/",
                type:'POST',
                data:{'deal_id': deal_id_to_edit},
                success:function(response){
                    let bull_attachments = response['bull_attachments'];
                    if(bull_attachments.length > 0) {
                        let files = "";
                        for(var i=0; i<bull_attachments.length; i++){
                            let bull_attachment = bull_attachments[i];
                            files += "<a href=" + bull_attachment.url + ">" + bull_attachment.filename + "</a> <a class='remove_file' data-id='remove_bull_" + deal_id_to_edit + "_file_" + bull_attachment.id + "' href='#'><i class='ft-trash-2'></i></a><br />";
                        }
                        $('#target_bull_thesis').html(files);
                    }
                    let our_attachments = response['our_attachments'];
                    if(our_attachments.length > 0) {
                        let files = "";
                        for(var i=0; i<our_attachments.length; i++){
                            let our_attachment = our_attachments[i];
                            files += "<a href=" + our_attachment.url + ">" + our_attachment.filename + "</a> <a class='remove_file' data-id='remove_our_" + deal_id_to_edit + "_file_" + our_attachment.id + "' href='#'><i class='ft-trash-2'></i></a><br />";
                        }
                        $('#target_our_thesis').html(files);
                    }
                    let bear_attachments = response['bear_attachments'];
                    if(bear_attachments.length > 0) {
                        let files = "";
                        for(var i=0; i<bear_attachments.length; i++){
                            let bear_attachment = bear_attachments[i];
                            files += "<a href=" + bear_attachment.url + ">" + bear_attachment.filename + "</a> <a class='remove_file' data-id='remove_bear_" + deal_id_to_edit + "_file_" + bear_attachment.id + "' href='#'><i class='ft-trash-2'></i></a><br />";
                        }
                        $('#target_bear_thesis').html(files);
                    }
                },
                error: function (err) {
                    console.log(err);
                }
             });
            
            $.ajax({
                url: "edit_ess_deal",
                method: "POST",
                data: {
                    'deal_id': deal_id_to_edit,
                    'prepopulation_request': true,
                    'csrfmiddlewaretoken': csrfmiddlewaretoken
                },
                success: function (response) {
                    let deal_object = response['deal_object'][0];
                    let bull_thesis_files = response['bull_thesis_files'];
                    let our_thesis_files = response['our_thesis_files'];
                    let bear_thesis_files = response['bear_thesis_files'];

                    let latest_upside = response['latest_upside'];
                    let latest_wic = response['latest_wic'];
                    let latest_downside = response['latest_downside'];
                    latest_downside = "Model : " + "<strong>"+parseFloat(latest_downside).toFixed(2).toString()+"</strong>";
                    latest_wic = "Model : " + "<strong>"+ parseFloat(latest_wic).toFixed(2).toString()+"</strong>";
                    latest_upside = "Model : " + "<strong>"+ parseFloat(latest_upside).toFixed(2).toString()+"</strong>";

                    $('#latest_model_downside').html(latest_downside.trim());
                    $('#latest_model_upside').html(latest_upside.trim());
                    $('#latest_model_wic').html(latest_wic.trim());

                    // clear the Ticker Hedge Table
                    $('#ess_new_deal_form').trigger('reset');
                    console.log(deal_object);
                    let related_peers_length = response['related_peers'].length;
                    // Get all Required Fields

                    $('#select_based_off').val(deal_object.how_to_adjust);
                    $('#premium_format').val(deal_object.premium_format);

                    //If adjustments are not null and contains Yes then check it
                    if (deal_object.pt_up_check != null && deal_object.pt_up_check === 'Yes') {
                        $('#pt_up_check').prop('checked', true);
                    }
                    else {
                        $('#pt_up_check').prop('checked', false);
                    }

                    if (deal_object.pt_down_check != null && deal_object.pt_down_check === 'Yes') {
                        $('#pt_down_check').prop('checked', true);
                    }
                    else {
                        $('#pt_down_check').prop('checked', false);
                    }

                    if (deal_object.pt_wic_check != null && deal_object.pt_wic_check === 'Yes') {
                        $('#pt_wic_check').prop('checked', true);
                    }
                    else {
                        $('#pt_wic_check').prop('checked', false);
                    }

                    let multiples_dict = JSON.parse(response['multiples_dict']);

                    //Now    Get all the Peers
                    let related_peers = response['related_peers'];

                    // Fill Values in the Modal and Then OPEN the Modal
                    $('#ess_idea_new_deal_tradegroup').val(deal_object.tradegroup);
                    $('#ess_idea_new_deal_ticker').val(deal_object.alpha_ticker);
                    $('#ess_idea_new_deal_situation_overview').summernote('code', deal_object.situation_overview);
                    $('#ess_idea_new_deal_company_overview').summernote('code', deal_object.company_overview);
                    $('#ess_idea_new_deal_pt_up').val(parseFloat(deal_object.pt_up).toFixed(2));
                    $('#ess_idea_new_deal_pt_down').val(parseFloat(deal_object.pt_down).toFixed(2));
                    $('#ess_idea_new_deal_pt_wic').val(parseFloat(deal_object.pt_wic).toFixed(2));
                    $('#ess_idea_new_deal_unaffected_date').val(deal_object.unaffected_date);
                    $('#ess_idea_new_deal_expected_close').val(deal_object.expected_close);
                    $('#ess_bull_thesis').summernote('code', deal_object.bull_thesis);
                    $('#ess_our_thesis').summernote('code', deal_object.our_thesis);
                    $('#ess_bear_thesis').summernote('code', deal_object.bear_thesis);
                    $('#ess_M_select').val(deal_object.m_value);
                    $('#ess_O_select').val(deal_object.o_value);
                    $('#ess_S_select').val(deal_object.s_value);
                    $('#ess_A_select').val(deal_object.a_value);
                    $('#ess_I_select').val(deal_object.i_value);
                    $('#ess_C_select').val(deal_object.c_value);
                    // Overviews
                    $('#ess_M_overview').val(deal_object.m_overview);
                    $('#ess_O_overview').val(deal_object.o_overview);
                    $('#ess_S_overview').val(deal_object.s_overview);
                    $('#ess_A_overview').val(deal_object.a_overview);
                    $('#ess_I_overview').val(deal_object.i_overview);
                    $('#ess_C_overview').val(deal_object.c_overview);
                    $('#ess_idea_new_deal_update_id').val(deal_object.id);
                    $('#ess_idea_new_deal_cix_index').val(deal_object.cix_index);
                    $('#ess_idea_new_deal_price_target_date').val(deal_object.price_target_date);
                    //Add category


                    $('#ev_sales_weight').val(multiples_dict[0]['EV/Sales']);
                    $('#ev_ebitda_weight').val(multiples_dict[1]['EV/EBITDA']);
                    $('#p_eps_weight').val(multiples_dict[2]['P/EPS']);
                    $('#dvd_yield_weight').val(multiples_dict[3]['DVD yield']);
                    $('#fcf_yield_weight').val(multiples_dict[4]['FCF yield']);


                    $('#ess_category_select').val(deal_object.category);
                    $('#ess_catalyst_select').val(deal_object.catalyst);
                    $('#ess_deal_type').val(deal_object.deal_type);

                    $('#ess_catalyst_tier_select').val(deal_object.catalyst_tier);
                    $('#ess_idea_gics_sector').val(deal_object.gics_sector);
                    $('#ess_hedges_select').val(deal_object.hedges);
                    $('#ess_idea_status').val(deal_object.status);
                    $('#ess_idea_lead_analyst').val(deal_object.lead_analyst);


                    // Adjust Peers
                    for (var i = 0; i < related_peers_length; i++) {
                        $('#ticker_hedge_' + (i + 1) + '_ticker').val(related_peers[i][2]);
                        $('#ticker_hedge_' + (i + 1) + '_hedge').val(related_peers[i][3]);  // i+1 is done since row numbering starts with 1 in html
                    }

                    $('#ess_idea_new_deal_modal').modal('show');

                },
                error: function (err_response) {
                    swal("Error!", "Updating Deal Failed!. Please check the inputs", "error");
                }
            });


        }
        else if (current_deal.search('delete_') != -1) {
            //Logic for Deleting a deal
            //First Popup sweetAlert to Confirm Deletion

            let deal_id_to_delete = current_deal.split('_')[1];
            let delete_all_versions = 'false';

            // Send this Deal key to Django View to Delete and Wait for Response. If Response is successful, then Delete the row from DataTable
            
            swal({
                title: "Please select one option",
                icon: "warning",
                className: 'delete-swal-wide',
                buttons: {
                    cancel: {
                        text: "Cancel",
                        visible: true,
                        closeModal: true,
                        value: 0,
                    },
                    delete_current: {
                        text: "Delete Selected Version",
                        visible: true,
                        closeModal: false,
                        value: 1
                    },
                    delete_all: {
                        text: "Delete All Versions",
                        visible: true,
                        closeModal: false,
                        value: 2
                    }
                },
                dangerMode: true,
            }).then(value => {
                switch (value) {
                    case 0:
                        break;
                    case 1:
                        delete_all_versions = 'false';
                        delete_ess_idea(deal_id_to_delete, delete_all_versions);
                        break;
                    case 2:
                        delete_all_versions = 'true';
                        delete_ess_idea(deal_id_to_delete, delete_all_versions);
                        break;
                }
            });
        }
        else {
            //Logic to View the Deal
            //Just take the URL and redirect to the page. Front-end handling
            let idea_to_view = current_deal.split('_')[1];
            window.open("../risk/show_ess_idea?ess_idea_id=" + idea_to_view, '_blank');
            return false;
        }

        function delete_ess_idea(deal_id, delete_all_versions) {
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
                        url: '../risk/delete_ess_idea',
                        data: {'id': deal_id, 'delete_all_versions': delete_all_versions},
                        success: function (response) {
                            if (response === "all_ess_idea_deleted") {
                                //Delete Row from DataTable
                                swal("Success! All the versions of the selected IDEA has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                ess_idea_table.row($("#row_" + deal_id)).remove().draw();
    
                            }
                            else if (response === "selected_ess_idea_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The IDEA has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                ess_idea_table.row($("#row_" + deal_id)).remove().draw();
    
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
