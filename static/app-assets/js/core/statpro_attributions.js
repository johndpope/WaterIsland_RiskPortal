$(document).ready(function () {


    $('#amchart-contributions').hide();
    $(".dp-multiple-months").datepicker({
        changeMonth: true,
        changeYear: true,
    });

    /** Get the Data on Submit and POST via Ajax. Show loader while the items are retrieved! **/

    $('#statpro_attribution_form').on('submit', function (e) {
        e.preventDefault();
        $('#amchart-contributions').hide();
        var start_date = $('#statpro_attribution_start_date').val();
        var end_date = $('#statpro_attribution_end_date').val();
        var fund_name = $('#statpro_attribution_fund').val();
        var csrf_token = $('#statpro_csrf_token').val();
        $('#statpro_attribution_table').DataTable().clear().draw();
        $('#statpro_attribution_table').DataTable().destroy();
        // Show the Loader and Make an Ajax Call
        $('.loader-inner').loaders();
        $.ajax({
            url: '../get_attribution/',
            type: 'POST',
            data: {
                'start_date': start_date,
                'end_date': end_date,
                'fund_name': fund_name,
                'csrfmiddlewaretoken': csrf_token
            },
            success: function (response) {
                // Render the DataTable and stop the Loader
                // Destroy Existing Datatable

                if (response === 'No Data Available') {
                    swal("Error!", "No Data Available for the given dates", "error");
                    $('.loader-inner').empty();
                    return;
                }


                var data2 = $.parseJSON(response)
                $('.loader-inner').empty();
                $('#statpro_attribution_table').DataTable({
                    dom: 'Bfrtip',
                    buttons: [
                       {extend: 'copy', className: 'btn btn-lg btn-primary dt-button buttons-copy buttons-flash'},
                        {extend: 'excel', className: 'btn btn-lg btn-success dt-button buttons-excel buttons-flash'},
                        {extend: 'pdf', className: 'btn btn-lg btn-secondary dt-button buttons-pdf buttons-flash'},
                        {extend: 'print', className: 'btn btn-lg btn-danger dt-button buttons-print buttons-flash'}
                    ],
                    "data": data2,
                    "columns": [
                        {"data": "TradeGroup", "width": "30%"},
                        {"data": "Compounded Contribution", "width": "25%"},
                        {"data": "From", "width": "22%"},
                        {"data": "To", "width": "22%"}
                    ],
                    "aoColumnDefs": [{
                        "aTargets": [1],
                        "mRender": function (data) {
                            return parseFloat(data).toFixed(1);
                        }
                    },
                    ],


                });


                // Draw Amcharts
                var monthly_contributions_chart_data = generateMonthlyContributionsChartData(data2);
                var monthly_contributions = AmCharts.makeChart("monthly-contribution-chart", {
                    "type": "serial",
                    "theme": "black",
                    "legend": {
                        "useGraphSettings": true
                    },
                    "hideCredits": true,
                    "dataProvider": monthly_contributions_chart_data,
                    "synchronizeGrid": true,
                    "valueAxes": [{
                        "id": "v1",
                        "axisColor": "#FF6600",
                        "axisThickness": 2,
                        "axisAlpha": 1,
                        "position": "left",
                    },],
                    "graphs": [{
                        "lineColor": "#FF6600",
                        "valueAxis": "v1",
                        "bullet": "round",
                        "bulletBorderThickness": 1,
                        "hideBulletsCount": 30,
                        "title": "Compounded Contributions",
                        "valueField": "contribution",
                        "fillAlphas": 0.1
                    }],
                    "chartScrollbar": {},
                    "chartCursor": {
                        "cursorPosition": "mouse"
                    },
                    "categoryField": "date",
                    "categoryAxis": {
                        "parseDates": true,
                        "axisColor": "#000000",
                        "minorGridEnabled": true
                    },
                    "export": {
                        "enabled": true,
                        "position": "bottom-right"
                    }
                });
                $('#amchart-contributions').fadeIn(3000);
            },

            error: function (err_response) {
                // Just Stop the loader and display Sweet alert
                $('.loader-inner').empty();

            }

        })

    });

    //
});

function generateMonthlyContributionsChartData(data2) {
    var chartData = [];
    for (var i = 0; i < data2.length; i++) {
        chartData.push({
            date: new Date(data2[i].From.toString() + " 00:00"),
            contribution: data2[i]["Compounded Contribution"],
        })
    }

    return chartData;
}