from typing import Iterable

from models import BotState


def aggregate_results(state: BotState, k: int) -> str:
    if not state.menu:
        return 'Меню не загружено.'
    voters: Iterable[int] = {uid for votes in state.votes.values() for uid in votes}
    N = len(voters)
    if N == 0:
        return 'Нет голосов.'
    veto_threshold = N / 2
    sums = {p.id: 0 for p in state.menu}
    veto_counts = {p.id: 0 for p in state.menu}
    for pid, user_votes in state.votes.items():
        for score in user_votes.values():
            if score == 'veto':
                veto_counts[pid] += 1
            else:
                sums[pid] += int(score)
    available = [p for p in state.menu if veto_counts[p.id] <= veto_threshold]
    available.sort(key=lambda p: sums[p.id], reverse=True)
    chosen = available[:k]
    lines = [f'{p.name}: {sums[p.id]}' for p in chosen]
    return 'Выбранные пиццы:\n' + '\n'.join(lines)
