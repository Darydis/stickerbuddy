from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Pizza:
    id: int
    name: str

@dataclass
class BotState:
    menu: List[Pizza] = field(default_factory=list)
    # votes[pizza_id][user_id] = score or 'veto'
    votes: Dict[int, Dict[int, str]] = field(default_factory=dict)
