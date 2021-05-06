import discord
from discord.ext import commands
from dataclasses import dataclass
from itertools import combinations
import random
import os

bot = commands.Bot(command_prefix='!', help_command=None)


@dataclass
class Player:
    """
    The Player class represents a discord user. The rank value
    is determined based off of their Valorant Competitive rank.
    """
    user: str
    rank: int

    def __str__(self):
        return self.user


@dataclass
class TeamCombination:
    """
    The TeamCombination class represents a possible pairing
    of 5 players vs 5 players. The evaluation is the difference
    between these teams and perfectly fair teams
    """
    team1: list[Player]
    team2: list[Player]
    evaluation: float

# RANKS is a dictionairy that maps a Valorant rank to elo
RANKS = {
    'bronze1': 640,
    'bronze2': 670,
    'bronze3': 710,
    'silver1': 800,
    'silver2': 830,
    'silver3': 860,
    'gold1': 960,
    'gold2': 990,
    'gold3': 1020,
    'plat1': 1050,
    'plat2': 1080,
    'plat3': 1110
}

CURRENT_PLAYERS = []

TEAMS = []

CURRENT_TEAM: int = 0

TEAM1 = []
TEAM2 = []

GAME_OVER = True

@bot.command()
async def help(ctx):
    embed=discord.Embed(title="5v5 Bot Help")
    embed.set_thumbnail(url="https://yt3.ggpht.com/ytc/AAUvwnh5cX3Hpigfm2Y3X1VAd1QrVBWgzFeaIM8RAuTu=s900-c-k-c0x00ffffff-no-rj")
    embed.add_field(name="!join (rank)", value="Adds you to the 5v5 (!join gold2)", inline=False)
    embed.add_field(name="!players", value="Displays all players in the 5v5", inline=False)
    embed.add_field(name="!maketeams", value="Makes teams according to rankings", inline=False)
    embed.add_field(name="!next", value="Shows a new variation of teams", inline=False)
    embed.add_field(name="!choose", value="Locks in the teams", inline=False)
    embed.add_field(name="!winner (0,1,2)", value="Input the winner of the 5v5 (!winner 1 for Team 1, 0 for a tie)", inline=False)
    embed.add_field(name="!boost", value="Slightly increases the ranking of a player", inline=False)
    embed.add_field(name="!kick (player-name)", value="Kicks a player from the 5v5", inline=False)
    embed.add_field(name="!leave", value="Removes you from the 5v5", inline=False)
    await ctx.send(embed=embed)
    

def win_probability(team1: list[Player], team2: list[Player]) -> float:
    """
    win_probability calculates the probability of one team winning using the
    elo equation
    """
    sum1 = sum(a.rank for a in team1)
    sum2 = sum(a.rank for a in team2)
    p = 1 / (1 + 10 ** ((sum1 - sum2) / 400))
    return p


@bot.command()
async def join(ctx, rank):
    """
    The join function adds a user to the current party if they send the message
    !join <current rank>
    """
    player = ctx.author
    for p in CURRENT_PLAYERS:
        if p.user == str(player):
            await ctx.send(str(player) + ' has already been added to the game!')
            return
    if rank not in RANKS:
        await ctx.send("Please give a valid rank!")
        return
    elo = RANKS[rank]
    if len(CURRENT_PLAYERS) >= 10:
        await ctx.send('There are already 10 people in the game')
        return
    CURRENT_PLAYERS.append(Player(str(player), elo))
    embed=discord.Embed()
    embed.add_field(name="Join success", value=str(player) + " has successfully joined!", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def reset(ctx):
    """
    The reset function removes all players from the current party and resets
    all of the global variables
    """
    CURRENT_PLAYERS.clear()
    TEAM1.clear()
    TEAM2.clear()
    TEAMS.clear()
    global CURRENT_TEAM
    CURRENT_TEAM = 0
    await ctx.send("Current players has been reset")


def format_players(players):
    """
    format_players takes a Player class and makes a string
    that is outputed in the Discord channel
    """
    if not players:
        return "No players added"
    result = ""
    cnt = 1
    for player in players:
        result += str(cnt) + ". " + player.user + "\n"
        cnt += 1
    return result


@bot.command()
async def players(ctx):
    """
    players returns a list of all the players currently in the party
    """
    embed=discord.Embed()
    embed.add_field(name="Players", value=format_players(CURRENT_PLAYERS), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def maketeams(ctx):
    """
    maketeams checks every combination of the party and returns a team
    that is relatively equal in strength
    """
    global CURRENT_TEAM, TEAMS
    CURRENT_TEAM = 0
    TEAMS = []
    if len(CURRENT_PLAYERS) != 10:
        await ctx.send('Please get 10 players!')
        return
    for combo in combinations(CURRENT_PLAYERS, 5):
        team2 = [x for x in CURRENT_PLAYERS if x not in combo]
        evaluation = abs(0.5 - win_probability(combo, team2))
        TEAMS.append(TeamCombination(combo, team2, evaluation))
    TEAMS.sort(key=lambda x: x.evaluation)
    TEAMS = TEAMS[:20]
    random.shuffle(TEAMS)

    embed=discord.Embed()
    embed.add_field(name="5v5 Teams", value='Team 1:\n' + format_players(TEAMS[0].team1) + '\nTeam 2:\n' + format_players(TEAMS[0].team2), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def next(ctx):
    """
    newteams gives another team combination of similar fairness
    """
    global CURRENT_TEAM
    CURRENT_TEAM += 1
    if CURRENT_TEAM < len(TEAMS):
        embed=discord.Embed()
        embed.add_field(name="5v5 Teams", value='Team 1:\n' + format_players(TEAMS[CURRENT_TEAM].team1) + '\nTeam 2:\n' + format_players(
            TEAMS[CURRENT_TEAM].team2), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Teams have not been made")


@bot.command()
async def choose(ctx):
    """
    choose locks in the current team choices and the game begins!
    """
    global TEAM1, TEAM2, GAME_OVER
    TEAM1 = TEAMS[CURRENT_TEAM].team1
    TEAM2 = TEAMS[CURRENT_TEAM].team2
    GAME_OVER = False
    await ctx.send('glhf!')


@bot.command()
async def winner(ctx, val):
    """
    winner tells the bot who won the game - Team 1 or Team 2.
    The team ranks are adjusted accordingly
    """
    global GAME_OVER, TEAM1, TEAM2
    if GAME_OVER:
        await ctx.send('There is no game right now - get some friends and make teams')
        return
    if val not in {'0', '1', '2'}:
        await ctx.send('Not a valid team!')
    if val == '1':
        for player in TEAM1:
            player.rank += 8
        for player in TEAM2:
            player.rank -= 8
    elif val == '2':
        for player in TEAM2:
            player.rank += 8
        for player in TEAM1:
            player.rank -= 8
    GAME_OVER = True
    await ctx.send('GGWP! Want to play another?')


@bot.command()
async def boost(ctx):
    """
    boost slightly increases a player's rank to deal with the possibility
    of their abilities being higher than their rank
    """
    player = str(ctx.author)
    for p in CURRENT_PLAYERS:
        if p.user == player:
            p.rank += 8
            cur = p
            break
    await ctx.send(cur.user + "'s elo has been increased")


@bot.command()
async def leave(ctx):
    """
    leave removes a player from the current party
    """
    player = str(ctx.author)
    for p in CURRENT_PLAYERS:
        if p.user == player:
            CURRENT_PLAYERS.remove(p)
            break
    await ctx.send('You have left the party. We hope you had fun!')


@bot.command()
async def kick(ctx, player):
    """
    kick forces a player out of the current lobby
    """
    kicked = False
    for p in CURRENT_PLAYERS:
        if p.user == player:
            CURRENT_PLAYERS.remove(p)
            kicked = True
            break
    if kicked:
        await ctx.send(str(player) + " has been kicked. rip")
    else:
        await ctx.send(str(player) + ' is not in the party.')


bot.run(os.getenv('BOT-KEY'))
