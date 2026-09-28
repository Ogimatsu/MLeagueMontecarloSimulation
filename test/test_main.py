"""実行方法： python -B -m unittest test.test_main -v"""

import contextlib
import io
import itertools
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch

from app import const


MAIN_PATH = Path(__file__).resolve().parents[1] / "app" / "main.py"
VALID_DRAWS = (23100, 47200, 22900)
EXPECTED_SCORES = [47200, 23100, 22900, 6800]
POINT_TOLERANCE = 1e-10


class MainTest(unittest.TestCase):
    def run_main(self, draws=VALID_DRAWS, order=("C", "A", "D", "B")):
        """乱数の戻り値を有限の固定データに置き換えて、実際のmain.pyを実行する。"""
        selected_teams = iter(order[:-1])
        remaining_teams = set(order)

        def choose_team(population, weights, k):
            """抽選候補と重みを確認し、指定した順序でチームを選ぶ。"""
            self.assertEqual(set(population), remaining_teams)
            self.assertEqual(len(population), len(remaining_teams))
            self.assertEqual(weights, [1.0] * len(population))
            self.assertEqual(k, 1)
            selected = next(selected_teams)
            remaining_teams.remove(selected)
            return [selected]

        # main.pyの「import const」がapp.constを参照するようにする。
        # 実行後は、モジュールの登録情報と乱数関数を元に戻す。
        with (
            patch.dict(sys.modules, {"const": const}),
            patch("random.choices", side_effect=choose_team) as choices,
            patch("random.gauss", side_effect=draws) as gauss,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            state = runpy.run_path(str(MAIN_PATH), run_name="__main__")

        self.assertEqual(choices.call_count, const.PLAYER_COUNT - 1)
        return state, gauss.call_count

    def test_ranking_and_team_points(self):
        """各チームに順位と対応するMリーグポイントが正しく割り当てられることを確認する。"""
        # 最後に残る4着のチームも含め、全24通りの着順を確認する。
        for order in itertools.permutations("ABCD"):
            with self.subTest(order=order):
                state, _ = self.run_main(order=order)
                self.assertEqual(
                    state["ranking"], dict(enumerate(order, start=1))
                )
                self.assertEqual(state["teams"], dict.fromkeys("ABCD", 1.0))
                self.assertEqual(state["players_score"], EXPECTED_SCORES)
                self.assertEqual(
                    state["result"],
                    dict(zip(order, [67.2, 3.1, -17.1, -53.2])),
                )

    def assert_regenerated(self, invalid_draws):
        """不正な得点が破棄され、次の得点候補で再生成されることを確認する。"""
        # 検証処理が働かなければ、最初の不正な得点が返されてテストが失敗する。
        # 再生成が終わらない場合も、用意した乱数を使い切るとStopIterationで失敗する。
        state, draw_count = self.run_main((*invalid_draws, *VALID_DRAWS))
        self.assertEqual(draw_count, len(invalid_draws) + len(VALID_DRAWS))
        self.assertEqual(state["players_score"], EXPECTED_SCORES)

    def test_out_of_range_scores_are_regenerated(self):
        """抽選した得点または4人目の得点が上下限を超えた場合、再生成されることを確認する。"""
        invalid_batches = {
            "drawn_above_max": (const.MAX_SCORE + const.SCORE_UNIT, -30000, -10000),
            "drawn_below_min": (const.MIN_SCORE - const.SCORE_UNIT, 50000, 60000),
            "fourth_above_max": (-10000, -20000, 0),
            "fourth_below_min": (60000, 55000, 50000),
        }
        for case, draws in invalid_batches.items():
            with self.subTest(case=case):
                self.assert_regenerated(draws)

    def test_tied_scores_are_regenerated(self):
        """2人の同点、4人目との同点、全員同点のいずれでも再生成されることを確認する。"""
        invalid_batches = {
            "two_drawn_scores_tie": (30000, 30000, 25000),
            "fourth_score_ties": (40000, 30000, 15000),
            "all_scores_tie": (25000, 25000, 25000),
        }
        for case, draws in invalid_batches.items():
            with self.subTest(case=case):
                self.assert_regenerated(draws)

    def test_total_score_is_100000(self):
        """4人の得点の合計が100,000点であることを確認する。"""
        state, _ = self.run_main()
        self.assertEqual(len(state["players_score"]), const.PLAYER_COUNT)
        self.assertEqual(sum(state["players_score"]), 100000)

    def test_total_base_point_is_minus_20(self):
        """浮動小数点の微小な誤差を許容し、4人の素点の合計が-20.0ptであることを確認する。"""
        state, _ = self.run_main()
        self.assertEqual(len(state["base_point"]), const.PLAYER_COUNT)
        self.assertAlmostEqual(
            sum(state["base_point"]), -20.0, delta=POINT_TOLERANCE
        )

    def test_total_game_point_is_zero(self):
        """4人のMリーグポイントとチーム別結果の合計が、誤差の許容範囲内で0.0ptであることを確認する。"""
        state, _ = self.run_main()
        self.assertEqual(len(state["game_point"]), const.PLAYER_COUNT)
        self.assertAlmostEqual(
            sum(state["game_point"]), 0.0, delta=POINT_TOLERANCE
        )
        self.assertAlmostEqual(
            sum(state["result"].values()), 0.0, delta=POINT_TOLERANCE
        )


if __name__ == "__main__":
    unittest.main()
