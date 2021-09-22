from dataclasses import dataclass


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


class Server:
    """
    Represents one discord servers - stores all info related to said server
    """

    current_players: list[Player]
    teams: list[TeamCombination]
    current_team: int
    team1: list[Player]
    team2: list[Player]
    game_over: bool

    def __init__(self):
        self.current_team = 0
        self.current_players = []
        self.teams = []
        self.team1 = []
        self.team2 = []
        self.game_over = True
