$(document).ready(function () {

    $('#submit_expoures_as_of').on('click', function(){
        // Get the Date
        let as_of = $('#exposures_as_of').val();
        window.location.replace('../exposures/exposures_snapshot?as_of='+as_of);


    });

    let exposures = $.parseJSON($('#exposures').val());

    Object.keys(exposures).forEach(function (fund) {
        addFundMainTab(fund, 'fundtabs', 'fund-tab-content', 'Across', exposures);

    });


});

function addFundMainTab(name, addToTab, addToContent, sleeve, exposures) {
    // create the tab


    // Tab content should actually be another Tab and Tab content, this time with Funds Sleeves

    // create the tab content
    if (name === 'ARB') {
        $('<li class="nav-item"><a class="nav-link active" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
        $('<div class="tab-pane active" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
    }
    else {
        $('<li class="nav-item"><a class="nav-link" href="#tab' + name + '" data-toggle="tab">' + name + '</a></li>').appendTo('#' + addToTab);
        $('<div class="tab-pane" id="tab' + name + '"><br></div>').appendTo('#' + addToContent);
    }


    // Append to id 'tab'+name another set of <ul and classes with actual fund Sleeves
    $('<ul class="nav nav-pills nav-fill" id="sleevetabs' + name + '"></ul>').appendTo('#tab' + name);

    $('<div class="tab-content" id="sleevetabcontent' + name + '"><br></div>').appendTo('#tab' + name);


    // Do this Iteratively for each fund
    Object.keys(exposures[name]).forEach(function (i) {
        // Add Fund and its Sleeve Content
        Object.keys(exposures[name][i]).forEach(function (sleeve_data) {

                if (i === '0') {
                    $('<li class="nav-item"><a class="nav-link active" href="#tab' + name + sleeve_data.replace(/ /g, '') + '" data-toggle="tab">' + sleeve_data + '</a></li>').appendTo('#sleevetabs' + name);
                }
                else {
                    $('<li class="nav-item"><a class="nav-link" href="#tab' + name + sleeve_data.replace(/ /g, '') + '" data-toggle="tab">' + sleeve_data + '</a></li>').appendTo('#sleevetabs' + name);
                }


                if (sleeve_data === 'All Sleeves') {
                    let top_data = JSON.parse(exposures[name][i][sleeve_data]);
                    $('<div class="tab-pane active" id="tab' + name + sleeve_data.replace(/ /g, '') + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + sleeve_data.replace(/ /g, '') + '">' +
                        '<tfoot><tr><td></td><td></td><td class="font-weight-bold">Total</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table><br><br><br>' +
                        '<div style="background-color: #30303d; color: #fff; width:100%;height:500px" id="PieChart_' + name + sleeve_data.replace(/ /g, '') + '"></div></div>').appendTo('#sleevetabcontent' + name);
                    initializeDatatableSummary(top_data, 'table' + name + sleeve_data.replace(/ /g, ''));
                    initializePieChart("PieChart_" + name + sleeve_data.replace(/ /g, ''), top_data, 'all'); // Show by LongShort + Sleeve
                }
                else {
                    $('<div class="tab-pane" id="tab' + name + sleeve_data.replace(/ /g, '') + '"></div>').appendTo('#sleevetabcontent' + name); //Create Tab with no Content...
                    // Add another NAV to this Tab-pane
                    $('<ul class="nav nav-pills nav-fill" id="sleevelongshort' + name + sleeve_data.replace(/ /g, '') + '"></ul>').appendTo('#tab' + name + sleeve_data.replace(/ /g, ''));
                    $('<div class="tab-content" id="Tabsleevelongshort' + name + sleeve_data.replace(/ /g, '') + '"><br></div>').appendTo('#tab' + name + sleeve_data.replace(/ /g, ''));

                    // Iterate over each Sleeve and Append the Long/Short Tabs
                    Object.keys(exposures[name][i][sleeve_data]).forEach(function (j) {

                        Object.keys(exposures[name][i][sleeve_data][j]).forEach(function (longshort) {
                            let longshort_data = JSON.parse(exposures[name][i][sleeve_data][j][longshort]);
                            // Values are Total, Long, Short
                            if (longshort === 'Total') {
                                $('<li class="nav-item"><a class="nav-link active" href="#tab' + name + sleeve_data.replace(/ /g, '') + longshort + '" data-toggle="tab">' + longshort + '</a></li>').appendTo('#sleevelongshort' + name + sleeve_data.replace(/ /g, ''));
                            }
                            else {
                                $('<li class="nav-item"><a class="nav-link" href="#tab' + name + sleeve_data.replace(/ /g, '') + longshort + '" data-toggle="tab">' + longshort + '</a></li>').appendTo('#sleevelongshort' + name + sleeve_data.replace(/ /g, ''));
                            }


                            if (longshort === 'Total') {
                                $('<div class="tab-pane active" id="tab' + name + sleeve_data.replace(/ /g, '') + longshort + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + sleeve_data.replace(/ /g, '') + longshort + '">' +
                                    '<tfoot><tr><td></td><td></td><td class="font-weight-bold">Total</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table><br><br><br>' +
                                    '<div style="background-color: #30303d; color: #fff; width:100%;height:500px" id="PieChart_' + name + sleeve_data.replace(/ /g, '') + longshort + '"></div></div>').appendTo('#Tabsleevelongshort' + name + sleeve_data.replace(/ /g, ''));

                                initializePieChart("PieChart_" + name + sleeve_data.replace(/ /g, '') + longshort, longshort_data, 'bucket');  // Show by LongShort + Bucket

                            }
                            else {
                                $('<div class="tab-pane" id="tab' + name + sleeve_data.replace(/ /g, '') + longshort + '"><table class="table table-striped text-dark" style="width:100%" id="table' + name + sleeve_data.replace(/ /g, '') + longshort + '">' +
                                    '<tfoot><tr><td></td><td></td><td class="font-weight-bold">Total</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table><br></div>').appendTo('#Tabsleevelongshort' + name + sleeve_data.replace(/ /g, ''));
                            }
                            var extra_data = "";
                            if (longshort === 'Long' || longshort === 'Short') {
                                extra_data = {"title": 'TradeGroup', data: '.tradegroup'};
                                initializeDatatableSleeves(longshort_data, 'table' + name + sleeve_data.replace(/ /g, '') + longshort, extra_data);
                            }
                            else {
                                initializeDatatableSleeves(longshort_data, 'table' + name + sleeve_data.replace(/ /g, '') + longshort, extra_data);
                            }


                        });

                    });

                }

            }
        );
        //
    });

    //data: JSON.parse(exposures[name][i][sleeve_data][j][longshort])

    //table id: #table' + name + sleeve_data.replace(/ /g, '') + longshort
    function initializeDatatableSummary(data, table_id) {
        $('#' + table_id).DataTable({
            data: data,
            lengthChange: false,
            paginate: false,
            columns: [
                {title: 'Date', data: '.date'},
                {title: 'LongShort', data: '.longshort'},
                {title: 'Sleeve', data: '.sleeve'},
                {title: 'Alpha Exposure', data: '.alpha_exposure'},
                {title: 'Hedge Exposure', data: '.hedge_exposure'},
                {title: 'Net Exposure', data: '.net_exposure'},
                {title: 'Gross Exposure', data: '.gross_exposure'},
                {title: 'Capital', data: '.capital'},
                {title: 'Directional Equity Risk', data: '.directional_equity_risk'},
                {title: 'Directional Credit Risk', data: '.directional_credit_risk'},
                {title: 'Directional IR Risk', data: '.directional_ir_risk'},
            ],
            "columnDefs": [{
                "targets": [3, 4, 5, 6, 7, 8, 9, 10],
                "createdCell": function (td, cellData, rowData, rowIndex) {
                    //Check for % Float and %Shares Out
                    if (cellData < 0) {
                        $(td).css('color', 'red')
                    }
                    else {
                        $(td).css('color', 'green')
                    }
                },
                "render": $.fn.dataTable.render.number(',', '.', 2),
            }],
            "footerCallback": function (row, data, start, end, display) {

                var api = this.api();
                nb_cols = api.columns().nodes().length;
                var j = 3;
                while (j < nb_cols) {
                    var pageTotal = api
                        .column(j, {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return parseFloat(Number(a) + Number(b)).toFixed(2);
                        }, 0);
                    // Update footer
                    if (pageTotal < 0) {
                        $(api.column(j).footer()).html('<span class="red">' + pageTotal + '</span>');
                    }
                    else {
                        $(api.column(j).footer()).html('<span class="green">' + pageTotal + '</span>');
                    }

                    j++;
                }
            }
        })
    }

    // For LongShort
    function initializeDatatableSleeves(data, table_id, extra_data) {
        var column_targets = [3, 4, 5, 6, 7, 8, 9, 10];
        var sum_start_column = 3;
        var columns_structure = [
            {title: 'Bucket', data: '.bucket'},
            {title: 'LongShort', data: '.longshort'},
            {title: 'Alpha Exposure', data: '.alpha_exposure'},
            {title: 'Hedge Exposure', data: '.hedge_exposure'},
            {title: 'Net Exposure', data: '.net_exposure'},
            {title: 'Gross Exposure', data: '.gross_exposure'},
            {title: 'Capital', data: '.capital'},
            {title: 'Directional Equity Risk', data: '.directional_equity_risk'},
            {title: 'Directional Credit Risk', data: '.directional_credit_risk'},
            {title: 'Directional IR Risk', data: '.directional_ir_risk'},];
        if (extra_data !== "") {
            columns_structure.unshift(extra_data);
            column_targets = [4, 5, 6, 7, 8, 9, 10, 11];
            sum_start_column = 4;
        }
        columns_structure.unshift({title: 'Date', data: '.date'});

        $('#' + table_id).DataTable({
            data: data,
            lengthChange: false,
            paginate: false,
            columns: columns_structure,
            "columnDefs": [{
                "targets": column_targets,
                "createdCell": function (td, cellData, rowData, rowIndex) {
                    //Check for % Float and %Shares Out
                    if (cellData < 0) {
                        $(td).css('color', 'red')
                    }
                    else {
                        $(td).css('color', 'green')
                    }
                },
                "render": $.fn.dataTable.render.number(',', '.', 2),
            }],
            "footerCallback": function (row, data, start, end, display) {

                var api = this.api();
                nb_cols = columns_structure.length;
                var j = sum_start_column;
                while (j < nb_cols) {
                    var pageTotal = api
                        .column(j, {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return parseFloat(Number(a) + Number(b)).toFixed(2);
                        }, 0);
                    // Update footer
                    if (pageTotal < 0) {

                        $(api.column(j).footer()).html('<span class="red">' + pageTotal + '</span>');
                    }
                    else {
                        $(api.column(j).footer()).html('<span class="green">' + pageTotal + '</span>');
                    }

                    j++;
                }
            }
        })
    }


    function initializePieChart(div_id, data, type) {
        // Create Proper Data Format
        var custom_data = [];

        Object.keys(data).forEach(function (index) {
            if (type === 'all') {
                custom_data.push({
                    "capital": data[index]['sleeve'] + " " + data[index]['longshort'],
                    "value": parseFloat(data[index]['capital']).toFixed(2)
                })
            }
            else {
                custom_data.push({
                    "capital": data[index]['bucket'] + " " + data[index]['longshort'],
                    "value": parseFloat(data[index]['capital']).toFixed(2)
                })
            }
        });


        AmCharts.makeChart(div_id, {
            "type": "pie",
            "theme": "dark",
            "dataProvider": custom_data,
            "valueField": "value",
            "titleField": "capital",
            "outlineAlpha": 0.4,
            "depth3D": 15,
            "labelText": "[[title]]: [[value]]" + "%",
            "angle": 30,
            "export": {
                "enabled": true
            }
        });


    }
}
