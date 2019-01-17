$(document).ready(function () {

    var json_deals = $('#json_speculated_deals').val();
    json_deals = $.parseJSON(json_deals);

    $('#speculated_mna_deals_table').DataTable({
       "aaData":json_deals,
       "columns":[{
           "data":"Date Loaded", render:function(data,type,row){if (data==null) {return ''} else {return data.split('T')[0]} }
           },{
            "data":"Action Id"
           },{
            "data":"Announce Date", render:function(data,type,row){if (data==null) {return ''} else {return data.split('T')[0]} }
           },{
            "data":"Proposed Date", render:function(data,type,row){if (data==null) {return ''} else {return data.split('T')[0]} }
           },{
            "data":"Target Ticker",render: function(data,type,row) {
                    return '<a href="../compare_equity_bond?target_ticker='+data+'&proposed_date='+row['Proposed Date'].split('T')[0]+'" target=_blank >'+data+'</a>'}
           },{
            "data":"Acquirer Ticker"
           },{
            "data":"Announced Premium"
           },{
            "data":"Current Premium"
           }]
    });




});
