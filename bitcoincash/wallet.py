# Copyright (C) 2012-2014 The python-bitcoinlib developers
#
# This file is part of python-bitcoinlib.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of python-bitcoinlib, including this file, may be copied, modified,
# propagated, or distributed except according to the terms contained in the
# LICENSE file.

"""Wallet-related functionality

Includes things like representing addresses and converting them to/from
scriptPubKeys; currently there is no actual wallet support implemented.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

_bord = ord
if sys.version > '3':
    _bord = lambda x: x

import bitcoincash
import bitcoincash.base58
import bitcoincash.cashaddr
import bitcoincash.core
import bitcoincash.core.key
import bitcoincash.core.script as script

class CBitcoinAddressError(Exception):
    """Raised when an invalid Bitcoin address is encountered"""

class CBitcoinAddress(bitcoincash.cashaddr.CashAddrData):
    """A Bitcoin address"""

    @classmethod
    def from_bytes(cls, data, prefix, kind):
        self = super(CBitcoinAddress, cls).from_bytes(data, prefix, kind)

        if kind == bitcoincash.cashaddr.SCRIPT_TYPE:
            self.__class__ = P2SHBitcoinAddress

        elif kind == bitcoincash.cashaddr.PUBKEY_TYPE:
            self.__class__ = P2PKHBitcoinAddress

        else:
            raise CBitcoinAddressError('Type %d not a recognized Bitcoin Address' % kind)

        if prefix != bitcoincash.params.CASHADDR_PREFIX:
            raise CBitcoinAddressError("The address looks valid, "
                "however prefix does not match selected network params "
                "(got {}, expected {}".format(
                    prefix, bitcoincash.params.CASHADDR_PREFIX))

        return self

    @classmethod
    def from_scriptPubKey(cls, scriptPubKey):
        """Convert a scriptPubKey to a CBitcoinAddress

        Returns a CBitcoinAddress subclass, either P2SHBitcoinAddress or
        P2PKHBitcoinAddress. If the scriptPubKey is not recognized
        CBitcoinAddressError will be raised.
        """
        try:
            return P2SHBitcoinAddress.from_scriptPubKey(scriptPubKey)
        except (CBitcoinAddressError, ValueError):
            pass

        try:
            return P2PKHBitcoinAddress.from_scriptPubKey(scriptPubKey)
        except (CBitcoinAddressError, ValueError):
            pass

        raise CBitcoinAddressError('scriptPubKey not a valid address')

    def to_scriptPubKey(self):
        """Convert an address to a scriptPubKey"""
        raise NotImplementedError

class P2SHBitcoinAddress(CBitcoinAddress):
    @classmethod
    def from_bytes(cls, data, prefix, kind):

        if kind != bitcoincash.cashaddr.SCRIPT_TYPE:
            raise ValueError('Address type encoding incorrect for P2SH address: got %d; expected %d' % \
                                (kind, bitcoincash.cashaddr.SCRIPT_TYPE))

        return super(P2SHBitcoinAddress, cls).from_bytes(data, prefix, kind)

    @classmethod
    def from_redeemScript(cls, redeemScript):
        """Convert a redeemScript to a P2SH address

        Convenience function: equivalent to P2SHBitcoinAddress.from_scriptPubKey(redeemScript.to_p2sh_scriptPubKey())
        """
        return cls.from_scriptPubKey(redeemScript.to_p2sh_scriptPubKey())

    @classmethod
    def from_scriptPubKey(cls, scriptPubKey):
        """Convert a scriptPubKey to a P2SH address

        Raises CBitcoinAddressError if the scriptPubKey isn't of the correct
        form.
        """
        if scriptPubKey.is_p2sh():
            return cls.from_bytes(scriptPubKey[2:22],
                    bitcoincash.params.CASHADDR_PREFIX, bitcoincash.cashaddr.SCRIPT_TYPE)

        else:
            raise CBitcoinAddressError('not a P2SH scriptPubKey')

    def to_scriptPubKey(self):
        """Convert an address to a scriptPubKey"""
        assert self.kind == bitcoincash.cashaddr.SCRIPT_TYPE
        return script.CScript([script.OP_HASH160, self, script.OP_EQUAL])

class P2PKHBitcoinAddress(CBitcoinAddress):
    @classmethod
    def from_bytes(cls, data, prefix, kind):
        if kind != bitcoincash.cashaddr.PUBKEY_TYPE:
            raise ValueError('Address type incorrect for P2PKH address: got %d; expected %d' % \
                                (kind, bitcoincash.cashaddr.PUBKEY_TYPE))

        return super(P2PKHBitcoinAddress, cls).from_bytes(data, prefix, kind)

    @classmethod
    def from_pubkey(cls, pubkey, accept_invalid=False):
        """Create a P2PKH bitcoin address from a pubkey

        Raises CBitcoinAddressError if pubkey is invalid, unless accept_invalid
        is True.

        The pubkey must be a bytes instance; CECKey instances are not accepted.
        """
        if not isinstance(pubkey, bytes):
            raise TypeError('pubkey must be bytes instance; got %r' % pubkey.__class__)

        if not accept_invalid:
            if not isinstance(pubkey, bitcoincash.core.key.CPubKey):
                pubkey = bitcoincash.core.key.CPubKey(pubkey)
            if not pubkey.is_fullyvalid:
                raise CBitcoinAddressError('invalid pubkey')

        pubkey_hash = bitcoincash.core.Hash160(pubkey)
        return P2PKHBitcoinAddress.from_bytes(pubkey_hash,
                bitcoincash.params.CASHADDR_PREFIX, bitcoincash.cashaddr.PUBKEY_TYPE)

    @classmethod
    def from_scriptPubKey(cls, scriptPubKey, accept_non_canonical_pushdata=True, accept_bare_checksig=True):
        """Convert a scriptPubKey to a P2PKH address

        Raises CBitcoinAddressError if the scriptPubKey isn't of the correct
        form.

        accept_non_canonical_pushdata - Allow non-canonical pushes (default True)

        accept_bare_checksig          - Treat bare-checksig as P2PKH scriptPubKeys (default True)
        """
        if accept_non_canonical_pushdata:
            # Canonicalize script pushes
            scriptPubKey = script.CScript(scriptPubKey) # in case it's not a CScript instance yet

            try:
                scriptPubKey = script.CScript(tuple(scriptPubKey)) # canonicalize
            except bitcoincash.core.script.CScriptInvalidError:
                raise CBitcoinAddressError('not a P2PKH scriptPubKey: script is invalid')

        if (len(scriptPubKey) == 25
                and _bord(scriptPubKey[0])  == script.OP_DUP
                and _bord(scriptPubKey[1])  == script.OP_HASH160
                and _bord(scriptPubKey[2])  == 0x14
                and _bord(scriptPubKey[23]) == script.OP_EQUALVERIFY
                and _bord(scriptPubKey[24]) == script.OP_CHECKSIG):
            return cls.from_bytes(scriptPubKey[3:23],
                    bitcoincash.params.CASHADDR_PREFIX, bitcoincash.cashaddr.PUBKEY_TYPE)

        elif accept_bare_checksig:
            pubkey = None

            # We can operate on the raw bytes directly because we've
            # canonicalized everything above.
            if (len(scriptPubKey) == 35 # compressed
                  and _bord(scriptPubKey[0])  == 0x21
                  and _bord(scriptPubKey[34]) == script.OP_CHECKSIG):

                pubkey = scriptPubKey[1:34]

            elif (len(scriptPubKey) == 67 # uncompressed
                    and _bord(scriptPubKey[0]) == 0x41
                    and _bord(scriptPubKey[66]) == script.OP_CHECKSIG):

                pubkey = scriptPubKey[1:65]

            if pubkey is not None:
                return cls.from_pubkey(pubkey, accept_invalid=True)

        raise CBitcoinAddressError('not a P2PKH scriptPubKey')

    def to_scriptPubKey(self):
        """Convert an address to a scriptPubKey"""
        assert self.kind == bitcoincash.cashaddr.PUBKEY_TYPE
        return script.CScript([script.OP_DUP, script.OP_HASH160, self, script.OP_EQUALVERIFY, script.OP_CHECKSIG])

class CKey(object):
    """An encapsulated private key

    Attributes:

    pub           - The corresponding CPubKey for this private key

    is_compressed - True if compressed

    """
    def __init__(self, secret, compressed=True):
        self._cec_key = bitcoincash.core.key.CECKey()
        self._cec_key.set_secretbytes(secret)
        self._cec_key.set_compressed(compressed)

        self.pub = bitcoincash.core.key.CPubKey(self._cec_key.get_pubkey(), self._cec_key)

    @property
    def is_compressed(self):
        return self.pub.is_compressed

    def sign(self, hash):
        return self._cec_key.sign(hash)

    def sign_compact(self, hash):
        return self._cec_key.sign_compact(hash)

class CBitcoinSecretError(bitcoincash.base58.Base58Error):
    pass

class CBitcoinSecret(bitcoincash.base58.CBase58Data, CKey):
    """A base58-encoded secret key"""

    @classmethod
    def from_secret_bytes(cls, secret, compressed=True):
        """Create a secret key from a 32-byte secret"""
        self = cls.from_bytes(secret + (b'\x01' if compressed else b''),
                              bitcoincash.params.BASE58_PREFIXES['SECRET_KEY'])
        self.__init__(None)
        return self

    def __init__(self, s):
        if self.nVersion != bitcoincash.params.BASE58_PREFIXES['SECRET_KEY']:
            raise CBitcoinSecretError('Not a base58-encoded secret key: got nVersion=%d; expected nVersion=%d' % \
                                      (self.nVersion, bitcoincash.params.BASE58_PREFIXES['SECRET_KEY']))

        CKey.__init__(self, self[0:32], len(self) > 32 and _bord(self[32]) == 1)

def legacy_to_cashaddr(legacy_addr):
    legacy = bitcoincash.base58.CBase58Data(legacy_addr)

    if legacy.nVersion == bitcoincash.params.BASE58_PREFIXES['PUBKEY_ADDR']:
        addr_type = bitcoincash.cashaddr.PUBKEY_TYPE
    elif legacy.nVersion == bitcoincash.params.BASE58_PREFIXES['SCRIPT_ADDR']:
        addr_type = bitcoincash.cashaddr.SCRIPT_TYPE
    else:
        raise CBitcoinAddressError("Unknown base58 address version {}".format(legacy.nVersion))

    return bitcoincash.cashaddr.encode_full(
            bitcoincash.params.CASHADDR_PREFIX, addr_type, legacy.to_bytes())


__all__ = (
        'CBitcoinAddressError',
        'CBitcoinAddress',
        'P2SHBitcoinAddress',
        'P2PKHBitcoinAddress',
        'CKey',
        'CBitcoinSecretError',
        'CBitcoinSecret',
        'legacy_to_cashaddr',
)
