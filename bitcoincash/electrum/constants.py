
# copied values from electrum source

# IDK, maybe?
ELECTRUM_VERSION = '2.6.4'  # version of the client package
PROTOCOL_VERSION = '0.10'   # protocol version requested

# note: 'v' and 'p' are effectively reserved as well.
PROTOCOL_CODES = dict(t='TCP (plaintext)', h='HTTP (plaintext)', s='SSL', g='Websocket')
"""
Which protocol is used. Usually paired with port number.
"""

# from electrum/lib/network.py at Jun/2016
#
DEFAULT_PORTS = { 't':50001, 's':50002, 'h':8081, 'g':8082}

DEFAULT_SERVER = 'bitcoincash.network'
"""
If server info is not provided, default to this server.
"""

BOOTSTRAP_SERVERS = {
    '7nshufncf3nmp7pa42oqhnj6whsjgo2eok4jveex62tczuhvqur5ciad.onion': {   't': '50001'},
    'bch.imaginary.cash': {'s': '50002', 't': '50001'},
    'bch.loping.net': {'s': '50002', 't': '50001'},
    'bch.soul-dev.com': {'s': '50002'},
    'bch0.kister.net': {'s': '50002', 't': '50001'},
    'bchx.disdev.org': {'s': '50002'},
    'bitcoincash.network': {'s': 50002, 't': 50001},
    'bitcoincash.quangld.com': {'s': '50002', 't': '50001'},
    'blackie.c3-soft.com': {'s': '50002', 't': '50001'},
    'bxdp2p6abpqt5etc.onion': {'t': '50001'},
    'crypto.mldlabs.com': {'s': '50002', 't': '50001'},
    'electron-cash.dragon.zone': {'s': '50002', 't': '50001'},
    'electron.coinucopia.io': {'s': '50002', 't': '50001'},
    'electron.jochen-hoenicke.de': {'s': '51002', 't': '51001'},
    'electroncash.de': {'s': '50002', 't': '50001'},
    'electroncash.dk': {'s': '50002', 't': '50001'},
    'electrum-abc.criptolayer.net': {'s': '50012'},
    'electrum.imaginary.cash': {'s': '50002', 't': '50001'},
    'electrumx-cash.1209k.com': {'s': '50002', 't': '50001'},
    'electrumx.hillsideinternet.com': {'s': '50002', 't': '50001'},
    'greedyhog.ddns.net': {'s': '50002', 't': '50001'},
    'jh3jgcrwweh6yvmprtjnp72u2hqn34nlftlg3msrr4vmlapft4yvt2id.onion': {   's': '50002',
                                                                          't': '50001'},
    'jktsologn7uprtwn7gsgmwuddj6rxsqmwc2vaug7jwcwzm2bxqnfpwad.onion': {   's': '50002',
                                                                          't': '50001'},
    'kisternetg2pq7wx.onion': {'t': '50001'},
    'wallet.satoshiscoffeehouse.com': {'s': '50002', 't': '50001'}
}



