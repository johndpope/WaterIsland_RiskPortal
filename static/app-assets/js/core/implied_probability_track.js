$(document).ready(function () {

    let implied_probability_chart = $.parseJSON($('#implied_probability_chart').val());
    let field_names = $.parseJSON($('#field_names').val());

    let title = "Implied Probability Tracker";
    let fieldMappingsArray = ['AED Long', 'AED Short', 'N/A', 'Post Re-org Equity', 'Soft Universe Imp. Prob',
        'Spec M&A', 'Spin-Off', 'Stub Value', 'TAQ Long', 'TAQ Short', 'Transformational M&A', 'Turnaround',
        'Universe (Long)', 'Universe (Short)', 'Universe (Unclassified)'];

    let datasets = createDataSets(implied_probability_chart, field_names, fieldMappingsArray, false, fieldMappingsArray);

    console.log(datasets);
    let graphs = [];
    let counter = 1;
    let is_hidden = true;
    for (var i in fieldMappingsArray) {
        if (fieldMappingsArray[i] === 'Universe (Long)' || fieldMappingsArray[i] === 'Universe (Short)' || fieldMappingsArray[i] === 'Universe (Unclassified)') {
            is_hidden = false;
        }
        else {
            is_hidden = true;
        }
        graphs.push({
            "useDataSetColors": false,
            "id": "g" + counter++,
            "hidden": is_hidden,
            "valueField": fieldMappingsArray[i],
            "valueAxis": "a1",
            "title": fieldMappingsArray[i].toString(),
            "lineThickness": 1.5,
            "lineColor": randomColor({
                luminosity: 'bright',
                hue: 'random',
            }),
        });
    }

    let probability_tracker = AmCharts.makeChart("implied_probability_track", createLineChartConfigs(implied_probability_chart, datasets, graphs, title, '%', 'black'));

    $('#ess_implied_probability_table').DataTable({
        order: [[0, 'asc']],
        columnDefs: [{
            targets: [2], render: function (data) {
                return parseFloat(data).toFixed(2).toString() + " %"
            }
        },
            {
                targets: [0], render: function (data) {
                    return moment(data).format('YYYY-MM-DD');
                }
            }],
        "pageLength": 100,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'copy',
                text: '<i class="fa fa-copy"></i> Copy',

            }, {
                extend: 'csv',
                text: '<i class="fa fa-book"></i> CSV',

            }],
            dom: {
                container: {
                    className: 'dt-buttons'
                },
                button: {
                    className: 'btn btn-default'
                }
            }
        },
        initComplete: function () {
            this.api().columns([0, 1]).every(function () {
                var column = this;
                $(column.header()).append("<br>");
                var select = $('<select class="custom-select" ><option value=""></option></select>')
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
    })


});