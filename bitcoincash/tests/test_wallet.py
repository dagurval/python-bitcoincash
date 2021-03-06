# Copyright (C) 2013-2015 The python-bitcoinlib developers
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

import hashlib
import unittest

from bitcoincash.core import b2x, x
from bitcoincash.core.script import CScript, IsLowDERSignature
from bitcoincash.core.key import CPubKey, is_libsec256k1_available, use_libsecp256k1_for_signing
from bitcoincash.wallet import *
import bitcoincash.cashaddr

class Test_CBitcoinAddress(unittest.TestCase):
    def test_create_from_string(self):
        """Create CBitcoinAddress's from strings"""

        def T(str_addr, expected_bytes, expected_type, expected_class):
            addr = CBitcoinAddress(str_addr)
            self.assertEqual(addr.to_bytes(), expected_bytes)
            self.assertEqual(addr.kind, expected_type)
            self.assertEqual(addr.__class__, expected_class)

        T('bitcoincash:qp3wjpa3tjlj042z2wv7hahsldgwhwy0rq9sywjpyy',
          x('62e907b15cbf27d5425399ebf6f0fb50ebb88f18'), bitcoincash.cashaddr.PUBKEY_TYPE,
          P2PKHBitcoinAddress)

        T('bitcoincash:pppxdlr09s5xr4l7y2dj0xnesqa0efa6xsxkp8ax88',
          x('4266fc6f2c2861d7fe229b279a79803afca7ba34'), bitcoincash.cashaddr.SCRIPT_TYPE,
          P2SHBitcoinAddress)

    def test_wrong_prefix(self):
        """Creating a CBitcoinAddress from wrong prefix fails"""

        # tests run in mainnet, so both of the following should fail
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress('bchtest:qp3wjpa3tjlj042z2wv7hahsldgwhwy0rqpzqfskrc')

        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress('bchtest:pppxdlr09s5xr4l7y2dj0xnesqa0efa6xszy9ql3qm')

    def test_from_scriptPubKey(self):
        def T(hex_scriptpubkey, expected_str_address, expected_class):
            scriptPubKey = CScript(x(hex_scriptpubkey))
            addr = CBitcoinAddress.from_scriptPubKey(scriptPubKey)
            self.assertEqual(str(addr), expected_str_address)
            self.assertEqual(addr.__class__, expected_class)

        T('a914000000000000000000000000000000000000000087',
          'bitcoincash:pqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq7k2ehe5v',
          P2SHBitcoinAddress)
        T('76a914000000000000000000000000000000000000000088ac',
          'bitcoincash:qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqfnhks603',
          P2PKHBitcoinAddress)

    def test_from_nonstd_scriptPubKey(self):
        """CBitcoinAddress.from_scriptPubKey() with non-standard scriptPubKeys"""

        # Bad P2SH scriptPubKeys

        # non-canonical pushdata
        scriptPubKey = CScript(x('a94c14000000000000000000000000000000000000000087'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

        # Bad P2PKH scriptPubKeys

        # Missing a byte
        scriptPubKey = CScript(x('76a914000000000000000000000000000000000000000088'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

        # One extra byte
        scriptPubKey = CScript(x('76a914000000000000000000000000000000000000000088acac'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

        # One byte changed
        scriptPubKey = CScript(x('76a914000000000000000000000000000000000000000088ad'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

    def test_from_invalid_scriptPubKey(self):
        """CBitcoinAddress.from_scriptPubKey() with invalid scriptPubKeys"""

        # We should raise a CBitcoinAddressError, not any other type of error

        # Truncated P2SH
        scriptPubKey = CScript(x('a91400000000000000000000000000000000000000'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

        # Truncated P2PKH
        scriptPubKey = CScript(x('76a91400000000000000000000000000000000000000'))
        with self.assertRaises(CBitcoinAddressError):
            CBitcoinAddress.from_scriptPubKey(scriptPubKey)

    def test_to_scriptPubKey(self):
        """CBitcoinAddress.to_scriptPubKey() works"""
        def T(str_addr, expected_scriptPubKey_hexbytes):
            addr = CBitcoinAddress(str_addr)

            actual_scriptPubKey = addr.to_scriptPubKey()
            self.assertEqual(b2x(actual_scriptPubKey), expected_scriptPubKey_hexbytes)

        T('bitcoincash:pqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq7k2ehe5v',
          'a914000000000000000000000000000000000000000087')

        T('bitcoincash:qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqfnhks603',
          '76a914000000000000000000000000000000000000000088ac')

class Test_P2SHBitcoinAddress(unittest.TestCase):
    def test_from_redeemScript(self):
        addr = P2SHBitcoinAddress.from_redeemScript(CScript())
        self.assertEqual(str(addr), 'bitcoincash:pz689gnx6z7cnsfhq6jpxtx0k9hhcwulev5cpumfk0')

class Test_P2PKHBitcoinAddress(unittest.TestCase):
    def test_from_non_canonical_scriptPubKey(self):
        def T(hex_scriptpubkey, expected_str_address):
            scriptPubKey = CScript(x(hex_scriptpubkey))
            addr = P2PKHBitcoinAddress.from_scriptPubKey(scriptPubKey)
            self.assertEqual(str(addr), expected_str_address)

            # now test that CBitcoinAddressError is raised with accept_non_canonical_pushdata=False
            with self.assertRaises(CBitcoinAddressError):
                P2PKHBitcoinAddress.from_scriptPubKey(scriptPubKey, accept_non_canonical_pushdata=False)

        T('76a94c14000000000000000000000000000000000000000088ac',
            legacy_to_cashaddr('1111111111111111111114oLvT2'))
        T('76a94d1400000000000000000000000000000000000000000088ac',
            legacy_to_cashaddr('1111111111111111111114oLvT2'))
        T('76a94e14000000000000000000000000000000000000000000000088ac',
            legacy_to_cashaddr('1111111111111111111114oLvT2'))

        # make sure invalid scripts raise CBitcoinAddressError
        with self.assertRaises(CBitcoinAddressError):
            P2PKHBitcoinAddress.from_scriptPubKey(x('76a94c14'))

    def test_from_bare_checksig_scriptPubKey(self):
        def T(hex_scriptpubkey, expected_str_address):
            scriptPubKey = CScript(x(hex_scriptpubkey))
            addr = P2PKHBitcoinAddress.from_scriptPubKey(scriptPubKey)
            self.assertEqual(str(addr), expected_str_address)

            # now test that CBitcoinAddressError is raised with accept_non_canonical_pushdata=False
            with self.assertRaises(CBitcoinAddressError):
                P2PKHBitcoinAddress.from_scriptPubKey(scriptPubKey, accept_bare_checksig=False)

        # compressed
        T('21000000000000000000000000000000000000000000000000000000000000000000ac',
            legacy_to_cashaddr('14p5cGy5DZmtNMQwTQiytBvxMVuTmFMSyU'))

        # uncompressed
        T('410000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ac',
            legacy_to_cashaddr('1QLFaVVt99p1y18zWSZnespzhkFxjwBbdP'))

        # non-canonical encoding
        T('4c21000000000000000000000000000000000000000000000000000000000000000000ac',
            legacy_to_cashaddr('14p5cGy5DZmtNMQwTQiytBvxMVuTmFMSyU'))

        # odd-lengths are *not* accepted
        with self.assertRaises(CBitcoinAddressError):
            P2PKHBitcoinAddress.from_scriptPubKey(x('2200000000000000000000000000000000000000000000000000000000000000000000ac'))

    def test_from_valid_pubkey(self):
        """Create P2PKHBitcoinAddress's from valid pubkeys"""

        def T(pubkey, expected_str_addr):
            addr = P2PKHBitcoinAddress.from_pubkey(pubkey)
            self.assertEqual(str(addr), legacy_to_cashaddr(expected_str_addr))

        T(x('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71'),
          '1C7zdTfnkzmr13HfA2vNm5SJYRK6nEKyq8')
        T(x('0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71a1518063243acd4dfe96b66e3f2ec8013c8e072cd09b3834a19f81f659cc3455'),
          '1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T')

        T(CPubKey(x('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71')),
          '1C7zdTfnkzmr13HfA2vNm5SJYRK6nEKyq8')
        T(CPubKey(x('0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71a1518063243acd4dfe96b66e3f2ec8013c8e072cd09b3834a19f81f659cc3455')),
          '1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T')

    def test_from_invalid_pubkeys(self):
        """Create P2PKHBitcoinAddress's from invalid pubkeys"""

        # first test with accept_invalid=True
        def T(invalid_pubkey, expected_str_addr):
            addr = P2PKHBitcoinAddress.from_pubkey(invalid_pubkey, accept_invalid=True)
            self.assertEqual(str(addr), expected_str_addr)

        T(x(''),
          legacy_to_cashaddr('1HT7xU2Ngenf7D4yocz2SAcnNLW7rK8d4E'))
        T(x('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c72'),
          legacy_to_cashaddr('1L9V4NXbNtZsLjrD3nkU7gtEYLWRBWXLiZ'))

        # With accept_invalid=False we should get CBitcoinAddressError's
        with self.assertRaises(CBitcoinAddressError):
            P2PKHBitcoinAddress.from_pubkey(x(''))
        with self.assertRaises(CBitcoinAddressError):
            P2PKHBitcoinAddress.from_pubkey(x('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c72'))
        with self.assertRaises(CBitcoinAddressError):
            P2PKHBitcoinAddress.from_pubkey(CPubKey(x('0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c72')))

    def test_to_scriptHash(self):
        # P2PKH, example from electrumx doc
        addr = CBitcoinAddress("bitcoincash:qp3wjpa3tjlj042z2wv7hahsldgwhwy0rq9sywjpyy")
        self.assertEqual("8b01df4e368ea28f8dc0423bcf7a4923e3a12d307c875e47a0cfbf90b5c39161",
            addr.to_scriptHash())

        # P2SH, eatbch
        addr = CBitcoinAddress("bitcoincash:pp8skudq3x5hzw8ew7vzsw8tn4k8wxsqsv0lt0mf3g")
        self.assertEqual("829ce9ce75a8a8a01bf27a7365655506614ef0b8f5a7ecbef19093951a73b686", addr.to_scriptHash())

class Test_CBitcoinSecret(unittest.TestCase):
    def test(self):
        def T(base58_privkey, expected_hex_pubkey, expected_is_compressed_value):
            key = CBitcoinSecret(base58_privkey)
            self.assertEqual(b2x(key.pub), expected_hex_pubkey)
            self.assertEqual(key.is_compressed, expected_is_compressed_value)

        T('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS',
          '0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71a1518063243acd4dfe96b66e3f2ec8013c8e072cd09b3834a19f81f659cc3455',
          False)
        T('L3p8oAcQTtuokSCRHQ7i4MhjWc9zornvpJLfmg62sYpLRJF9woSu',
          '0378d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71',
          True)

    def test_sign(self):
        key = CBitcoinSecret('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        hash = b'\x00' * 32
        sig = key.signECDSA(hash)

        # Check a valid signature
        self.assertTrue(key.pub.verifyECDSA(hash, sig))
        self.assertTrue(IsLowDERSignature(sig))

        # Check that invalid hash returns false
        self.assertFalse(key.pub.verifyECDSA(b'\xFF'*32, sig))

        # Check that invalid signature returns false.
        #
        # Note the one-in-four-billion chance of a false positive :)
        self.assertFalse(key.pub.verifyECDSA(hash, sig[0:-4] + b'\x00\x00\x00\x00'))

    def test_sign_invalid_hash(self):
        key = CBitcoinSecret('5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS')
        with self.assertRaises(TypeError):
          sig = key.signECDSA('0' * 32)

        hash = b'\x00' * 32
        with self.assertRaises(ValueError):
          sig = key.signECDSA(hash[0:-2])


class Test_RFC6979(unittest.TestCase):
    def test(self):
        if not is_libsec256k1_available():
            return

        use_libsecp256k1_for_signing(True)

        # Test Vectors for RFC 6979 ECDSA, secp256k1, SHA-256
        # (private key, message, expected k, expected signature)
        test_vectors = [
            (0x1, "Satoshi Nakamoto", 0x8F8A276C19F4149656B280621E358CCE24F5F52542772691EE69063B74F15D15, "934b1ea10a4b3c1757e2b0c017d0b6143ce3c9a7e6a4a49860d7a6ab210ee3d82442ce9d2b916064108014783e923ec36b49743e2ffa1c4496f01a512aafd9e5"),
            (0x1, "All those moments will be lost in time, like tears in rain. Time to die...", 0x38AA22D72376B4DBC472E06C3BA403EE0A394DA63FC58D88686C611ABA98D6B3, "8600dbd41e348fe5c9465ab92d23e3db8b98b873beecd930736488696438cb6b547fe64427496db33bf66019dacbf0039c04199abb0122918601db38a72cfc21"),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140, "Satoshi Nakamoto", 0x33A19B60E25FB6F4435AF53A3D42D493644827367E6453928554F43E49AA6F90, "fd567d121db66e382991534ada77a6bd3106f0a1098c231e47993447cd6af2d06b39cd0eb1bc8603e159ef5c20a5c8ad685a45b06ce9bebed3f153d10d93bed5"),
            (0xf8b8af8ce3c7cca5e300d33939540c10d45ce001b8f252bfbc57ba0342904181, "Alan Turing", 0x525A82B70E67874398067543FD84C83D30C175FDC45FDEEE082FE13B1D7CFDF1, "7063ae83e7f62bbb171798131b4a0564b956930092b33b07b395615d9ec7e15c58dfcc1e00a35e1572f366ffe34ba0fc47db1e7189759b9fb233c5b05ab388ea"),
            (0xe91671c46231f833a6406ccbea0e3e392c76c167bac1cb013f6f1013980455c2, "There is a computer disease that anybody who works with computers knows about. It's a very serious disease and it interferes completely with the work. The trouble with computers is that you 'play' with them!", 0x1F4B84C23A86A221D233F2521BE018D9318639D5B8BBD6374A8A59232D16AD3D, "b552edd27580141f3b2a5463048cb7cd3e047b97c9f98076c32dbdf85a68718b279fa72dd19bfae05577e06c7c0c1900c371fcd5893f7e1d56a37d30174671f6")
        ]
        for vector in test_vectors:
            secret = CBitcoinSecret.from_secret_bytes(x('{:064x}'.format(vector[0])))
            encoded_sig = secret.signECDSA(hashlib.sha256(vector[1].encode('utf8')).digest())

            assert(encoded_sig[0] == 0x30)
            assert(encoded_sig[1] == len(encoded_sig)-2)
            assert(encoded_sig[2] == 0x02)

            rlen = encoded_sig[3]
            rpos = 4
            assert(rlen in (32, 33))

            if rlen == 33:
                assert(encoded_sig[rpos] == 0)
                rpos += 1
                rlen -= 1

            rval = encoded_sig[rpos:rpos+rlen]
            spos = rpos+rlen
            assert(encoded_sig[spos] == 0x02)

            spos += 1
            slen = encoded_sig[spos]
            assert(slen in (32, 33))

            spos += 1
            if slen == 33:
                assert(encoded_sig[spos] == 0)
                spos += 1
                slen -= 1

            sval = encoded_sig[spos:spos+slen]
            sig = b2x(rval + sval)
            assert(str(sig) == vector[3])

        use_libsecp256k1_for_signing(False)
