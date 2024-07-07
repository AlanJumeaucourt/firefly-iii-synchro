import asyncio
import logging
import os
import signal
from typing import List
from dataclasses import dataclass
import math

from dotenv import load_dotenv

from kresus import Kresus
from firefly_api import FireflyIIIAPI
from models import Transaction
from discordbot import DiscordBot

from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

@dataclass
class Config:
    firefly_api_url: str
    firefly_api_token: str
    kresus_api_url: str
    start_date: str
    discord_channel_id: str
    discord_token: str

    @classmethod
    def load(cls):
        load_dotenv()
        return cls(
            firefly_api_url=cls._load_env_var("FIREFLY_API_URL"),
            firefly_api_token=cls._load_env_var("FIREFLY_API_TOKEN"),
            kresus_api_url=cls._load_env_var("KRESUS_API_URL"),
            start_date=cls._load_env_var("START_DATE"),
            discord_channel_id=cls._load_env_var("DISCORD_CHANNEL_ID"),
            discord_token=cls._load_env_var("DISCORD_TOKEN"),
        )

    @staticmethod
    def _load_env_var(var_name: str) -> str:
        value = os.getenv(var_name)
        if value is None:
            raise EnvironmentError(f"{var_name} environment variable is not set")
        return value

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
    kresus_transactions = await kresus_api.list_transactions(start_date)
    firefly_transactions = await firefly_api.list_transactions(start=start_date)
    return check_kresus_missing_transactions(kresus_transactions, firefly_transactions)

async def periodic_task(coro, sleep_time: int):
    while True:
        try:
            await coro()
        except Exception as e:
            logger.error(f"Error in periodic task: {e}", exc_info=True)
        await asyncio.sleep(sleep_time)

async def run_bot(config: Config):
    async with Kresus(config.kresus_api_url) as kresus_api:
        async with FireflyIIIAPI(config.firefly_api_url, config.firefly_api_token) as firefly_api:
            discord_bot = DiscordBot(config.discord_token, int(config.discord_channel_id), firefly_api)

            async def fetch_and_update():
                missing_transactions = await fetch_missing_transactions(kresus_api, firefly_api, config.start_date)
                discord_bot.missing_transactions = missing_transactions
                logger.info(f"Found {len(missing_transactions)} missing transactions.")

            tasks = [
                periodic_task(fetch_and_update, 30),
                periodic_task(discord_bot.post_missing_transactions, 10),
                periodic_task(discord_bot.check_reaction, 10),
                discord_bot.start(),
            ]

            await asyncio.gather(*tasks)

async def main():
    config = Config.load()
    logger.info(f"Configuration loaded: {config}")

    await run_bot(config)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user.")

