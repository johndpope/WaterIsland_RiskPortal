# Calculates PL (Used for Gross RoR accounting for Hedges)
def calculate_pl_sec_impact(row):
    if row['SecType'] == 'EQ' and row['AlphaHedge'] == 'Hedge':
        return 0    # Assume 0 pnl impact on Equity Hedges. Cant say for sure where acquirer would trade

    if row['SecType'] != 'EXCHOPT':
        return (row['deal_value'] * row['FxFactor'] * row['QTY']) - (row['CurrentMktVal'] * row['FxFactor'])

    if row['PutCall'] == 'CALL':
        if row['StrikePrice'] <= row['deal_value']:
            x = (row['deal_value'] - row['StrikePrice']) * (row['QTY']) * row['FxFactor']
        else:
            x = 0
    elif row['PutCall'] == 'PUT':
        if row['StrikePrice'] >= row['deal_value']:
            x = (row['StrikePrice'] - row['deal_value']) * (row['QTY']) * row['FxFactor']
        else:
            x = 0
    return -row['CurrentMktVal'] + x


