import unittest

import numpy as np

from datafaultbench.simulation import Scenario, simulate_scenario


class SimulationTests(unittest.TestCase):
    def test_simulation_is_deterministic(self):
        scenario = Scenario("test", 6, 12, 12, 0.01, 0.5, "global_null", 0.0, 1.0)
        left = simulate_scenario(scenario, 20, 0.05, 123)
        right = simulate_scenario(scenario, 20, 0.05, 123)
        self.assertTrue(left.equals(right))

    def test_selected_index_within_grid(self):
        scenario = Scenario("test", 12, 12, 12, 0.01, 0.0, "signal", 0.01, 1.0)
        frame = simulate_scenario(scenario, 30, 0.05, 5)
        self.assertTrue(frame.selected_candidate.between(0, 11).all())
        self.assertTrue(np.isfinite(frame.cal_mean).all())
        self.assertTrue(np.isfinite(frame.final_mean).all())

    def test_null_external_rate_not_structurally_forced(self):
        scenario = Scenario("test", 36, 26, 16, 0.015, 0.5, "global_null", 0.0, 1.0)
        frame = simulate_scenario(scenario, 200, 0.05, 77)
        self.assertGreaterEqual(frame.external_reject.mean(), 0.0)
        self.assertLessEqual(frame.external_reject.mean(), 0.2)


if __name__ == "__main__":
    unittest.main()
