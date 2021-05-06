from discord.ext import commands
from dataclasses import dataclass
from itertools import combinations
import random
import os

bot = commands.Bot(command_prefix='!')


@dataclass
class Player:
    user: str
    rank: int

    def __str__(self):
        return self.user


@dataclass
class TeamCombination:
    team1: list[Player]
    team2: list[Player]
    evaluation: float


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


def win_probability(team1: list[Player], team2: list[Player]) -> float:
    sum1 = sum(a.rank for a in team1)
    sum2 = sum(a.rank for a in team2)
    p = 1 / (1 + 10 ** ((sum1 - sum2) / 400))
    return p


@bot.command()
async def join(ctx, rank):
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
    await ctx.send(str(player) + ' has successfully joined!')


@bot.command()
async def reset(ctx):
    CURRENT_PLAYERS.clear()
    await ctx.send("Current players has been reset")


def format_players(players):
    if not players:
        return "No players added"
    result = ""
    cnt = 1
    for player in players:
        result += str(cnt) + ". " + player.user + " (" + str(player.rank) + ")" + "\n"
        cnt += 1
    return result


@bot.command()
async def players(ctx):
    await ctx.send(format_players(CURRENT_PLAYERS))


@bot.command()
async def maketeams(ctx):
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
    await ctx.send('Team 1:\n' + format_players(TEAMS[0].team1) + '\nTeam 2:\n' + format_players(TEAMS[0].team2))


@bot.command()
async def newteams(ctx):
    global CURRENT_TEAM
    CURRENT_TEAM += 1
    if CURRENT_TEAM < len(TEAMS):
        await ctx.send('Team 1:\n' + format_players(TEAMS[CURRENT_TEAM].team1) + '\nTeam 2:\n' + format_players(
            TEAMS[CURRENT_TEAM].team2))


@bot.command()
async def choose(ctx):
    global TEAM1, TEAM2, GAME_OVER
    TEAM1 = TEAMS[CURRENT_TEAM].team1
    TEAM2 = TEAMS[CURRENT_TEAM].team2
    GAME_OVER = False
    await ctx.send('Have fun!')


@bot.command()
async def winner(ctx, val):
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
async def bump(ctx):
    player = str(ctx.author)
    for p in CURRENT_PLAYERS:
        if p.user == player:
            p.rank += 8
            cur = p
            break
    await ctx.send(cur.user + ' has been bumped up to ' + str(cur.rank))


@bot.command()
async def leave(ctx):
    player = str(ctx.author)
    for p in CURRENT_PLAYERS:
        if p.user == player:
            CURRENT_PLAYERS.remove(p)
            break
    await ctx.send('You have left the party. We hope you had fun!')


@bot.command()
async def kick(ctx, player):
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


bot.run(os.getenv('KEY'))
