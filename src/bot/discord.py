import asyncio
import logging
from typing import List, Optional
from discord.ext import commands
import discord
from discord import Intents, Message, User, TextChannel, Embed, Member, Colour
from models import Transaction
import json
import hashlib
from api import FireflyIIIAPI


logger = logging.getLogger(__name__)


class DiscordBot:
    def __init__(self, token: str, channel_id: int, firefly_api: FireflyIIIAPI):
        intents = Intents.default()
        intents.message_content = True
        intents.reactions = True

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.token = token
        self.channel_id = int(channel_id)
        self.channel: Optional[TextChannel] = None
        self.firefly_api = firefly_api
        self.missing_transactions: List[Transaction] = []

        self.bot.event(self.on_ready)
        self.bot.event(self.on_raw_reaction_add)

    async def on_ready(self):
        logger.info(f"Bot is ready. Logged in as {self.bot.user}")
        self.channel = self.bot.get_channel(self.channel_id)

        if not self.channel:
            logger.error(
                f"Failed to find channel with ID {self.channel_id}. Bot may not have access."
            )
            return

        logger.info(f"Bot connected to channel: {self.channel.name}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            logger.error(f"Failed to find channel with ID {payload.channel_id}")
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            logger.error(f"Failed to find message with ID {payload.message_id}")
            return

        user = self.bot.get_user(payload.user_id)
        if user is None:
            user = await self.bot.fetch_user(payload.user_id)

        if user is None:
            logger.error(f"Failed to find user with ID {payload.user_id}")
            return

        await self.handle_reaction(message, payload.emoji, user)

    async def handle_reaction(
        self, message: Message, emoji: discord.PartialEmoji, user: User | Member
    ):
        logger.info(f"Reaction {emoji} added by {user.name} on message {message.id}.")

        if (
            user.id != self.bot.user.id
            and str(emoji) == "➕"
            and message.author == self.bot.user
            and "🔄" not in [str(r.emoji) for r in message.reactions]
        ):

            await message.add_reaction("🔄")

            transaction = self.find_transaction_from_message(message)
            if transaction:
                await self.process_transaction(message, transaction)
            else:
                logger.error("Failed to find transaction from message.")

    async def process_transaction(self, message: Message, transaction: Transaction):
        try:
            transaction_added = await self.add_missing_transaction(transaction)
            actual_embed = message.embeds[0].to_dict()
            sha256_field = None
            for field in actual_embed['fields']:
                if field["name"] == "Sha256":
                    sha256_field = field["value"]
                    break

            new_embed = self.format_transaction_embedded(transaction_added, "Transaction added", discord.Colour.green(), sha256_field)
            new_embed.add_field(name="Link", value=f"{self.firefly_api.api_url.replace('/api/v1', '')}/transactions/show/{transaction_added.transaction_id}", inline=False)
            await message.edit(embed=new_embed)
            await message.add_reaction("✅")
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            await message.add_reaction("❌")

    async def check_reaction(self):
        if self.channel is None:
            logger.error("Channel not set. Please call start() method first.")
            return

        logger.info("Checking reactions...")
        async for message in self.channel.history(limit=200):
            for reaction in message.reactions:
                if str(reaction.emoji) == "➕" and not reaction.me:
                    await self.handle_reaction(
                        message, reaction.emoji, reaction.message.author
                    )

    async def post_missing_transactions(self):
        if self.channel is None:
            logger.error("Channel not set. Please call start() method first.")
            return

        logger.info("Start posting missing transactions...")

        for transaction in self.missing_transactions:
            if not await self.is_transaction_posted(
                self.channel, self.sha256_transaction(transaction)
            ):
                embed = self.format_transaction_embedded(transaction, "Missing transaction", discord.Colour.orange())
                message = await self.channel.send(embed=embed)
                await message.add_reaction("➕")
            else:
                logger.info(f"Transaction {transaction} already posted.")

    async def add_missing_transaction(self, transaction: Transaction) -> Transaction:
        logger.info(f"Adding transaction {transaction} to Firefly-III...")
        transaction_added = await self.firefly_api.store_transaction(transaction)
        logger.info(f"Transaction {transaction} added to Firefly-III.")
        return transaction_added

    def find_transaction_from_message(self, message: Message) -> Optional[Transaction]:
        for field in message.embeds[0].fields:
            if field.name == "Sha256":
                transaction_sha256 = field.value
                for missing_transaction in self.missing_transactions:
                    if (
                        self.sha256_transaction(missing_transaction)
                        == transaction_sha256
                    ):
                        logger.info(
                            f"Transaction {missing_transaction} found from message."
                        )
                        return missing_transaction
        return None

    async def start(self):
        await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()
        logger.info("Bot closed.")

    @staticmethod
    def sha256_transaction(transaction: Transaction) -> str:
        return hashlib.sha256(
            json.dumps(
                transaction.__dict__, indent=4, sort_keys=True, default=str
            ).encode()
        ).hexdigest()

    @staticmethod
    async def is_transaction_posted(
        channel: TextChannel, transaction_sha256: str
    ) -> bool:
        async for message in channel.history(limit=200):
            for embed in message.embeds:
                for field in embed.fields:
                    if field.name == "Sha256" and field.value == transaction_sha256:
                        return True
        return False

    @staticmethod
    def format_transaction_embedded(transaction: Transaction, title: str, color: Colour, sha_256: str = None) -> Embed:
        embed = Embed(title=title, color=color)
        embed.add_field(
            name="Sha256",
            value=sha_256 if sha_256 else DiscordBot.sha256_transaction(transaction),
            inline=False,
        )
        embed.add_field(name="Date", value=transaction.date, inline=False)
        embed.add_field(name="Amount", value=transaction.amount, inline=False)
        embed.add_field(name="Type", value=transaction.type, inline=False)
        embed.add_field(name="Description", value=transaction.description, inline=False)
        embed.add_field(name="Source", value=transaction.source_name, inline=False)
        embed.add_field(
            name="Destination", value=transaction.destination_name, inline=False
        )
        return embed


# Usage example
async def main():
    token = "your_discord_token"
    channel_id = 123456789  # Replace with your channel ID
    firefly_api = FireflyIIIAPI(
        "https://your-firefly-instance.com/api", "your-api-token"
    )

    bot = DiscordBot(token, channel_id, firefly_api)

    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
