import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from cryptoaddress import EthereumAddress
from tinydb import TinyDB, Query

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = os.getenv('DB_PATH')
COMMANDS_CHANNEL_ID = int(os.getenv('COMMANDS_CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
ALLOW_ROLE = os.getenv('ALLOW_ROLE')

db = TinyDB(DB_PATH)
Entry = Query()


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='$', description="", intents=intents)


def getFullName(ctx):
    return f'{ctx.author.name}#{ctx.author.discriminator}'


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


def has_role_in_server(role: str, guildId: int):
    '''
    Check that a user has a given role in a given server
    '''
    def predicate(ctx):
        result = role in [role_.name for role_ in bot.get_guild(
            guildId).get_member(ctx.author.id).roles]
        if result:
            return result
        else:
            raise commands.CommandError(
                f"Role `{role}` is required to run this command.")

    return commands.check(predicate)


def command_channel_restriction(botChannelId: int):
    '''
    Check if context is in the commands channel or bot DM
    '''
    def predicate(ctx):
        return (isinstance(ctx.channel, discord.channel.DMChannel) or (ctx.channel.id == botChannelId))
    return commands.check(predicate)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        return
    elif isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print(f'{getFullName(ctx)} attempted to execute command without permission on message {ctx.message.id}')
    await ctx.send(error)


@bot.command()
@command_channel_restriction(COMMANDS_CHANNEL_ID)
@has_role_in_server(ALLOW_ROLE, GUILD_ID)
async def registerWallet(ctx, address: str):
    '''
    Register a wallet address for a given user and write it to the database
    '''
    print('Register', getFullName(ctx), address)
    id = ctx.author.id
    db.upsert({'id': id, 'name': getFullName(ctx),
              'address': address}, Entry.id == id)

    await checkWallet(ctx)



@bot.command()
@command_channel_restriction(COMMANDS_CHANNEL_ID)
@has_role_in_server(ALLOW_ROLE, GUILD_ID)
async def removeWallet(ctx):
    '''
    Remove a wallet address for a given user from the database
    '''
    print('Remove for', getFullName(ctx))
    id = ctx.author.id
    db.remove(Entry.id == id)

    await checkWallet(ctx)


@bot.command()
@command_channel_restriction(COMMANDS_CHANNEL_ID)
async def checkWallet(ctx):
    '''
    Check the registered address for a given user
    '''
    results = db.search(Entry.id == ctx.author.id)
    address = results[0]["address"] if len(results) > 0 else None

    response = f'The registered address for `{getFullName(ctx)}` is `{address}`.'

    if address is not None:
        try:
            EthereumAddress(address)
        except ValueError as e:
            response += ' **Attention!! The provided address is not a valid Ethereum address!**'

    await ctx.send(response)

bot.run(TOKEN)
