from app import const
from app.schedule import create_schedule
from app.simulate_phase import carry_over_points, simulate_phase

def main():
    all_teams = [
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

    teams = {
        name: {
            "weight": 1.0,
            "point": 0.0,
            "regular_end_points": None,
            "regular_end_rank": None,
            "semifinal_start_points": None,
            "semifinal_end_points": None,
            "semifinal_end_rank": None,
            "final_start_points": None,
            "final_end_points": None,
            "final_end_rank": None,
        }
        for name in all_teams
    }

    # チームの強さは全チーム同じで対戦チームの影響を受けないため、
    # 予めスケジュールを作成し、それを全シーズンで行う。
    regular_schedule = create_schedule(
        const.REGULAR_GAMES_PER_TEAM, const.REGULAR_TEAMS, teams.keys()
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
    semifinal_schedule = create_schedule(
        const.SEMIFINAL_GAMES_PER_TEAM, const.SEMIFINAL_TEAMS, semifinal_teams_default
    )

    season_result = {}

    regular_result = simulate_phase(teams, const.REGULAR_PHASE, regular_schedule)

    semifinal_teams = dict(regular_result[:const.SEMIFINAL_TEAMS])

    # セミファイナルのスケジュールをセミファイナル進出チームに置き換える
    semi_mapping = {
        f"REGULAR_{rank}": team_name
        for rank, team_name in enumerate(semifinal_teams, start=1)
    }
    semifinal_schedule = [
        [semi_mapping[team] for team in card] for card in semifinal_schedule
    ]

    semifinal_teams = carry_over_points(const.SEMIFINAL_PHASE, const.REGULAR_PHASE, semifinal_teams)
    semifinal_result = simulate_phase(semifinal_teams, const.SEMIFINAL_PHASE, semifinal_schedule)

    final_teams = dict(semifinal_result[:const.FINAL_TEAMS])
    final_teams = carry_over_points(const.FINAL_PHASE, const.SEMIFINAL_PHASE, final_teams)
    final_result =simulate_phase(final_teams, const.FINAL_PHASE)

    # 全チームのシーズン成績を集約する
    season_result.update(dict(final_result))
    # セミ敗退チームを追加
    season_result.update(
        dict(semifinal_result[-(const.SEMIFINAL_TEAMS - const.FINAL_TEAMS):])
    )
    # レギュラー敗退チームを追加
    season_result.update(
        dict(regular_result[-(const.REGULAR_TEAMS - const.SEMIFINAL_TEAMS):])
    )
    return season_result


if __name__ == "__main__":
    main()
