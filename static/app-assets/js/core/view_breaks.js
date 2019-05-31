$(document).ready(function () {
    let data = $('#data').val();
    data = JSON.parse(data);
    let breaks_table = $('#breaks_table').DataTable({
        paging: true,
        pageLength: 25,
        striped: true,
        pagination: true,
        sortable: true,
        processing: true,
        searching: true,
        "columns": [
            {"data": "Business Date"},
            {"data": "Client ID"},
            {"data": "Account Mnemonic"},
            {"data": "Account Number"},
            {"data": "Product Type"},
            {"data": "Trade Date Quantity"},
        ],
        "data": data,
        columnDefs: [{
            targets: [0], render: function (data) {
                return moment(data, 'YYYYMMDD').format('YYYY-MM-DD');
            }
        }],
        "aaSorting": [[0,'desc'],
    });
});