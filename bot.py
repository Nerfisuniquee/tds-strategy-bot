import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from typing import List

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

STRATS_FILE = 'strategies.json'

# PERMISSION SETTINGS - CHANGE THESE
ALLOWED_USER_ID = 748100466579210251  # Replace with your Discord User ID
ALLOWED_ROLE_NAMES = ["Creator", "Activity Helper", "Tester", "Carry Manager"]  # Role names that can edit strats

# Permission check function
def can_edit_strats(interaction: discord.Interaction) -> bool:
    # Check if user is the specific allowed user
    if interaction.user.id == ALLOWED_USER_ID:
        return True
    
    # Check if user has any of the allowed roles
    if interaction.guild:  # Make sure it's in a server
        user_roles = [role.name for role in interaction.user.roles]
        if any(role in ALLOWED_ROLE_NAMES for role in user_roles):
            return True
    
    return False

# Predefined choices for maps
MAP_CHOICES = [
    app_commands.Choice(name="Polluted Wastelands 2", value="Polluted Wastelands 2"),
    app_commands.Choice(name="Pizza Party", value="Pizza Party"),
    app_commands.Choice(name="Badlands 2", value="Badlands 2"),
    app_commands.Choice(name="Fallen", value="Fallen"),
    app_commands.Choice(name="Molten", value="Molten"),
    app_commands.Choice(name="Event", value="Event"),
    app_commands.Choice(name="Missions", value="Missions"),
    app_commands.Choice(name="Hardcore", value="Hardcore"),
    app_commands.Choice(name="Hardcore Missions", value="Hardcore Missions"),
    app_commands.Choice(name="Hidden Wave", value="Hidden Wave"),
]

# Predefined choices for player modes
PLAYER_CHOICES = [
    app_commands.Choice(name="Solo", value="Solo"),
    app_commands.Choice(name="Duo", value="Duo"),
    app_commands.Choice(name="Trio", value="Trio"),
    app_commands.Choice(name="Quad", value="Quad"),
]

# Load strategies from file
def load_strategies():
    if os.path.exists(STRATS_FILE):
        with open(STRATS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save strategies to file
def save_strategies(strategies):
    with open(STRATS_FILE, 'w') as f:
        json.dump(strategies, f, indent=2)

strategies = load_strategies()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} is online!')
    print(f'Loaded {sum(len(v["strats"]) for v in strategies.values())} strategies')

@bot.tree.command(name="addstrat", description="Add a new strategy")
@app_commands.describe(
    map_name="Map name",
    players="Player mode",
    strat_name="Strategy name",
    link="Google Docs link to the strategy",
    notes="Optional: Important notes for this strategy",
    dps_options="Optional: DPS priorities (e.g., Accelerator — Pursuit — Engineer)",
    image_urls="Optional: Image URLs separated by commas (e.g., url1, url2, url3)"
)
@app_commands.choices(map_name=MAP_CHOICES, players=PLAYER_CHOICES)
async def add_strategy(
    interaction: discord.Interaction,
    map_name: app_commands.Choice[str],
    players: app_commands.Choice[str],
    strat_name: str,
    link: str,
    notes: str = None,
    dps_options: str = None,
    image_urls: str = None
):
    # Permission check
    if not can_edit_strats(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to add strategies!",
            ephemeral=True
        )
        return
    
    map_value = map_name.value
    player_value = players.value
    key = f"{map_value}_{player_value}".lower().replace(" ", "_")
    
    if key not in strategies:
        strategies[key] = {
            'map': map_value,
            'players': player_value,
            'strats': []
        }
    
    # Parse multiple image URLs
    images = []
    if image_urls:
        images = [url.strip() for url in image_urls.split(',') if url.strip()]
    
    strat_id = len(strategies[key]['strats']) + 1
    strategies[key]['strats'].append({
        'id': strat_id,
        'name': strat_name,
        'link': link,
        'notes': notes,
        'dps_options': dps_options,
        'images': images,
        'added_by': str(interaction.user)
    })
    
    save_strategies(strategies)
    
    embed = discord.Embed(
        title="✅ Strategy Added",
        description=f"Added strategy for **{map_value}** ({player_value})",
        color=discord.Color.green()
    )
    embed.add_field(name="Strategy Name", value=strat_name, inline=False)
    embed.add_field(name="Link", value=link, inline=False)
    if notes:
        embed.add_field(name="📝 Notes", value=notes, inline=False)
    if dps_options:
        embed.add_field(name="🎯 DPS Options", value=dps_options, inline=False)
    if images:
        embed.add_field(name="🖼️ Images", value=f"{len(images)} image(s) added", inline=False)
        embed.set_image(url=images[0])  # Show first image as preview
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="strat", description="Get strategies for a map")
@app_commands.describe(
    map_name="Map name",
    players="Player mode",
    amount="Number of strategies to show (default: 3)"
)
@app_commands.choices(map_name=MAP_CHOICES, players=PLAYER_CHOICES)
async def get_strategy(
    interaction: discord.Interaction,
    map_name: app_commands.Choice[str],
    players: app_commands.Choice[str],
    amount: int = 3
):
    map_value = map_name.value
    player_value = players.value
    key = f"{map_value}_{player_value}".lower().replace(" ", "_")
    
    if key not in strategies or not strategies[key]['strats']:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_value}** ({player_value})",
            ephemeral=True
        )
        return
    
    strats = strategies[key]['strats'][:amount]
    
    embed = discord.Embed(
        title=f"📋 {map_value} - {player_value}",
        description=f"Showing {len(strats)} of {len(strategies[key]['strats'])} available strategies",
        color=discord.Color.blue()
    )
    
    for strat in strats:
        embed.add_field(
            name=f"Strat {strat['id']}: {strat['name']}",
            value=strat['link'],
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="removestrat", description="Remove a strategy")
@app_commands.describe(
    map_name="Map name",
    players="Player mode",
    strat_id="Strategy ID to remove"
)
@app_commands.choices(map_name=MAP_CHOICES, players=PLAYER_CHOICES)
async def remove_strategy(
    interaction: discord.Interaction,
    map_name: app_commands.Choice[str],
    players: app_commands.Choice[str],
    strat_id: int
):
    # Permission check
    if not can_edit_strats(interaction):
        await interaction.response.send_message(
            "❌ You don't have permission to remove strategies!",
            ephemeral=True
        )
        return
    
    map_value = map_name.value
    player_value = players.value
    key = f"{map_value}_{player_value}".lower().replace(" ", "_")
    
    if key not in strategies:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_value}** ({player_value})",
            ephemeral=True
        )
        return
    
    # Find and remove the strategy
    original_count = len(strategies[key]['strats'])
    strategies[key]['strats'] = [s for s in strategies[key]['strats'] if s['id'] != strat_id]
    
    if len(strategies[key]['strats']) == original_count:
        await interaction.response.send_message(
            f"❌ Strategy #{strat_id} not found for **{map_value}** ({player_value})",
            ephemeral=True
        )
        return
    
    # Re-index remaining strategies
    for i, strat in enumerate(strategies[key]['strats'], 1):
        strat['id'] = i
    
    # Remove key if no strategies left
    if not strategies[key]['strats']:
        del strategies[key]
    
    save_strategies(strategies)
    
    embed = discord.Embed(
        title="🗑️ Strategy Removed",
        description=f"Removed strategy #{strat_id} from **{map_value}** ({player_value})",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="liststrats", description="List all available maps and modes")
async def list_strategies(interaction: discord.Interaction):
    if not strategies:
        await interaction.response.send_message("❌ No strategies stored yet!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📚 Available Strategies",
        color=discord.Color.purple()
    )
    
    for key, data in sorted(strategies.items()):
        embed.add_field(
            name=f"{data['map']} - {data['players']}",
            value=f"{len(data['strats'])} strategies",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="viewstrat", description="View a specific strategy")
@app_commands.describe(
    map_name="Map name",
    players="Player mode",
    strat_id="Strategy ID to view"
)
@app_commands.choices(map_name=MAP_CHOICES, players=PLAYER_CHOICES)
async def view_strategy(
    interaction: discord.Interaction,
    map_name: app_commands.Choice[str],
    players: app_commands.Choice[str],
    strat_id: int
):
    map_value = map_name.value
    player_value = players.value
    key = f"{map_value}_{player_value}".lower().replace(" ", "_")
    
    if key not in strategies:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_value}** ({player_value})",
            ephemeral=True
        )
        return
    
    strat = next((s for s in strategies[key]['strats'] if s['id'] == strat_id), None)
    
    if not strat:
        await interaction.response.send_message(
            f"❌ Strategy #{strat_id} not found for **{map_value}** ({player_value})",
            ephemeral=True
        )
        return
    
    # Main embed with details
    embed = discord.Embed(
        title=f"Strategy #{strat_id}: {strat['name']}",
        description=f"**{map_value}** - {player_value}",
        color=discord.Color.gold()
    )
    embed.add_field(name="🔗 Link", value=strat['link'], inline=False)
    
    if strat.get('notes'):
        embed.add_field(name="📝 Notes", value=strat['notes'], inline=False)
    if strat.get('dps_options'):
        embed.add_field(name="🎯 DPS Options", value=strat['dps_options'], inline=False)
    
    embed.set_footer(text=f"Added by {strat['added_by']}")
    
    # Get images (support both old 'loadout_image' and new 'images' format)
    images = strat.get('images', [])
    if not images and strat.get('loadout_image'):
        images = [strat['loadout_image']]
    
    if images:
        # Set first image in the main embed
        embed.set_image(url=images[0])
        await interaction.response.send_message(embed=embed)
        
        # Send additional images as separate embeds
        for img_url in images[1:]:
            img_embed = discord.Embed(color=discord.Color.gold())
            img_embed.set_image(url=img_url)
            await interaction.followup.send(embed=img_embed)
    else:
        await interaction.response.send_message(embed=embed)

# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN') or os.environ.get('DISCORD_TOKEN')
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Available env vars:", list(os.environ.keys()))
        exit(1)
    print("Token found! Starting bot...")
    
    # Retry logic for rate limits
    import time
    max_retries = 5
    retry_delay = 60  # Start with 60 seconds
    
    for attempt in range(max_retries):
        try:
            bot.run(TOKEN)
            break  # If successful, exit the loop
        except discord.errors.HTTPException as e:
            if e.status == 429:  # Rate limit error
                print(f"Rate limited! Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise  # Re-raise other HTTP errors
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
