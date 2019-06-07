from bbgclient import bbgclient

from django.db import IntegrityError

from risk.models import MA_Deals, MaDealsActionIdDetails

BLOOMBERG_MAPPING = {
    'target_name': 'CA051',
    'target_ticker': 'CA052',
    'target_industry': 'CA053',
    'target_country': 'CA830',
    'acquirer_name': 'CA055',
    'acquirer_ticker': 'CA054',
    'acquirer_industry': 'CA056',
    'acquirer_country': 'CA831',
    'deal_type': 'CA062',
    'deal_status': 'CA061',
    'nature_of_bid': 'CA075',
    'transaction_type': 'CA834',
    'announced_date': 'CA057',
    'mergers_agreement_date': 'CA932',
    'expected_completion_date': 'CA835',
    'drop_dead_date': 'CA947',
    'go_shop_period_end_date': 'CA921',
    'termination_date': 'CA058',
    'net_debt': 'CA074',
    'deal_description': 'CA926',
    'ebitda_total_tvm': 'CA890',
    'ebit_total_tvm': 'CA891',
    'revenue_total_tvm': 'CA892',
    'total_assets_total_tvm': 'CA893',
    'free_cashflow_total_tvm': 'CA898',
    'ebitda_equity_tvm': 'CA903',
    'ebit_equity_tvm': 'CA904',
    'revenue_equity_tvm': 'CA905',
    'total_assets_equity_tvm': 'CA906',
    'free_cashflow_equity_tvm': 'CA911',
    'deal_currency': 'CA848',
    'payment_type': 'CA071',
    'cash_terms': 'CA072',
    'stock_terms': 'CA073',
    'percent_owned': 'CA065',
    'percent_sought': 'CA066',
    'announced_total_value': 'CA060',
    'announced_premium': 'CA063',
    'target_to_acquirer_termination_fees': 'CA866',
    'acquirer_to_target_termination_fess': 'CA867',
    'pending_approvals': 'CA883',
    'expired_approvals': 'CA884',
    'approved_approvals': 'CA885',
    'extended_approvals': 'CA886',
    'blocked_approvals': 'CA887',
    'early_termination_approvals': 'CA888'
}


def get_data_from_bloombery_using_action_id(action_id_list):
    fields = list(BLOOMBERG_MAPPING.values())
    for action_id in action_id_list:
        if 'action' not in action_id.lower():
            action_id_list.remove(action_id)
            action_id = str(action_id) + ' Action'
            action_id_list.append(action_id)
    result = bbgclient.get_secid2field(action_id_list, 'tickers', fields, req_type='refdata')
    return result


def get_data_from_bloomberg_by_bg_id(bloomberg_id_list, field_list):
    for bloomberg_id in bloomberg_id_list:
        bloomberg_id_list.remove(bloomberg_id)
        bloomberg_id = bloomberg_id.strip()
        bloomberg_id_list.append(bloomberg_id)
    result = bbgclient.get_secid2field(bloomberg_id_list, 'tickers', field_list, req_type='refdata')
    return result


def save_bloomberg_data_to_table(result, ma_deals_list):
    columns = list(BLOOMBERG_MAPPING.keys())
    unique_ma_deals = set()
    for ma_deal in ma_deals_list:
        if ma_deal.deal_name not in unique_ma_deals:
            unique_ma_deals.add(ma_deal.deal_name)
            action_id = str(ma_deal.action_id)
            if action_id:
                bloomberg_action_id = str(ma_deal.action_id)
                if 'action' not in bloomberg_action_id.lower():
                    bloomberg_action_id = bloomberg_action_id + ' Action'
                if result.get(bloomberg_action_id):
                    data = result[bloomberg_action_id]
                    object_data = {'action_id': action_id}
                    for column in columns:
                        object_data[column] = data.get(BLOOMBERG_MAPPING[column])[0]
                    try:
                        MaDealsActionIdDetails.objects.create(**object_data)
                    except IntegrityError as e:
                        raise IntegrityError
