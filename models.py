from dataclasses import dataclass, field
from typing import List, Dict, Set


@dataclass
class Pizza:
    id: int
    name: str

@dataclass
class Poll:
    id: int
    menu: List[Pizza]
    votes: Dict[int, Dict[int, str]] = field(default_factory=dict)
    # chat ids of users who joined the poll
    participants: Set[int] = field(default_factory=set)


@dataclass
class BotState:
    polls: Dict[int, Poll] = field(default_factory=dict)
    next_poll_id: int = 1