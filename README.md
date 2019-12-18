# python-bitcoincash

This Python3 library provides an easy interface to the bitcoin data
structures and protocol. The approach is low-level and "ground up", with a
focus on providing tools to manipulate the internals of how Bitcoin Cash works.

**[Reference documentation](https://bitcoincash.network/python)**

## Requirements

    sudo apt-get install libssl-dev

The RPC interface, `bitcoincash.rpc`, is designed to work with Bitcoin Unlimited v1.7.0.
Older versions are out of consensus.


## Structure

Everything consensus critical is found in the modules under bitcoincash.core. This
rule is followed pretty strictly, for instance chain parameters are split into
consensus critical and non-consensus-critical.

    bitcoincash.core            - Basic core definitions, datastructures, and
                                  (context-independent) validation
    bitcoincash.core.key        - ECC pubkeys
    bitcoincash.core.script     - Scripts and opcodes
    bitcoincash.core.scripteval - Script evaluation/verification
    bitcoincash.core.serialize  - Serialization

Non-consensus critical modules include the following:

    bitcoincash          - Chain selection
    bitcoincash.base58   - Base58 encoding
    bitcoincash.bloom    - Bloom filters (incomplete)
    bitcoincash.cashaddr - Cashaddr encoding
    bitcoincash.electrum - Bitcoin Electrum RPC interface support
    bitcoincash.net      - Network communication (in flux)
    bitcoincash.messages - Network messages (in flux)
    bitcoincash.rpc      - Bitcoin Satoshi-client RPC interface support
    bitcoincash.wallet   - Wallet-related code, currently Bitcoin address and
                           private key support

Effort has been made to follow the Satoshi source relatively closely, for
instance Python code and classes that duplicate the functionality of
corresponding Satoshi C++ code uses the same naming conventions: CTransaction,
CBlockHeader, nValue etc. Otherwise Python naming conventions are followed.


## Mutable vs. Immutable objects

Like the Bitcoin Unlimited codebase CTransaction is immutable and
CMutableTransaction is mutable; unlike the Bitcoin Core codebase this
distinction also applies to COutPoint, CTxIn, CTxOut, and CBlock.


## Endianness Gotchas

Rather confusingly Bitcoin Unlimited shows transaction and block hashes as
little-endian hex rather than the big-endian the rest of the world uses for
SHA256. python-bitcoincashlib provides the convenience functions x() and lx() in
bitcoin.core to convert from big-endian and little-endian hex to raw bytes to
accomodate this. In addition see b2x() and b2lx() for conversion from bytes to
big/little-endian hex.


## Module import style

While not always good style, it's often convenient for quick scripts if
`import *` can be used. To support that all the modules have `__all__` defined
appropriately.


# Example Code

See `examples/` directory. For instance this example creates a transaction
spending a pay-to-script-hash transaction output:

    $ PYTHONPATH=. examples/spend-pay-to-script-hash-txout.py
    <hex-encoded transaction>


## Selecting the chain to use

Do the following:

    import bitcoincash
    bitcoincash.SelectParams(NAME)

Where NAME is one of 'testnet', 'mainnet', or 'regtest'. The chain currently
selected is a global variable that changes behavior everywhere, just like in
the Satoshi codebase.


## Unit tests

Under bitcoincash/tests using test data from Bitcoin Unlimited. To run them:

    python3 -m unittest discover

To also enable electrum tests (these connect to a remote server), set the
`ELECTRUM_TESTS` env variable

    ELECTRUM_TESTS=1 python3 -m unittest discover


Alternately, if Tox (see https://tox.readthedocs.org/) is available on your
system, you can run unit tests for multiple Python versions:

    ./runtests.sh

HTML coverage reports can then be found in the htmlcov/ subdirectory.

## Documentation

Sphinx documentation is in the "doc" subdirectory. Run "make help" from there
to see how to build. You will need the Python "sphinx" package installed.

Currently this is just API documentation generated from the code and
docstrings. Higher level written docs would be useful, perhaps starting with
much of this README. Pages are written in reStructuredText and linked from
index.rst.
