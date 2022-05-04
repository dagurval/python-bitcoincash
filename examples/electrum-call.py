from bitcoincash.electrum import Electrum
import asyncio

async def main():
    cli = Electrum()
    await cli.connect()
    print(await cli.RPC('blockchain.block.header', 613880))
    await cli.close()

asyncio.run(main())
