$(document).ready(function(){
   $('#sizing_by_risk_adj_prob').on('click', function(){
       // Parse all float values
       let arb_max_risk = parseFloat($('#arb_max_risk'));
       let win_prob = parseFloat($('#win_prob').val());
       let loss_prob = parseFloat($('#lose_prob').val());
       let risk_adj_loss = parseFloat($('#risk_adj_loss').val());

       let data = {
           'arb_max_risk': arb_max_risk,
           'win_prob': win_prob,
           'loss_prob': loss_prob,
           'risk_adj_loss': risk_adj_loss
       };
       // Sumbit Ajax Request and Show Toastr
       submitAjaxRequest(data, '../portfolio_optimization/update_normlized_sizing_by_risk_adj_prob');
   });


   $('#soft_catalyst_risk_sizing_table tr td button').on('click', function(){
       let tr = $(this).closest('tr');
       let inputs = tr.find('input');
       let tds = tr.find('td');

       let tier = $(tds[0]).text();
       let win_probability = parseFloat($(inputs[0]).val());
       let loss_probability = parseFloat($(inputs[1]).val());
       let max_risk = parseFloat($(inputs[2]).val());
       let avg_position = parseFloat($(inputs[3]).val());
       // Set the Attributes

       let data = {
           'tier': tier,
           'win_probability': win_probability,
           'loss_probability': loss_probability,
           'max_risk': max_risk,
           'avg_position': avg_position
       };

       submitAjaxRequest(data, '../portfolio_optimization/update_soft_catalyst_risk_sizing');
   });




   $('#win_prob').on('focusout', function(){
      // Parse and cal all float values
      let arb_max_risk = parseFloat($('#arb_max_risk').val());
      let win_prob = parseFloat($('#win_prob').val());

      let lose_prob = 100.0 - win_prob;
      let risk_adj_loss = arb_max_risk * lose_prob/100.0;

      $('#lose_prob').val(lose_prob+" %");
      $('#risk_adj_loss').val(risk_adj_loss+ " %")

   });


   $("#soft_catalyst_risk_sizing_table tr td .soft_focus_out").on('focusout', function(){
       let tr = $(this).closest('tr');
       let inputs = tr.find('input');
       let tds = tr.find('td');
       let win_probability = parseFloat($(inputs[0]).val());
       let loss_probability = 100.0 -  win_probability;
       let max_risk = parseFloat($('#risk_adj_loss').val())/ (loss_probability) * 100.0;
       max_risk = max_risk.toFixed(2)
       // If H 1 then 20% weight else 25% weight for Avg Positions
       let weight = 25;
       if($(tds[0]).text() === 'H 1'){
           weight = 20;
       }
       let avg_position = Math.abs((max_risk / weight)*100.0).toFixed(2);
       // Set the Attributes
       $(inputs[1]).val(loss_probability);
       $(inputs[2]).val(max_risk);
       $(inputs[3]).val(avg_position);
   });


    function submitAjaxRequest(data, url){
       $.ajax({
           type: 'POST',
           data: data,
           url: url,
           success:function(response){
               if (response === 'Failed') {
                    toastr.error('Updating Failed', 'Please check your Inputs', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
                else {
                    toastr.success('Successfully Updated', 'Please Refresh the page', {
                        positionClass: 'toast-top-right',
                        containerId: 'toast-top-right'
                    });
                }
           },
           error: function(err){
               alert(err);
           }
       })


    }

    // Deal Type Table Script

    var deal_type_table = $('#deal_type_table').DataTable({
        "aaSorting": [[0,'desc']],
        "pageLength": 10,
    });

    $('#ess_optimization_new_type').on("click", function(){
        $('#modal_label').html('Add New Deal Type');
        $('#deal_type_id_to_edit').val("");
    });

    $('.table-responsive').on("click", "#deal_type_table tr td li a", function (e) {
        var current_deal_type = this.id.toString();
        // Handle Selected Logic Here
        if (current_deal_type.search('edit_deal_type_') != -1) {
            var deal_type_id_to_edit = current_deal_type.split('_').pop(); //Get the ID
            $('#submit_deal_type_edit_form').trigger('reset');
            $('#modal_label').html('Edit Deal Type');
            var deal_type = '';
            var long_probability = '';
            var long_irr = '';
            var long_max_risk = '';
            var long_max_size = '';
            var short_probability = '';
            var short_irr = '';
            var short_max_risk = '';
            var short_max_size = '';
            $.ajax({
                url: "../portfolio_optimization/get_deal_type_details/",
                type: 'POST',
                data: {'deal_type_id_to_edit': deal_type_id_to_edit},
                success: function (response) {
                    let deal_type_details = response['deal_type_details'];
                    deal_type = deal_type_details.deal_type;
                    long_probability = deal_type_details.long_probability;
                    long_irr = deal_type_details.long_irr;
                    long_max_risk = deal_type_details.long_max_risk;
                    long_max_size = deal_type_details.long_max_size;
                    short_probability = deal_type_details.short_probability;
                    short_irr = deal_type_details.short_irr;
                    short_max_risk = deal_type_details.short_max_risk;
                    short_max_size = deal_type_details.short_max_size;
                    $('#deal_type').val(deal_type);
                    $('#long_probability').val(long_probability);
                    $('#long_irr').val(long_irr);
                    $('#long_max_risk').val(long_max_risk);
                    $('#long_max_size').val(long_max_size);
                    $('#short_probability').val(short_probability);
                    $('#short_irr').val(short_irr);
                    $('#short_max_risk').val(short_max_risk);
                    $('#short_max_size').val(short_max_size);
                    console.log("HERE", deal_type_id_to_edit);
                    $('#deal_type_id_to_edit').val(deal_type_id_to_edit);
                },
                error: function (err) {
                    console.log(err);
                }
            });
            $('#add_new_deal_type_modal').modal('show');
        }
        else if (current_deal_type.search('delete_deal_type_') != -1) {
            //First Popup sweetAlert to Confirm Deletion
            deal_type_id_to_edit = current_deal_type.split('_').pop();

            swal({
                title: "Are you sure?",
                text: "Once deleted, you will not be able to recover this deal type!",
                icon: "warning",
                buttons: true,
                dangerMode: true,
            }).then((willDelete) => {
                if (willDelete) {
                    //Handle Ajax request to Delete
                    $.ajax({
                        type: 'POST',
                        url: '../portfolio_optimization/delete_deal_type/',
                        data: {'id': deal_type_id_to_edit},
                        success: function (response) {
                            if (response === "deal_type_deleted") {
                                //Delete Row from DataTable
                                swal("Success! The Deal Type has been deleted!", {icon: "success"});
                                //ReDraw The Table by Removing the Row with ID equivalent to dealkey
                                deal_type_table.row($("#row_" + deal_type_id_to_edit)).remove().draw();

                            }
                            else if (response === 'deal_does_not_exist') {
                                location.reload();
                            }
                            else {
                                //show a sweet alert
                                swal("Error!", "Deleting Deal Type Failed!", "error");
                                console.log('Deletion failed');
                            }
                        },
                        error: function (error) {
                            swal("Error!", "Deleting Deal Type Failed!", "error");
                            console.log(error);
                        }
                    });

                }
            });
        }
    });
});