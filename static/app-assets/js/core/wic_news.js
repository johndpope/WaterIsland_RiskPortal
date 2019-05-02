$(document).ready(function(){
    //Create a Datatable out of retrieved Values
    var wic_news_table = $('#wic_news_table').DataTable({
        "aaSorting": [[0,'desc']],
        "pageLength": 100,
        });
    $('#wic_news_article').summernote({'height':450});

    $('#wic_news_url').on('focusout',function(){
       var url = $('#wic_news_url').val();
       if(url.length > 0){
           //Display a toast
           toastr.info('Gathering Info from URL & automatically creating a short-summary!', 'Hang Tight!',
               {positionClass: 'toast-top-right', containerId: 'toast-top-right'});
           var csrf_token = $('#wic_news_csrf_token').val();
            //Open an Ajax Request
           $.ajax({
               type: 'POST',
               url: '../news/get_article_from_url',
               data: {
                   'csrfmiddlewaretoken': csrf_token,
                   'url': url
               },
               success: function (response) {
                   $('#wic_news_article').summernote('code',response.text);
                   $('#wic_news_summary').summernote('code',response.nlp_summary);
                   $('#wic_news_author').val(response.authors);
               }
           })
       }
    });



    $('#submit_wic_news_form').on('submit',function(e){
        e.preventDefault(); //to Stop from Refreshing
        //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
        var article = $('#wic_news_article').summernote('code');
        var date = $('#wic_news_date').val();
        var title = $('#wic_news_title').val();
        var source = $('#wic_news_source').val();
        var author = $('#wic_news_author').val();
        var tickers = $('#wic_news_tickers').val();
        var csrf_token = $('#wic_news_csrf_token').val();
        var url = $('#wic_news_url').val();
        //POST The Data to be Inserted into the Database

        $.ajax({
            type:'POST',
            url:'../news/add_new_wic_news_item',
            data:{'csrfmiddlewaretoken':csrf_token, 'article':article, 'date':date, 'title':title, 'source':source, 'author':author, 'tickers':tickers, 'url':url},
            success:function(response){
                $('#wic_news_modal').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
                // Reset the News Submission Form
                $('#submit_wic_news_form')[0].reset();

                // Reset the SummerNote
                $('#wic_news_article').summernote('code','');

                if(response === 'failed'){
                    swal("Error!", "Adding News Item Failed!", "error");
                }
                else{
                     toastr.success('Added', 'Please Refresh the page', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }



            },
            error:function(err_response){
                console.log(err_response+' in wic_news.js while trying to save new News Item');
            }

        });



    });


    /* Function to delete a News Item */
     // Event Delegation for Dynamically added elements

    $('.table-responsive').on("click","#wic_news_table tr td li a", function(){

        var current_news = this.id.toString();
        // Handle Selected Logic Here
        if(current_news.search('edit_')!=-1){
            //Logic for Editing a Deal
            // Steps. Populate Edit Modal with existing fields. Show Modal. Make changes through Ajax. Get Response. Display success Alert
            news_id_to_edit = current_news.split('_')[1]; //Get the ID
            var edit_row = $('#row_'+news_id_to_edit);

            var $tds = edit_row.find('td');
            var date = $tds.eq(0).text();
            var title = $tds.eq(1).text();
            var source = $tds.eq(2).text();
            var url = $tds.eq(3).children().attr('href');
            var author = $tds.eq(4).text();
            var article = $tds.eq(4).attr('data-value');
            var tickers = $tds.eq(5).text();
            // Populate the Edit Modal Inputs with these values
            $('#wic_news_edit_id').val(news_id_to_edit);
            $('#wic_news_edit_date').val(date);
            $('#wic_news_edit_title').val(title);
            $('#wic_news_edit_source').val(source);
            $('#wic_news_edit_url').val(url);
            $('#wic_news_edit_author').val(author);
            $('#wic_news_edit_tickers').val(tickers);
            $('#wic_news_edit_article').summernote({'height':'450px'});
            $('#wic_news_edit_article').summernote('code', article);

            // Display the Modal
            $('#wic_news_edit_modal').modal('show');

        }
        else if(current_news.search('delete_')!=-1){
            //Logic for Deleting a deal
            //First Popup sweetAlert to Confirm Deletion

            news_id_to_delete = current_news.split('_')[1];

            // Send this Deal key to Django View to Delete and Wait for Response. If Response is successful, then Delete the row from DataTable

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this news item!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
                }).then((willDelete) => {
                    if (willDelete) {
                        //Handle Ajax request to Delete
                        $.ajax({
                            type:'POST',
                            url:'../news/delete_wic_news_item',
                            data:{'id':news_id_to_delete,'csrfmiddlewaretoken':$('#wic_news_csrf_token').val()},
                            success:function(response){
                                if(response==="wic_news_deleted"){
                                    //Delete Row from DataTable
                                    swal("Success! The News has been deleted!", {icon: "success"});
                                    //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                    wic_news_table.row($("#row_"+news_id_to_delete)).remove().draw();

                                }
                                else{
                                    //show a sweet alert
                                    swal("Error!", "Deleting News Failed!", "error");
                                    console.log('Deletion failed');
                                }
                            },
                            error:function (error) {
                                swal("Error!", "Deleting News Failed!", "error");
                                console.log(error);
                            }
                        });

                    }
                });
        }
        else{
            //Logic to View the Deal
            //Just take the URL and redirect to the page. Front-end handling
            news_to_view = current_news.split('_')[1];
            var edit_row = $('#row_'+news_to_view);
            var $tds = edit_row.find('td');
            var url = $tds.eq(3).children().attr('href');
            window.open(url, 'Water Island', 'WIC Sets');
        }



    });


    /* EDITING CURRENT NEWS ITEM */
    $('#submit_wic_news_edit_form').on('submit',function(e){
        e.preventDefault(); //to Stop from Refreshing
        //Get all the fields and make an Ajax call. Wait for Response, if positive, show toaster and append this new row to the existing table
        var id = $('#wic_news_edit_id').val();
        var article = $('#wic_news_edit_article').summernote('code');
        var date = $('#wic_news_edit_date').val();
        var title = $('#wic_news_edit_title').val();
        var source = $('#wic_news_edit_source').val();
        var author = $('#wic_news_edit_author').val();
        var tickers = $('#wic_news_edit_tickers').val();
        var csrf_token = $('#wic_edit_news_csrf_token').val();
        var url = $('#wic_news_edit_url').val();
        //POST The Data to be Inserted into the Database

        $.ajax({
            type:'POST',
            url:'../news/update_wic_news_item',
            data:{'csrfmiddlewaretoken':csrf_token, 'article':article, 'date':date, 'title':title, 'source':source, 'author':author, 'tickers':tickers, 'url':url,'id':id},
            success:function(response){
                $('#wic_news_edit_modal').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();
                // Reset the News Submission Form
                $('#submit_wic_news_edit_form')[0].reset();

                // Reset the SummerNote
                $('#wic_news_edit_article').summernote('code','');

                if(response === 'failed'){
                    swal("Error!", "Updating News Item Failed!", "error");
                }
                else{
                    var monthNames = ["Jan", "Feb", "March", "April", "May", "June",
                      "July", "August", "Sept", "Oct", "Nov", "Dec"
                    ];
                    //Response was Success. Append this row to the Existing DataTable

                    // First Remove the Existing Row
                    wic_news_table.row($('#row_'+id)).remove();

                    var date_split = date.split('-');
                    var year = date_split[0];
                    var month = date_split[1];
                    var day = date_split[2];

                    var newRow = '<tr id="row_'+id+'"><td>'+monthNames[month-1]+' '+day+', '+year+'</td>'+'<td>'+title+'</td>'+'<td>'+source+'</td>'+'<td>'+url+'</td>'+'<td>'+author+'</td>' + '<td>'+tickers+'</td>'+
                    '<td><div class="btn-group">' +
                    '<button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
                    '<i class="ft-settings"></i>' +
                    '</button>' +
                    '<ul class="dropdown-menu">' +
                    '<li><a id="edit_'+id+'" data-value="{{ news_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-edit-2"></i> Edit</a></li>' +
                    '<li><a id="delete_'+id+'" data-value="{{ news_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-trash-2"></i> Delete</a></li>' +
                    '<li><a id="view_'+id+'" data-value="{{ news_item.id }}" class=\'dropdown-item\' href="#"><i class="ft-plus-circle primary"></i> View</a></li>' +
                    '</ul>' +
                    '</div></td></tr>';

                //Re-initialize Datatable again
                    wic_news_table.row.add($(newRow)).draw();
                }



            },
            error:function(err_response){
                console.log(err_response+' in wic_news.js while trying to save new News Item');
            }

        });



    });


});