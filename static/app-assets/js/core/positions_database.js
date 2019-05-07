$(document).ready(function () {
    $('#wic_positions_table').DataTable({
        "pageLength": 100,
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'print',
                text: '<i class="fa fa-print"></i> Print',
                title: 'WIC Positions',
                customize: function (win) {

                    $(win.document.body)
                        .css('font-size', '10pt')
                        .prepend(
                            '<p> Water Island Capital, Risk Portal</p>'
                        );

                    $(win.document.body).find('table')
                        .addClass('compact')
                        .css('font-size', 'inherit');

                    var css = '@page { size: landscape; }',
                        head = win.document.head || win.document.getElementsByTagName('head')[0],
                        style = win.document.createElement('style');

                    style.type = 'text/css';
                    style.media = 'print';

                    if (style.styleSheet) {
                        style.styleSheet.cssText = css;
                    }
                    else {
                        style.appendChild(win.document.createTextNode(css));
                    }

                    head.appendChild(style);
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
        }
    });

    $('#submit_wic_positions_as_of').on('click', function(){
       // Get as of date
       let as_of = $('#wic_positions_as_of').val();
       let url = '../securities/wic_positions?as_of='+as_of;
       window.location.href = url;
    });

    // Handler for Detailed Report Download
    $('#positions_details_download').on('click', function(){
        let as_of = $('#wic_detailed_as_of').val();

        if(as_of){
            let url = '../securities/wic_positions_detailed_report_download?as_of='+as_of;
            window.location.href = url;
        }
        else{
            swal("Date required!", "Please select a date for detailed report!", "info");
        }

    });

});