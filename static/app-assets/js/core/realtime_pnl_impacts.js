$(document).ready(function () {
    let data = $('#realtime_pnl_impacts').val();

    var realtime_pnl_table = $('#realtime_pnl_table').DataTable({
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
            {"data" :"Total YTD PnL_ARB"},
            {"data" :"Total YTD PnL_AED"},
            {"data" :"Total YTD PnL_LG"},
            {"data" :"Total YTD PnL_MACO"},
            {"data" :"Total YTD PnL_TAQ"},
            {"data" :"Total YTD PnL_CAM"},

        ],
        "columnDefs": [{
            "targets": [1,2,3,4,5,6],
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


    });


setInterval( function () {
    realtime_pnl_table.ajax.reload(null, true);
    console.log('Requesting Updated P&L..');
}, 3600000); // Every Hour

});