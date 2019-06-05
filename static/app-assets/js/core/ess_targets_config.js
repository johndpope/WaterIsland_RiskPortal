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
});