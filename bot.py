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
    print(f'Loaded {sum(len(v) for v in strategies.values())} strategies')

# Create a group for strat commands
@bot.tree.command(name="addstrat", description="Add a new strategy")
@app_commands.describe(
    map_name="Map name (e.g., Polluted Wastelands 2)",
    players="Player mode (e.g., Duo, Solo, Trio)",
    strat_name="Strategy name",
    link="Google Docs link to the strategy"
)
async def add_strategy(
    interaction: discord.Interaction,
    map_name: str,
    players: str,
    strat_name: str,
    link: str
):
    key = f"{map_name}_{players}".lower().replace(" ", "_")
    
    if key not in strategies:
        strategies[key] = {
            'map': map_name,
            'players': players,
            'strats': []
        }
    
    strat_id = len(strategies[key]['strats']) + 1
    strategies[key]['strats'].append({
        'id': strat_id,
        'name': strat_name,
        'link': link,
        'added_by': str(interaction.user)
    })
    
    save_strategies(strategies)
    
    embed = discord.Embed(
        title="✅ Strategy Added",
        description=f"Added strategy for **{map_name}** ({players})",
        color=discord.Color.green()
    )
    embed.add_field(name="Strategy Name", value=strat_name, inline=False)
    embed.add_field(name="Link", value=link, inline=False)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="strat", description="Get strategies for a map")
@app_commands.describe(
    map_name="Map name (e.g., Polluted Wastelands 2)",
    players="Player mode (e.g., Duo, Solo, Trio)",
    amount="Number of strategies to show (default: 3)"
)
async def get_strategy(
    interaction: discord.Interaction,
    map_name: str,
    players: str,
    amount: int = 3
):
    key = f"{map_name}_{players}".lower().replace(" ", "_")
    
    if key not in strategies or not strategies[key]['strats']:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_name}** ({players})",
            ephemeral=True
        )
        return
    
    strats = strategies[key]['strats'][:amount]
    
    embed = discord.Embed(
        title=f"📋 {map_name} - {players}",
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
    map_name="Map name (e.g., Polluted Wastelands 2)",
    players="Player mode (e.g., Duo, Solo, Trio)",
    strat_id="Strategy ID to remove"
)
async def remove_strategy(
    interaction: discord.Interaction,
    map_name: str,
    players: str,
    strat_id: int
):
    key = f"{map_name}_{players}".lower().replace(" ", "_")
    
    if key not in strategies:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_name}** ({players})",
            ephemeral=True
        )
        return
    
    # Find and remove the strategy
    original_count = len(strategies[key]['strats'])
    strategies[key]['strats'] = [s for s in strategies[key]['strats'] if s['id'] != strat_id]
    
    if len(strategies[key]['strats']) == original_count:
        await interaction.response.send_message(
            f"❌ Strategy #{strat_id} not found for **{map_name}** ({players})",
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
        description=f"Removed strategy #{strat_id} from **{map_name}** ({players})",
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
    map_name="Map name (e.g., Polluted Wastelands 2)",
    players="Player mode (e.g., Duo, Solo, Trio)",
    strat_id="Strategy ID to view"
)
async def view_strategy(
    interaction: discord.Interaction,
    map_name: str,
    players: str,
    strat_id: int
):
    key = f"{map_name}_{players}".lower().replace(" ", "_")
    
    if key not in strategies:
        await interaction.response.send_message(
            f"❌ No strategies found for **{map_name}** ({players})",
            ephemeral=True
        )
        return
    
    strat = next((s for s in strategies[key]['strats'] if s['id'] == strat_id), None)
    
    if not strat:
        await interaction.response.send_message(
            f"❌ Strategy #{strat_id} not found for **{map_name}** ({players})",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title=f"Strategy #{strat_id}: {strat['name']}",
        description=f"**{map_name}** - {players}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Link", value=strat['link'], inline=False)
    embed.set_footer(text=f"Added by {strat['added_by']}")
    
    await interaction.response.send_message(embed=embed)

# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        exit(1)
    bot.run(TOKEN)
