$(document).ready(function () {

  let downsides_data = $.parseJSON($('#arb_downsides_data').val());
  let spread_data = $.parseJSON($('#spread_data').val());
  let rebate_data = $.parseJSON($('#rebate_data').val());
  let sizing_data = $.parseJSON($('#sizing_data').val());
  let scenario_data = $.parseJSON($('#scenario_data').val());
  let passive_data = $.parseJSON($('#passive_data').val());

  window.onload = function() {
    var non_decimal_fields = ['sizing_val_fund_assets', 'passive_value_size_shares', 'passive_value_spend',
                              'sizing_val_float_so', 'sizing_val_five_cap', 'hedging_hedge', 'hedging_target_short',
                              'estimated_liquidity_bbg_est_daily_vol', 'estimated_liquidity_credit_team_view']
    var all_input_fields = document.getElementsByTagName("input");
    for (var i = 0; i < all_input_fields.length; i++) {
      var input_field = all_input_fields[i];
      if (input_field.id && input_field.value && input_field.type != 'hidden') {
        var decimal = 2;
        if (input_field.id.includes('deal_terms_value_share')) {
          decimal = 4;
        }
        else if (non_decimal_fields.includes(input_field.id)) {
          decimal = 0;
        }
        else if (input_field.id.includes('days_to_close_') || input_field.id.includes('dollars_to_make_') || input_field.id.includes('dollars_to_lose_')) {
          decimal = 0;
        }
        $('#' + input_field.id).val(convert_to_decimal(input_field.value, decimal));
      }
    }
  }
  // Downsides Data Table
  var downsides_table = $('#arb_downsides_table').DataTable({
    data: downsides_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      { data: 'type' },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="upside_value_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
    responsive: true,
  });

  // Passive Phase in ARB Table
  var passive_table = $('#passive_table').DataTable({
    data: passive_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.key.toLowerCase().includes('nav')) {
            style = get_style(row.value);
          }
          if (row.type_input == 'true') {
            return '<input id="passive_value_' + row.id + '" onchange="onChange(id)" style="' + style +
              '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
          }
          else {
            return '<input id="passive_value_' + row.id + '" disabled onchange="onChange(id)" style="' + style +
              '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.value + '">';
          }
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
    responsive: true,
  });

  // Deal Terms & Spread table
  var deal_terms_spread = $('#deal_terms_spread_table').DataTable({
    data: spread_data,
    autoWidth: false,
    columns: [
      {
        orderable: false,
        render: function (data, type, row) {
          if (row.key.toLowerCase().includes('gross') | row.key.toLowerCase().includes('spread')) {
            return '<p style="font-weight: bold;">' + row.key + '</p>';
          }
          return row.key;
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.key.toLowerCase().includes('gross') | row.key.toLowerCase().includes('spread')) {
            style = "font-weight: bold;";
          }
          if (row.type_input == 'true') {
            return '<input id="deal_terms_' + row.id + '" onchange="onChange(id)" style="' + style +
              '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="30" value="' + row.type + '">';
          }
          else {
            return '<input id="deal_terms_' + row.id + '" disabled onchange="onChange(id)" style="' + style +
              '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.type + '">';
          }
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.key.toLowerCase().includes('gross') | row.key.toLowerCase().includes('spread')) {
            style = "font-weight: bold;";
          }
          if (row.type_input2 == 'true') {
            return '<input id="deal_terms_value_' + row.id + '" onchange="onChange(id)" style="' + style +
              '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
          }
          else {
            return '<input id="deal_terms_value_' + row.id + '" disabled onchange="onChange(id)" style="' + style +
              '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.value + '">';
          }
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
    responsive: true,
  });

  // Rebate level table
  var rebate_levels_table = $('#rebate_levels_table').DataTable({
    data: rebate_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          if (row.type_input == 'true') {
            return '<input id="rebate_acq_val_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.acq_value + '">';
          }
          else {
            return '<input id="rebate_acq_val_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" value="' + row.acq_value + '">';
          }
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          if (row.type_input == 'true') {
          return '<input id="rebate_target_val_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.target_value + '">';
          }
          else {
            return '<input id="rebate_target_val_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" value="' + row.target_value + '">'; 
          }
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
  });

  // Sizing table
  var sizing_table = $('#sizing_table').DataTable({
    data: sizing_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="sizing_val_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
  });

  // Scenario table
  var scenario_table = $('#scenario_table').DataTable({
    data: scenario_data,
    autoWidth: false,
    'createdRow': function( row, data, dataIndex ) {
      $(row).attr('db-id', data.database_id);
    },
    columns: [
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="scenario_' + row.id + '" class="form-control form-control-sm" type="text" maxlength="30" value="' + row.scenario + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="last_price_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.last_price + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="dividends_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.dividends + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="rebate_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.rebate + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="hedge_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.hedge + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="deal_value_' + row.id + '" disabled onchange="onChange(id)" onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.deal_value + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="spread_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.spread + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="gross_pct_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.gross_pct) +
                 '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.gross_pct + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="annual_pct_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.annual_pct) +
                 '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.annual_pct + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="exp_close_' + row.id + '" onchange="onChange(id)" class="form-control form-control-sm" type="date" value="' + row.estimated_closing_date + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="days_to_close_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.days_to_close + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="dollars_to_make_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.dollars_to_make) +
                 '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.dollars_to_make + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="dollars_to_lose_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.dollars_to_lose) +
                 '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.dollars_to_lose + '">';
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="implied_prob_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.implied_prob + '">';
        }
      },
    ],
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
  });

  // Add new row to Scenario table
  $('#addScenarioRow').on('click', function () {
    scenario_row_count = scenario_table.rows().count();
    let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + scenario_row_count.toString()).data()[0].database_id;
    let random_id = Math.random().toString().replace(".", "");
    let last_price = $('#last_price_' + db_id.toString()).val();
    let dividends = $('#dividends_' + db_id.toString()).val();
    let exp_close = $('#exp_close_' + db_id.toString()).val();
    let deal_value = $('#deal_value_' + db_id.toString()).val();
    let dollars_to_lose = $('#dollars_to_lose_' + db_id.toString()).val();
    let implied_prob = $('#implied_prob_' + db_id.toString()).val();
    let spread = convert_to_decimal(deal_value - last_price, 2);
    let credit_idea_id = parseFloat(new URLSearchParams(window.location.search).get('credit_idea_id'));
    scenario_row_count += 1;
    scenario_table.row.add(
      {
        'id': random_id, 'credit_idea_id': credit_idea_id, 'scenario': '', 'last_price': last_price, 'dividends': dividends,
        'rebate': '', 'hedge': 0.00, 'deal_value': deal_value, 'spread': spread, 'gross_pct': '', 'annual_pct': '',
        'days_to_close': '', 'dollars_to_make': '', 'dollars_to_lose': dollars_to_lose, 'implied_prob': implied_prob,
        'estimated_closing_date': exp_close, 'database_id': random_id
      }
    ).node().id = 'scenario_row_' + scenario_row_count.toString();
    scenario_table.draw(false);
    onChange('exp_close_' + random_id.toString());
  });

  // Save all the Equity card data
  $('#save_equity_button').on('click', function (event) {
    let credit_idea_id = parseFloat(new URLSearchParams(window.location.search).get('credit_idea_id'));
    let equity_data = get_master_data('equity');
    console.log(equity_data);
    save_data(credit_idea_id, equity_data)
  });

    // Save all the Credit card data
    $('#save_credit_button').on('click', function (event) {
      let credit_idea_id = parseFloat(new URLSearchParams(window.location.search).get('credit_idea_id'));
      let credit_data = get_master_data('credit');
      console.log(credit_data);
      save_data(credit_idea_id, credit_data)
    });

  function save_data(credit_idea_id, master_data) {
    $.ajax({
      type: 'POST',
      data: {'credit_idea_id':credit_idea_id, 'master_data': JSON.stringify(master_data)},
      success: function (response) {
          if (response === "success") {
              swal("Success! The Credit Idea Equity has been saved!", {icon: "success"});
              window.location.reload();
          }
          else {
              //show a sweet alert
              swal("Error!", "Saving the Credit Idea Equity Failed!", "error");
          }
      },
      error: function (error) {
          swal("Error!", "Saving the Credit Idea Equity Failed!", "error");
      }
    });
  }

  function get_master_data(section) {
    let = master_data = {}
    if (section == 'equity') {
      scenario_keys = ['scenario', 'last_price', 'dividends', 'rebate', 'hedge', 'deal_value', 'spread', 'gross_pct',
                      'annual_pct', 'days_to_close', 'dollars_to_make', 'dollars_to_lose', 'implied_prob', 'exp_close']
      row_prefix = 'scenario_';
      cell_prefix = '';
      table_ids = ['scenario_table'];
      credit_idea_details_keys = ['upside_value_upside', 'upside_value_base_downside', 'upside_value_outlier_downside',
                                  'deal_terms_target_ticker', 'deal_terms_acq_ticker', 'deal_terms_value_cash',
                                  'deal_terms_value_share', 'deal_terms_value_target_dividend', 'deal_terms_value_acq_dividend',
                                  'sizing_val_fund_assets', 'sizing_val_float_so', 'rebate_acq_val_pb_rate',
                                  'rebate_target_val_pb_rate', 'passive_value_nav_impact', 'deal_terms_value_deal_value']
      credit_data_key = 'equity_details';
      scenario_data_key = 'equity_scenario_data';
    }
    else if (section == 'credit') {
      scenario_keys = ['scenario', 'bond_last_price', 'bond_redemption', 'bond_carry_earned', 'bond_rebate',
                       'bond_hedge', 'bond_deal_value', 'bond_spread', 'returns_gross_pct', 'returns_annual_pct',
                       'returns_estimated_closing_date', 'returns_days_to_close', 'profits_principal', 'profits_carry',
                       'profits_rebate', 'profits_hedge', 'profits_total', 'profits_day_of_break']

      credit_idea_details_keys = ['bond_information_bond_ticker', 'bond_information_face_value_of_bonds',
        'bond_information_bbg_security_name', 'bond_information_bbg_interest_rate', 'bond_information_bbg_issue_size',
        'bond_price_est_purchase_price', 'bond_price_bbg_bid_price', 'bond_price_bbg_ask_price', 'bond_price_bbg_last_price',
        'potential_outcomes_value_base_break_price', 'potential_outcomes_value_conservative_break_price',
        'potential_outcomes_value_call_price', 'potential_outcomes_value_make_whole_price', 'potential_outcomes_equity_claw_value',
        'potential_outcomes_value_equity_claw_value', 'potential_outcomes_value_blend', 'potential_outcomes_value_change_of_control',
        'potential_outcomes_value_acq_credit', 'hedging_proposed_ratio', 'estimated_liquidity_bbg_est_daily_vol',
        'estimated_liquidity_bbg_actual_thirty_day', 'estimated_liquidity_credit_team_view']
      table_ids = ['scenario_without_hedge_table', 'scenario_with_hedge_table'];
      credit_data_key = 'credit_details';
      scenario_data_key = 'credit_scenario_data';
    }
    scenario_data_list = [];
    for (var k = 0; k < table_ids.length; k++) {
      table_id = table_ids[k];
      if (table_id == 'scenario_without_hedge_table') {
        row_prefix = 'scenario_wo_hedge_';
        cell_prefix = 'scenario_wo_hedge_';
      }
      else if (table_id == 'scenario_with_hedge_table') {
        row_prefix = 'scenario_w_hedge_';
        cell_prefix = 'scenario_w_hedge_';
      }
      scenario_row_count = $('#' + table_id).DataTable().rows().count();
      for (var i = 1; i <= scenario_row_count; i++) {
        scenario_temp_dict = {};
        let db_id = $('#' + table_id).DataTable().rows('#' + row_prefix + 'row_' + i.toString()).data()[0].database_id;
        for (var j = 0; j < scenario_keys.length; j++) {
          let cell_key = scenario_keys[j];
          let scenario_key = cell_prefix + cell_key;
          scenario_temp_dict[cell_key] = $('#' + scenario_key + "_" + db_id.toString()).val();
        }
        scenario_temp_dict['database_id'] = db_id;
        if (table_id == 'scenario_without_hedge_table') {
          scenario_temp_dict['is_hedge'] = false;
        }
        else if (table_id == 'scenario_with_hedge_table') {
          scenario_temp_dict['is_hedge'] = true;
        }
        scenario_data_list.push(scenario_temp_dict);
      }
    }

    credit_idea_details = {}
      for (var i = 0; i < credit_idea_details_keys.length; i++) {
        let credit_idea_details_key = credit_idea_details_keys[i];
        credit_idea_details[credit_idea_details_key] = $('#' + credit_idea_details_key).val();
    }
    master_data[scenario_data_key] = scenario_data_list;
    master_data[credit_data_key] = credit_idea_details;
    return master_data;
  }

  // Call onchange method on exp_close for all rows in Equity Scenario Table to update all other dependent fields.
  let scenario_row_count = scenario_table.rows().count();
  for (var i = 1; i <= scenario_row_count; i++) {
    let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
    $('#exp_close_' + db_id.toString()).trigger('onchange');
  }

});

function onChange(id) {
  if (id.includes('exp_close_')) {
    let row_id = id.split("_").pop()
    update_days_to_close(row_id);
    onChange('days_to_close_' + row_id);
    update_rebate_adjusted_spread_date();
  }
  else if (id.includes('days_to_close_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_rebate(row_id);
    onChange('rebate_' + row_id);
  }
  else if (id.includes('passive_value_nav_impact')) {
    update_passive_value_size_shares();
    onChange('passive_value_size_shares');
  }
  else if (id.includes('sizing_val_fund_assets')) {
    update_passive_value_size_shares();
    onChange('passive_value_size_shares');

    update_passive_value_aum();
  }
  else if (id.includes('passive_value_size_shares')) {
    update_passive_value_spend();
    onChange('passive_value_spend');

    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_dollars_to_make(db_id);
      update_dollars_to_lose(db_id);
    }
  }
  else if (id.includes('passive_value_spend')) {
    update_passive_value_aum();
  }
  else if (id.includes('sizing_val_float_so')) {
    update_sizing_val_five_cap();
    onChange('sizing_val_five_cap');
  }
  else if (id.includes('last_price_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('deal_value_' + row_id);
  }
  else if (id.includes('dividends_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('rebate_' + row_id);
  }
  else if (id.includes('hedge_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('rebate_' + row_id);
  }
  else if (id.includes('deal_terms_value_share')) {
    update_deal_terms_value_deal_value();
    onChange('deal_terms_value_deal_value');

    update_upside_value_topping_spread();
    onChange('upside_value_topping_spread');

    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_rebate(db_id);
      onChange('rebate_' + db_id.toString());
    }

    update_deal_terms_value_dvd_adjusted_spread();
    onChange('deal_terms_value_dvd_adjusted_spread')
  }
  else if (id.includes('deal_terms_value_dvd_adjusted_spread')) {
    update_deal_terms_value_rebate_adjusted_spread();
  }
  else if (id.includes('deal_terms_value_deal_value')) {
    update_deal_terms_value_gross_spread();
    onChange('deal_terms_value_gross_spread');
    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_deal_Value(db_id);
      onChange('deal_value_' + db_id);
    }
  }
  else if (id.includes('deal_terms_value_gross_spread')) {
    update_deal_terms_value_dvd_adjusted_spread();
    onChange('deal_terms_value_dvd_adjusted_spread');

    update_passive_value_size_shares();
    onChange('passive_value_size_shares');

    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_dollars_to_lose(db_id);
      update_implied_prob(db_id);
    }
  }
  else if (id.includes('rebate_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_deal_Value(row_id);
    onChange('deal_value_' + row_id);
  }
  else if (id.includes('deal_value_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_spread(row_id);
    onChange('spread_' + row_id);
  }
  else if (id.includes('spread_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_gross_pct(row_id);
    onChange('gross_pct_' + row_id);
    update_dollars_to_make(row_id);
  }
  else if (id.includes('gross_pct_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_annual_pct(row_id);
  }
  else if (id.includes('sizing_val_five_cap')) {
    update_sizing_val_capacity();
  }
  else if (id.includes('rebate_acq_val_pb_rate')) {
    update_rebate_acq_val_rebate_pct();
    onChange('rebate_acq_val_rebate_pct');
    
  }
  else if (id.includes('rebate_target_val_pb_rate')) {
    update_rebate_target_val_rebate_pct();
    // onChange('rebate_target_val_rebate_pct');
  }
  else if (id.includes('rebate_acq_val_rebate_pct')) {
    onChange('deal_terms_value_share');
  }
  else if (id.includes('rebate_acq_val_funds_rate')) {
    $('#rebate_target_val_funds_rate').val(parseFloat($('#rebate_acq_val_funds_rate').val()));
    onChange('rebate_acq_val_pb_rate');
    onChange('rebate_target_val_pb_rate');
  }
  else if (id.includes('deal_terms_value_target_ticker')) {
    update_sizing_val_capacity();
    update_deal_terms_value_curr_price();
    onChange('deal_terms_value_curr_price');
    update_upside_value_normal_spread();
    update_passive_value_spend();
    onChange('passive_value_spend');
    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_last_price(db_id);
      onChange('last_price_' + db_id.toString());
    }
  }
  else if (id.includes('deal_terms_value_curr_price')) {
    update_deal_terms_value_gross_spread();
    onChange('deal_terms_value_gross_spread');
  }
  else if (id.includes('deal_terms_value_acq_ticker')) {
    update_deal_terms_value_deal_value();
    onChange('deal_terms_value_deal_value');
    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_rebate(db_id);
      onChange('rebate_' + db_id.toString());
    }
    update_upside_value_thirty_premium();
    onChange('upside_value_thirty_premium')
  }
  else if (id.includes('upside_value_thirty_premium')) {
    update_upside_value_topping_spread();
    onChange('upside_value_topping_spread');
  }
  else if (id.includes('upside_value_topping_spread')) {
    update_passive_value_size_shares();
    onChange('passive_value_size_shares');

    scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_dollars_to_lose(db_id);
      update_implied_prob(db_id);
    }
  }
  else if (id.includes('deal_terms_value_cash')) {
    update_upside_value_topping_spread();
    onChange('upside_value_topping_spread');

    update_deal_terms_value_deal_value();
    onChange('deal_terms_value_deal_value');
  }
}

function focusOut(id) {
  $('#' + id).val($('#' + id).val().replace(/,/g, ''));
}

function update_sizing_val_capacity() {
  let capacity = ((parseFloat($('#sizing_val_five_cap').val()) *
                   parseFloat($('#deal_terms_value_target_ticker').val())) /
                  (parseFloat($('#sizing_val_fund_assets').val()))) * 100;
  $('#sizing_val_capacity').val(capacity.toFixed(2));
}

function update_rebate_acq_val_rebate_pct() {
  let rebate_pct = parseFloat($('#rebate_acq_val_funds_rate').val()) - parseFloat($('#rebate_acq_val_pb_rate').val())
  $('#rebate_acq_val_rebate_pct').val(rebate_pct.toFixed(2));
}

function update_rebate_target_val_rebate_pct() {
  let rebate_pct = parseFloat($('#rebate_target_val_funds_rate').val()) - parseFloat($('#rebate_target_val_pb_rate').val())
  $('#rebate_target_val_rebate_pct').val(rebate_pct.toFixed(2));
}

function update_annual_pct(row_id) {
  if (parseFloat($('#days_to_close_' + row_id).val()) != 0) {
    let annual = (365 / parseFloat($('#days_to_close_' + row_id).val())) * parseFloat($('#gross_pct_' + row_id).val());
    $('#annual_pct_' + row_id).val(annual.toFixed(2));
  }
}

function update_gross_pct(row_id) {
  if (parseFloat($('#last_price_' + row_id).val()) != 0) {
    let gross = (parseFloat($('#spread_' + row_id).val()) / parseFloat($('#last_price_' + row_id).val())) * 100;
    $('#gross_pct_' + row_id).val(gross.toFixed(2));
  }
}

function update_last_price(row_id) {
  $('#last_price_' + row_id.toString()).val(parseFloat($('#deal_terms_value_target_ticker').val()));
}

function update_dollars_to_make(row_id) {
  let dollars_to_make = parseFloat($('#spread_' + row_id).val()) * parseFloat($('#passive_value_size_shares').val());
  $('#dollars_to_make_' + row_id).val(dollars_to_make.toFixed());
}

function update_dollars_to_lose(row_id) {
  let dollars_to_lose = ((parseFloat($('#deal_terms_value_gross_spread').val()) - parseFloat($('#upside_value_topping_spread').val())) *
                              parseFloat($('#passive_value_size_shares').val()));
  $('#dollars_to_lose_' + row_id.toString()).val(dollars_to_lose.toFixed());
}

function update_spread(row_id) {
  let spread = parseFloat($('#deal_value_' + row_id).val()) - parseFloat($('#last_price_' + row_id).val());
  $('#spread_' + row_id).val(spread.toFixed(2));
}

function update_deal_Value(row_id) {
  let deal_value = (parseFloat($('#deal_terms_value_deal_value').val()) + parseFloat($('#dividends_' + row_id).val()) +
                    parseFloat($('#rebate_' + row_id).val()) - parseFloat($('#hedge_' + row_id).val()));
  $('#deal_value_' + row_id).val(deal_value.toFixed(2));
}

function update_deal_terms_value_deal_value() {
  let current_deal_value = parseFloat($('#deal_terms_value_cash').val()) + (parseFloat($('#deal_terms_value_share').val()) *
                           parseFloat($('#deal_terms_value_acq_ticker').val()));
  $('#deal_terms_value_deal_value').val(current_deal_value.toFixed(2));
}

function update_rebate(row_id) {
  let rebate_pct = (parseFloat($('#deal_terms_value_share').val()) * parseFloat($('#deal_terms_value_acq_ticker').val()) *
                    parseFloat($('#rebate_acq_val_rebate_pct').val()) * 0.01 * parseFloat($('#days_to_close_' + row_id.toString()).val())) / 365;
  $('#rebate_' + row_id.toString()).val(rebate_pct.toFixed(2));
}

function update_deal_terms_value_gross_spread() {
  let gross_Spread = parseFloat($('#deal_terms_value_deal_value').val()) - parseFloat($('#deal_terms_value_curr_price').val());
  $('#deal_terms_value_gross_spread').val(gross_Spread.toFixed(2));
}

function update_days_to_close(row_id) {
  let days_to_close = Math.ceil(Math.abs(new Date($('#exp_close_' + row_id).val()) - new Date()) / (1000 * 60 * 60 * 24));
  $('#days_to_close_' + row_id).val(days_to_close);
}

function update_passive_value_size_shares() {
  if ((parseFloat($('#upside_value_topping_spread').val()) - parseFloat($('#deal_terms_value_gross_spread').val())) != 0) {
    let size_in_shares = (parseFloat($('#passive_value_nav_impact').val()) * 0.01 * parseFloat($('#sizing_val_fund_assets').val())) /
                         (parseFloat($('#upside_value_topping_spread').val()) - parseFloat($('#deal_terms_value_gross_spread').val()));
    $('#passive_value_size_shares').val(Math.abs(size_in_shares).toFixed());
  }
}

function update_passive_value_aum() {
  if (parseFloat($('#sizing_val_fund_assets').val()) != 0) {
    let aum_pct = (parseFloat($('#passive_value_spend').val()) / parseFloat($('#sizing_val_fund_assets').val())) * 100;
    $('#passive_value_aum').val(aum_pct.toFixed(2));
  }
}

function update_passive_value_spend() {
  let spend = parseFloat($('#passive_value_size_shares').val()) * parseFloat($('#deal_terms_value_target_ticker').val());
  $('#passive_value_spend').val(spend.toFixed());
}

function update_sizing_val_five_cap() {
  let five_percent_cap = (parseFloat($('#sizing_val_float_so').val()) * 0.05).toFixed();
  $('#sizing_val_five_cap').val(five_percent_cap);
}

function update_deal_terms_value_curr_price() {
  $('#deal_terms_value_curr_price').val(parseFloat($('#deal_terms_value_target_ticker').val()));
}

function update_upside_value_normal_spread() {
  let upside_normal_spread = parseFloat($('#deal_terms_value_target_ticker').val()) - parseFloat($('#deal_terms_value_acq_ticker').val());
  $('#upside_value_normal_spread').val(upside_normal_spread.toFixed(2));
}

function update_upside_value_thirty_premium() {
  let upside_thirty_premium = (1 + 0.3) * parseFloat($('#deal_terms_value_acq_ticker').val());
  $('#upside_value_thirty_premium').val(upside_thirty_premium.toFixed(2));
}

function update_upside_value_topping_spread() {
  let upside_topping_spread = ((parseFloat($('#upside_value_thirty_premium').val()) * parseFloat($('#deal_terms_value_share').val())) +
                                parseFloat($('#deal_terms_value_cash').val())) - parseFloat($('#upside_value_base_downside').val())
  $('#upside_value_topping_spread').val();
}

function update_implied_prob(row_id) {
  let implied_prob = (1 - (parseFloat($('#deal_terms_value_gross_spread').val()) / parseFloat($('#upside_value_topping_spread').val()))) * 100;
  $('#implied_prob_' + row_id.toString()).val(implied_prob.toFixed(2));
}

function update_deal_terms_value_rebate_adjusted_spread() {
  let base_rebate_value = 0;
  scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_' + db_id.toString()).val().toString().toLowerCase().includes('base')) {
        base_rebate_value = parseFloat($('#rebate_' + db_id.toString()).val());
      }
  }
  let rebate_adj_spread = parseFloat($('#deal_terms_value_dvd_adjusted_spread').val()) + base_rebate_value;
  $('#deal_terms_value_rebate_adjusted_spread').val(rebate_adj_spread.toFixed(2));
}

function update_deal_terms_value_dvd_adjusted_spread() {
  let dvd_adj_spread = (parseFloat($('#deal_terms_value_gross_spread').val()) + parseFloat($('#deal_terms_value_target_dividend').val()) -
                       parseFloat($('#deal_terms_value_acq_dividend').val()) * parseFloat($('#deal_terms_value_share').val()));
  $('#deal_terms_value_dvd_adjusted_spread').val(dvd_adj_spread.toFixed(2));
}

function update_rebate_adjusted_spread_date() {
  let base_exp_close = '';
  scenario_row_count = $('#scenario_table').DataTable().rows().count();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_' + db_id.toString()).val().toString().toLowerCase().includes('base')) {
        base_exp_close = $('#exp_close_' + db_id.toString()).val();
        base_exp_close = moment(base_exp_close).format('MM/DD/YYYY');
      }
  }
  $('#deal_terms_rebate_adjusted_spread').val(base_exp_close);
}

function get_style(data_value) {
  let style = "font-weight: bold; ";
  if (parseFloat(data_value) == 0) {
    style = "";
  }
  else if (parseFloat(data_value) < 0) {
    style += "color: red; background-color: #f7073645 !important;";
  }
  else {
    style += "color: green; background-color: lightgreen !important;";
  }
  return style;
}


function convert_to_decimal(value, decimal) {
  if (isNaN(value)) {
    return value;
  }
  value = parseFloat(value);
  return value.toFixed(decimal);
}
