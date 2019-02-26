$(document).ready(function () {
    let data = $('#realtime_pnl_impacts').val();

    var realtime_pnl_table = $('#realtime_pnl_table').DataTable({
        "lengthChange": false,
        "paging": false,
        "language": {
        "processing": "Refreshing PnL"
        },

        "processing": true,
        "searching":true,
        "ajax":{
            "url":"live_tradegroup_pnl",
            "type":"POST",
            dataSrc: function (json) {
                        let obj = JSON.parse(json["data"]);
                        return obj;
                    }
        },
        "columns":[
            {"data" :"TradeGroup_"},
            {"data" :"Sleeve_"},
            {"data" :"Catalyst_"},
            {"data" :"Total YTD PnL_ARB"},
            {"data" :"Total YTD PnL_AED"},
            {"data" :"Total YTD PnL_LG"},
            {"data" :"Total YTD PnL_MACO"},
            {"data" :"Total YTD PnL_TAQ"},
            {"data" :"Total YTD PnL_CAM"},

        ],
        "columnDefs": [{
            "targets": [3,4,5,6,7,8],
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
        initComplete: function () {
            this.api().columns([1, 2]).every(function () {
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

    });


setInterval( function () {
    realtime_pnl_table.ajax.reload(null, true);
    console.log('Requesting Updated P&L..');
}, 3600000); // Every Hour

});