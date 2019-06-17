$(document).ready(function () {
    var first_tab_row = true;
    let summary_data = $.parseJSON($('#summary_data').val());
    if (summary_data.msg == 'Success') {
        let data = summary_data.data;
        if (typeof data === 'object') {
            let data_keys_parent = '';
            let data_keys = Object.keys(data);
            addTabs(data_keys_parent, data_keys, data, 0, 'appendData', 'ul_id_0', first_tab_row);
        }
        $(".loader-wrapper").remove();
    }
    else {
        alert("ERROR");
    }

    function addTabs(data_keys_parent, data_keys, data, tab_row_count, div_id, ul_id, first_tab_row) {
        if (first_tab_row) {
            $('<ul class="nav nav-tabs nav-justified nav-underline no-hover-bg" id="' + ul_id + '"></ul>').appendTo('#' + div_id);
        }
        else {
            $('<ul class="nav nav-pills nav-fill" id="' + ul_id + '"></ul>').appendTo('#' + div_id);
        }
        $('<div class="tab-content" id="tab_content_' + data_keys_parent + tab_row_count + '"></div>').appendTo('#' + div_id);
        data_keys.forEach(function (name, index) {
            let modified_name = name.replace('<', '1').replace('>', 2).replace(/[^\w\s]/gi, '').replace(/ /g, '');
            id_name = data_keys_parent + modified_name
            $('<li class="nav-item"><a class="nav-link" href="#tab' + id_name + '" data-toggle="tab" id="a_' + id_name + '">' + name + '</a></li>').appendTo('#' + ul_id);
            $('<div class="tab-pane" id="tab' + id_name + '"><br></div>').appendTo('#tab_content_' + data_keys_parent + tab_row_count);
            if (index == 0) {
                $('#a_' + id_name).addClass('active');
                $('#tab' + id_name).addClass('active');
            }     
            if (typeof data[name] === 'object' & !Array.isArray(data[name])) {
                let new_div_id = 'tab' + id_name;
                addTabs(id_name, Object.keys(data[name]), data[name], tab_row_count + 1, new_div_id, 'ul_id_' + id_name);
            }
            else {
                $('<br><table class="table table-striped text-dark" style="width:100%" id="table' + id_name + '"><tfoot><tr><td></td><td class="font-weight-bold">Total</td><td></td><td></td><td></td><td></td><td></td><td></td></tr></tfoot></table>').appendTo('#tab' + id_name);
                initializeDatatable(data[name], 'table' + id_name);
            }
        });
    }

    function initializeDatatable(data, table_id) {
        $('#' + table_id).DataTable({
            data: data,
            lengthChange: false,
            dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
                '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
                '<"row"<"col-sm-5"i><"col-sm-7"p>>',

            buttons: {
                buttons: [{
                    extend: 'print',
                    text: '<i class="fa fa-print"></i> Print',
                    title: 'Risk Factors Summary',
                    customize: function (win) {
                        $(win.document.body)
                            .css('font-size', '10pt')
                            .prepend(
                                '<p> Water Island Capital, Risk Portal</p>'
                            );

                        $(win.document.body).find('table')
                            .addClass('compact')
                            .css('font-size', 'inherit');
                    },
                    autoPrint: true,
                }, {
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
            paginate: false,
            columns: [
                {title: 'Deal Name', data: 'deal_name'},
                {title: 'Status', data: 'deal_status'},
                {title: 'Alpha Mkt Val', data: 'alpha_mkt_val'},
                {title: 'Alpha Hedge Mkt Val', data: 'alphahedge_mkt_val'},
                {title: 'Hedhe Mkt Val', data: 'hedge_mkt_val'},
                {title: 'Alpha AlphaHedge Mkt Val', data: 'alpha_alphahedge_val'},
                {title: 'Deal Mkt Val', data: 'deal_mkt_val'},
                {title: 'Base Case NAV Impacts', data: 'base_case_nav_impacts'},
            ],
            "columnDefs": [{
                "targets": [2, 3, 4, 5, 6, 7],
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
                var j = 2;
                while (j < nb_cols) {
                    var pageTotal = api
                        .column(j, {page: 'current'})
                        .data()
                        .reduce(function (a, b) {
                            return parseFloat(Number(a) + Number(b)).toFixed(2);
                        }, 0);
                    // Update footer
                    if (pageTotal < 0) {
                        pageTotal = parseFloat(pageTotal).toLocaleString('en-US');
                        $(api.column(j).footer()).html('<span class="red">' + pageTotal + '</span>');
                    }
                    else {
                        pageTotal = parseFloat(pageTotal).toLocaleString('en-US');
                        $(api.column(j).footer()).html('<span class="green">' + pageTotal + '</span>');
                    }

                    j++;
                }
            }
        })
    }


});