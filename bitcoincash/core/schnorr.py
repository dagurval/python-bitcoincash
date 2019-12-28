#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python3 -*-
# This file (c) 2019 Mark Lundeberg & Calin Culianu
# Part of the Electron Cash SPV Wallet
# License: MIT
#
# Copyright (C) 2019 The python-bitcoinlib developers
#
# This file is part of python-bitcoinlib.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of python-bitcoinlib, including this file, may be copied, modified,
# propagated, or distributed except according to the terms contained in the
# LICENSE file.
'''
This is a Python-only Schnorr sign/verify. Compared to the libsecp256k1 bundled with
Bitcoin Unlimited this is much less secure as it contains side channel
vulnerabilities, and must not be used in an automated-signing environment.
'''
import os
import sys
import hmac, hashlib

IS_AVAILABLE = False
try:
    import ecdsa
    IS_AVAILABLE = True
except ImportError as e:
    from unittest.mock import Mock
    ecdsa = Mock()

def is_available():
    """If Schnorr is available in this installation. Schnorr requires python
    module ecdsa to be installed."""
    global IS_AVAILABLE
    return IS_AVAILABLE

def jacobi(a, n):
    """Jacobi symbol"""
    # Based on the Handbook of Applied Cryptography (HAC), algorithm 2.149.
    # This is more than 2x faster than the one from python ecdsa package, due
    # to usage of bitwise arithmetic and no recursion.
    assert n >= 3
    assert n & 1 == 1
    a = a % n
    s = 1
    while a > 1:
        a1, e = a, 0
        while a1 & 1 == 0:
            a1, e = a1 >> 1, e+1
        if not (e & 1 == 0 or n & 7 == 1 or n & 7 == 7):
            s = -s
        if a1 == 1:
            return s
        if n & 3 == 3 and a1 & 3 == 3:
            s = -s
        a, n = n%a1, a1
    if a == 0:
        return 0
    if a == 1:
        return s

def nonce_function_rfc6979(order, privkeybytes, msg32, algo16=b'', ndata=b''):
    """ pure python RFC6979 deterministic nonce generation, done in
    libsecp256k1 style -- see nonce_function_rfc6979() in secp256k1.c.
    """
    assert len(privkeybytes) == 32
    assert len(msg32) == 32
    assert len(algo16) in (0, 16)
    assert len(ndata) in (0, 32)
    assert order.bit_length() == 256

    V = b'\x01'*32
    K = b'\x00'*32
    blob = bytes(privkeybytes) + msg32 + ndata + algo16
    # initialize
    K = hmac.HMAC(K, V+b'\x00'+blob, 'sha256').digest()
    V = hmac.HMAC(K, V, 'sha256').digest()
    K = hmac.HMAC(K, V+b'\x01'+blob, 'sha256').digest()
    V = hmac.HMAC(K, V, 'sha256').digest()
    # loop forever until an in-range k is found
    while True:
        # see RFC6979 3.2.h.2 : we take a shortcut and don't build T in
        # multiple steps since the first step is always the right size for
        # our purpose.
        V = hmac.HMAC(K, V, 'sha256').digest()
        T = V
        assert len(T) == 32
        k = int.from_bytes(T, 'big')
        if k > 0 and k < order:
            break
        K = hmac.HMAC(K, V+b'\x00', 'sha256').digest()
        V = hmac.HMAC(K, V, 'sha256').digest()
    return k


def sign(privkey, message_hash):
    '''Create a Schnorr signature.

    Returns a 64-long bytes object (the signature), or raise ValueError
    on failure. Failure can occur due to an invalid private key.

    `privkey` should be the 32 byte raw private key (as you would get from
    bitcoin.deserialize_privkey, etc).

    `message_hash` should be the 32 byte sha256d hash of the tx input (or
    message) you want to sign
    '''

    if not is_available():
        raise NotImplementedError("Schnorr is not available because module 'ecdsa' is not installed.")

    if not isinstance(privkey, bytes) or len(privkey) != 32:
        raise ValueError('privkey must be a bytes object of length 32')
    if not isinstance(message_hash, bytes) or len(message_hash) != 32:
        raise ValueError('message_hash must be a bytes object of length 32')

    G = ecdsa.SECP256k1.generator
    order = G.order()
    fieldsize = G.curve().p()

    secexp = int.from_bytes(privkey, 'big')
    if not 0 < secexp < order:
        raise ValueError('could not sign')
    pubpoint = secexp * G
    pubbytes = point_to_ser(pubpoint, comp=True)

    k = nonce_function_rfc6979(order, privkey, message_hash,
                               algo16=b'Schnorr+SHA256\x20\x20')
    R = k * G
    if jacobi(R.y(), fieldsize) == -1:
        k = order - k
    rbytes = R.x().to_bytes(32,'big')

    ebytes = hashlib.sha256(rbytes + pubbytes + message_hash).digest()
    e = int.from_bytes(ebytes, 'big')

    s = (k + e*secexp) % order

    return rbytes + s.to_bytes(32, 'big')

def point_to_ser(P, comp):
    bfh = bytes.fromhex
    if comp:
        return bfh( ('%02x'%(2+(P.y()&1)))+('%064x'%P.x()) )
    return bfh( '04'+('%064x'%P.x())+('%064x'%P.y()) )

def ECC_YfromX(x, curved, odd):
    _p = curved.p()
    _a = curved.a()
    _b = curved.b()
    for offset in range(128):
        Mx = x + offset
        My2 = pow(Mx, 3, _p) + _a * pow(Mx, 2, _p) + _b % _p
        My = pow(My2, (_p+1)//4, _p )

        if curved.contains_point(Mx,My):
            if odd == bool(My&1):
                return [My,offset]
            return [_p-My,offset]
    raise Exception('ECC_YfromX: No Y found')


def ser_to_point(Aser):
    generator = ecdsa.ecdsa.generator_secp256k1
    curve = ecdsa.ecdsa.curve_secp256k1
    from ecdsa.util import string_to_number
    from ecdsa.ellipticcurve import Point
    _r  = generator.order()
    assert Aser[0] in [0x02, 0x03, 0x04]
    if Aser[0] == 0x04:
        return Point( curve, string_to_number(Aser[1:33]), string_to_number(Aser[33:]), _r )
    Mx = string_to_number(Aser[1:])
    return Point( curve, Mx, ECC_YfromX(Mx, curve, Aser[0] == 0x03)[0], _r )


def verify(pubkey, signature, message_hash):
    '''Verify a Schnorr signature, returning True if valid.

    May raise a ValueError or return False on failure.

    `pubkey` should be the the raw public key bytes (as you would get from
    bitcoin.pubic_key_from_private_key, after hex decoding, etc).

    `signature` should be the 64 byte schnorr signature as would be returned
    from `sign` above.

    `message_hash` should be the 32 byte sha256d hash of the tx message to be
    verified'''

    if not is_available():
        raise NotImplementedError("Schnorr is not available because module 'ecdsa' is not installed.")

    if not isinstance(pubkey, bytes) or len(pubkey) not in (33, 65):
        raise ValueError('pubkey must be a bytes object of either length 33 or 65')
    if not isinstance(signature, bytes) or len(signature) != 64:
        raise ValueError('signature must be a bytes object of length 64')
    if not isinstance(message_hash, bytes) or len(message_hash) != 32:
        raise ValueError('message_hash must be a bytes object of length 32')
    G = ecdsa.SECP256k1.generator
    order = G.order()
    fieldsize = G.curve().p()

    try:
        pubpoint = ser_to_point(pubkey)
    except:
        # off-curve points, failed decompression, bad format,
        # point at infinity:
        raise ValueError('pubkey could not be parsed')

    rbytes = signature[:32]
    ## these unnecessary since below we do bytes comparison and
    ## R.x() is always < fieldsize.
    # r = int.from_bytes(rbytes, 'big')
    # if r >= fieldsize:
    #    return False

    sbytes = signature[32:]
    s = int.from_bytes(sbytes, 'big')
    if s >= order:
        return False

    # compressed format, regardless of whether pubkey was compressed or not:
    pubbytes = point_to_ser(pubpoint, comp=True)

    ebytes = hashlib.sha256(rbytes + pubbytes + message_hash).digest()
    e = int.from_bytes(ebytes, 'big')

    R = s*G + (- e)*pubpoint

    if R == ecdsa.ellipticcurve.INFINITY:
        return False

    if jacobi(R.y(), fieldsize) != 1:
        return False

    return (R.x().to_bytes(32, 'big') == rbytes)

class BlindSigner:
    """ Schnorr blind signature creator, signer side.

    We calculate R = k*G for some secret k, and share R with the requester.
    Then, upon receiving an e value, we calculate s = k + e*x, where x is our
    private key, and return s to the requester. The requester can use this to
    create a valid Schnorr signature from our public key, without us being able
    to link the exact request to the unblinded signature.

    The most CPU-intense part of this is initialization, where the R value is
    generated.

    Security note: If we were to sign two distinct requests for the same R,
    then our private key could be recovered. Thus, you can only call .sign()
    once (and this class enforces this restriction in a thread-safe manner).
    If you need a new blind signature then you must create a new instance.

    Security note 2: If an adversary knows that this private key is related
    to another key (say, they are related by multiplication or addition of a
    known factor), then the adversary can use blind signatures to get a valid
    signature *from the other key*! For example, all keys in a BIP32 "xpub"
    are related, and so you should seriously avoid using this function with
    standard BIP32 or any other public key derivation method.

    Security note 3: If a blind signer allows multiple blind signature
    requests to be serviced in parallel (i.e., have multiple `.get_R`'s issued
    at the same time, having not yet received the parameters for `.sign`),
    then an adversary can perform work and submit carefully designed requests
    that allow an additional signature to be created. E.g., with 511 parallel
    requests, 512 signatures could be produced with ~2^35 work of precomputation
    on the part of the adversary.

    See:

    - Schnorr 2001 "Security of Blind Discrete Log Signatures against Interactive Attacks"
      https://www.math.uni-frankfurt.de/~dmst/research/papers/schnorr.blind_sigs_attack.2001.pdf
    - Wagner 2002 "A Generalized Birthday Problem"
      https://www.iacr.org/archive/crypto2002/24420288/24420288.pdf
    - A possible solution that should make it so at least 2^70 work is needed
      to get an additional signature: https://eprint.iacr.org/2019/877
    """
    order = ecdsa.SECP256k1.generator.order()

    def __init__(self):
        if not is_available():
            raise NotImplementedError("Schnorr is not available because"
            " module 'ecdsa' is not installed.")
        k = ecdsa.util.randrange(self.order)
        # we store k in a list since .pop() is atomic.
        self._kcontainer = [k]
        Rpoint = k * ecdsa.SECP256k1.generator
        self.R = point_to_ser(Rpoint, comp=True)

    def get_R(self):
        return self.R

    def sign(self, privkey, ebytes):
        assert len(privkey) == 32
        assert len(ebytes) == 32
        try:
            k = self._kcontainer.pop()
        except IndexError:
            raise RuntimeError("Attempted to sign twice!")

        x = int.from_bytes(privkey, 'big')
        e = int.from_bytes(ebytes, 'big')

        s = (k + e * x) % self.order
        return s.to_bytes(32, 'big')


class BlindSignatureRequest:
    """ Schnorr blind signature creator, requester side.

    We expect to be set up with two elliptic curve points
    (serialized as bytes) -- the Blind signer's public key, and
    a nonce point whose secret is known by the signer. Also, the
    32-byte message_hash should be provided.

    Upon construction, this creates and remembers the blinding factors,
    and also performs the expensive math needed to create the blind
    signature request. One initialized, call .get_request() to obtain
    the 32-byte request that should be sent to the signer. Once you get
    back their 32-byte response, call finalize().

    The resultant Schnorr signatures follow the standard BCH Schnorr
    convention (using Jacobi symbol, pubkey prefixing and SHA256).

    Internally we use two random blinding factors a,b. Due to the jacobi
    thing, we have to also include a signflip factor c = +/- 1.

        [signer provides: R = k*G]
        R' = c*(R + a*G + b*P)
        choose c = +1 or -1 such that jacobi(R'.y(), fieldsize) = +1
        e' = Hash(R'.x | ser_compressed(P) | message32)
        e = c*e' + b mod n
        [send to signer: e]
        [signer provides: s = k + e*x]
        s' = c*(s + a) mod n

        resulting unblinded signature: (R'.x, s')

    Ref: https://blog.cryptographyengineering.com/a-note-on-blind-signature-schemes/
    """
    order = ecdsa.SECP256k1.generator.order()
    fieldsize = ecdsa.SECP256k1.curve.p()

    def __init__(self, pubkey, R, message_hash):
        """ Expects three bytes objects """
        if not is_available():
            raise NotImplementedError("Schnorr is not available because"
            " module 'ecdsa' is not installed.")
        assert isinstance(pubkey, bytes)
        assert isinstance(R, bytes)
        assert len(message_hash) == 32

        self.pubkey = pubkey
        self.R = R
        self.message_hash = message_hash

        self.a = ecdsa.util.randrange(self.order)
        self.b = ecdsa.util.randrange(self.order)
        self._calc_initial()
        assert self.c in (-1, +1)
        ehash = hashlib.sha256(self.Rxnew + self.pubkey_compressed + message_hash).digest()
        self.e = (self.c * int.from_bytes(ehash,'big') + self.b) % self.order

        self.enew = int.from_bytes(ehash,'big') % self.order # debug

    def _calc_initial(self):
        # Internal function, calculates Rxnew, c, and compressed pubkey.
        try:
            Rpoint = ser_to_point(self.R)
        except:
            # off-curve points, failed decompression, bad format,
            # point at infinity:
            raise ValueError('R could not be parsed')
        try:
            pubpoint = ser_to_point(self.pubkey)
        except:
            # off-curve points, failed decompression, bad format,
            # point at infinity:
            raise ValueError('pubkey could not be parsed')

        self.pubkey_compressed = point_to_ser(pubpoint, comp=True)

        # multiply & add the points -- takes ~190 microsec
        Rnew = Rpoint + self.a * ecdsa.SECP256k1.generator + self.b * pubpoint
        self.Rxnew = Rnew.x().to_bytes(32,'big')
        y = Rnew.y()

        # calculate the jacobi symbol (+1 or -1). ~30 microsec
        self.c = jacobi(y, self.fieldsize)

    def get_request(self,):
        """ returns 32 bytes e value, to be sent to the signer """
        return self.e.to_bytes(32,'big')

    def finalize(self, sbytes, check = True):
        """ expects 32 bytes s value, returns 64 byte finished signature

        If check=True (default) this will perform a verification of the result.
        Upon failure it raises RuntimeError. The cause for this error is that
        the blind signer has provided an incorrect blinded s value."""
        assert len(sbytes) == 32

        s = int.from_bytes(sbytes,'big')

        snew = (self.c*(s + self.a)) % self.order

        sig = self.Rxnew + snew.to_bytes(32,'big')
        if check and not verify(self.pubkey, sig, self.message_hash):
            raise RuntimeError("Blind signature verification failed.")
        return sig

__all__ = (
    'sign',
    'verify',
    'is_available',
    'BlindSigner',
    'BlindSignatureRequest'
)
