# Team Challenges and Multiplayer Features

import random
from dataclasses import dataclass, field
from enum import Enum


class ChallengeType(Enum):
    QUIZ_BATTLE = "quiz_battle"
    TEAM_TOURNAMENT = "team_tournament"
    SPEED_CHALLENGE = "speed_challenge"


@dataclass
class Team:
    team_id: str
    team_name: str
    leader_id: int
    members: list[int] = field(default_factory=list)
    max_members: int = 5
    total_points: int = 0
    challenges_won: int = 0

    def add_member(self, user_id: int) -> bool:
        if len(self.members) >= self.max_members:
            return False
        if user_id not in self.members:
            self.members.append(user_id)
            return True
        return False


@dataclass
class MultiplayerQuizBattle:
    battle_id: str
    room_code: str
    host_id: int
    topic: str
    difficulty: str = "medium"
    max_participants: int = 4
    participants: list[int] = field(default_factory=list)
    scores: dict[int, int] = field(default_factory=dict)
    is_active: bool = False

    def add_participant(self, user_id: int) -> bool:
        if len(self.participants) >= self.max_participants:
            return False
        if user_id not in self.participants:
            self.participants.append(user_id)
            self.scores[user_id] = 0
            return True
        return False

    def submit_score(self, user_id: int, points: int):
        self.scores[user_id] = self.scores.get(user_id, 0) + points

    def get_leaderboard(self) -> list[dict]:
        rankings = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"rank": idx + 1, "user_id": user_id, "score": score}
            for idx, (user_id, score) in enumerate(rankings)
        ]


class TeamChallengeManager:
    def __init__(self):
        self.teams: dict[str, Team] = {}
        self.battles: dict[str, MultiplayerQuizBattle] = {}

    def create_team(self, team_name: str, leader_id: int) -> Team:
        team_id = f"team_{random.randint(100000, 999999)}"
        team = Team(team_id=team_id, team_name=team_name, leader_id=leader_id, members=[leader_id])
        self.teams[team_id] = team
        return team

    def create_quiz_battle(self, host_id: int, topic: str, max_participants: int = 4) -> MultiplayerQuizBattle:
        battle_id = f"battle_{random.randint(100000, 999999)}"
        room_code = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(6))

        battle = MultiplayerQuizBattle(
            battle_id=battle_id,
            room_code=room_code,
            host_id=host_id,
            topic=topic,
            max_participants=max_participants
        )

        battle.add_participant(host_id)
        self.battles[battle_id] = battle
        return battle

    def get_team_leaderboard(self, limit: int = 10) -> list[Team]:
        sorted_teams = sorted(self.teams.values(), key=lambda t: t.total_points, reverse=True)
        return sorted_teams[:limit]
