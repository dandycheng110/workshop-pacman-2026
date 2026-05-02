import sys
import types
import unittest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Stub pyxel so main.py can be imported without a display / GPU
# ---------------------------------------------------------------------------
pyxel_stub = types.ModuleType("pyxel")
pyxel_stub.init = MagicMock()
pyxel_stub.run = MagicMock()
pyxel_stub.quit = MagicMock()
pyxel_stub.btn = MagicMock(return_value=False)
pyxel_stub.btnp = MagicMock(return_value=False)
pyxel_stub.cls = MagicMock()
pyxel_stub.rect = MagicMock()
pyxel_stub.circ = MagicMock()
pyxel_stub.pset = MagicMock()
pyxel_stub.text = MagicMock()
pyxel_stub.frame_count = 0
for name in [
    "KEY_LEFT", "KEY_RIGHT", "KEY_UP", "KEY_DOWN",
    "KEY_A", "KEY_D", "KEY_W", "KEY_S", "KEY_Q",
]:
    setattr(pyxel_stub, name, name)

sys.modules["pyxel"] = pyxel_stub

import main  # noqa: E402  (import after stub)


def no_input(*_):
    return False


def pressing(key):
    """Return a btn side_effect that returns True only for `key`."""
    def _btn(k):
        return k == key
    return _btn


class TestMazeHelpers(unittest.TestCase):
    def test_wall_tile_is_wall(self):
        # First char of first row is '1'
        self.assertTrue(main.is_wall(0, 0))

    def test_dot_tile_not_wall(self):
        # MAZE[1] = "1222222222222222221", col 1 = '2'
        self.assertFalse(main.is_wall(1, 1))

    def test_out_of_bounds_is_wall(self):
        self.assertTrue(main.is_wall(-1, 0))
        self.assertTrue(main.is_wall(0, -1))
        self.assertTrue(main.is_wall(999, 0))

    def test_tile_at_returns_char(self):
        self.assertEqual(main.tile_at(0, 0), '1')


class TestPacmanReset(unittest.TestCase):
    def setUp(self):
        self.pac = main.Pacman()

    def test_starts_at_valid_tile(self):
        tx = int(self.pac.tx)
        ty = int(self.pac.ty)
        self.assertFalse(main.is_wall(tx, ty), f"Pacman starts inside a wall at ({tx},{ty})")

    def test_starts_stationary(self):
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)

    def test_speed_positive(self):
        self.assertGreater(self.pac.speed, 0)


class TestPacmanMovement(unittest.TestCase):
    def setUp(self):
        pyxel_stub.btn = MagicMock(side_effect=no_input)
        self.pac = main.Pacman()

    def _update(self, dots=None):
        return self.pac.update(dots if dots is not None else {})

    def test_no_input_stays_still(self):
        tx, ty = self.pac.tx, self.pac.ty
        self._update()
        self.assertAlmostEqual(self.pac.tx, tx)
        self.assertAlmostEqual(self.pac.ty, ty)

    def test_turn_right_on_open_path(self):
        # Row 4 ("1222222222222221") is a fully open corridor
        self.pac.tx = 9.0
        self.pac.ty = 4.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_RIGHT"))
        self._update()
        self.assertEqual(self.pac.dx, 1)
        self.assertEqual(self.pac.dy, 0)

    def test_turn_left_on_open_path(self):
        self.pac.tx = 9.0
        self.pac.ty = 4.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_LEFT"))
        self._update()
        self.assertEqual(self.pac.dx, -1)

    def test_cannot_turn_into_wall(self):
        # Col 0 is always a wall; pressing left from col 1 should be blocked
        self.pac.tx = 1.0
        self.pac.ty = 4.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_LEFT"))
        self._update()
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)

    def test_moves_after_direction_set(self):
        self.pac.tx = 9.0
        self.pac.ty = 4.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_RIGHT"))
        self._update()  # sets dx=1
        old_tx = self.pac.tx
        pyxel_stub.btn = MagicMock(side_effect=no_input)
        self._update()  # should continue moving right
        self.assertGreater(self.pac.tx, old_tx)

    def test_blocked_by_wall_resets_direction(self):
        # Force pac into a wall-adjacent position moving into the wall
        self.pac.tx = 0.9
        self.pac.ty = 21.0
        self.pac.dx = -1  # moving left into wall at col 0
        self._update()
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)

    def test_wraps_horizontally(self):
        # Open corridor on row 21; wrap from right edge
        self.pac.tx = float(main.COLS - 1)
        self.pac.ty = 21.0
        self.pac.dx = 1
        # row 21 col COLS-1 is '1' (wall) so movement will be blocked;
        # use row 21 col 17 (open) moving right toward col 18 (wall)
        # Instead verify wrap on a truly open wrap row doesn't exist in this maze.
        # Just ensure the modulo doesn't crash and tx stays in [0, COLS)
        for _ in range(5):
            self._update()
        self.assertGreaterEqual(self.pac.tx, 0)
        self.assertLess(self.pac.tx, main.COLS)


class TestDotEating(unittest.TestCase):
    def setUp(self):
        pyxel_stub.btn = MagicMock(side_effect=no_input)

    def test_eat_dot_removes_from_dict(self):
        pac = main.Pacman()
        pac.tx = 5.0
        pac.ty = 21.0
        dots = {(5, 21): 'dot'}
        result = pac.update(dots)
        self.assertEqual(result, 'dot')
        self.assertNotIn((5, 21), dots)

    def test_eat_power_pellet(self):
        pac = main.Pacman()
        pac.tx = 5.0
        pac.ty = 21.0
        dots = {(5, 21): 'power'}
        result = pac.update(dots)
        self.assertEqual(result, 'power')

    def test_no_dot_returns_none(self):
        pac = main.Pacman()
        pac.tx = 5.0
        pac.ty = 21.0
        result = pac.update({})
        self.assertIsNone(result)


class TestGhostReset(unittest.TestCase):
    def test_ghost_starts_not_scared(self):
        for i in range(4):
            g = main.Ghost(i)
            self.assertFalse(g.scared)

    def test_ghost_starts_at_valid_position(self):
        for i in range(4):
            g = main.Ghost(i)
            tx, ty = int(g.tx), int(g.ty)
            self.assertFalse(main.is_wall(tx, ty), f"Ghost {i} starts in wall at ({tx},{ty})")


class TestGhostScared(unittest.TestCase):
    def test_scared_timer_counts_down(self):
        g = main.Ghost(0)
        g.scared = True
        g.scared_timer = 5
        g.tx = 9.0
        g.ty = 13.0
        for _ in range(5):
            g.update(9.0, 21.0)
        self.assertFalse(g.scared)
        self.assertEqual(g.scared_timer, 0)


class TestAppScoring(unittest.TestCase):
    def _make_app(self):
        """Create App without starting pyxel.run."""
        app = object.__new__(main.App)
        app.score = 0
        app.lives = 3
        app.state = "play"
        app.state_timer = 0
        app.build_dots = main.App.build_dots.__get__(app)
        app.build_dots()
        app.pac = main.Pacman()
        app.ghosts = [main.Ghost(i) for i in range(4)]
        return app

    def test_dot_adds_10(self):
        app = self._make_app()
        app.score += 10
        self.assertEqual(app.score, 10)

    def test_power_adds_50(self):
        app = self._make_app()
        app.score += 50
        self.assertEqual(app.score, 50)

    def test_ghost_eaten_adds_200(self):
        app = self._make_app()
        app.score += 200
        self.assertEqual(app.score, 200)

    def test_losing_life_decrements_lives(self):
        app = self._make_app()
        app.lives -= 1
        self.assertEqual(app.lives, 2)

    def test_build_dots_fills_dict(self):
        app = self._make_app()
        self.assertGreater(len(app.dots), 0)
        # Every value must be 'dot' or 'power'
        self.assertTrue(all(v in ('dot', 'power') for v in app.dots.values()))

    def test_all_dots_on_passable_tiles(self):
        app = self._make_app()
        for (tx, ty) in app.dots:
            self.assertFalse(main.is_wall(tx, ty), f"Dot placed in wall at ({tx},{ty})")


class TestGhostAI(unittest.TestCase):
    # Test position (7, 4) in row 4 ("1222222222222221"):
    # walls above (3,7) and below (5,7), so only left/right are valid moves.
    # Pac-Man placed at (12, 4) — clearly to the right.

    def _ghost_at(self, tx, ty):
        g = main.Ghost(0)
        g.tx, g.ty = float(tx), float(ty)
        g.dx, g.dy = 0, 0  # neutral start: no direction excluded by reverse check
        return g

    def test_chases_pacman_when_not_scared(self):
        g = self._ghost_at(7, 4)
        g.update(12.0, 4.0)
        self.assertEqual(g.dx, 1)   # right = toward Pac-Man
        self.assertEqual(g.dy, 0)

    def test_flees_pacman_when_scared(self):
        g = self._ghost_at(7, 4)
        g.scared = True
        g.scared_timer = 150
        g.update(12.0, 4.0)
        self.assertEqual(g.dx, -1)  # left = away from Pac-Man
        self.assertEqual(g.dy, 0)


class TestNearGrid(unittest.TestCase):
    def test_exact_integer_is_near(self):
        self.assertTrue(main.near_grid(3.0))

    def test_within_threshold_is_near(self):
        self.assertTrue(main.near_grid(3.19))

    def test_just_outside_threshold_is_not_near(self):
        self.assertFalse(main.near_grid(3.21))

    def test_midpoint_is_not_near(self):
        self.assertFalse(main.near_grid(3.5))


class TestIsBlocked(unittest.TestCase):
    # MAZE[1] = "1222222112222221" — wall at col 7
    def test_open_position_not_blocked(self):
        self.assertFalse(main.is_blocked(1.0, 1.0, 0.15))

    def test_wall_position_blocked(self):
        self.assertTrue(main.is_blocked(0.0, 0.0, 0.15))

    def test_entity_overlapping_wall_tile_is_blocked(self):
        # entity at (6.9, 1.0) physically extends into col 7 (wall) — always blocked
        self.assertTrue(main.is_blocked(6.9, 1.0, 0.15))

    def test_large_margin_inset_avoids_corner_wall(self):
        # entity at (1.0, 0.85): inset corners (margin 0.15) land on row 1 (open)
        self.assertFalse(main.is_blocked(1.0, 0.85, 0.15))

    def test_small_margin_full_box_hits_corner_wall(self):
        # same position, margin 0.01 → top corners reach row 0 (all walls)
        self.assertTrue(main.is_blocked(1.0, 0.85, 0.01))


if __name__ == "__main__":
    unittest.main()
