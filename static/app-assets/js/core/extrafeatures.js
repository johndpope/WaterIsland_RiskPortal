$(document).ready(function(){
    setWeather();
    setTweets();
    function populateNewsCarousels(url_address) {
        $.ajax({
            type:'GET',
            url:url_address,
            cache:false,
            success:function (news_data) {
                // Populate the Carousel Here
                //Empty existing data first
                var news_sources = [];

                for (var i=0;i<news_data.articles.length;i++){
                    if(news_data.articles[i].urlToImage!=null && news_data.articles[i].description!=null){
                        $('<div class="carousel-item carousel-news-image center" ><img src="'+news_data.articles[i].urlToImage+' " alt="NO IMAGE FOUND"><div class="carousel-caption"><h3>'+news_data.articles[i].title+'</h3>' +
                        '<p>'+news_data.articles[i].description+'</p></div></div>').appendTo('.carousel-inner');
                        $('<li data-target="#carousel-interval" data-slide-to='+i+'></li>').appendTo('.carousel-indicators');
                        news_sources.push(news_data.articles[i].source.name.toString());
                    }
                    else{
                        continue;
                    }
               }

               //Todo Sources aren't properly aligned with the news
               var prev_index = 0;
               $('#news-footer-cite').text(news_sources[prev_index]);
               $('.carousel-item').first().addClass('active');
               $('.carousel-indicators > li').first().addClass('active');
               $('#carousel-interval').on('slide.bs.carousel', function(e) {
                   if(e.direction === 'left'){
                        var idx = $(this).find('.active').index();
                        $('#news-footer-cite').text(news_sources[idx+1]);
                   }
                   else{
                       var idx = $(this).find('.active').index();
                       $('#news-footer-cite').text(news_sources[idx-1]);
                   }

               });

            },
            error:function (err) {
                console.log(err);
            }
        });
    }


    populateNewsCarousels('../news/get_top_news');
    setInterval(function(){$('#carousel-inner').children().remove();
                $('#carousel-indicators').children().remove();populateNewsCarousels('../news/get_top_news')},700000);

     $('#weather-reload').click(function(){
        setWeather();
    });

    $('#tweet-reload').click(function(){
        //setTweets();
    });

     function setWeather(){
      $.ajax({
      type: "GET",
      url: "../weather/get_nyc_weather",
      success: function(data){
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

         if($.isEmptyObject(data.humidity) && data.humidity==0){
            $('#weather-sunset').text('No Data');
         }
         else{
             $('#weather-sunset').html("<strong>"+data.humidity.toString()+"</strong>"+"%");
         }
         if($.isEmptyObject(data.snow)){
            $('#weather-snow').text('No Snow');
         }
         else{
             $('#weather-snow').text(data.rain);
         }

         $('#weather-temp').text(data.temperature.temp+" F");

         if(data.status.toString().toLowerCase().search('clouds')!=-1){
             //Set cloudy background image
             $('#weather-background-image').css({"background-image":"url('http://mcny.org/sites/default/files/New-York-14-10-2489.jpg')"});
         }

         else if(data.status.toString().toLowerCase().search('rain')!=-1){
             //Set rainy background image
             $('#weather-background-image').css({"background-image":"url('https://ak9.picdn.net/shutterstock/videos/13897619/thumb/1.jpg?i10c=img.resize(height:160)')"});
         }

         else if(data.status.toString().toLowerCase().search('snow')!=-1){
             //Set snowy background image
             $('#weather-background-image').css({"background-image":"url('https://c1.staticflickr.com/9/8361/8327626299_0c9b5df9e9_b.jpg')"});
         }

         else if(data.status.toString().toLowerCase().search('mist')!=-1){
             //Set Misty background image
             $('#weather-background-image').css({"background-image":"url('https://www.travel-holiday.net/wp-content/uploads/2015/05/Misty-looking-New-York-Skyline-1024x586.jpg')"});
         }

        else if(data.status.toString().toLowerCase().search('thunder')!=-1){
             //Set Misty background image
             $('#weather-background-image').css({"background-image":"url('https://isardasorensen.files.wordpress.com/2012/05/tp-tuesday-storm-5-29-12.jpg')"});
         }
         else{
             //Set normal background
             $('#weather-background-image').css({"background-image":"url('https://images.icanvas.com/2d/TEO86.jpg')"});
         }

      }
    }).then(function () {
        setTimeout(setWeather,700000);
    });
   };

    
    //Function for Populating Tweets
    var flag = false;
    function setTweets() {
      $.ajax({
        type: "GET",
        url: "../tweets/get_latest_tweets",
        success: function(data) {
          //clear all children first
            $('#tweets-list').empty();
          for (var i = 0; i < data.length; i++) {
            $('<li>' + data[i].text + '<div class="card-footer bg-twitter"><div class="card-profile-image"><img src="' + data[i].pic + '" class="rounded-circle img-border box-shadow-1" alt="Card Image"></div>' +
              '<footer class="blockquote-footer bg-twitter white"><strong>@' + data[i].screen_name + '</strong></footer></div></li>').appendTo($('#tweets-list'))
          }

          if (!flag) {
            $('#tweet-slider').unslider('calculateSlides');
            flag = true;
          }


        },
        error: function(err) {
          console.log(err);
        }
      }).then(function() {
        //setTimeout(setTweets, 8000); //Todo: Check how to do this async (dynamic adding of points)
      });
    }


    $('#breakfast-textarea').keyup(function () {
        if($('#breakfast-textarea').val().length==0){
            $("#previous-breakfast-options").prop("disabled", false);
        }
        else{
            $("#previous-breakfast-options").prop("disabled", true);
        }

    });

    $('#previous-breakfast-options').change(function () {

        if($('#previous-breakfast-options').val()==="Previous Orders"){
            $("#breakfast-textarea").prop("disabled", false);
        }
        else{
            $("#breakfast-textarea").prop("disabled", true);
        }

    });

    $('#submit-breakfast-order').click(function (e) {
        //Get the selector values and submit an ajax request
        var previous_order = $('#previous-breakfast-options').val();
        var new_order = $('#breakfast-textarea').val();

        var order_to_submit = '';
        if(new_order.length>0){
            //Submit the New Order
            order_to_submit = new_order;
        }
        else{
            //Submit the Previous order
            order_to_submit = previous_order;
        }
        $.ajax({
        type: "POST",
        url: "../breakfast/submit_breakfast_order",
        data:{'order':order_to_submit, 'csrfmiddlewaretoken':$('#breakfast-csrf-token').val()},
        success: function(breakfast_response) {
        $('#swing').modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();

        if(breakfast_response === 'done'){
            swal({   title: "Sweet!",   text: "Your Order has been placed!",   icon: "static/app-assets/images/icons/thumbs-up.jpg" });
        }
        else{
            swal("Warning!", "Orders after 8.30am might not go through. Still, we'll try our best.!", "warning");
        }

        },
        error: function(err) {
          console.log(err);
        }
      }).then(function() {
        //setTimeout(setTweets, 8000); //Todo: Check how to do this async (dynamic adding of points)
      });

    })

});
