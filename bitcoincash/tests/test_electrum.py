import bitcoincash.electrum
from bitcoincash.core import CBlockHeader, x, b2lx
import asyncio
import unittest
import os

def skip_unless_enabled():
    if 'ELECTRUM_TESTS' in os.environ and os.environ['ELECTRUM_TESTS']:
           return

    raise unittest.SkipTest("Electrum tests disabled. Set ELECTRUM_TEST env variable to enable")

class TestElectrum(unittest.TestCase):
    def test_basic_rpc(self):
        skip_unless_enabled()
        loop = asyncio.get_event_loop()
        cli = bitcoincash.electrum.Electrum(loop = loop)
        loop.run_until_complete(cli.connect())

        header_hex = loop.run_until_complete(cli.RPC('blockchain.block.header', 613880))
        header = CBlockHeader.deserialize(x(header_hex))
        self.assertEqual(
                "f9acfe3f0e98fc321123f787e21e17984998f46866d30244328bf7552051d57a",
                b2lx(header.hashMerkleRoot))

        cli.close()
        loop.close()

if __name__ == '__main__':
    unittest.main()
