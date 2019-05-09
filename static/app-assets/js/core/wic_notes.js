$(document).ready(function () {

    var file = "";
    var ticker_index = -1;
    var selectedTickerValue = "";
    var selected_ticker_list = {};

    var options = {
        url: function(phrase) {
          return "../search/";
        },
        getValue: function(element) {
          return element;
        },
        list: {
            maxNumberOfElements: 10,
            onSelectItemEvent: function() {
                selectedTickerValue = $("#wic_notes_tickers").val();
            },
            onClickEvent: function() {
                ticker_index += 1;
                $("#wic_notes_tickers").val();
                file = $('#wic_notes_tickers_id').html();
                selected_ticker_list[ticker_index] = selectedTickerValue;
                file += "<big class='badge badge-pill badge-info'>" + selectedTickerValue + " <a class='remove_ticker' data-id='remove_ticker_" + ticker_index.toString() +
                        "' href='#'><i class='ft-trash-2'></i></a></big>  "
                $("#wic_notes_tickers_id").html(file);
                var requiredElement = document.getElementById("wic_notes_tickers_id");
                if (requiredElement.innerHTML.trim().length > 0) {
                    if ($("#wic_notes_tickers").parent().next().attr('class') == 'ticker_error_div') {
                        $("#wic_notes_tickers").parent().next().css("display", "none");
                    }
                    document.getElementById("wic_notes_tickers_div").style.display = "block";
                    $("#wic_notes_tickers").removeAttr("required");
                }
                else {
                    document.getElementById("wic_notes_tickers_div").style.display = "none";
                    if (document.getElementById("tickerCheckbox").checked) {
                        $("#wic_notes_tickers").removeAttr("required");
                    }
                    else {
                        $("#wic_notes_tickers").prop("required", true);
                    }
                }
            }
        },
        ajaxSettings: {
          dataType: "json",
          method: "POST",
          data: {dataType: "json"}
        },
        preparePostData: function(data) {
          data.phrase = $("#wic_notes_tickers").val();
          return data;
        },
        requestDelay: 400
    };
    $("#wic_notes_tickers").easyAutocomplete(options)

    $('.tickerCheckbox').on("click", function () {
        var checkBox = document.getElementById("tickerCheckbox");
        var text = document.getElementById("wic_notes_other_tickers_div");
        if (checkBox.checked == true){
            text.style.display = "block";
            $("#wic_notes_tickers").removeAttr("required");
            $("#wic_notes_other_tickers").prop('required', true);
        } else {
            text.style.display = "none";
            $("#wic_notes_tickers").prop('required', true);
            $("#wic_notes_other_tickers").removeAttr("required");
        }
    });

    var remove_file_ids = [];

    //Create a Datatable out of retrieved Values
    var wic_notes_table = $('#wic_notes_table').DataTable({
        columnDefs: [{
            targets: [0], render: function (data) {
                return moment(data).format('YYYY-MM-DD');
            }
        }],
        "aaSorting": [[0,'desc']],
        "pageLength": 25,
    });
    $('#wic_note_article').summernote({'height': '450px'});

    $('#submit_wic_notes_form').on('submit', function (e) {
        var continue_form_submit = true;
        if ($("#wic_notes_tickers").parent().next().attr('class') == 'ticker_error_div') {
            $("#wic_notes_tickers").parent().next().css("display", "none");
        }
        if (document.getElementById("tickerCheckbox").checked == false) {
            var requiredElement = document.getElementById("wic_notes_tickers_id");
            if (requiredElement.innerHTML.trim().length == 0) {
                $("#wic_notes_tickers").parent().after("<div class='ticker_error_div' "+
                    "style='color:red;margin-bottom: 20px;'>Please select a ticker from the search bar. If you can not find it, click on `Other Tickers` checkbox and type it there.</div>");
                e.preventDefault();
                continue_form_submit = false;
            }
        }
        if (continue_form_submit == true) {
            e.preventDefault(); //to Stop from Refreshing
            //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
            swal({
                title: "Saving",
                text: "Hold on!",
                buttons: false,
                icon: "info",
                closeOnClickOutside: false,
            });
            var article = $('#wic_note_article').summernote('code');
            var date = $('#wic_notes_date').val();
            var title = $('#wic_notes_title').val();
            var author = $('#wic_notes_author').val();
            var tickers = "";
            var ticker_list = [];
            var keys = Object.keys(selected_ticker_list);
            keys.forEach(function(key){
                ticker_list.push(selected_ticker_list[key].trim());
            });
            tickers = ticker_list.join(", ");
            var other_tickers = $('#wic_notes_other_tickers').val();
            var all_tickers = "";
            if (tickers != "" && other_tickers != "") {
                all_tickers = tickers + ", " + other_tickers
            }
            else if (tickers != "") {
                all_tickers = tickers;
            }
            else {
                all_tickers = other_tickers;
            }
            var emails = $('#wic_notes_emails').val();
            var csrf_token = $('#wic_notes_csrf_token').val();

            var data = new FormData();
            var notes_files = $('#notes_attachments_model')[0].files;

            for (var i = 0; i < notes_files.length; i++) {
                var file = notes_files[i];
                data.append('filesNotes[]', file, file.name);
            }
            data.append('article', article);
            data.append('date', date);
            data.append('title', title);
            data.append('author', author);
            data.append('tickers', tickers);
            data.append('other_tickers', other_tickers);
            data.append('emails', emails);

            //POST The Data to be Inserted into the Database

            $.ajax({
                type: 'POST',
                url: '../notes/create_note/',
                processData: false,
                contentType: false,
                data: data,
                success: function (response) {
                    $('#wic_notes_modal').modal('hide');
                    $('body').removeClass('modal-open');
                    $('.modal-backdrop').remove();
                    // Reset the Notes Submission Form
                    // Reset the SummerNote
                    $('#wic_note_article').summernote('code', '');

                    if (response.note_created == 'false') {
                        swal("Error!", "Adding Note Failed!", "error");
                    }
                    else if (response.note_created == 'true') {
                        var monthNames = ["Jan", "Feb", "March", "April", "May", "June",
                            "July", "August", "Sept", "Oct", "Nov", "Dec"
                        ];
                        //Response was Success. Append this row to the Existing DataTable
                        var date_split = date.split('-');
                        var year = date_split[0];
                        var month = date_split[1];
                        var day = date_split[2];
                        var newRow = '<tr id="row_' + response.notes_id + '"><td>' + monthNames[month - 1] + ' ' + day + ', ' + year + '</td>' + '<td>' + title + '</td>' + '<td>' + author + '</td>' + '<td>' + all_tickers + '</td>' +
                            '<td><div class="btn-group">' +
                            '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                            '<i class="ft-settings"></i>' +
                            '</button>' +
                            '<ul class="dropdown-menu">' +
                            '<li><a id="edit_' + response.notes_id + '" data-value=' + response.notes_id + ' class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                            '<li><a id="delete_' + response.notes_id + '" data-value=' + response.notes_id + ' class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                            '<li><a id="view_' + response.notes_id + '" data-value=' + response.notes_id + ' class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
                            '</ul>' +
                            '</div></td></tr>';

                        //Re-initialize Datatable again
                        wic_notes_table.row.add($(newRow)).draw();
                        if (response.email_sent == 'false') {
                            swal("Email not sent", "Your note has been saved but email has not been sent to the recipients.", "warning");
                        }
                        else {
                            swal("Good job! " + author, "Your note has been saved.", "success");
                        }
                    }


                },
                error: function (err_response) {
                    console.log(err_response + ' in wic_notes.js while trying to save new Notes Item');
                }

            });
        }
    });

    /* Function to delete a Note Item */
    // Event Delegation for Dynamically added elements

    $('.table-responsive').on("click", "#wic_notes_table tr td li a", function () {

        var current_note = this.id.toString();
        // Handle Selected Logic Here
        if (current_note.search('edit_') != -1) {
            //Logic for Editing a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response.
            // Display success Alert
            var notes_id_to_edit = current_note.split('_')[1]; //Get the ID
            remove_file_ids = [];
            $('#submit_wic_notes_edit_form').trigger('reset');
            $('#edit_selected_notes_attachments').empty();
            $('#edit_notes_attachments').empty();

            var date = '';
            var title = '';
            var author = '';
            var article = '';
            var tickers = '';
            $('#edit_selected_notes_attachments').text('');
            // Collect Note Details and Attachments through Ajax
            $.ajax({
                url: "../notes/get_note_details/",
                type: 'POST',
                data: {'notes_id': notes_id_to_edit},
                success: function (response) {
                    let attachments = response['attachments'];
                    let note_details = response['note_details'];
                    if (attachments.length > 0) {
                        let files = "";
                        for (var i = 0; i < attachments.length; i++) {
                            files += "<a href=" + attachments[i].url + " target='_blank'>" + attachments[i].filename +
                                     "</a> <a class='remove_file' data-id='remove_notes_" + notes_id_to_edit +
                                     "_file_" + attachments[i].id + "' href='#'><i class='ft-trash-2'></i></a><br />";
                        }
                        $('#edit_notes_attachments').html(files);
                    }
                    date = moment(new Date(note_details.date)).format('YYYY-MM-DD');
                    tickers = note_details.tickers;
                    author = note_details.author;
                    article = note_details.article;
                    title = note_details.title;
                    $('#wic_notes_edit_id').val(notes_id_to_edit);
                    $('#wic_notes_edit_date').val(date.toString()); //Todo: Date not setting
                    $('#wic_notes_edit_title').val(title);
                    $('#wic_notes_edit_author').val(author);
                    $('#wic_notes_edit_article').summernote({'height': "400px"});
                    $('#wic_notes_edit_article').summernote('code', article);
                    $('#wic_notes_edit_tickers').val(tickers);
                },
                error: function (err) {
                    console.log(err);
                }
            });

            // Display the Modal
            $('#wic_note_edit_modal').modal('show');

        }
        else if (current_note.search('delete_') != -1) {
            //Logic for Deleting a deal
            //First Popup sweetAlert to Confirm Deletion

            notes_id_to_edit = current_note.split('_')[1];

            // Send this Deal key to Django View to Delete and Wait for Response. If Response is successful, then Delete the row from DataTable

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this Note!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../notes/delete_note/',
                        data: {'id': notes_id_to_edit, 'csrfmiddlewaretoken': $('#wic_notes_csrf_token').val()},
                        success: function (response) {
                            if (response === "wic_note_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The Note has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                wic_notes_table.row($("#row_" + notes_id_to_edit)).remove().draw();

                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Note Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Note Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }
        else {
            //Logic to View the Deal
            //Just take the URL and redirect to the page. Front-end handling
            $('#view_notes_attachments').empty();
            var note_to_view = current_note.split('_')[1];

            $.ajax({
                url: "../notes/get_note_details/",
                type: 'POST',
                data: {'notes_id': note_to_view},
                success: function (response) {
                    let attachments = response['attachments'];
                    let note_details = response['note_details'];
                    if (attachments.length > 0) {
                        let files = "";
                        for (var i = 0; i < attachments.length; i++) {
                            files += "<a href=" + attachments[i].url + " target='_blank'>" + attachments[i].filename + "</a><br />";
                        }
                        $('#view_notes_attachments').html(files);
                    }
                    var article = note_details.article;
                    $('#wic_note_view_article').summernote({'height': "400px"});
                    $('#wic_note_view_article').summernote('code', article);
                },
                error: function (err) {
                    console.log(err);
                }
            });
            $('#wic_notes_view_modal').modal('show');
        }
    });


    /* EDITING CURRENT Notes ITEM */
    $('#submit_wic_notes_edit_form').on('submit', function (e) {
        e.preventDefault(); //to Stop from Refreshing
        //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
        swal({
            title: "Saving",
            text: "Hold on!",
            buttons: false,
            icon: "info",
            closeOnClickOutside: false,
        });
        var id = $('#wic_notes_edit_id').val();
        var article = $('#wic_notes_edit_article').summernote('code').toString();
        var date = $('#wic_notes_edit_date').val();
        var title = $('#wic_notes_edit_title').val();
        var author = $('#wic_notes_edit_author').val();
        var tickers = $('#wic_notes_edit_tickers').val();

        //POST The Data to be Inserted into the Database
        var data = new FormData();
        var notes_files = $('#edit_notes_attachments_model')[0].files;
        console.log(notes_files);
        for (var i = 0; i < notes_files.length; i++) {
            var file = notes_files[i];
            data.append('filesNotes[]', file, file.name);
        }
        data.append('remove_file_ids', remove_file_ids)
        data.append('id', id);
        data.append('article', article);
        data.append('date', date);
        data.append('title', title);
        data.append('author', author);
        data.append('tickers', tickers);
        $.ajax({
            type: 'POST',
            url: '../notes/update_note/',
            data: data,
            processData: false,
            contentType: false,
            success: function (response) {
                $('#wic_note_edit_modal').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
                // Reset the Note Submission Form


                // Reset the SummerNote
                $('#wic_notes_edit_article').summernote('code', '');

                if (response === 'failed') {
                    swal("Error!", "Updating Notes Item Failed!", "error");
                }
                else {
                    swal("Good job! " + author, "Your note has been updated.", "success");
                    var monthNames = ["Jan", "Feb", "March", "April", "May", "June",
                        "July", "August", "Sept", "Oct", "Nov", "Dec"
                    ];
                    //Response was Success. Append this row to the Existing DataTable

                    // First Remove the Existing Row
                    wic_notes_table.row($('#row_' + id)).remove();

                    var date_split = date.split('-');
                    var year = date_split[0];
                    var month = date_split[1];
                    var day = date_split[2];

                    var newRow = '<tr id="row_' + response + '"><td>' + monthNames[month - 1] + ' ' + day + ', ' + year + '</td>' + '<td>' + title + '</td>' + '<td>' + author + '</td>' + '<td>' + tickers + '</td>' +
                        '<td><div class="btn-group">' +
                        '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                        '<i class="ft-settings"></i>' +
                        '</button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a id="edit_' + response + '" data-value=' + response + ' class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                        '<li><a id="delete_' + response + '" data-value=' + response + ' class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                        '<li><a id="view_' + response + '" data-value=' + response + ' class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
                        '</ul>' +
                        '</div></td></tr>';

                    //Re-initialize Datatable again
                    wic_notes_table.row.add($(newRow)).draw();
                    remove_file_ids = [];
                }


            },
            error: function (err_response) {
                console.log(err_response + ' in wic_notes.js while trying to save new Notes Item');
            }
        });
    });

    function readURL(input, target) {
        var text = "";
        if (input.files && input.files[0]) {
            for (var i = 0; i < input.files.length; i++) {
                text += input.files[i].name + "<br>";
            }
            $(target).html(text);
        }

    }

    $('#notes_attachments_model').change(function () {
        readURL(this, '#notes_attachments');
    });

    $('#edit_notes_attachments_model').change(function () {
        readURL(this, '#edit_selected_notes_attachments');
    });

    var wrapper = $(".display_attachments");
    $(wrapper).on("click", ".remove_file", function (e) {
        var index = -1;
        var file_id = $(this).attr('data-id');
        remove_file_ids[remove_file_ids.length] = file_id.split("_").pop()
        var fileList = $('#edit_notes_attachments').html().split("<br>")
        for (var i = 0; i < fileList.length; i++) {
            if (fileList[i].includes(file_id)) {
                index = i;
                break;
            }
        }
        fileList.splice(index, 1);
        fileList = fileList.join("<br>")
        $('#edit_notes_attachments').html(fileList);

    });

    var wrapper = $(".display_tickers");
    $(wrapper).on("click", ".remove_ticker", function (e) {
        var index = -1;
        ticker_index -= 1;
        var ticker_id = $(this).attr('data-id');
        remove_ticker_id = ticker_id.split("_").pop()
        delete selected_ticker_list[remove_ticker_id];
        var tickerList = $('#wic_notes_tickers_id').html().split("  ")
        for (var i = 0; i < tickerList.length; i++) {
            if (tickerList[i].includes(ticker_id)) {
                index = i;
                break;
            }
        }
        tickerList.splice(index, 1);
        tickerList = tickerList.join("  ")
        $('#wic_notes_tickers_id').html(tickerList);
        var requiredElement = document.getElementById("wic_notes_tickers_id");
        if (requiredElement.innerHTML.trim().length > 0) {
            if ($("#wic_notes_tickers").parent().next().attr('class') == 'ticker_error_div') {
                $("#wic_notes_tickers").parent().next().css("display", "none");
            }
            document.getElementById("wic_notes_tickers_div").style.display = "block";
            $("#wic_notes_tickers").removeAttr("required");
        }
        else {
            document.getElementById("wic_notes_tickers_div").style.display = "none";
            if (document.getElementById("tickerCheckbox").checked) {
                $("#wic_notes_tickers").removeAttr("required");
            }
            else {
                $("#wic_notes_tickers").prop("required", true);
            }
        }
    });
});