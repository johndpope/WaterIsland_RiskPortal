$(document).ready(function () {
    $('#submit_arb_ror_as_of').on('click', function () {
        let as_of = $('#arb_ror_as_of').val();
        if (as_of) {
            window.location.href = "../portfolio_optimization/arb_hard_optimization?as_of=" + as_of;
        }
        else {
            swal('Error!', 'Select Date please!', 'error');
        }
    });

    var table = $('#arb_hard_opt_table').DataTable({
        "order": [[9, 'desc']],
        "lengthChange": false,
        "paging":false,
        autoWidth: false,
        "columnDefs": [{
            "targets": [4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,20,21,22, 25, 26, 27],
            "render": $.fn.dataTable.render.number(',', '.', 2),
        }, {
            "targets": [13, 14],
            "render": $.fn.dataTable.render.number(',', '.', 2),
            "createdCell": function (td, cellData, rowData, rowIndex) {

                if (cellData >= 5) {
                    $(td).addClass('table-danger')
                }
                else if (cellData < 5 && cellData > 4) {
                    $(td).addClass('table-warning')
                }
            }
        },{
                targets: [4,5,6,3,7,12,13,14],
                visible: false
            }],
        scrollY: "50vh",
        scrollX: true,
        fixedColumns: {
            leftColumns: 2,
            rightColumns:1,
        },
        dom: '<"row"<"col-sm-6"Bl><"col-sm-6"f>>' +
            '<"row"<"col-sm-12"<"table-responsive"tr>>>' +
            '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        buttons: {
            buttons: [{
                extend: 'csv',
                text: '<i class="fa fa-print"></i> Export to CSV',
                className: 'btn btn-default btn-xs',
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


    $('a.toggle-vis').on( 'click', function (e) {
        e.preventDefault();

        // Get the column API object
        var column = $(this).attr('data-column');
        let columns = [];
        if(column === 'Float'){
            columns = [12,13,14]
        }
        else if(column === 'Duration'){
            columns = [3, 7]
        }
        else if(column === 'Mstrat'){
            columns = [15,16,17,18]
        }
        else if(column === 'Spread'){
            columns = [4,5,6]
        }

        for(var col_toggle=0;col_toggle<columns.length;col_toggle++){
            let col = table.column(columns[col_toggle]);
            col.visible( ! col.visible() );
        }
        // Toggle the visibility

    } );


    // Rebal Multiples
    $('#arb_hard_opt_table tr .rebal_multiple input').on('focusout', function(){

        let rebal_multiple = $(this).val();
        let id = $(this).attr('id');
        let row_id = id.split('_')[2];
        let value_to_set = null;
        if(rebal_multiple){
           // Set value of Rebal Target = multiple * ARB_% of AUM
            value_to_set = parseFloat($('#arb_pct_aum_'+row_id).html()) * parseFloat(rebal_multiple)/parseFloat($('#aed_risk_mult_'+row_id).html());
            value_to_set = parseFloat(value_to_set.toFixed(2));
        }
        else{
            // Its just AED % of AUM
            value_to_set = $('#aed_pct_aum_'+row_id).html();
        }
        $('#rebal_target_'+row_id).val(value_to_set);
    });





    $('#arb_hard_opt_table tr td button').on('click', function (e) {
        var save_button_id = $(this).attr('id');
        if (save_button_id && save_button_id.includes("save_note_")) {
            let id = save_button_id.split("_").pop();
            if (!id) {
                id = $(this).parent().parent().attr('id');
            }

            let note = $(this).parent().find("textarea").val();

            $.ajax({
                type: 'POST',
                url: '../portfolio_optimization/save_hard_opt_commment',
                data: {'id': id, 'note': note},
                success: function (response) {
                    if (response === 'Success') {
                        toastr.success('Your Note was updated!', 'Changes saved!', {
                            positionClass: 'toast-top-right',
                            containerId: 'toast-top-right'
                        });
                    }
                    else {
                        toastr.error('Failed to store the changes!', 'Please copy your edit and store it to avoid data loss!', {
                            positionClass: 'toast-top-right',
                            containerId: 'toast-top-right'
                        });
                    }
                },
                error: function (err) {
                    alert(err);
                }
            })
        }

        else if (save_button_id && save_button_id.includes("save_rebal_target_")) {
            let id = save_button_id.split("_").pop();
            if (!id) {
                id = $(this).parent().parent().attr('id');
            }

            let rebal_multiple = $('#rebal_multiple_'+id).val();

            console.log(rebal_multiple);
            let rebal_target = $('#rebal_target_'+id).val();
            console.log(rebal_target);

            // Fire an Ajax query to save the rebal multiple  and the  comment
            // $.ajax({
            //     type: 'POST',
            //     url: '../portfolio_optimization/save_hard_opt_commment',
            //     data: {'id': id, 'note': note},
            //     success: function (response) {
            //         if (response === 'Success') {
            //             toastr.success('Your Note was updated!', 'Changes saved!', {
            //                 positionClass: 'toast-top-right',
            //                 containerId: 'toast-top-right'
            //             });
            //         }
            //         else {
            //             toastr.error('Failed to store the changes!', 'Please copy your edit and store it to avoid data loss!', {
            //                 positionClass: 'toast-top-right',
            //                 containerId: 'toast-top-right'
            //             });
            //         }
            //     },
            //     error: function (err) {
            //         alert(err);
            //     }
            // })
        }


    });


});

document.onload = function () {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust()
        .fixedColumns().update()
};

$(window).resize(function () {
    $($.fn.dataTable.tables(true)).DataTable()
        .columns.adjust()
        .fixedColumns().relayout()
});
