$(document).ready(function () {

  let passive_phase_arb_data = $.parseJSON($('#passive_phase_arb_data').val());
  let bond_price_data = $.parseJSON($('#bond_price_data').val());
  let bond_information_data = $.parseJSON($('#bond_information_data').val());
  let estimated_liquidity_data = $.parseJSON($('#estimated_liquidity_data').val());
  let potential_outcomes_data = $.parseJSON($('#potential_outcomes_data').val());
  let hedging_data = $.parseJSON($('#hedging_data').val());
  let scenario_wo_hedge_data = $.parseJSON($('#scenario_wo_hedge_data').val());
  let scenario_w_hedge_data = $.parseJSON($('#scenario_w_hedge_data').val());


  var passive_phase_arb_table = $('#passive_phase_arb_table').DataTable({
    data: passive_phase_arb_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="bond_information_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
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

  var bond_information_table = $('#bond_information_table').DataTable({
    data: bond_information_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="bond_information_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
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

  var bond_price_table = $('#bond_price_table').DataTable({
    data: bond_price_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.id.toLowerCase().includes('est_purchase_price')) {
            style = "font-weight: bold;";
          }
          return '<input id="bond_price_' + row.id + '" onchange="onChange(id)" style="' + style +
            '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="15" value="' + row.value + '">';
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

  var potential_outcomes_table = $('#potential_outcomes_table').DataTable({
    data: potential_outcomes_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.id.toLowerCase().includes('equity_claw_value')) {
            style = "font-weight: bold;";
          }
          if (row.type_input == 'true') {
            return '<input id="potential_outcomes_' + row.id + '" onchange="onChange(id)" style="' + style +
              '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="30" value="' + row.type + '">';
          }
          else {
            return '<input id="potential_outcomes_' + row.id + '" disabled onchange="onChange(id)" style="' + style +
              '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.type + '">';
          }
        }
      },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="potential_outcomes_value_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
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

  var hedging_table = $('#hedging_table').DataTable({
    data: hedging_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          return '<input id="hedging_' + row.id + '" onchange="onChange(id)" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
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

  var estimated_liquidity_table = $('#estimated_liquidity_table').DataTable({
    data: estimated_liquidity_data,
    autoWidth: false,
    columns: [
      { data: 'key' },
      {
        orderable: false,
        render: function (data, type, row) {
          let style = "";
          if (row.id.toLowerCase().includes('credit_team_view')) {
            style = "font-weight: bold;";
          }
          return '<input id="estimated_liquidity_' + row.id + '" onchange="onChange(id)" style="' + style +
            '" onfocusout="focusOut(id)" class="form-control form-control-sm" type="text" maxlength="10" value="' + row.value + '">';
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

  // Scenario Without Hedge table
  var scenario_without_hedge_table = $('#scenario_without_hedge_table').DataTable({
    data: scenario_wo_hedge_data,
    autoWidth: false,
    'createdRow': function( row, data, dataIndex ) {
      $(row).attr('db-id', data.database_id);
    },
    columns: get_columns_for_databale('scenario_wo_hedge_'),
    sorting: false,
    ordering: false,
    paging: false,
    searching: false,
    info: false,
  });

    // Scenario With Hedge table
    var scenario_with_hedge_table = $('#scenario_with_hedge_table').DataTable({
      data: scenario_w_hedge_data,
      autoWidth: false,
      'createdRow': function( row, data, dataIndex ) {
        $(row).attr('db-id', data.database_id);
      },
      columns: get_columns_for_databale('scenario_w_hedge_'),
      sorting: false,
      ordering: false,
      paging: false,
      searching: false,
      info: false,
    });

  $('#addScenarioWoHedgeRow').on('click', function () {
    add_row('scenario_without_hedge_table', 'scenario_wo_hedge_')
  });

  $('#addScenarioWHedgeRow').on('click', function () {
    add_row('scenario_with_hedge_table', 'scenario_w_hedge_')
  });

  function add_row(table_id, prefix) {
    count = $('#' + table_id).DataTable().rows().count();
    let random_id = Math.random().toString().replace(".", "");
    let db_id = $('#' + table_id).DataTable().rows('#' + prefix + 'row_' + count.toString()).data()[0].database_id;
    bond_last_price = $('#' + prefix + 'bond_last_price_' + db_id.toString()).val();
    bond_carry_earned = $('#' + prefix + 'bond_carry_earned_' + db_id.toString()).val();
    bond_rebate = $('#' + prefix + 'bond_rebate_' + db_id.toString()).val();
    returns_estimated_closing_date = $('#' + prefix + 'returns_estimated_closing_date_' + db_id.toString()).val();
    count += 1;
    let credit_idea_id = parseFloat(new URLSearchParams(window.location.search).get('credit_idea_id'));
    $('#' + table_id).DataTable().row.add(
      {
        'id': random_id, 'credit_idea_id': credit_idea_id, 'scenario': '', 'bond_last_price': bond_last_price,
        'bond_redemption': '', 'bond_carry_earned': bond_carry_earned, 'bond_rebate': bond_rebate, 'bond_hedge': 0.00,
        'bond_deal_value': '', 'bond_spread': '', 'returns_gross_pct': '', 'returns_annual_pct': '',
        'returns_estimated_closing_date': returns_estimated_closing_date, 'returns_days_to_close': '',
        'profits_principal': '', 'profits_carry': '', 'profits_rebate': '', 'profits_hedge': '', 'profits_total': '',
        'profits_day_of_break': '', 'database_id': random_id
      }
    ).node().id = prefix + 'row_' + count.toString();
    $('#' + table_id).DataTable().draw(false);
    onChange('exp_close_' + random_id.toString());
  };
});

function get_columns_for_databale(prefix) {
  var output = [
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'scenario_' + row.id + '" class="form-control form-control-sm" type="text" maxlength="30" value="' + row.scenario + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_last_price_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_last_price + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_redemption_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_redemption + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_carry_earned_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_carry_earned + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_rebate_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_rebate + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_hedge_' + row.id + '" disabled onchange="onChange(id)" onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_hedge + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_deal_value_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_deal_value + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'bond_spread_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.bond_spread + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'returns_gross_pct_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.returns_gross_pct) +
               '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.returns_gross_pct + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'returns_annual_pct_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.returns_annual_pct) +
               '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.returns_annual_pct + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'returns_estimated_closing_date_' + row.id + '" onchange="onChange(id)" class="form-control form-control-sm" type="date" value="' + row.returns_estimated_closing_date + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'returns_days_to_close_' + row.id + '" disabled onchange="onChange(id)" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.returns_days_to_close + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_principal_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_principal) +
               '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_principal + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_carry_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_carry) +
               '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_carry + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_rebate_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_rebate) +
          '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_rebate + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_hedge_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_hedge) +
          '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_hedge + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_total_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_total) +
        '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_total + '">';
      }
    },
    {
      orderable: false,
      render: function (data, type, row) {
        return '<input id="' + prefix + 'profits_day_of_break_' + row.id + '" disabled onchange="onChange(id)" style="' + get_style(row.profits_day_of_break) +
          '" class="form-control form-control-sm input-label" type="text" maxlength="10" value="' + row.profits_day_of_break + '">';
      }
    },
  ]
  return output;
}