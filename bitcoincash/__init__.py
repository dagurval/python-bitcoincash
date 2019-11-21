# Copyright (C) 2012-2018 The python-bitcoinlib developers
#
# This file is part of python-bitcoinlib.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of python-bitcoinlib, including this file, may be copied, modified,
# propagated, or distributed except according to the terms contained in the
# LICENSE file.

from __future__ import absolute_import, division, print_function, unicode_literals

import bitcoincash.core

# Note that setup.py can break if __init__.py imports any external
# dependencies, as these might not be installed when setup.py runs. In this
# case __version__ could be moved to a separate version.py and imported here.
__version__ = '0.1.0'

class MainParams(bitcoincash.core.CoreMainParams):
    """
    DB_MAGIC: Magic bytes used as separator in block storage. Previously named
              MESSAGE_START.
    NETWORK_MAGIC: Prefix for messages in the P2P protocol. Previously named
                   MESSAGE_START and had the same value as DB_MAGIC.
    """
    DB_MAGIC = b'\xf9\xbe\xb4\xd9'
    NETWORK_MAGIC = b'\xe3\xe1\xf3\xe8'
    DEFAULT_PORT = 8333
    RPC_PORT = 8332

    DNS_SEEDS = (
        ('bitcoinunlimited.info', 'btccash-seeder.bitcoinunlimited.info'),
        ('bitcoinabc.org', 'seed.bitcoinabc.org'),
        ('bitcoinforks.org', 'seed-abc.bitcoinforks.org'),
        ('deadalnix.me', 'seed.deadalnix.me'))

    BASE58_PREFIXES = {'PUBKEY_ADDR':0,
                       'SCRIPT_ADDR':5,
                       'SECRET_KEY' :128}
    CASHADDR_PREFIX = "bitcoincash"

class TestNetParams(bitcoincash.core.CoreTestNetParams):
    """
    DB_MAGIC: Magic bytes used as separator in block storage. Previously named
              MESSAGE_START.
    NETWORK_MAGIC: Prefix for messages in the P2P protocol. Previously named
                   MESSAGE_START and had the same value as DB_MAGIC.
    """
    DB_MAGIC = b'\x0b\x11\x09\x07'
    NETWORK_MAGIC = b'\xf4\xe5\xf3\xf4'
    DEFAULT_PORT = 18333
    RPC_PORT = 18332

    DNS_SEEDS = (
        ('bitcoinabc.org', 'testnet-seed.bitcoinabc.org'),
        ('bitcoinforks.org', 'testnet-seed-abc.bitcoinforks.org'),
        ('bitcoinunlimited.info', 'testnet-seed.bitcoinunlimited.info'),
        ('deadalnix.me', 'testnet-seed.deadalnix.me'))

    BASE58_PREFIXES = {'PUBKEY_ADDR':111,
                       'SCRIPT_ADDR':196,
                       'SECRET_KEY' :239}
    CASHADDR_PREFIX = "bchtest"

class RegTestParams(bitcoincash.core.CoreRegTestParams):
    """
    DB_MAGIC: Magic bytes used as separator in block storage. Previously named
              MESSAGE_START.
    NETWORK_MAGIC: Prefix for messages in the P2P protocol. Previously named
                   MESSAGE_START and had the same value as DB_MAGIC.
    """
    DB_MAGIC = b'\xfa\xbf\xb5\xda'
    NETWORK_MAGIC = b'\xda\xb5\xbf\xfa'
    DEFAULT_PORT = 18444
    RPC_PORT = 18443
    DNS_SEEDS = ()
    BASE58_PREFIXES = {'PUBKEY_ADDR':111,
                       'SCRIPT_ADDR':196,
                       'SECRET_KEY' :239}
    CASHADDR_PREFIX = "bchreg"

"""Master global setting for what chain params we're using.

However, don't set this directly, use SelectParams() instead so as to set the
bitcoincash.core.params correctly too.
"""
#params = bitcoincash.core.coreparams = MainParams()
params = MainParams()

def SelectParams(name):
    """Select the chain parameters to use

    name is one of 'mainnet', 'testnet', or 'regtest'

    Default chain is 'mainnet'
    """
    global params
    bitcoincash.core._SelectCoreParams(name)
    if name == 'mainnet':
        params = bitcoincash.core.coreparams = MainParams()
    elif name == 'testnet':
        params = bitcoincash.core.coreparams = TestNetParams()
    elif name == 'regtest':
        params = bitcoincash.core.coreparams = RegTestParams()
    else:
        raise ValueError('Unknown chain %r' % name)
