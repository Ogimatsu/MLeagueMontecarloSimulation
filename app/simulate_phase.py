import math

from app import const
from app.game import game


def round_up(prev_points):
    """小数第二位以下について、ポイントが増える方向へ調整して小数第一位までとする。"""
    adjusted_points = math.ceil(prev_points * 10) / 10
    return adjusted_points


def carry_over_points(next_phase: str, prev_phase: str, teams: dict):
    """前フェーズ終了時点のMリーグポイントの50%を次フェーズに持ち越す"""
    for _, team_data in teams.items():
        team_data[f"{next_phase}_start_points"] = round_up(
            team_data[f"{prev_phase}_end_points"] * const.CARRY_OVER_RATE
        )
    return teams


def simulate_phase(
    teams: dict,
    phase: str,
    schedule: list | None = None,
):
    # セミファイナル・ファイナルの場合は、前フェーズの持越ポイントをポイントに加算する
    if phase in (const.SEMIFINAL_PHASE, const.FINAL_PHASE):
        for _, team_data in teams.items():
            team_data["point"] = team_data[f"{phase}_start_points"]

    # 当該フェーズのスケジュールに基づいて対戦を実行する
    if phase in (const.REGULAR_PHASE, const.SEMIFINAL_PHASE):
        # レギュラー・セミファイナルの場合は、スケジュールのカードを順番に実行する
        for card in schedule:
            # 対戦カード
            card_teams = {name: teams[name] for name in card}
            # print("対戦カード：", card_teams)

            # 1カードの結果を集計する
            card_result = {name: 0.0 for name in card}
            # print("カード結果：", card_result)

            # 1カードにつき2半荘実行する
            for _ in range(const.GAMES_PER_CARD):
                game_result = game(card_teams)
                # print("1半荘結果：", game_result)

                # 1半荘分をカード結果へ加算
                for team_name, team_point in game_result.items():
                    card_result[team_name] = round(
                        card_result[team_name] + team_point, 1
                    )

            # print("1カード実行結果：", card_result)

            # 2半荘が終了してからteamsへ加算
            for team_name, card_point in card_result.items():
                teams[team_name]["point"] = round(
                    teams[team_name]["point"] + card_point, 1
                )
            # print("1カード実行後全体成績", teams)
    else:
        # ファイナルの場合は4チームしかないのでそのまま対戦を実行する
        for _ in range(const.FINAL_GAMES_PER_TEAM):
            game_result = game(teams)

            # 1半荘分をteamsへ加算
            for team_name, team_point in game_result.items():
                teams[team_name]["point"] = round(
                    teams[team_name]["point"] + team_point, 1
                )

    # 全カード消化後、Mリーグポイント順にチームを並べ替える
    phase_result = sorted(teams.items(), key=lambda x: x[1]["point"], reverse=True)

    # 当該フェーズの順位及びMリーグポイントを当該項目に格納する
    for rank, (team_name, team_data) in enumerate(phase_result, start=1):
        team_data[f"{phase}_end_points"] = team_data["point"]
        team_data[f"{phase}_end_rank"] = rank
        # 集計用ポイントをリセットする
        team_data["point"] = 0.0
    return phase_result
