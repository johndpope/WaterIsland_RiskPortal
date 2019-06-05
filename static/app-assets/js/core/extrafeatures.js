$(document).ready(function () {
    setWeather();
    setTweets();
    setPnlMonitors();
    setInterval(setPnlMonitors, 150000);
    let aum_df = JSON.parse($('#aum_df').val());
    Morris.Bar({
        element: 'monthly-sales',
        data: aum_df,
        xkey: 'fund',
        xLabelAngle: '70',
        ykeys: ['aum'],
        labels: ['Assets'],
        barGap: 4,
        barSizeRatio: 0.5,
        gridTextColor: '#fff',
        gridLineColor: '#fff',
        resize: true,
        barColors: ['#000'],
        hideHover: 'auto',
    });

    function populateNewsCarousels(url_address) {
        $.ajax({
            type: 'GET',
            url: url_address,
            cache: false,
            success: function (news_data) {
                // Populate the Carousel Here
                //Empty existing data first
                var news_sources = [];

                for (var i = 0; i < news_data.articles.length; i++) {
                    var article = news_data.articles[i];
                    if (article.urlToImage != null && article.description != null) {
                        $('<div class="carousel-item carousel-news-image center" ><img src="' + article.urlToImage + ' " alt="NO IMAGE FOUND"><div class="carousel-caption"><h3><br>' + news_data.articles[i].title + '</h3>' +
                            '<p>' + article.description + '</p><p><a href="' + article.url + '" target="_blank">Read More</a></p></div></div>').appendTo('.carousel-inner');
                        $('<li data-target="#carousel-interval" data-slide-to=' + i + '></li>').appendTo('.carousel-indicators');
                        news_sources.push(article.source.name.toString());
                    }
                    else {
                        continue;
                    }
                }

                //Todo Sources aren't properly aligned with the news
                var prev_index = 0;
                $('#news-footer-cite').text(news_sources[prev_index]);
                $('.carousel-item').first().addClass('active');
                $('.carousel-indicators > li').first().addClass('active');
                $('#carousel-interval').on('slide.bs.carousel', function (e) {
                    if (e.direction === 'left') {
                        var idx = $(this).find('.active').index();
                        $('#news-footer-cite').text(news_sources[idx + 1]);
                    }
                    else {
                        var idx = $(this).find('.active').index();
                        $('#news-footer-cite').text(news_sources[idx - 1]);
                    }

                });

            },
            error: function (err) {
                console.log(err);
            }
        });
    }


    populateNewsCarousels('../news/get_top_news');
    setInterval(function () {
        $('#carousel-inner').children().remove();
        $('#carousel-indicators').children().remove();
        populateNewsCarousels('../news/get_top_news')
    }, 700000);

    $('#weather-reload').click(function () {
        setWeather();
    });

    function setWeather() {
        $.ajax({
            type: "GET",
            url: "../weather/get_nyc_weather",
            success: function (data) {
                var month = new Array();
                month[0] = "January";
                month[1] = "February";
                month[2] = "March";
                month[3] = "April";
                month[4] = "May";
                month[5] = "June";
                month[6] = "July";
                month[7] = "August";
                month[8] = "September";
                month[9] = "October";
                month[10] = "November";
                month[11] = "December";


                $('#weather-current-day').text(new Date().getDate());
                $('#weather-current-month').text(month[new Date().getMonth()]);
                $('#weather-detailed-status').text(data.status.toUpperCase());

                if ($.isEmptyObject(data.humidity) && data.humidity == 0) {
                    $('#weather-sunset').text('No Data');
                }
                else {
                    $('#weather-sunset').html("<strong>" + data.humidity.toString() + "</strong>" + "%");
                }
                if ($.isEmptyObject(data.snow)) {
                    $('#weather-snow').text('No Snow');
                }
                else {
                    $('#weather-snow').text(data.rain);
                }

                $('#weather-temp').text(data.temperature.temp + " F");
                let url = "https://images.icanvas.com/2d/TEO86.jpg";

                if (data.status.toString().toLowerCase().search('clouds') != -1) {
                    //Set cloudy background image
                    url = 'http://mcny.org/sites/default/files/New-York-14-10-2489.jpg';
                }

                else if (data.status.toString().toLowerCase().search('rain') != -1) {
                    //Set rainy background image
                    url = 'https://ak9.picdn.net/shutterstock/videos/13897619/thumb/1.jpg?i10c=img.resize(height:160)';
                }

                else if (data.status.toString().toLowerCase().search('snow') != -1) {
                    //Set snowy background image
                    url = 'https://c1.staticflickr.com/9/8361/8327626299_0c9b5df9e9_b.jpg';
                }

                else if (data.status.toString().toLowerCase().search('mist') != -1) {
                    //Set Misty background image
                    url = 'https://www.travel-holiday.net/wp-content/uploads/2015/05/Misty-looking-New-York-Skyline-1024x586.jpg';
                }

                else if (data.status.toString().toLowerCase().search('thunder') != -1) {
                    //Set Misty background image
                    url = 'https://isardasorensen.files.wordpress.com/2012/05/tp-tuesday-storm-5-29-12.jpg';
                }
                else {
                    //Set normal background
                    url = 'https://images.icanvas.com/2d/TEO86.jpg';
                }
                let css = {
                    "background-image": "url(" + url + ")",
                    "background-repeat": "no-repeat",
                    "background-size": "100% 100%"
                };
                $('#weather-background-image').css(css);

            }
        }).then(function () {
            setTimeout(setWeather, 700000);
        });
    };


    //Function for Populating Tweets
    var flag = false;

    function setTweets() {
        $.ajax({
            type: "GET",
            url: "../tweets/get_latest_tweets",
            success: function (data) {
                //clear all children first
                $('#tweets-list').empty();
                for (var i = 0; i < data.length; i++) {
                    $('<li>' + data[i].text + '<div class="card-footer bg-twitter"><div class="card-profile-image"><img src="' + data[i].pic + '" class="rounded-circle img-border box-shadow-1" alt="Card Image"></div>' +
                        '<footer class="blockquote-footer bg-twitter white"><strong>@' + data[i].screen_name + '</strong></footer></div></li>').appendTo($('#tweets-list'))
                }

                if (!flag) {
                    $('#tweet-slider').unslider({
                        speed: 500,
                        delay: 2000,
                        keys: true,
                        dots: true,
                        fluid:false
                    });
                    flag = true;
                }


            },
            error: function (err) {
                console.log(err);
            }
        }).then(function () {
            //setTimeout(setTweets, 8000); //Todo: Check how to do this async (dynamic adding of points)
        });
    }


    function setPnlMonitors() {
        // Displays and Updates in realtime (P&L Monitors across the Board)
        $('#pnl_monitors_card').empty();
        $('#pnl_monitors_card').append('Refreshing P&L monitors');
        $('#pnl_monitors_card').empty();
        $.ajax({
            type: "GET",
            url: "../realtime_pnl_impacts/live_pnl_monitors",
            success: function (data) {
                let pnl_monitors_data = $.parseJSON(data['data']);
                let last_updated = data['last_updated'];

                let span = '<span class="badge badge-secondary">' + moment(last_updated).format('MMMM Do YYYY, h:mm a') + '</span>';
                $('#synced_on_placeholder').text("Synced on: ");
                $('#synced_on_placeholder').append(span);
                // Collect Distinct Funds
                let funds_order = ['ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV', 'TACO', 'TAQ'];


                let first_header = '<tr class="' + "border border-dark" + '">';
                first_header += '<th>P&L Targets</th>';
                let second_header = '<tr>';
                second_header += '<th>Loss Budgets</th>';
                for (var i = 0; i < funds_order.length; i++) {
                    // Create a Header with Funds Info
                    first_header += '<th>' + funds_order[i] + '</th>'
                    second_header += '<th>' + funds_order[i] + '</th>'
                }
                first_header += '</tr>';
                second_header += '</tr>';

                let pnl_rows = '';
                $.each(pnl_monitors_data, function (metric, funds_dict) {
                    let style = "";
                    let class_ = "";
                    if (metric === 'Loss Budgets') {
                        style = "font-weight:bold";
                        class_ = "border border-dark";
                    }
                    pnl_rows += '<tr class="' + class_ + '"style="' + style + '">';
                    pnl_rows += '<td style="white-space:nowrap;">' + metric + '</td>';
                    for (var i = 0; i < funds_order.length; i++) {
                        // Append for each fund...
                        pnl_rows += '<td style="white-space:nowrap;">' + funds_dict[funds_order[i]]
                        if (metric == 'Ann. Gross P&L Target %') {
                            edit_button = '<button type="button" class="btn btn-link btn-sm" id="edit_profit_' +
                                funds_order[i] + '"><span class="icon-fixed-width icon-pencil"></span></button>';
                            pnl_rows += edit_button
                        }
                        else if (metric == 'Ann Loss Budget %') {
                            edit_button = '<button type="button" class="btn btn-link btn-sm" id="edit_loss_' +
                                funds_order[i] + '"><span class="icon-fixed-width icon-pencil"></span></button>';
                            pnl_rows += edit_button
                        }
                        pnl_rows += '</td>'
                    }
                    pnl_rows += '</tr>'
                });

                let table = "<div class='table-responsive'><table id='realtime_pnl_monitors_table' style='width: 100%;' " +
                    "class=\"table table-striped table-hover text-dark\"><thead>" +
                    first_header + "</thead>" + "<tbody>" + pnl_rows + "</tbody></table>" +
                    "<p style='text-align: right'>" +
                    "* Above data has been calculated using Average YTD Investable Assets</p></div>";


                // Append table
                $('#pnl_monitors_card').append(table);
                var target_index = [];
                for (var i = 1; i <= funds_order.length; i++) {
                    target_index.push(i);
                }
                $('#realtime_pnl_monitors_table').DataTable({
                    'bInfo': false,
                    'searching': false,
                    'paging': false,
                    'ordering': false,
                    "columnDefs": [{
                        "targets": target_index,
                        "createdCell": function (td, cellData, rowData, rowIndex) {
                            if (rowIndex !== 7) {
                                cellData = cellData.replace('%', '').replace(',', '');
                                if (parseFloat(cellData) < 0) {
                                    $(td).css('color', 'red')
                                }
                                else {
                                    $(td).css('color', 'green')
                                }
                            }

                        },
                    }],
                });
            },
            error: function (err) {
                console.log(err);
            }
        });
    }

    $(document).on("click", "button", function () {
        var button_id = this.id;
        if (button_id.includes("edit_profit_") || button_id.includes("edit_loss_")) {
            var fund = button_id.split("_").pop()
            var is_profit_target = false;
            var title = "Update Profit/Loss Target Percentage";
            var text = "Enter a value";
            var success = "The value has been updated"
            if (button_id.includes("edit_profit_")) {
                is_profit_target = true;
                title = "Update Profit Target Percentage for " + fund.toUpperCase();
                text = "Enter a new value for Profit Target %"
                success = "The Profit Target has been updated to "
            }
            else if (button_id.includes("edit_loss_")) {
                is_profit_target = false;
                title = "Update Loss Budget Percentage for " + fund.toUpperCase();
                text = "Enter a new value for Loss Budget %"
                success = "The Loss Budget has been updated to "
            }
            swal({
                title: title,
                text: text,
                content: 'input',
                buttons: ["Cancel",
                    {text: "Save", closeModal: false}],
            }).then((value) => {
                if (value) {
                    $.ajax({
                        type: 'POST',
                        url: '../realtime_pnl_impacts/update_profit_loss_targets',
                        data: {'fund': fund, 'is_profit_target': is_profit_target, 'value': value},
                        success: function (response) {
                            if (response === "Success") {
                                swal("Success! " + success + value + "% for " + fund, {icon: "success"});
                                setPnlMonitors();

                            }
                            else {
                                swal("Error!", "The value could not be updated", "error");
                                console.log('Deletion failed', fund, value);
                            }
                        },
                        error: function (error) {
                            swal("Error!", "The value could not be updated", "error");
                            console.log(error, fund, value);
                        }
                    });

                }
            });
        }
    });

    $('#breakfast-textarea').keyup(function () {
        if ($('#breakfast-textarea').val().length == 0) {
            $("#previous-breakfast-options").prop("disabled", false);
        }
        else {
            $("#previous-breakfast-options").prop("disabled", true);
        }

    });

    $('#previous-breakfast-options').change(function () {

        if ($('#previous-breakfast-options').val() === "Previous Orders") {
            $("#breakfast-textarea").prop("disabled", false);
        }
        else {
            $("#breakfast-textarea").prop("disabled", true);
        }

    });

    $('#submit-breakfast-order').click(function (e) {
        //Get the selector values and submit an ajax request
        var previous_order = $('#previous-breakfast-options').val();
        var new_order = $('#breakfast-textarea').val();

        var order_to_submit = '';
        if (new_order.length > 0) {
            //Submit the New Order
            order_to_submit = new_order;
        }
        else {
            //Submit the Previous order
            order_to_submit = previous_order;
        }
        $.ajax({
            type: "POST",
            url: "../breakfast/submit_breakfast_order",
            data: {'order': order_to_submit, 'csrfmiddlewaretoken': $('#breakfast-csrf-token').val()},
            success: function (breakfast_response) {
                $('#swing').modal('hide');
                $('body').removeClass('modal-open');
                $('.modal-backdrop').remove();

                if (breakfast_response === 'done') {
                    swal({
                        title: "Sweet!",
                        text: "Your Order has been placed!",
                        icon: "static/app-assets/images/icons/thumbs-up.jpg"
                    });
                }
                else {
                    swal("Warning!", "Orders after 8.30am might not go through. Still, we'll try our best.!", "warning");
                }

            },
            error: function (err) {
                console.log(err);
            }
        }).then(function () {
            //setTimeout(setTweets, 8000); //Todo: Check how to do this async (dynamic adding of points)
        });

    })


});
