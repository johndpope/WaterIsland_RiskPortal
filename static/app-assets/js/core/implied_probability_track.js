$(document).ready(function () {

    let implied_probability_chart = $.parseJSON($('#implied_probability_chart').val());
    let field_names = $.parseJSON($('#field_names').val());

    let title = "Implied Probability Tracker";
    let fieldMappingsArray = ['AED Long', 'AED Short', 'N/A', 'Post Re-org Equity', 'Soft Universe Imp. Prob',
        'Spec M&A', 'Spin-Off', 'Stub Value', 'TAQ Long', 'TAQ Short', 'Transformational M&A', 'Turnaround',
        'Universe (Long)', 'Universe (Short)', 'Universe (Unclassified)', 'ESS IDEA Universe', 'Hard-3', 'Soft-1', 'Soft-2', 'Soft-3', 'Hard-1', 'Hard-2', 'SPX INDEX Ret(%)'];

    let datasets = createDataSets(implied_probability_chart, field_names, fieldMappingsArray, false, fieldMappingsArray);

    let graphs = [];
    let counter = 1;
    let is_hidden = true;
    for (var i in fieldMappingsArray) {
        if (fieldMappingsArray[i] === 'Universe (Long)' || fieldMappingsArray[i] === 'Universe (Short)' || fieldMappingsArray[i] === 'ESS IDEA Universe') {
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
        order: [[0, 'desc']],
        columnDefs: [
            {
                targets: [2], render: function (data) {
                    return parseFloat(data).toFixed(2).toString() + " %"
                },

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
            this.api().columns([1]).every(function () {
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
    });


    $('#ess_implied_probability_table').on('click', '.btn-details', function () {
        let date = $(this).parent().data('date');
        let deal_type = $(this).parent().data('deal');
        let data = {'date': date, 'deal_type': deal_type};
        // Make Ajax Request, Gather Data in JSON, Open
        $('#modal_label').html('Implied Prob (%) for ' + deal_type + ' ( ' + date + ' )');
        $('#ess_drilldown_modal').modal('show');
        $('#ess_implied_probability_drilldown').DataTable({
            "language": {
                "processing": "Gathering Drilldown data...."
            },
            destroy: true,
            'paging': false,
            dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
                '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
                '<"row"<"col-sm-5"i><"col-sm-7"p>>',
            buttons: {
                buttons: [{
                    extend: 'copy',
                    text: '<i class="fa fa-copy"></i> Copy',
                    exportOptions: {
                        columns: ':visible',
                        stripHtml: false
                    }
                },
                ],
            },
            "createdRow": function( row, data, dataIndex){
                if(!data.implied_probability){
                    $(row).addClass('table-danger');
                }
            },
            "processing": true,
            "searching": true,
            "ajax": {
                "url": "../portfolio_optimization/ess_implied_prob_drilldown",
                "type": "POST",
                "data": data,
                dataSrc: function (json) {
                    let obj = JSON.parse(json["data"]);
                    if(obj === null){
                        swal({
                            title: "No Data available",
                            text: "Data not found!",
                            icon: "warning",
                            dangerMode: true,
                        });
                        $('#ess_drilldown_modal').modal('hide');
                    }
                    return obj;
                }
            },
            "columns": [
                {"data": "Date"},
                {"data": "alpha_ticker"},
                {"data": "price"},
                {"data": "deal_type"},
                {"data": "implied_probability"},
                {"data": "idea_link"},
            ],
            "footerCallback": function (row, data, start, end, display) {
                var api = this.api();
                var count = 1;
                // Total over all pages
                let avg = api
                    .column( 4 )
                    .data()
                    .reduce( function (a, b) {
                        var x = parseFloat(a) || 0;
                        var y = parseFloat(b) || 0;
                        if (!x) {return y;}
                        if (!y) {return x;}
                        count += 1;
                        return x + y;
                    }, 0 );
                let average = avg/count;
                // Update footer
                $(api.column(4).footer()).html(
                    average.toFixed(2).toString() + ' % ( ' + avg.toFixed(2).toString() + ' / ' + count.toString() + ' )'
                );
            }
        });
    });

});

