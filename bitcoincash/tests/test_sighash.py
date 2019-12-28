# Copyright (C) 2013-2017 The python-bitcoinlib developers
# Copyright (C) 2019 The python-bitcoincashlib developers
#
# This file is part of python-bitcoinlib.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of python-bitcoinlib, including this file, may be copied, modified,
# propagated, or distributed except according to the terms contained in the
# LICENSE file.

import json
import os
import unittest

from bitcoincash.core import *
from bitcoincash.core.script import *
from bitcoincash.core.scripteval import *

def load_test_vectors(name):
    with open(os.path.dirname(__file__) + '/data/' + name, 'r') as fd:
        for test_case in json.load(fd):
            if len(test_case) == 1:
                continue # comment

            raw_tx, raw_script, input_index, hashType, sighnature_hash = test_case

            tx = CTransaction.deserialize(x(raw_tx))
            script = CScript(x(raw_script))
            amount = 0
            yield (tx, script, input_index, hashType, sighnature_hash)



class Test_SigHash(unittest.TestCase):

    def test_sighash(self):
        failures = []
        for test in load_test_vectors('sighash.json'):
            (tx, script, input_index, hashType, signature_hash) = test
            try:
                CheckTransaction(tx)
            except CheckTransactionError as e:
                self.fail("test failed CheckTransaction(): {}".format(e))
                continue

            try:
                sh = SignatureHash(script, tx, input_index, hashType, 0,
                        legacy_allow = True, legacy_raw = True)
            except ValueError as e:
                self.fail("test failed SignatureHash(): {}".format(e))
                continue

            self.assertEqual(b2lx(sh), signature_hash)

