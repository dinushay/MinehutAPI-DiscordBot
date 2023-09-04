import discord
from discord.ext import commands, tasks
import requests
import datetime
import configparser

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

config = configparser.ConfigParser()
config.read('config.ini')

token = config['BotConfig']['token']
channel_id = int(config['BotConfig']['channel_id'])
server_name = config['BotConfig']['server_name']
update_interval_seconds = int(config['BotConfig']['update_interval_seconds'])

display_config = config['BotDisplayRecommended']
display_server_last_online = display_config.getboolean('display_server_last_online')
display_total_joins = display_config.getboolean('display_total_joins')
display_server_status = display_config.getboolean('display_server_status')
display_server_online_players = display_config.getboolean('display_server_online_players')

display_config = config['BotDisplay']
display_creation = display_config.getboolean('display_creation')
display_motd = display_config.getboolean('display_motd')
display_categories = display_config.getboolean('display_categories')
display_credits_per_day = display_config.getboolean('display_credits_per_day')
display_server_plan = display_config.getboolean('display_server_plan')
display_visibility = display_config.getboolean('display_visibility')
display_suspended = display_config.getboolean('display_suspended')
display_server_version_type = display_config.getboolean('display_server_version_type')

api_url = f"https://api.minehut.com/server/{server_name}?byName=true"

message = None
api_error_message = None

@bot.event
async def on_ready():
    channel = bot.get_channel(channel_id)

    async for message in channel.history(limit=1):
        await message.delete()
    
    print(f"Bot {bot.user.name} is online!")

    query_api.change_interval(seconds=update_interval_seconds)
    query_api.start()
    await update_bot_status()

@tasks.loop(seconds=60)
async def query_api():
    global message
    global api_error_message

    url = api_url
    print(f"Calling API: {url}")
    response = requests.get(url)

    default_color = discord.Color.blurple()
    default_bot_status = discord.Status.online

    bot_status = default_bot_status

    if response.status_code == 200:
        data = response.json()
        server_name = data['server']['name']

        # Extract additional information from API data
        creation_timestamp = data['server']['creation']
        creation_datetime = datetime.datetime.fromtimestamp(creation_timestamp / 1000)

        motd = data['server']['motd']
        categories = ", ".join(data['server']['categories'])
        credits_per_day = data['server']['credits_per_day']
        server_plan = data['server']['server_plan']
        visibility = data['server']['visibility']
        suspended = data['server']['suspended']
        server_version_type = data['server']['server_version_type']

        players_status = "N/A"

        if 'online' in data['server']:
            if data['server']['online']:
                status = "Online"
                bot_status = discord.Status.online
                color = discord.Color.green()
                activity_text = f"{server_name} is online"
            else:
                status = "Offline"
                bot_status = discord.Status.dnd
                color = discord.Color.dark_red()
                activity_text = f"{server_name} is offline"
        else:
            status = "N/A"
            color = default_color

        if display_server_online_players:
            players_status = f"{data['server']['playerCount']} / {data['server']['maxPlayers']}"

        embed = discord.Embed(title=f"Server Info - {server_name}", color=color)

        if display_server_status:
            embed.add_field(name="Server status", value=status, inline=True)

        if display_server_online_players:
            embed.add_field(name="Server online players", value=players_status, inline=True)

        if display_total_joins:
            embed.add_field(name="Total joins", value=data['server']['joins'], inline=False)

        if display_server_last_online:
            epoch_time = data['server']['last_online'] / 1000
            date_last_online = f"<t:{int(epoch_time)}:R>"
            embed.add_field(name="Last server start", value=date_last_online, inline=False)

        if display_creation:
            date_creation = f"<t:{int(creation_timestamp / 1000)}:f>"
            embed.add_field(name="Creation", value=date_creation, inline=True)

        if display_motd:
            embed.add_field(name="MOTD", value=f"```{motd}```", inline=True)

        if display_categories:
            embed.add_field(name="Categories", value=categories, inline=True)

        if display_credits_per_day:
            embed.add_field(name="Credits Per Day", value=credits_per_day, inline=True)

        if display_server_plan:
            embed.add_field(name="Server Plan", value=server_plan, inline=True)

        if display_visibility:
            embed.add_field(name="Visibility", value=visibility, inline=True)

        if display_suspended:
            embed.add_field(name="Suspended", value=suspended, inline=True)

        if display_server_version_type:
            embed.add_field(name="Server Version Type", value=server_version_type, inline=True)

        now = datetime.datetime.now()
        time = now.strftime("%M:%S")
        embed.set_footer(text=f"Last updated: XX:{time}")

        channel = bot.get_channel(channel_id)

        if message is None:
            message = await channel.send(embed=embed, silent=True)
            print(f"Message sent to {channel.name}")
        else:
            await message.edit(embed=embed)
            print(f"Message edited in {channel.name}")

        if api_error_message is not None:
            await api_error_message.delete()
        
        await update_bot_status(bot_status, activity_text)
    else:
        if api_error_message is not None:
            await api_error_message.delete()
        
        print(f"Request failed with status code: {response.status_code}")
        await update_bot_status(discord.Status.idle, "API Error")
        channel = bot.get_channel(channel_id)
        embed = discord.Embed(title="API Error", description=f"Minehut-API request failed with status code: {response.status_code}", color=orange)
        api_error_message = await channel.send(embed=embed, silent=True)
        print(f"API Error message sent to {channel.name}")

        # Delete "Server Info" message if it exists
        if message is not None:
            await message.delete()
            message = None

        await update_bot_status(discord.Status.idle, "API Error")

async def update_bot_status(status=discord.Status.invisible, activity_text=None):
    await bot.change_presence(status=status, activity=discord.Game(name=activity_text))

bot.run(token)
