$(document).ready(function () {

    var remove_file_ids = [];

    //Create a Datatable out of retrieved Values
    var wic_notes_table = $('#wic_notes_table').DataTable();
    $('#wic_note_article').summernote({'height': 200});


    $('#submit_wic_notes_form').on('submit', function (e) {
        e.preventDefault(); //to Stop from Refreshing
        //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
        var article = $('#wic_note_article').summernote('code').replace(/<\/?[^>]+(>|$)/g, "");
        var date = $('#wic_notes_date').val();
        var title = $('#wic_notes_title').val();
        var author = $('#wic_notes_author').val();
        var tickers = $('#wic_notes_tickers').val();
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

                if (response === 'failed') {
                    swal("Error!", "Adding Note Failed!", "error");
                }
                else {
                    var monthNames = ["Jan", "Feb", "March", "April", "May", "June",
                        "July", "August", "Sept", "Oct", "Nov", "Dec"
                    ];
                    //Response was Success. Append this row to the Existing DataTable
                    var date_split = date.split('-');
                    var year = date_split[0];
                    var month = date_split[1];
                    var day = date_split[2];
                    var newRow = '<tr id="row_' + response + '"><td>' + monthNames[month - 1] + ' ' + day + ', ' + year + '</td>' + '<td>' + title + '</td>' + '<td>' + author + '</td>' + '<td>' + article + '</td>' + '<td>' + tickers + '</td>' +
                        '<td><div class="btn-group">' +
                        '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                        '<i class="ft-settings"></i>' +
                        '</button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a id="edit_' + response + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                        '<li><a id="delete_' + response + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                        '<li><a id="view_' + response + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
                        '</ul>' +
                        '</div></td></tr>';

                    //Re-initialize Datatable again
                    wic_notes_table.row.add($(newRow)).draw();
                }


            },
            error: function (err_response) {
                console.log(err_response + ' in wic_notes.js while trying to save new Notes Item');
            }

        });


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
            var edit_row = $('#row_' + notes_id_to_edit);
            remove_file_ids = [];
            $('#submit_wic_notes_edit_form').trigger('reset');

            var $tds = edit_row.find('td');
            var date = $tds.eq(0).text();
            var title = $tds.eq(1).text();
            var author = $tds.eq(2).text();
            var article = $tds.eq(3).data('article');
            var tickers = $tds.eq(4).text();
            var formatted_date = moment(new Date(date)).format('YYYY-MM-DD');
            $('#edit_selected_notes_attachments').text('');
            // Collect Uploaded Files through Ajax
            $.ajax({
               url:"../notes/get_attachments/",
               type:'POST',
               data:{'notes_id':notes_id_to_edit},
               success:function(response){
                   let attachments = response['attachments'];
                   if(attachments.length > 0){
                       let files = "";
                       for(var i=0;i<attachments.length;i++){
                           console.log(attachments[i])
                           files += "<a href=" + attachments[i].url + ">" + attachments[i].filename + "</a> <a class='remove_file' data-id='remove_notes_" + notes_id_to_edit + "_file_" + attachments[i].id + "' href='#'><i class='ft-trash-2'></i></a><br />";
                       }
                       $('#edit_notes_attachments').html(files);
                   }
               },
               error: function (err) {
                   console.log(err);
               }
            });


            // Populate the Edit Modal Inputs with these values
            $('#wic_notes_edit_id').val(notes_id_to_edit);
            $('#wic_notes_edit_date').val(formatted_date.toString()); //Todo: Date not setting
            $('#wic_notes_edit_title').val(title);
            $('#wic_notes_edit_author').val(author);
            $('#wic_notes_edit_article').summernote('code', article);
            $('#wic_notes_edit_tickers').val(tickers);

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
            var note_to_view = current_note.split('_')[1];
            var edit_row = $('#row_' + note_to_view);
            var $tds = edit_row.find('td');
            var article = $tds.eq(3).attr('data-article');
            // Just populate WicNote View Article
            $('#wic_note_view_article').summernote({'height': "400px"});
            $('#wic_note_view_article').summernote('code', article);
            $('#wic_notes_view_modal').modal('show');
        }
    });


    /* EDITING CURRENT Notes ITEM */
    $('#submit_wic_notes_edit_form').on('submit', function (e) {
        e.preventDefault(); //to Stop from Refreshing
        //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
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

                    var newRow = '<tr id="row_' + id + '"><td>' + monthNames[month - 1] + ' ' + day + ', ' + year + '</td>' + '<td>' + title + '</td>' + '<td>' + author + '</td>' + '<td>' + article + '</td>' + '<td>' + tickers + '</td>' +
                        '<td><div class="btn-group">' +
                        '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                        '<i class="ft-settings"></i>' +
                        '</button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a id="edit_' + id + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                        '<li><a id="delete_' + id + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                        '<li><a id="view_' + id + '" data-value="{{ notes_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
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
    $(wrapper).on("click", ".remove_file", function(e){
        var index = -1;
        var file_id = $(this).attr('data-id');
        remove_file_ids[remove_file_ids.length] = file_id.split("_").pop()
        var fileList = $('#edit_notes_attachments').html().split("<br>")
        for (var i = 0; i< fileList.length; i++) {
            if (fileList[i].includes(file_id)) {
                index = i;
                break;
            }
        }
        console.log(remove_file_ids);
        fileList.splice(index, 1);
        fileList = fileList.join("<br>")
        $('#edit_notes_attachments').html(fileList);

    });

});