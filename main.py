import os
import random
from itertools import combinations

import discord
from discord.ext import commands

from server import Player, TeamCombination, Server

bot = commands.Bot(command_prefix='!', help_command=None)

servers = {}

# RANKS is a dictionary that maps a Valorant rank to elo
# Larger increments are used for ranks with greater skill disparity
RANKS = {
    'iron1': 570,
    'iron2': 610,
    'iron3': 650,
    'bronze1': 670,
    'bronze2': 690,
    'bronze3': 710,
    'silver1': 730,
    'silver2': 750,
    'silver3': 770,
    'gold1': 800,
    'gold2': 830,
    'gold3': 860,
    'plat1': 880,
    'plat2': 900,
    'plat3': 920,
    'diamond1': 940,
    'diamond2': 960,
    'diamond3': 980,
    'radiant': 1020
}


def get_server(guild) -> Server:
    return servers[guild]


@bot.before_invoke
async def create_guild(ctx):
    print(ctx.guild.id)
    if ctx.guild not in servers:
        servers[ctx.guild] = Server()


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="5v5 Bot Help")
    embed.set_thumbnail(
        url="https://yt3.ggpht.com/ytc/AAUvwnh5cX3Hpigfm2Y3X1VAd1QrVBWgzFeaIM8RAuTu=s900-c-k-c0x00ffffff-no-rj")
    embed.add_field(name="!join (rank)", value="Adds you to the 5v5 (!join gold2)", inline=False)
    embed.add_field(name="!players", value="Displays all players in the 5v5", inline=False)
    embed.add_field(name="!maketeams", value="Makes teams according to rankings", inline=False)
    embed.add_field(name="!next", value="Shows a new variation of teams", inline=False)
    embed.add_field(name="!choose", value="Locks in the teams", inline=False)
    embed.add_field(name="!winner (0,1,2)", value="Input the winner of the 5v5 (!winner 1 for Team 1, 0 for a tie)",
                    inline=False)
    embed.add_field(name="!boost", value="Slightly increases the ranking of a player", inline=False)
    embed.add_field(name="!kick (player-name)", value="Kicks a player from the 5v5", inline=False)
    embed.add_field(name="!leave", value="Removes you from the 5v5", inline=False)
    embed.add_field(name="!reset", value="Removes all players", inline=False)
    embed.add_field(name="!randommap", value="Gives a random map", inline=False)
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
    server = get_server(ctx.guild)
    current_players = server.current_players
    player = ctx.author
    for p in current_players:
        if p.user == str(player):
            await ctx.send(str(player) + ' has already been added to the game!')
            return
    if rank not in RANKS:
        await ctx.send("Please give a valid rank!")
        return
    elo = RANKS[rank]
    if len(current_players) >= 10:
        await ctx.send('There are already 10 people in the game')
        return
    current_players.append(Player(str(player), elo))
    embed = discord.Embed()
    embed.add_field(name="Join success", value=str(player) + " has successfully joined!", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def reset(ctx):
    """
    The reset function removes all players from the current party and resets
    all of the global variables
    """
    server = get_server(ctx.guild)
    server.current_players.clear()
    server.team1.clear()
    server.team2.clear()
    server.teams.clear()
    server.current_team = 0
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
    server = get_server(ctx.guild)
    embed = discord.Embed()
    embed.add_field(name="Players", value=format_players(server.current_players), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def maketeams(ctx):
    """
    maketeams checks every combination of the party and returns a team
    that is relatively equal in strength
    """
    server = get_server(ctx.guild)
    server.current_team = 0
    server.teams = []
    if len(server.current_players) != 10:
        await ctx.send('Please get 10 players!')
        return
    for combo in combinations(server.current_players, 5):
        team2 = [x for x in server.current_players if x not in combo]
        evaluation = abs(0.5 - win_probability(combo, team2))
        server.teams.append(TeamCombination(combo, team2, evaluation))
    server.teams.sort(key=lambda x: x.evaluation)
    server.teams = server.teams[:20]
    random.shuffle(server.teams)

    embed = discord.Embed()
    embed.add_field(name="5v5 Teams",
                    value='Team 1:\n' + format_players(server.teams[0].team1) + '\nTeam 2:\n' + format_players(
                        server.teams[0].team2), inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def next(ctx):
    """
    next gives another team combination of similar fairness
    """
    server = get_server(ctx.guild)
    server.current_team += 1
    if server.current_team < len(server.teams):
        embed = discord.Embed()
        embed.add_field(name="5v5 Teams", value='Team 1:\n' + format_players(
            server.teams[server.current_team].team1) + '\nTeam 2:\n' + format_players(
            server.teams[server.current_team].team2), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("Teams have not been made")


@bot.command()
async def choose(ctx):
    """
    choose locks in the current team choices and the game begins!
    """
    server = get_server(ctx.guild)
    server.team1 = server.teams[server.current_team].team1
    server.team2 = server.teams[server.current_team].team2
    server.game_over = False
    await ctx.send('glhf!')


@bot.command()
async def winner(ctx, val):
    """
    winner tells the bot who won the game - Team 1 or Team 2.
    The team ranks are adjusted accordingly
    """
    server = get_server(ctx.guild)
    if server.game_over:
        await ctx.send('There is no game right now - get some friends and make teams')
        return
    if val not in {'0', '1', '2'}:
        await ctx.send('Not a valid team!')
    if val == '1':
        for player in server.team1:
            player.rank += 8
        for player in server.team2:
            player.rank -= 8
    elif val == '2':
        for player in server.team2:
            player.rank += 8
        for player in server.team1:
            player.rank -= 8
    server.game_over = True
    await ctx.send('GGWP! Want to play another?')


@bot.command()
async def boost(ctx):
    """
    boost slightly increases a player's rank to deal with the possibility
    of their abilities being higher than their rank
    """
    server = get_server(ctx.guild)
    player = str(ctx.author)
    for p in server.current_players:
        if p.user == player:
            p.rank += 8
            break
    await ctx.send(player + "'s elo has been increased")


@bot.command()
async def leave(ctx):
    """
    leave removes a player from the current party
    """
    server = get_server(ctx.guild)
    player = str(ctx.author)
    for p in server.current_players:
        if p.user == player:
            server.current_players.remove(p)
            break
    await ctx.send('You have left the party. We hope you had fun!')


@bot.command()
async def kick(ctx, player):
    """
    kick forces a player out of the current lobby
    """
    server = get_server(ctx.guild)
    kicked = False
    for p in server.current_players:
        if p.user == player:
            server.current_players.remove(p)
            kicked = True
            break
    if kicked:
        await ctx.send(str(player) + " has been kicked. rip")
    else:
        await ctx.send(str(player) + ' is not in the party.')


@bot.command()
async def randommap(ctx):
    await ctx.send(random.choice(['Bind', 'Split', 'Haven', 'Icebox', 'Breeze']))


bot.run(os.getenv('BOT-KEY'))
