$(document).ready(function () {
    let data_hard = $('#df_hard').val();
    data_hard = JSON.parse(data_hard);
    let portfolio_hard_table = $('#portfolio_hard_table').DataTable({
        paging: false,
        striped: true,
        pagination: true,
        sortable: true,
        processing: true,
        searching: false,
        "columns": [
            {"data": "Catalyst"},
            {"data": "Tier"},
            {"data": "Sleeve"},
            {"data": "Strategy"},
            {"data": "CurrentLongs"},
            {"data": "CurrentAUMLongs"},
            {"data": "CurrentShorts"},
            {"data": "CurrentAUMShorts"},
        ],
        "data": data_hard,
    });

    let data_soft = $('#df_soft').val();
    data_soft = JSON.parse(data_soft);
    let portfolio_soft_table = $('#portfolio_soft_table').DataTable({
        paging: false,
        striped: true,
        pagination: true,
        sortable: true,
        processing: true,
        searching: false,
        "columns": [
            {"data": "Catalyst"},
            {"data": "Tier"},
            {"data": "Sleeve"},
            {"data": "Strategy"},
            {"data": "CurrentLongs"},
            {"data": "CurrentAUMLongs"},
            {"data": "CurrentShorts"},
            {"data": "CurrentAUMShorts"},
        ],
        "data": data_soft,
    });
});
