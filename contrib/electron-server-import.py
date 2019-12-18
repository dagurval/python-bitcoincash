"""
Used to parse servers from Electron Cash `servers.json` file and convert
them to a fromat that fits electrum/constants.py.
"""

import json
import pprint

servers = {
    'bitcoincash.network': {'s': 50002, 't': 50001}
}

with open("servers.json") as fh:
    data = json.load(fh)

    for key, value in data.items():
        if not key in servers:
            servers[key] = { }
        if 's' in value:
            servers[key]['s'] = value['s']
        if 't' in value:
            servers[key]['t'] = value['t']

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(servers)
