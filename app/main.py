from app import const
from app.schedule import create_schedule
from app.simulate_phase import carry_over_points, simulate_phase
from copy import deepcopy


def main():
    """指定シーズン数を実行してその結果を返す"""
    team_names = [
        "Ａチーム",
        "Ｂチーム",
        "Ｃチーム",
        "Ｄチーム",
        "Ｅチーム",
        "Ｆチーム",
        "Ｇチーム",
        "Ｈチーム",
        "Ｉチーム",
        "Ｊチーム",
    ]

    teams_template = {
        name: {
            "weight": 1.0,
            "point": 0.0,
            "regular_end_rank": None,
            "regular_end_points": None,
            "semifinal_start_points": None,
            "semifinal_end_rank": None,
            "semifinal_end_points": None,
            "final_start_points": None,
            "final_end_rank": None,
            "final_end_points": None,
        }
        for name in team_names
    }

    # チームの強さは全チーム同じで対戦チームの影響を受けないため、
    # 予めスケジュールを作成し、それを全シーズンで行う。
    regular_schedule = create_schedule(
        const.REGULAR_GAMES_PER_TEAM, const.REGULAR_TEAM_COUNT, teams_template.keys()
    )

    # セミファイナルのスケジュールについても、予めデフォルトのチーム名で作成する
    semifinal_teams_default = [
        "REGULAR_1",
        "REGULAR_2",
        "REGULAR_3",
        "REGULAR_4",
        "REGULAR_5",
        "REGULAR_6",
    ]
    semifinal_schedule_template = create_schedule(
        const.SEMIFINAL_GAMES_PER_TEAM, const.SEMIFINAL_TEAM_COUNT, semifinal_teams_default
    )

    # 全シーズンを格納
    result = []

    # ここから指定シーズン分実行する
    for season_number in range(1, const.SEASON_COUNT + 1):
        # 1シーズン分を格納
        season_result = {
            "season": season_number,
            "teams": None,
            }
        teams = deepcopy(teams_template)

        # 1シーズンの各フェーズの結果を格納
        team_results = {}

        regular_result = simulate_phase(teams, const.REGULAR_PHASE, regular_schedule)

        semifinal_teams = dict(regular_result[:const.SEMIFINAL_TEAM_COUNT])

        # セミファイナルのスケジュールをセミファイナル進出チームに置き換える
        semifinal_mapping = {
            f"REGULAR_{rank}": team_name
            for rank, team_name in enumerate(semifinal_teams, start=1)
        }
        semifinal_schedule = [
            [semifinal_mapping[team] for team in card] for card in semifinal_schedule_template
        ]

        semifinal_teams = carry_over_points(
            const.SEMIFINAL_PHASE,
            const.REGULAR_PHASE,
            semifinal_teams
        )
        semifinal_result = simulate_phase(
            semifinal_teams,
            const.SEMIFINAL_PHASE,
            semifinal_schedule
        )

        final_teams = dict(semifinal_result[:const.FINAL_TEAM_COUNT])
        final_teams = carry_over_points(
            const.FINAL_PHASE,
            const.SEMIFINAL_PHASE,
            final_teams
        )
        final_result =simulate_phase(final_teams, const.FINAL_PHASE)

        # 全チームのシーズン成績を集約する
        team_results.update(dict(final_result))
        # セミ敗退チームを追加
        team_results.update(
            dict(semifinal_result[-(const.SEMIFINAL_TEAM_COUNT - const.FINAL_TEAM_COUNT):])
        )
        # レギュラー敗退チームを追加
        team_results.update(
            dict(regular_result[-(const.REGULAR_TEAM_COUNT - const.SEMIFINAL_TEAM_COUNT):])
        )

        # シーズン結果に関係しないweight、point欄は削除する
        for _, team_data in team_results.items():
            del team_data["weight"]
            del team_data["point"]

        season_result["teams"] = team_results
        result.append(season_result)

    print(len(result))
    return result


if __name__ == "__main__":
    main()
