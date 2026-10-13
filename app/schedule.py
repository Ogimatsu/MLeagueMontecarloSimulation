import random
from collections import Counter

from app import const


def create_schedule(games_per_team, team_count, team_names):
    scheduled_card_counts = Counter()

    # 1チーム当たりの必要なカード数
    cards_per_team = games_per_team // const.GAMES_PER_CARD

    # 全チームの総カード数
    card_total = team_count * cards_per_team // const.PLAYER_COUNT

    # 各チームの残りカード数
    remaining_cards = {team: cards_per_team for team in team_names}

    schedule = []

    # 対戦カードの決定
    for _ in range(card_total):
        names = [name for name in remaining_cards.keys()]
        random.shuffle(names)

        # 残りカード数の多いチームを優先して対戦カードを作成する
        names.sort(key=lambda name: remaining_cards[name], reverse=True)

        # 先頭4チームを選び、対戦カードに追加する
        card = names[:const.PLAYER_COUNT]
        schedule.append(card)

        scheduled_card_counts.update(card)

        # 当該4チームの残り対戦カード数を更新する
        updated_remaining_cards = {team: remaining_cards[team] - 1 for team in card}
        remaining_cards.update(updated_remaining_cards)

    # 完成した日程について、以下のいずれかに該当する場合はエラーとする
    # １．作成した総カード数でない
    # ２．全チームのカード数が規定数でない
    if len(schedule) != card_total or not all(
        value == cards_per_team for value in scheduled_card_counts.values()
    ):
        raise ValueError("不正なスケジュールです")
    return schedule
