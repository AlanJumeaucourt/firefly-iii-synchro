import asyncio
import logging
import os
import signal
from typing import List
import math

from dotenv import load_dotenv

from kresus import Kresus
from firefly_api import FireflyIIIAPI
from models import Transaction
from discordbot import DiscordBot

# pylint: disable=W1203 # logging format is not a constant string

# Setup logging
logger = logging.getLogger(__name__)
from logging_config import setup_logging

setup_logging()


class ConfigLoader:
    @staticmethod
    def __load_env_var(var_name: str) -> str:
        var = os.getenv(var_name)
        if var is None:
            raise EnvironmentError(f"{var_name} environment variable is not set")
        return var

    @staticmethod
    def load_config():
        load_dotenv()
        return {
            "firefly_api_url": ConfigLoader.__load_env_var("FIREFLY_API_URL"),
            "firefly_api_token": ConfigLoader.__load_env_var("FIREFLY_API_TOKEN"),
            "kresus_api_url": ConfigLoader.__load_env_var("KRESUS_API_URL"),
            "start_date": ConfigLoader.__load_env_var("START_DATE"),
            "discord_channel_id": ConfigLoader.__load_env_var("DISCORD_CHANNEL_ID"),
            "discord_token": ConfigLoader.__load_env_var("DISCORD_TOKEN"),
        }


def check_kresus_missing_transactions(
    local_transactions: List[Transaction], transactions_list: List[Transaction]
) -> List[Transaction]:
    """
    Compares Kresus transactions with those in an external dataset to identify missing transactions.

    Args:
        local_transactions (List[Transaction]): Transactions obtained from Kresus.
        transactions_list (List[Transaction]): Transactions from the external dataset.

    Returns:
        List[Transaction]: Transactions that are present in Kresus but missing in the external dataset.
    """
    missing_transactions: List[Transaction] = []

    for local_transaction in local_transactions:
        match_found = False

        for transaction in transactions_list:
            if (
                local_transaction.date == transaction.date
                and math.isclose(
                    local_transaction.amount, transaction.amount, abs_tol=0.001
                )
                and (
                    (local_transaction.source_name == transaction.source_name)
                    or (
                        local_transaction.destination_name
                        == transaction.destination_name
                    )
                )
            ):
                match_found = True
                break
        if not match_found:
            missing_transactions.append(local_transaction)

    return missing_transactions


async def fetch_missing_transactions(
    kresus_api: Kresus, firefly_api: FireflyIIIAPI, start_date: str
) -> List[Transaction]:
    """
    Fetches transactions from Kresus and Firefly-III, and identifies missing transactions.

    Args:
        kresus_api (Kresus): Instance of the Kresus API client.
        firefly_api (FireflyIIIAPI): Instance of the Firefly-III API client.
        start_date (str): The start date to fetch transactions from.

    Returns:
        List[Transaction]: List of missing transactions.
    """
    kresus_transactions = await asyncio.to_thread(
        kresus_api.list_transactions, start_date
    )
    firefly_transactions = await asyncio.to_thread(firefly_api.list_transactions)
    missing_transactions = check_kresus_missing_transactions(
        kresus_transactions, firefly_transactions
    )
    return missing_transactions


async def main() -> None:
    # Load configuration
    config = ConfigLoader.load_config()
    logger.info(f"Configuration loaded: {config}")

    # Initialize APIs and Discord bot
    kresus_api = Kresus(config["kresus_api_url"])
    firefly_api = FireflyIIIAPI(config["firefly_api_url"], config["firefly_api_token"])
    discord_bot = DiscordBot(
        config["discord_token"], config["discord_channel_id"], firefly_api
    )

    async def periodic_fetch(sleep_time: int):
        while True:
            try:
                missing_transactions = await fetch_missing_transactions(
                    kresus_api, firefly_api, config["start_date"]
                )
                discord_bot.missing_transactions = missing_transactions
                logger.info(f"Found {len(missing_transactions)} missing transactions.")
            except Exception as e:
                logger.error(f"Error fetching missing transactions: {e}")
            await asyncio.sleep(sleep_time)

    async def periodic_post_missing_transactions(sleep_time: int):
        while True:
            try:
                await discord_bot.post_missing_transactions()
            except Exception as e:
                logger.error(f"Error posting missing transactions: {e}")
            await asyncio.sleep(sleep_time)

    async def check_discord_reaction(sleep_time: int):
        while True:
            try:
                await discord_bot.check_reaction()
            except Exception as e:
                logger.error(f"Error checking reactions: {e}")
            await asyncio.sleep(sleep_time)

    async def shutdown(signal, loop):
        logger.info(f"Received exit signal {signal.name}...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.info(f"Cancelling {len(tasks)} tasks...")
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)
        loop.stop()

    loop = asyncio.get_running_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop)))

    asyncio.create_task(periodic_fetch(sleep_time=30))
    asyncio.create_task(periodic_post_missing_transactions(sleep_time=10))
    asyncio.create_task(check_discord_reaction(sleep_time=10))
    await discord_bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")
