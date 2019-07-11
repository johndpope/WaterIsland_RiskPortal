def parse_fld(id2fld2val,fld, id):
    try:
        return float(id2fld2val[id][fld][0])
    except:
        return None

