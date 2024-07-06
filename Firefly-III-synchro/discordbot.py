import asyncio
import logging
from typing import List
from discord.ext import commands
import discord
from discord import Intents, Message, Reaction, User, TextChannel, Embed
from models import Transaction  # Assuming you have a Transaction class
import json
import hashlib
from firefly_api import FireflyIIIAPI

# pylint: disable=W1203 # logging format is not a constant string

logger = logging.getLogger(__name__)





class DiscordBot:
    def __init__(self, token: str, channel_id: int, firefly_api: FireflyIIIAPI):
        intents = Intents.all()
        intents.typing = False
        intents.presences = False
        intents.reactions = True  # Enable reactions intent
        intents.messages = True  # Enable messages intent, necessary to read message content
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.token = token
        self.channel_id = int(channel_id)
        self.bot.event(self.on_ready)
        # self.bot.event(self.on_reaction_add)
        self.bot.event(self.on_raw_reaction_add)
        self.channel = None
        self.firefly_api = firefly_api
        self.missing_transactions: List[Transaction] = []



    async def on_ready(self):
        logger.info(f"Bot is ready. Logged in as {self.bot.user}")
        await self.bot.wait_until_ready()
        self.channel = self.bot.get_channel(self.channel_id)

        if not self.channel:
            logger.error(f"Failed to find channel with ID {self.channel_id}. Bot may not have access.")
            return

        logger.info(f"Bot connected to channel: {self.channel.name}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        # Check if the reaction is on a bot's message and is a check mark
        logger.info(f"Reaction {reaction.emoji} added by {user.name} on message {reaction.message.content}.")
        if user != self.bot.user and reaction.emoji == "➕" and reaction.message.author == self.bot.user and "🔄" not in [r.emoji for r in reaction.message.reactions]:
            await reaction.message.add_reaction("🔄")

            transaction_sha256 = None
            logger.info(f"Checking message {reaction.message.content} for sha256...")
            for field in reaction.message.embeds[0].fields:
                if field.name == "Sha256":
                    transaction_sha256 = field.value
                    break

            if transaction_sha256:
                transaction = self.find_transaction_from_message(reaction.message)
                logger.info(f"Transaction {transaction} found from message.")
                if transaction:
                    await self.add_missing_transaction(transaction)
                    new_embed = discord.Embed.from_dict(reaction.message.embeds[0].to_dict())
                    new_embed.title = "Transaction added"
                    new_embed.colour = 0x00FF00
                    await reaction.message.edit(embed=new_embed)
                    await reaction.message.add_reaction("✅")

                else:
                    logger.error(f"Failed to find transaction with sha256 {transaction_sha256}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        logger.info(f"Raw reaction added: {payload}")
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
        user = self.bot.get_user(payload.user_id)
        await self.on_reaction_add(reaction, user)

    async def check_reaction(self):
        if self.channel is None:
            logger.error("Channel not set. Please call start() method first.")
            return

        logger.info("Checking reactions...")
        async for message in self.channel.history(limit=200):
            for reaction in message.reactions:
                if reaction.emoji == "➕":
                    if not reaction.me:
                        await self.on_reaction_add(reaction, "FakeUser")

    async def post_missing_transactions(self):
        if self.channel is None:
            logger.error("Channel not set. Please call start() method first.")
            return

        logger.info("Start posting missing transactions...")

        if self.missing_transactions:
            for transaction in self.missing_transactions:
                transaction_exists = await self.is_transaction_posted(self.channel, self.sha256_transaction(transaction))
                if not transaction_exists:
                    embed = self.format_transaction_embeded(transaction)
                    send_message = await self.channel.send(embed=embed)
                    await send_message.add_reaction("➕")
                else:
                    logger.info(f"Transaction {transaction} already posted.")

    async def add_missing_transaction(self, transaction: Transaction):
        logger.info(f"Adding transaction {transaction} to Firefly-III...")
        self.firefly_api.put_transaction(transaction)
        logger.info(f"Transaction {transaction} added to Firefly-III.")

    def find_transaction_from_message(self, message: Message) -> Transaction:
        for field in message.embeds[0].fields:
            if field.name == "Sha256":
                transaction_sha256 = field.value
                for missing_transaction in self.missing_transactions:
                    if self.sha256_transaction(missing_transaction) == transaction_sha256:
                        logger.info(f"Transaction {missing_transaction} found from message.")
                        return missing_transaction

        return None

    async def start(self):
        await self.bot.start(self.token)

    async def stop(self):
        await self.bot.close()
        logger.info("Bot closed.")



    def sha256_transaction(self, transaction: Transaction) -> str:
        return hashlib.sha256(
            json.dumps(transaction.__dict__, indent=4, sort_keys=True, default=str).encode()
        ).hexdigest()

    async def is_transaction_posted(self, channel: TextChannel, transaction_sha256: str):
        async for message in channel.history(limit=200):  # Adjust limit as needed
            for embed in message.embeds:
                for field in embed.fields:
                    if field.name == "Sha256" and field.value == transaction_sha256:
                        return True
        return False

    def format_transaction_embeded(self, transaction: Transaction) -> Embed:
        embed = Embed(title="Missing transaction", color=0xFF5733)
        embed.add_field(name="Sha256", value=self.sha256_transaction(transaction), inline=False)
        embed.add_field(name="Date", value=transaction.date, inline=False)
        embed.add_field(name="Amount", value=transaction.amount, inline=False)
        embed.add_field(name="Type", value=transaction.type, inline=False)
        embed.add_field(name="Description", value=transaction.description, inline=False)
        embed.add_field(name="Source", value=transaction.source_name, inline=False)
        embed.add_field(name="Destination", value=transaction.destination_name, inline=False)
        return embed
