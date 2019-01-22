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
                        var obj = JSON.parse(json["data"]);
                        return obj;
                    }
        },
        "columns":[
            {"data" :"TradeGroup"},
            {"data" :"InceptionDate"},
            {"data" :"EndDate"},
            {"data" :"Status"},
            {"data" :"YTD($)"},
            {"data" :"Qty_x"},
            {"data" :"MKTVAL_CHG_USD"},
            {"data" :"Total YTD PnL"},
            {"data" :"Threshold I"},
            {"data" :"Threshold II"},
            {"data" :"Threshold III"},
        ],
        "columnDefs": [{
            "targets": [4, 6, 7],
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