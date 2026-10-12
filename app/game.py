import random

from app import const


def game(teams: dict):
    # 着順を決める
    remaining_teams = teams.copy()
    ranking = {}

    for rank in range(1, const.PLAYER_COUNT):
        # 1～3着のチームを決定
        selected_team = random.choices(
            list(remaining_teams.keys()),
            weights=[team["weight"] for team in remaining_teams.values()],
            k=1,
        )[0]
        ranking[rank] = selected_team
        remaining_teams.pop(selected_team)

    # 4着のチームを追加
    ranking[const.PLAYER_COUNT] = next(iter(remaining_teams))
    # print("順位：", ranking)

    # 得点算出を行う（得点算出のやり直し条件に掛からなくなるまでやり直す）
    while True:
        player_scores = []

        for _ in range(const.PLAYER_COUNT - 1):
            # 設定した正規分布に基づいて選手の得点を算出する
            score = (
                round(
                    random.gauss(const.MEAN_SCORE, const.STANDARD_DEVIATION_SCORE)
                    / const.SCORE_UNIT
                )
                * const.SCORE_UNIT
            )
            player_scores.append(score)

        # 4人目の得点は持ち点の総合計から3人の点数の合計を引いた残りとする
        player_scores.append(const.TOTAL_SCORE - sum(player_scores))

        # 得点算出のやり直し条件１：指定の範囲を超えた得点が存在する
        if any(
            score < const.MIN_SCORE or const.MAX_SCORE < score
            for score in player_scores
        ):
            # print("得点が指定の範囲を超えました")
            continue

        # 得点算出のやり直し条件２：同じ点数が複数存在する
        if len(set(player_scores)) != const.PLAYER_COUNT:
            # print("同じ点数が複数発生しました")
            continue

        break

    player_scores = sorted(player_scores, reverse=True)
    # print("得点：", player_scores)

    # 得点を素点に変換する
    base_points = [
        (val - const.RETURN_SCORE) / const.POINT_CONVERSION_UNIT
        for val in player_scores
    ]
    # print("素点：", base_points)

    # 順位点を加算し、Mリーグポイントを生成する
    m_league_points = [
        round(point + const.RANK_POINT[rank], 1)
        for rank, point in enumerate(base_points, start=1)
    ]
    # print("Mリーグポイント：", m_league_points)

    # 順位に対応したチームにMリーグポイントを割り当てる
    game_result = {team: m_league_points[rank - 1] for rank, team in ranking.items()}
    # print("試合結果：", game_result)

    return game_result
