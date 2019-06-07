from django.conf import settings
from ipware import get_client_ip

import workstation_mapper

def get_ip_addr(request):
    client_ip, is_routable = get_client_ip(request)
    if client_ip is None:
        ip_addr = 'NA'
    else:
        ip_addr = client_ip
    try:
        ip_addr = workstation_mapper.ip_mapper[ip_addr]
    except KeyError:
        ip_addr = client_ip
    return ip_addr


def get_channel_name(channel_name):
    if settings.DEBUG or settings.DEBUG == 'on':
        return 'test_channel'
    else:
        return channel_name
