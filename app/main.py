import random
import const


# 各チームごとに、強さの重み、Mリーグポイント、試合数を格納する。
teams = {
    "チームA": {
        "weight": 1.0,
        "point": 0.0,
        "game_count": 0,
    },
    "チームB": {
        "weight": 1.0,
        "point": 0.0,
        "game_count": 0,
    },
    "チームC": {
        "weight": 1.0,
        "point": 0.0,
        "game_count": 0,
    },    
    "チームD": {
        "weight": 1.0,
        "point": 0.0,
        "game_count": 0,
    },
}


def game(teams):
    # 着順を決める
    temp_teams = teams.copy()
    ranking = {}

    for rank in range(1, const.PLAYER_COUNT):
        # 1～3着のチームを決定
        selected = random.choices(
            list(temp_teams.keys()), 
            weights = [team["weight"] for team in temp_teams.values()], 
            k = 1
        )[0]
        ranking[rank] = selected
        temp_teams.pop(selected)

    # 4着のチームを追加
    ranking[const.PLAYER_COUNT] = next(iter(temp_teams))
    # print("順位：", ranking)

    # 得点算出を行う
    while True:
        players_score = []

        for _ in range(const.PLAYER_COUNT - 1):
            # 設定した正規分布に基づいて選手の得点を算出する
            score = round(
                random.gauss(const.MEAN_SCORE, const.STANDARD_DEVIATION_SCORE) / const.SCORE_UNIT
            ) * const.SCORE_UNIT
            players_score.append(score)

        # 4人目の得点は持ち点の総合計から3人の点数の合計を引いた残りとする
        players_score.append(const.TOTAL_SCORE - sum(players_score))

        # 得点算出のやり直し条件１：指定の範囲を超えた得点が存在する
        if any(
            score < const.MIN_SCORE or const.MAX_SCORE < score
            for score in players_score
        ):
            # print("得点が指定の範囲を超えました")
            continue

        # 得点算出のやり直し条件２：同じ点数が複数存在する
        if len(set(players_score)) != const.PLAYER_COUNT:
            # print("同じ点数が複数発生しました")
            continue

        # 得点算出のやり直し条件に掛からなかった場合、処理を抜ける
        break

    # 得点の大きい順に並べ替え
    players_score = sorted(players_score, reverse=True)
    # print("得点：", players_score)

    # 得点を素点に変換する
    base_point = [
        (val - const.POINT_BASE) / const.POINT_CONVERSION_UNIT
        for val in players_score
    ]
    # print("素点：", base_point)

    # 順位点を加算し、Mリーグポイントを生成する
    m_league_point = [
        round(point + const.RANK_POINT[rank], 1)
        for rank, point in enumerate(base_point, start=1)
    ]
    # print("Mリーグポイント：", m_league_point)

    # 順位に対応したチームにMリーグポイントを割り当てる
    game_result = {
        team: m_league_point[rank - 1]
        for rank, team in ranking.items()
    }
    # print("試合結果：", game_result)

    return game_result


# 指定の半荘数実行する
for i in range(5):
    game_result = game(teams)

    for team_name, team_point in game_result.items():
        teams[team_name]["point"] = round(teams[team_name]["point"] + team_point, 1)
        teams[team_name]["game_count"] += 1
    
print("指定半荘実行結果：", teams)

# Mリーグポイント順にチームを並べ替える
phase_result = sorted(
    teams.items(),
    key=lambda x: x[1]["point"],
    reverse=True
)
print("フェイズ最終順位：", phase_result)
