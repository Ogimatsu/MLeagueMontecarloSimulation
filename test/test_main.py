"""実行方法：python -B -m unittest test.test_main -v"""

import ast
import contextlib
from decimal import Decimal
import io
import itertools
from pathlib import Path
import random
import runpy
import sys
import unittest
from unittest.mock import patch

from app import const


MAIN_PATH = Path(__file__).resolve().parents[1] / "app" / "main.py"
TEAM_NAMES = ("チームA", "チームB", "チームC", "チームD")
VALID_DRAWS = (23100, 47200, 22900)
EXPECTED_SCORES = [47200, 23100, 22900, 6800]
EXPECTED_POINTS = [67.2, 3.1, -17.1, -53.2]
POINT_TOLERANCE = 1e-10
# 確認したい半荘数を追加・変更する。0は未実行時の境界確認用。
GAME_COUNTS = (0, 1, 5, 16, 20, 120, 1000)


class MainTest(unittest.TestCase):
    def run_main(self, game_count=1, draws=None, order=None):
        """ファイルを変更せず、指定半荘数で実行して最終状態・各半荘の変数・出力を返す。"""
        rng = random.Random(42)
        games = []
        output = io.StringIO()
        loop_overrides = []
        remaining_teams = set()
        selection_count = 0

        def test_range(*args):
            """main.py直下の実行回数だけ差し替え、game内の人数用rangeはそのまま使う。"""
            caller = sys._getframe(1)
            if caller.f_code.co_name == "<module>" and caller.f_code.co_filename == str(MAIN_PATH):
                # 現在の実装の「range(5)」を対象とする。構造が変わったらテストも見直す。
                self.assertEqual(args, (5,))
                loop_overrides.append(game_count)
                return range(game_count)
            return range(*args)

        def choose_team(population, weights, k):
            """指定した着順を再現するか、シードを固定した本物の抽選を行う。"""
            nonlocal selection_count, remaining_teams
            if order is None:
                return rng.choices(population, weights=weights, k=k)
            index = selection_count % (const.PLAYER_COUNT - 1)
            if index == 0:
                remaining_teams = set(order)
            self.assertEqual(set(population), remaining_teams)
            self.assertEqual(len(population), len(remaining_teams))
            self.assertEqual(weights, [1.0] * len(population))
            self.assertEqual(k, 1)
            selected = order[index]
            remaining_teams.remove(selected)
            selection_count += 1
            return [selected]

        def capture_game(frame, event, arg):
            """gameの正常終了時にローカル変数を記録し、既存の合計・順位テストで確認する。"""
            if (
                event == "return"
                and frame.f_code.co_filename == str(MAIN_PATH)
                and frame.f_code.co_name == "game"
                and isinstance(arg, dict)
            ):
                games.append(frame.f_locals.copy())

        # 名前解決と乱数だけを一時的に置き換え、終了時に元へ戻す。
        # 半荘の計算・集計・ソート・printは実際のmain.pyの処理を実行する。
        previous_profile = sys.getprofile()
        with (
            patch.dict(sys.modules, {"const": const}),
            patch("random.choices", side_effect=choose_team) as choices,
            patch("random.gauss", side_effect=rng.gauss if draws is None else draws) as gauss,
            contextlib.redirect_stdout(output),
        ):
            try:
                sys.setprofile(capture_game)
                state = runpy.run_path(
                    str(MAIN_PATH),
                    run_name="__main__",
                    init_globals={"range": test_range},
                )
            finally:
                sys.setprofile(previous_profile)

        self.assertEqual(loop_overrides, [game_count])
        self.assertEqual(len(games), game_count)
        self.assertEqual(choices.call_count, game_count * (const.PLAYER_COUNT - 1))
        return state, games, output.getvalue(), gauss.call_count

    def test_ranking_and_team_points(self):
        """全24通りの着順について、順位とチーム別Mリーグポイントの対応を確認する。"""
        for order in itertools.permutations(TEAM_NAMES):
            with self.subTest(order=order):
                _, games, _, _ = self.run_main(draws=VALID_DRAWS, order=order)
                game = games[0]
                self.assertEqual(game["ranking"], dict(enumerate(order, start=1)))
                self.assertEqual(game["players_score"], EXPECTED_SCORES)
                self.assertEqual(list(game["game_result"].items()), list(zip(order, EXPECTED_POINTS)))

    def assert_regenerated(self, invalid_draws):
        """不正な候補が破棄され、2回目の得点候補が採用されることを確認する。"""
        # 再生成されなければ結果が不一致となり、続きすぎれば有限の乱数を使い切って失敗する。
        _, games, _, draw_count = self.run_main(draws=(*invalid_draws, *VALID_DRAWS))
        self.assertEqual(draw_count, len(invalid_draws) + len(VALID_DRAWS))
        self.assertEqual(games[0]["players_score"], EXPECTED_SCORES)

    def test_out_of_range_scores_are_regenerated(self):
        """抽選した得点と4人目の得点について、上下限超過時の再生成を確認する。"""
        invalid_batches = {
            "抽選値が上限超過": (const.MAX_SCORE + const.SCORE_UNIT, -30000, -10000),
            "抽選値が下限未満": (const.MIN_SCORE - const.SCORE_UNIT, 50000, 60000),
            "4人目が上限超過": (-10000, -20000, 0),
            "4人目が下限未満": (60000, 55000, 50000),
        }
        for case, draws in invalid_batches.items():
            with self.subTest(case=case):
                self.assert_regenerated(draws)

    def test_tied_scores_are_regenerated(self):
        """2人の同点、4人目との同点、全員同点で再生成されることを確認する。"""
        for draws in ((30000, 30000, 25000), (40000, 30000, 15000), (25000, 25000, 25000)):
            with self.subTest(draws=draws):
                self.assert_regenerated(draws)

    def test_total_score_is_100000(self):
        """4人の得点の合計が100,000点であることを確認する。"""
        _, games, _, _ = self.run_main(draws=VALID_DRAWS)
        self.assertEqual(len(games[0]["players_score"]), const.PLAYER_COUNT)
        self.assertEqual(sum(games[0]["players_score"]), 100000)

    def test_total_base_point_is_minus_20(self):
        """4人の素点合計が、微小な誤差の許容範囲内で-20.0ptになることを確認する。"""
        _, games, _, _ = self.run_main(draws=VALID_DRAWS)
        self.assertEqual(len(games[0]["base_point"]), const.PLAYER_COUNT)
        self.assertAlmostEqual(sum(games[0]["base_point"]), -20.0, delta=POINT_TOLERANCE)

    def test_total_m_league_point_is_zero(self):
        """4人のMリーグポイントとチーム別結果の合計が0.0ptになることを確認する。"""
        _, games, _, _ = self.run_main(draws=VALID_DRAWS)
        self.assertEqual(len(games[0]["m_league_point"]), const.PLAYER_COUNT)
        self.assertAlmostEqual(sum(games[0]["m_league_point"]), 0.0, delta=POINT_TOLERANCE)
        self.assertAlmostEqual(sum(games[0]["game_result"].values()), 0.0, delta=POINT_TOLERANCE)

    def assert_short_output(self, state, output):
        """実際の出力に長い小数がなく、表示された集計値と順位が実行結果と一致することを確認する。"""
        lines = output.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("指定半荘実行結果："))
        self.assertTrue(lines[1].startswith("フェイズ最終順位："))
        self.assertEqual(ast.literal_eval(lines[0].split("：", 1)[1]), state["teams"])
        self.assertEqual(ast.literal_eval(lines[1].split("：", 1)[1]), state["phase_result"])
        # 小数第2位以降の桁や、微小な誤差を表す指数表記を検出する。
        self.assertNotRegex(output, r"\d+\.\d{2,}")
        self.assertNotRegex(output, r"\d(?:\.\d+)?[eE][+-]?\d+")

    def test_arbitrary_game_counts_are_sorted_by_total_points(self):
        """任意の半荘数について実行回数・累計値・Mリーグポイント降順を確認する。"""
        for game_count in GAME_COUNTS:
            with self.subTest(game_count=game_count):
                state, games, output, _ = self.run_main(game_count=game_count)
                teams = state["teams"]
                self.assertEqual(set(teams), set(TEAM_NAMES))
                # 十進数で独立に集計し、最後の1半荘だけの順位などを誤って採用していないか確認する。
                totals = {
                    name: sum(
                        (Decimal(str(game["game_result"][name])) for game in games),
                        Decimal(0),
                    )
                    for name in teams
                }
                for name, info in teams.items():
                    self.assertEqual(info["game_count"], game_count)
                    self.assertEqual(Decimal(str(info["point"])), totals[name])
                expected_order = sorted(totals, key=totals.get, reverse=True)
                self.assertEqual(
                    state["phase_result"], [(name, teams[name]) for name in expected_order]
                )
                self.assert_short_output(state, output)

    def test_repeated_fractional_points_have_short_output(self):
        """小数を繰り返し加算しても長い小数が出力されず、登録順と異なる順位になることを確認する。"""
        order = (TEAM_NAMES[1], TEAM_NAMES[3], TEAM_NAMES[0], TEAM_NAMES[2])
        for game_count in (3, 7, 120, 1000):
            with self.subTest(game_count=game_count):
                state, _, output, _ = self.run_main(
                    game_count=game_count,
                    draws=VALID_DRAWS * game_count,
                    order=order,
                )
                self.assertEqual([name for name, _ in state["phase_result"]], list(order))
                for name, point in zip(order, EXPECTED_POINTS):
                    self.assertEqual(
                        Decimal(str(state["teams"][name]["point"])),
                        Decimal(str(point)) * game_count,
                    )
                self.assert_short_output(state, output)


if __name__ == "__main__":
    unittest.main()
