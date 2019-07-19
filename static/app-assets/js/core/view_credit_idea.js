$(document).ready(function () {

  let downsides_data = $.parseJSON($('#arb_downsides_data').val());
  let spread_data = $.parseJSON($('#spread_data').val());
  let rebate_data = $.parseJSON($('#rebate_data').val());
  let sizing_data = $.parseJSON($('#sizing_data').val());
  let scenario_data = $.parseJSON($('#scenario_data').val());
  let passive_data = $.parseJSON($('#passive_data').val());

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
          return '<input id="upside_value_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + convert_to_decimal(row.value, 2) + '">';
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
    let scenario_row_count = scenario_table.rows().count();
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
      scenario_keys = ['upside', 'downside', 'scenario', 'is_deal_closed', 'bond_last_price',
                       'bond_redemption', 'bond_carry_earned', 'bond_rebate', 'bond_hedge', 'bond_deal_value',
                       'bond_spread', 'returns_gross_pct', 'returns_annual_pct', 'returns_estimated_closing_date',
                       'returns_days_to_close', 'profits_principal', 'profits_carry', 'profits_rebate', 'profits_hedge',
                       'profits_total', 'profits_day_of_break']

      credit_idea_details_keys = ['bond_information_bond_ticker', 'passive_phase_arb_face_value_of_bonds',
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
      let scenario_row_count = document.getElementById(table_id + "_tbody").rows.length;
      for (var i = 1; i <= scenario_row_count; i++) {
        scenario_temp_dict = {};
        let db_id = $('#' + table_id).DataTable().rows('#' + row_prefix + 'row_' + i.toString()).data()[0].database_id;
        for (var j = 0; j < scenario_keys.length; j++) {
          let cell_key = scenario_keys[j];
          let scenario_key = cell_prefix + cell_key;
          scenario_temp_dict[cell_key] = $('#' + scenario_key + "_" + db_id.toString()).val();
        }
        let is_upside = false;
        let is_downside = false;
        if (parseFloat($('input[name=' + cell_prefix + 'upside]:checked').val()) == parseFloat(db_id)) {
          is_upside = true;
        }
        if (parseFloat($('input[name=' + cell_prefix + 'downside]:checked').val()) == parseFloat(db_id)) {
          is_downside = true;
        }
        scenario_temp_dict['is_upside'] = is_upside;
        scenario_temp_dict['is_downside'] = is_downside;
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
  let scenario_table_row_count = scenario_table.rows().count();
  for (var i = 1; i <= scenario_table_row_count; i++) {
    let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
    $('#exp_close_' + db_id.toString()).trigger('onchange');
  }

});

function onChange(id) {
  if (id.startsWith('exp_close_')) {
    let row_id = id.split("_").pop()
    update_days_to_close(row_id);
    onChange('days_to_close_' + row_id);
    update_rebate_adjusted_spread_date();
    let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_returns_estimated_closing_date(db_id);
      onChange('scenario_w_hedge_returns_estimated_closing_date_' + db_id.toString());
    }

    scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_wo_hedge_returns_estimated_closing_date(db_id);
      onChange('scenario_wo_hedge_returns_estimated_closing_date_' + db_id.toString());
    }
  }
  else if (id.startsWith('scenario_w_hedge_returns_estimated_closing_date_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_returns_days_to_close(row_id);
    onChange('scenario_w_hedge_returns_days_to_close_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_returns_estimated_closing_date_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_returns_days_to_close(row_id);
    onChange('scenario_wo_hedge_returns_days_to_close_' + row_id);
  }
  else if (id.startsWith('days_to_close_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_rebate(row_id);
    onChange('rebate_' + row_id);
    if ($('#scenario_' + row_id.toString()).val().toString().toLowerCase().includes('base')) {
      update_hedging_less_short_rebate(row_id);
      onChange('hedging_less_short_rebate');
    }
  }
  else if (id.startsWith('scenario_w_hedge_returns_days_to_close_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_returns_annual_pct(row_id);
    update_scenario_w_hedge_bond_carry_earned(row_id);
    onChange('scenario_w_hedge_bond_carry_earned_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_returns_days_to_close_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_returns_annual_pct(row_id);
    update_scenario_wo_hedge_bond_carry_earned(row_id);
    onChange('scenario_wo_hedge_bond_carry_earned_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_bond_carry_earned_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_bond_deal_value(row_id);
    onChange('scenario_wo_hedge_bond_deal_value_' + row_id);
    update_scenario_wo_hedge_profits_carry(row_id);
    onChange('scenario_wo_hedge_profits_carry_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_profits_carry_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_profits_total(row_id);
  }
  else if (id.startsWith('scenario_w_hedge_profits_carry_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_profits_total(row_id);
  }
  else if (id.startsWith('scenario_w_hedge_bond_carry_earned_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_bond_deal_value(row_id);
    onChange('scenario_w_hedge_bond_deal_value_' + row_id);
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

    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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
  else if (id.startsWith('last_price_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('deal_value_' + row_id);
  }
  else if (id.startsWith('dividends_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('rebate_' + row_id);
  }
  else if (id.startsWith('hedge_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    onChange('rebate_' + row_id);
  }
  else if (id.includes('deal_terms_value_share')) {
    update_deal_terms_value_deal_value();
    onChange('deal_terms_value_deal_value');

    update_upside_value_topping_spread();
    onChange('upside_value_topping_spread');

    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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
    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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

    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_dollars_to_lose(db_id);
      update_implied_prob(db_id);
    }
  }
  else if (id.startsWith('rebate_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_deal_Value(row_id);
    onChange('deal_value_' + row_id);
    if ($('#scenario_' + row_id.toString()).val().toString().toLowerCase().includes('base')) {
      update_hedging_less_rebate(row_id);
      onChange('hedging_less_rebate');
    }
  }
  else if (id.startsWith('deal_value_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_spread(row_id);
    onChange('spread_' + row_id);
  }
  else if (id.startsWith('spread_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_gross_pct(row_id);
    onChange('gross_pct_' + row_id);
    update_dollars_to_make(row_id);
    if ($('#scenario_' + row_id.toString()).val().toString().toLowerCase().includes('base')) {
      update_hedging_arb_spread(row_id);
      onChange('hedging_arb_spread');
    }
  }
  else if (id.startsWith('gross_pct_') & (id.match(/\d+$/) != undefined )) {
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
    onChange('rebate_target_val_rebate_pct');
  }
  else if (id == 'rebate_target_val_rebate_pct') {
    update_hedging_less_short_rebate();
    onChange('hedging_less_short_rebate');
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
    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      update_last_price(db_id);
      onChange('last_price_' + db_id.toString());
    }
    update_hedging_target_short();
    onChange('hedging_target_short');
    update_hedging_less_short_rebate();
    onChange('hedging_less_short_rebate');
  }
  else if (id.includes('deal_terms_value_curr_price')) {
    update_deal_terms_value_gross_spread();
    onChange('deal_terms_value_gross_spread');
  }
  else if (id.includes('deal_terms_value_acq_ticker')) {
    update_deal_terms_value_deal_value();
    onChange('deal_terms_value_deal_value');
    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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

    let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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
  else if (id == 'passive_phase_arb_face_value_of_bonds') {
    update_passive_phase_arb_arb_spend();
    onChange('passive_phase_arb_arb_spend');

    let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_bond_rebate(db_id);
      onChange('scenario_w_hedge_bond_rebate_' + db_id);
      update_scenario_w_hedge_profits_principal(db_id);
      onChange('scenario_w_hedge_profits_principal_' + db_id);
      update_scenario_w_hedge_profits_carry(db_id);
      onChange('scenario_w_hedge_profits_carry_' + db_id);
      update_scenario_w_hedge_profits_rebate(db_id);
      onChange('scenario_w_hedge_profits_rebate_' + db_id);
    }

    scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_wo_hedge_profits_principal(db_id);
      onChange('scenario_wo_hedge_profits_principal_' + db_id);
      update_scenario_wo_hedge_profits_carry(db_id);
      onChange('scenario_wo_hedge_profits_carry_' + db_id);
    }
  }
  else if (id == 'passive_phase_arb_arb_spend') {
    update_hedging_hedge();
    onChange('hedging_hedge');
  }
  else if (id == 'hedging_hedge') {
    update_hedging_target_short();
    onChange('hedging_target_short');
  }
  else if (id == 'hedging_target_short') {
    let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_bond_rebate(db_id);
      onChange('scenario_w_hedge_bond_rebate_' + db_id.toString());
      // update_scenario_w_hedge_bond_hedge(db_id); TO-DO
      // onChange('scenario_w_hedge_bond_hedge_' + db_id.toString()); TO-DO
    }
  }
  else if (id == 'hedging_proposed_ratio') {
    update_hedging_hedge();
    onChange('hedging_hedge');
  }
  else if (id == 'hedging_arb_spread') {
    update_hedging_short_spread();
  }
  else if (id == 'hedging_less_rebate') {
    update_hedging_short_spread();
  }
  else if (id == 'hedging_less_short_rebate') {
    update_hedging_short_spread();

    let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_bond_rebate(db_id);
      onChange('scenario_w_hedge_bond_rebate_' + db_id);
    }
  }
  else if (id.startsWith('scenario_w_hedge_bond_rebate_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_bond_deal_value(row_id);
    onChange('scenario_w_hedge_bond_deal_value_' + row_id);
    update_scenario_w_hedge_profits_rebate(row_id);
    onChange('scenario_w_hedge_profits_rebate_' + row_id);

  }
  else if (id.startsWith('scenario_w_hedge_bond_deal_value_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_bond_spread(row_id);
    onChange('scenario_w_hedge_bond_spread_' + row_id);
  }
  else if (id.startsWith('scenario_w_hedge_bond_spread_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_returns_gross_pct(row_id);
    onChange('scenario_w_hedge_returns_gross_pct_' + row_id);
  }
  else if (id.startsWith('scenario_w_hedge_returns_gross_pct_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_returns_annual_pct(row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_bond_deal_value_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_bond_spread(row_id);
    onChange('scenario_wo_hedge_bond_spread_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_bond_spread_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_returns_gross_pct(row_id);
    onChange('scenario_wo_hedge_returns_gross_pct_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_returns_gross_pct_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_returns_annual_pct(row_id);
  }
  else if (id.startsWith('scenario_w_hedge_profits_rebate_')  & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_profits_total(row_id);
  }
  else if (id == 'bond_price_est_purchase_price') {
    update_passive_phase_arb_arb_spend();
    onChange('passive_phase_arb_arb_spend');

    let scenario_hedge_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_hedge_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_bond_last_price(db_id);
      onChange('scenario_w_hedge_bond_last_price_' + db_id.toString());
    }

    let scenario_wo_hedge_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_wo_hedge_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_wo_hedge_bond_last_price(db_id);
      onChange('scenario_wo_hedge_bond_last_price_' + db_id.toString());
    }
  }
  else if (id.startsWith('scenario_w_hedge_bond_last_price_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_bond_spread(row_id);
    onChange('scenario_w_hedge_bond_spread_' + row_id);
    update_scenario_w_hedge_profits_principal(row_id);
    onChange('scenario_w_hedge_profits_principal_' + row_id);
  }
  else if (id.startsWith('scenario_w_hedge_profits_principal_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_profits_total(row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_bond_last_price_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_bond_spread(row_id);
    onChange('scenario_wo_hedge_bond_spread_' + row_id);
    update_scenario_wo_hedge_returns_gross_pct(row_id);
    onChange('scenario_wo_hedge_returns_gross_pct_' + row_id);
    update_scenario_wo_hedge_profits_principal(row_id);
    onChange('scenario_wo_hedge_profits_principal_' + row_id);
  }
  else if (id == 'potential_outcomes_value_base_break_price') {
    let row_id = '3';
    let scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_wo_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes('no deal (base case)')) {
        row_id = db_id;
      }
    }
    update_scenario_wo_hedge_bond_redemption(row_id, 'potential_outcomes_value_base_break_price');
    onChange('scenario_wo_hedge_bond_redemption_' + row_id);
  }
  else if (id.startsWith('scenario_wo_hedge_bond_redemption_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_wo_hedge_bond_deal_value(row_id);
    onChange('scenario_wo_hedge_bond_deal_value_' + row_id);
    update_scenario_wo_hedge_profits_principal(row_id);
    onChange('scenario_wo_hedge_profits_principal_' + row_id);
    let redemption_row_id = '3';
    let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    let matching_scenario = $('#scenario_wo_hedge_scenario_' + row_id).val();
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_w_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes(matching_scenario.toLowerCase())) {
        redemption_row_id = db_id;
      }
    }
    update_scenario_w_hedge_bond_redemption(redemption_row_id, id);
    onChange('scenario_w_hedge_bond_redemption_' + row_id);
  }
  else if (id.startsWith('scenario_w_hedge_bond_redemption_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_bond_deal_value(row_id);
    onChange('scenario_w_hedge_bond_deal_value_' + row_id);
    update_scenario_w_hedge_profits_principal(row_id);
    onChange('scenario_w_hedge_profits_principal_' + row_id);
  }
  else if (id == 'potential_outcomes_value_conservative_break_price') {
    let row_id = '3';
    let scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_wo_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes('no deal (conservative case)')) {
        row_id = db_id;
      }
    }
    update_scenario_wo_hedge_bond_redemption(row_id, 'potential_outcomes_value_conservative_break_price');
    onChange('scenario_wo_hedge_bond_redemption_' + row_id);
  }
  else if (id == 'potential_outcomes_value_call_price') {
    let row_id = '3';
    let scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_wo_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes('bonds called (redemption)')) {
        row_id = db_id;
      }
    }
    update_scenario_wo_hedge_bond_redemption(row_id, 'potential_outcomes_value_call_price');
    onChange('scenario_wo_hedge_bond_redemption_' + row_id);
  }
  else if (id == 'potential_outcomes_value_make_whole_price') {
    update_potential_outcomes_value_blend();
  }
  else if (id == 'potential_outcomes_equity_claw_value') {
    update_potential_outcomes_value_blend();
  }
  else if (id == 'potential_outcomes_value_equity_claw_value') {
    update_potential_outcomes_value_blend();
  }
  else if (id == 'potential_outcomes_value_change_of_control') {
    let row_id = '3';
    let scenario_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_wo_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes('change of control (coc)')) {
        row_id = db_id;
      }
    }
    update_scenario_wo_hedge_bond_redemption(row_id, 'potential_outcomes_value_change_of_control');
    onChange('scenario_wo_hedge_bond_redemption_' + row_id);
  }
  else if (id == 'bond_information_bbg_interest_rate') {
    update_potential_outcomes_value_equity_claw_value();
    onChange('potential_outcomes_value_equity_claw_value');

    let scenario_hedge_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_hedge_row_count; i++) {
      let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_w_hedge_bond_carry_earned(db_id);
      onChange('scenario_w_hedge_bond_carry_earned_' + db_id);
    }
    scenario_hedge_row_count = document.getElementById("scenario_without_hedge_table_tbody").rows.length;
    for (var i = 1; i <= scenario_hedge_row_count; i++) {
      let db_id = $('#scenario_without_hedge_table').DataTable().rows('#scenario_wo_hedge_row_' + i.toString()).data()[0].database_id;
      update_scenario_wo_hedge_bond_carry_earned(db_id);
      onChange('scenario_wo_hedge_bond_carry_earned_' + db_id);
    }
  }
  else if (id.startsWith('scenario_wo_hedge_is_deal_closed_') & (id.match(/\d+$/) != undefined )) {
    let row_id = id.split("_").pop();
    update_scenario_w_hedge_is_deal_closed(row_id);
  }

}

function focusOut(id) {
  $('#' + id).val($('#' + id).val().replace(/,/g, ''));
}

function update_potential_outcomes_value_equity_claw_value() {
  let equity_claw_value = 100 + parseFloat($('#bond_information_bbg_interest_rate').val());
  $('#potential_outcomes_value_equity_claw_value').val(convert_to_decimal(equity_claw_value, 3));
}

function update_potential_outcomes_value_blend() {
  let potential_blend = 0;
  let potential_make_whole_price = parseFloat($('#potential_outcomes_value_make_whole_price').val());
  if (potential_make_whole_price == 0 || potential_make_whole_price == '' || isNaN(potential_make_whole_price)) {
    potential_blend = 0;
  }
  else {
    potential_blend = parseFloat($('#potential_outcomes_value_equity_claw_value').val()) *
                      parseFloat($('#potential_outcomes_equity_claw_value').val()) * 0.01 +
                      (1 - parseFloat($('#potential_outcomes_equity_claw_value').val()) * 0.01) * potential_make_whole_price;
  }
  $('#potential_outcomes_value_blend').val(convert_to_decimal(potential_blend, 3));
}

function update_scenario_wo_hedge_bond_redemption(row_id, source_id) {
  let value = parseFloat($('#' + source_id).val());
  $('#scenario_wo_hedge_bond_redemption_' + row_id.toString()).val(convert_to_decimal(value, 3));
}

function update_scenario_w_hedge_is_deal_closed(row_id) {
  let source_id = '1';
  let matching_scenario = $('#scenario_wo_hedge_scenario_' + row_id.toString()).val().toString().toLowerCase();
  let scenario_row_count = document.getElementById("scenario_with_hedge_table_tbody").rows.length;
  for (var i = 1; i <= scenario_row_count; i++) {
    let db_id = $('#scenario_with_hedge_table').DataTable().rows('#scenario_w_hedge_row_' + i.toString()).data()[0].database_id;
    if ($('#scenario_w_hedge_scenario_' + db_id.toString()).val().toString().toLowerCase().includes(matching_scenario)) {
      source_id = db_id;
    }
  }
  let value = $('#scenario_wo_hedge_is_deal_closed_' + row_id.toString()).val();
  $('#scenario_w_hedge_is_deal_closed_' + source_id.toString()).val(value);
}

function update_scenario_w_hedge_bond_redemption(row_id, source_id) {
  let value = parseFloat($('#' + source_id).val());
  $('#scenario_w_hedge_bond_redemption_' + row_id.toString()).val(convert_to_decimal(value, 3));
}

function update_scenario_w_hedge_returns_estimated_closing_date(row_id) {
  let base_exp_close = '';
  let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
  for (var i = 1; i <= scenario_row_count; i++) {
    let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
    if ($('#scenario_' + db_id.toString()).val().toString().toLowerCase().includes('base')) {
      base_exp_close = $('#exp_close_' + db_id.toString()).val();
    }
  }
  $('#scenario_w_hedge_returns_estimated_closing_date_' + row_id).val(base_exp_close);
}

function update_scenario_wo_hedge_profits_carry(row_id) {
  let profits_carry = parseFloat($('#scenario_wo_hedge_bond_carry_earned_' + row_id).val()) *
                      parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 0.01;
  $('#scenario_wo_hedge_profits_carry_' + row_id).val(convert_to_decimal(profits_carry, 0));
  update_color('scenario_wo_hedge_profits_carry_' + row_id, profits_carry);
}

function update_scenario_w_hedge_profits_carry(row_id) {
  let profits_carry = parseFloat($('#scenario_w_hedge_bond_carry_earned_' + row_id).val()) *
                      parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 0.01;
  $('#scenario_w_hedge_profits_carry_' + row_id).val(convert_to_decimal(profits_carry, 0));
  update_color('scenario_w_hedge_profits_carry_' + row_id, profits_carry);
}

function update_scenario_wo_hedge_returns_estimated_closing_date(row_id) {
  let base_exp_close = '';
  let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
  for (var i = 1; i <= scenario_row_count; i++) {
    let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
    if ($('#scenario_' + db_id.toString()).val().toString().toLowerCase().includes('base')) {
      base_exp_close = $('#exp_close_' + db_id.toString()).val();
    }
  }
  $('#scenario_wo_hedge_returns_estimated_closing_date_' + row_id).val(base_exp_close);
}

function update_passive_phase_arb_arb_spend() {
  let passive_arb_spend = parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * parseFloat($('#bond_price_est_purchase_price').val()) * 0.01;
  $('#passive_phase_arb_arb_spend').val(convert_to_decimal(passive_arb_spend, 0));
}

function update_hedging_hedge() {
  let hedging_hedge = parseFloat($('#passive_phase_arb_arb_spend').val()) * parseFloat($('#hedging_proposed_ratio').val()) * 0.01;
  $('#hedging_hedge').val(convert_to_decimal(hedging_hedge, 0));
}

function update_hedging_target_short() {
  let target_short = 0;
  if (parseFloat($('#deal_terms_value_target_ticker').val()) != 0) {
    target_short = parseFloat($('#hedging_hedge').val()) / parseFloat($('#deal_terms_value_target_ticker').val());
  }
  parseFloat($('#hedging_target_short').val(convert_to_decimal(target_short, 0)));
}

function update_hedging_arb_spread(spread_id) {
  let base_spread = parseFloat($('#spread_' + spread_id.toString()).val());
  $('#hedging_arb_spread').val(convert_to_decimal(base_spread, 2));
}

function update_hedging_short_spread() {
  let hedging_short_spread = parseFloat($('#hedging_arb_spread').val()) +
                             parseFloat($('#hedging_less_rebate').val()) +
                             parseFloat($('#hedging_less_short_rebate').val());
  $('#hedging_short_spread').val(convert_to_decimal(hedging_short_spread, 2));
}

function update_hedging_less_rebate(rebate_id) {
  let base_rebate = parseFloat($('#rebate_' + rebate_id.toString()).val()) * -1;
  $('#hedging_less_rebate').val(convert_to_decimal(base_rebate, 2));
}

function update_hedging_less_short_rebate() {
  let base_days_to_close = 0;
  let scenario_table_row_count = document.getElementById("scenario_table_tbody").rows.length;
    for (var i = 1; i <= scenario_table_row_count; i++) {
      let db_id = $('#scenario_table').DataTable().rows('#scenario_row_' + i.toString()).data()[0].database_id;
      if ($('#scenario_' + db_id.toString()).val().toString().toLowerCase().includes('base')) {
        base_days_to_close = parseFloat($('#days_to_close_' + db_id.toString()).val());
      }
  }
  let less_short_rebate = parseFloat($('#deal_terms_value_target_ticker').val()) * -1 *
                          parseFloat($('#rebate_target_val_rebate_pct').val()) * 0.01 *
                          base_days_to_close / 365;
  $('#hedging_less_short_rebate').val(convert_to_decimal(less_short_rebate, 2));
}

function update_scenario_w_hedge_bond_rebate(row_id) {
  let bond_rebate = 0;
  if (parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) != 0) {
    bond_rebate = parseFloat($('#hedging_target_short').val()) * parseFloat($('#hedging_less_short_rebate').val()) /
                      parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 100 * -1;
  }
  $('#scenario_w_hedge_bond_rebate_' + row_id).val(convert_to_decimal(bond_rebate, 3));
}

function update_scenario_w_hedge_bond_deal_value(row_id) {
  let bond_deal_value = parseFloat($('#scenario_w_hedge_bond_redemption_' + row_id).val()) +
                        parseFloat($('#scenario_w_hedge_bond_carry_earned_' + row_id).val()) +
                        parseFloat($('#scenario_w_hedge_bond_rebate_' + row_id).val()) +
                        parseFloat($('#scenario_w_hedge_bond_hedge_' + row_id).val());
  $('#scenario_w_hedge_bond_deal_value_' + row_id).val(convert_to_decimal(bond_deal_value, 3));
}

function update_scenario_wo_hedge_bond_deal_value(row_id) {
  let bond_deal_value = parseFloat($('#scenario_wo_hedge_bond_redemption_' + row_id).val()) +
                        parseFloat($('#scenario_wo_hedge_bond_carry_earned_' + row_id).val());
  $('#scenario_wo_hedge_bond_deal_value_' + row_id).val(convert_to_decimal(bond_deal_value, 3));
}

function update_scenario_w_hedge_profits_rebate(row_id) {
  let profits_rebate = parseFloat($('#scenario_w_hedge_bond_rebate_' + row_id).val()) *
                       parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 0.01;
  $('#scenario_w_hedge_profits_rebate_' + row_id).val(convert_to_decimal(profits_rebate, 0));
  update_color('scenario_w_hedge_profits_rebate_' + row_id, profits_rebate);
}

function update_scenario_w_hedge_bond_spread(row_id) {
  let bond_spread = parseFloat($('#scenario_w_hedge_bond_deal_value_' + row_id).val()) -
                    parseFloat($('#scenario_w_hedge_bond_last_price_' + row_id).val());
  $('#scenario_w_hedge_bond_spread_' + row_id).val(convert_to_decimal(bond_spread, 3));
}

function update_scenario_wo_hedge_bond_spread(row_id) {
  let bond_spread = parseFloat($('#scenario_wo_hedge_bond_deal_value_' + row_id).val()) -
                    parseFloat($('#scenario_wo_hedge_bond_last_price_' + row_id).val());
  $('#scenario_wo_hedge_bond_spread_' + row_id).val(convert_to_decimal(bond_spread, 3));
}

function update_scenario_w_hedge_bond_last_price(row_id) {
  $('#scenario_w_hedge_bond_last_price_' + row_id).val(convert_to_decimal(parseFloat($('#bond_price_est_purchase_price').val()), 3));
}

function update_scenario_wo_hedge_bond_last_price(row_id) {
  $('#scenario_wo_hedge_bond_last_price_' + row_id).val(convert_to_decimal(parseFloat($('#bond_price_est_purchase_price').val()), 3));
}

function update_scenario_w_hedge_returns_gross_pct(row_id) {
  let returns_gross_pct = 0;
  if (parseFloat($('#scenario_w_hedge_bond_last_price_' + row_id).val()) != 0) {
    returns_gross_pct = parseFloat($('#scenario_w_hedge_bond_spread_' + row_id).val()) /
                        parseFloat($('#scenario_w_hedge_bond_last_price_' + row_id).val()) * 100;
  }
  $('#scenario_w_hedge_returns_gross_pct_' + row_id).val(convert_to_decimal(returns_gross_pct, 2));
  update_color('scenario_w_hedge_returns_gross_pct_' + row_id, returns_gross_pct);
}

function update_scenario_wo_hedge_returns_gross_pct(row_id) {
  let returns_gross_pct = 0;
  if (parseFloat($('#scenario_wo_hedge_bond_last_price_' + row_id).val()) != 0) {
    returns_gross_pct = parseFloat($('#scenario_wo_hedge_bond_spread_' + row_id).val()) /
                        parseFloat($('#scenario_wo_hedge_bond_last_price_' + row_id).val()) * 100;
  }
  $('#scenario_wo_hedge_returns_gross_pct_' + row_id).val(convert_to_decimal(returns_gross_pct, 2));
  update_color('scenario_wo_hedge_returns_gross_pct_' + row_id, returns_gross_pct);
}

function update_scenario_w_hedge_returns_annual_pct(row_id) {
  let returns_annual_pct = 365 / parseFloat($('#scenario_w_hedge_returns_days_to_close_' + row_id).val()) *
                           parseFloat($('#scenario_w_hedge_returns_gross_pct_' + row_id).val());
  $('#scenario_w_hedge_returns_annual_pct_' + row_id).val(convert_to_decimal(returns_annual_pct, 2));
  update_color('scenario_w_hedge_returns_annual_pct_' + row_id, returns_annual_pct);
}

function update_scenario_wo_hedge_returns_annual_pct(row_id) {
  let returns_annual_pct = 365 / parseFloat($('#scenario_wo_hedge_returns_days_to_close_' + row_id).val()) *
                           parseFloat($('#scenario_wo_hedge_returns_gross_pct_' + row_id).val());
  $('#scenario_wo_hedge_returns_annual_pct_' + row_id).val(convert_to_decimal(returns_annual_pct, 2));
  update_color('scenario_wo_hedge_returns_annual_pct_' + row_id, returns_annual_pct);
}

function update_scenario_wo_hedge_bond_carry_earned(row_id) {
  let bond_carry_earned = 100 * parseFloat($('#bond_information_bbg_interest_rate').val()) *
                          parseFloat($('#scenario_wo_hedge_returns_days_to_close_' + row_id).val()) / 365 * 0.01;
  $('#scenario_wo_hedge_bond_carry_earned_' + row_id).val(convert_to_decimal(bond_carry_earned, 3));
}

function update_scenario_w_hedge_bond_carry_earned(row_id) {
  let bond_carry_earned = 100 * parseFloat($('#bond_information_bbg_interest_rate').val()) *
                          parseFloat($('#scenario_w_hedge_returns_days_to_close_' + row_id).val()) / 365 * 0.01;
  $('#scenario_w_hedge_bond_carry_earned_' + row_id).val(convert_to_decimal(bond_carry_earned, 3));
}

function update_scenario_w_hedge_profits_total(row_id) {
  let profits_total = parseFloat($('#scenario_w_hedge_profits_principal_' + row_id).val()) +
                      parseFloat($('#scenario_w_hedge_profits_carry_' + row_id).val()) +
                      parseFloat($('#scenario_w_hedge_profits_rebate_' + row_id).val()) +
                      parseFloat($('#scenario_w_hedge_profits_hedge_' + row_id).val());
  $('#scenario_w_hedge_profits_total_' + row_id).val(convert_to_decimal(profits_total, 0));
  update_color('scenario_w_hedge_profits_total_' + row_id, profits_total);
}

function update_scenario_wo_hedge_profits_total(row_id) {
  let profits_total = parseFloat($('#scenario_wo_hedge_profits_principal_' + row_id).val()) +
                      parseFloat($('#scenario_wo_hedge_profits_carry_' + row_id).val());
  $('#scenario_wo_hedge_profits_total_' + row_id).val(convert_to_decimal(profits_total, 0));
  update_color('scenario_wo_hedge_profits_total_' + row_id, profits_total);
}

function update_scenario_w_hedge_profits_principal(row_id) {
  let profits_principal = (parseFloat($('#scenario_w_hedge_bond_redemption_' + row_id).val()) -
                          parseFloat($('#scenario_w_hedge_bond_last_price_' + row_id).val())) *
                          parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 0.01;
  $('#scenario_w_hedge_profits_principal_' + row_id).val(convert_to_decimal(profits_principal, 0));
  update_color('scenario_w_hedge_profits_principal_' + row_id, profits_principal);
}

function update_scenario_wo_hedge_profits_principal(row_id) {
  let profits_principal = (parseFloat($('#scenario_wo_hedge_bond_redemption_' + row_id).val()) -
                          parseFloat($('#scenario_wo_hedge_bond_last_price_' + row_id).val())) *
                          parseFloat($('#passive_phase_arb_face_value_of_bonds').val()) * 0.01;
  $('#scenario_wo_hedge_profits_principal_' + row_id).val(convert_to_decimal(profits_principal, 0));
  update_color('scenario_wo_hedge_profits_principal_' + row_id, profits_principal);
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
    update_color('annual_pct_' + row_id, annual);
  }
}

function update_gross_pct(row_id) {
  if (parseFloat($('#last_price_' + row_id).val()) != 0) {
    let gross = (parseFloat($('#spread_' + row_id).val()) / parseFloat($('#last_price_' + row_id).val())) * 100;
    $('#gross_pct_' + row_id).val(gross.toFixed(2));
    update_color('gross_pct_' + row_id, gross);
  }
}

function update_last_price(row_id) {
  $('#last_price_' + row_id.toString()).val(parseFloat($('#deal_terms_value_target_ticker').val()));
}

function update_dollars_to_make(row_id) {
  let dollars_to_make = parseFloat($('#spread_' + row_id).val()) * parseFloat($('#passive_value_size_shares').val());
  $('#dollars_to_make_' + row_id).val(dollars_to_make.toFixed());
  update_color('dollars_to_make_' + row_id, dollars_to_make);
}

function update_dollars_to_lose(row_id) {
  let dollars_to_lose = ((parseFloat($('#deal_terms_value_gross_spread').val()) - parseFloat($('#upside_value_topping_spread').val())) *
                              parseFloat($('#passive_value_size_shares').val()));
  $('#dollars_to_lose_' + row_id.toString()).val(dollars_to_lose.toFixed());
  update_color('dollars_to_lose_' + row_id, dollars_to_lose);
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

function update_scenario_w_hedge_returns_days_to_close(row_id) {
  let days_to_close = Math.ceil(Math.abs(new Date($('#scenario_w_hedge_returns_estimated_closing_date_' + row_id).val()) - new Date()) / (1000 * 60 * 60 * 24));
  $('#scenario_w_hedge_returns_days_to_close_' + row_id).val(days_to_close);
}

function update_scenario_wo_hedge_returns_days_to_close(row_id) {
  let days_to_close = Math.ceil(Math.abs(new Date($('#scenario_wo_hedge_returns_estimated_closing_date_' + row_id).val()) - new Date()) / (1000 * 60 * 60 * 24));
  $('#scenario_wo_hedge_returns_days_to_close_' + row_id).val(days_to_close);
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
  let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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
  let scenario_row_count = document.getElementById("scenario_table_tbody").rows.length;
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
  if (parseFloat(data_value) < 0) {
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

function update_color(input_id, input_value) {
  let style = get_style(input_value);
  $('#' + input_id).attr('style', style);
}
