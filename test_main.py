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


# Frames needed for one full tile traversal at each speed
PAC_TILE_FRAMES = int(1 / main.Pacman().speed) + 1   # ~13 at speed 0.08
GHOST_TILE_FRAMES = int(1 / main.Ghost(0).speed) + 1  # ~17 at speed 0.06


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
        self.assertFalse(
            main.is_wall(self.pac.tile_x, self.pac.tile_y),
            f"Pacman starts inside a wall at ({self.pac.tile_x},{self.pac.tile_y})"
        )

    def test_starts_stationary(self):
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)
        self.assertEqual(self.pac.progress, 0.0)

    def test_speed_positive(self):
        self.assertGreater(self.pac.speed, 0)

    def test_tx_ty_properties_match_tile(self):
        # At rest, tx/ty equal the tile coords
        self.assertAlmostEqual(self.pac.tx, float(self.pac.tile_x))
        self.assertAlmostEqual(self.pac.ty, float(self.pac.tile_y))


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
        # Row 4 ("1322222222222231") is a fully open corridor
        self.pac.tile_x = 9
        self.pac.tile_y = 4
        self.pac.progress = 0.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_RIGHT"))
        self._update()
        self.assertEqual(self.pac.dx, 1)
        self.assertEqual(self.pac.dy, 0)

    def test_turn_left_on_open_path(self):
        self.pac.tile_x = 9
        self.pac.tile_y = 4
        self.pac.progress = 0.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_LEFT"))
        self._update()
        self.assertEqual(self.pac.dx, -1)

    def test_cannot_turn_into_wall(self):
        # Col 0 is always a wall; pressing left from col 1 should be blocked
        self.pac.tile_x = 1
        self.pac.tile_y = 4
        self.pac.progress = 0.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_LEFT"))
        self._update()
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)

    def test_moves_after_direction_set(self):
        self.pac.tile_x = 9
        self.pac.tile_y = 4
        self.pac.progress = 0.0
        pyxel_stub.btn = MagicMock(side_effect=pressing("KEY_RIGHT"))
        self._update()  # sets dx=1, advances progress
        old_tx = self.pac.tx
        pyxel_stub.btn = MagicMock(side_effect=no_input)
        self._update()  # should continue moving right
        self.assertGreater(self.pac.tx, old_tx)

    def test_stops_at_dead_end(self):
        # Row 1: "1222222112222221" — col 7 is a wall; col 6 is the last open tile
        # Pac moves right from col 5 to col 6, then stops (forward is wall, queue is also right)
        self.pac.tile_x = 5
        self.pac.tile_y = 1
        self.pac.dx = 1
        self.pac.dy = 0
        self.pac.next_dx = 1
        self.pac.next_dy = 0
        self.pac.progress = 0.0
        for _ in range(PAC_TILE_FRAMES):
            self._update()
        self.assertEqual(self.pac.dx, 0)
        self.assertEqual(self.pac.dy, 0)

    def test_wraps_horizontally(self):
        # Tunnel row 6: pac at col 15 going right wraps to left side
        self.pac.tile_x = main.COLS - 1
        self.pac.tile_y = 6
        self.pac.dx = 1
        self.pac.dy = 0
        self.pac.next_dx = 1
        self.pac.next_dy = 0
        self.pac.progress = 0.0
        for _ in range(PAC_TILE_FRAMES):
            self._update()
        self.assertGreaterEqual(self.pac.tile_x, 0)
        self.assertLess(self.pac.tile_x, main.COLS)
        self.assertLess(self.pac.tx, float(main.COLS) / 2)


class TestDotEating(unittest.TestCase):
    def setUp(self):
        pyxel_stub.btn = MagicMock(side_effect=no_input)

    def test_eat_dot_removes_from_dict(self):
        pac = main.Pacman()
        pac.tile_x = 5
        pac.tile_y = 1
        pac.progress = 0.0
        dots = {(5, 1): 'dot'}
        result = pac.update(dots)
        self.assertEqual(result, 'dot')
        self.assertNotIn((5, 1), dots)

    def test_eat_power_pellet(self):
        pac = main.Pacman()
        pac.tile_x = 5
        pac.tile_y = 1
        pac.progress = 0.0
        dots = {(5, 1): 'power'}
        result = pac.update(dots)
        self.assertEqual(result, 'power')

    def test_no_dot_returns_none(self):
        pac = main.Pacman()
        pac.tile_x = 5
        pac.tile_y = 1
        pac.progress = 0.0
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
            self.assertFalse(
                main.is_wall(g.tile_x, g.tile_y),
                f"Ghost {i} starts in wall at ({g.tile_x},{g.tile_y})"
            )

    def test_ghost_starts_with_valid_direction(self):
        for i in range(4):
            g = main.Ghost(i)
            self.assertFalse(
                main.is_wall(g.tile_x + g.dx, g.tile_y + g.dy),
                f"Ghost {i} initial direction leads into wall"
            )

    def test_ghost_starts_with_zero_progress(self):
        for i in range(4):
            g = main.Ghost(i)
            self.assertEqual(g.progress, 0.0)


class TestGhostScared(unittest.TestCase):
    def test_scared_timer_counts_down(self):
        g = main.Ghost(0)
        g.scared = True
        g.scared_timer = 5
        # Use a valid open tile so movement doesn't error
        g.tile_x = 9
        g.tile_y = 4
        g.dx, g.dy = 1, 0
        g.progress = 0.0
        for _ in range(5):
            g.update(9.0, 4.0)
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


class TestPickDirection(unittest.TestCase):
    # Same corridor: row 4, col 7 — only left/right valid.

    def test_picks_direction_toward_target(self):
        # target to the right → should pick (1, 0)
        result = main.pick_direction(7, 4, 0, 0, 12.0, 4.0)
        self.assertEqual(result, (1, 0))

    def test_picks_direction_away_from_target(self):
        # target to the right, moving away → should pick (-1, 0)
        result = main.pick_direction(7, 4, 0, 0, 12.0, 4.0, flee=True)
        self.assertEqual(result, (-1, 0))

    def test_respects_no_reverse(self):
        # currently moving right (dx=1); reversing to left must be excluded
        # target is to the left, but reversal forbidden → only right is valid
        result = main.pick_direction(7, 4, 1, 0, 2.0, 4.0)
        self.assertEqual(result, (1, 0))

    def test_returns_none_when_fully_blocked(self):
        # position (0, 0) is a wall corner — all neighbours are walls
        result = main.pick_direction(0, 0, 0, 0, 8.0, 8.0)
        self.assertIsNone(result)


class TestGhostAI(unittest.TestCase):
    # Test position (7, 4) in row 4 ("1322222222222231"):
    # four-way open intersection. Pac-Man placed at (12, 4) — to the right.

    def _ghost_arriving_at(self, tx, ty, dx=1, dy=0):
        """Ghost positioned one tile before (tx,ty), just about to arrive."""
        g = main.Ghost(0)
        g.tile_x = tx - dx
        g.tile_y = ty - dy
        g.dx, g.dy = dx, dy
        g.progress = 1.0 - g.speed + 0.001  # one update away from tile arrival
        return g

    def test_default_ai_fn_is_chase(self):
        g = self._ghost_arriving_at(7, 4)
        self.assertEqual(g.ai_fn(5.0, 3.0), (5.0, 3.0))

    def test_chases_pacman_when_not_scared(self):
        # Ghost arrives at (7,4) from left (dx=1); pick_direction excludes reverse.
        # Best non-reverse direction toward (12,4) is right (1,0).
        g = self._ghost_arriving_at(7, 4, dx=1, dy=0)
        g.update(12.0, 4.0)
        self.assertEqual(g.dx, 1)
        self.assertEqual(g.dy, 0)

    def test_flees_pacman_when_scared(self):
        # Ghost arrives at (7,4) from above (dy=1); pick_direction excludes reverse (up).
        # Farthest from (12,4): left (-1,0) at dist²=36 beats right (16) and down (26).
        g = self._ghost_arriving_at(7, 4, dx=0, dy=1)
        g.scared = True
        g.scared_timer = 150
        g.update(12.0, 4.0)
        self.assertEqual(g.dx, -1)
        self.assertEqual(g.dy, 0)

    def test_custom_ai_fn_is_used(self):
        # Ghost arrives at (7,4) from above; custom target at (2,4).
        # Closest non-reverse direction toward (2,4): left (-1,0) at dist²=25.
        g = self._ghost_arriving_at(7, 4, dx=0, dy=1)
        g.ai_fn = lambda pac_tx, pac_ty: (2.0, 4.0)
        g.update(12.0, 4.0)
        self.assertEqual(g.dx, -1)


class TestPinkyAI(unittest.TestCase):
    def _pac(self, tx, ty, dx, dy):
        p = main.Pacman()
        p.tile_x = tx
        p.tile_y = ty
        p.dx = dx
        p.dy = dy
        p.progress = 0.0
        return p

    def test_targets_4_tiles_ahead_moving_right(self):
        pac = self._pac(5, 4, 1, 0)
        ai = main.make_pinky_ai(pac)
        self.assertEqual(ai(5.0, 4.0), (9.0, 4.0))

    def test_targets_4_tiles_ahead_moving_up(self):
        pac = self._pac(5, 8, 0, -1)
        ai = main.make_pinky_ai(pac)
        self.assertEqual(ai(5.0, 8.0), (5.0, 4.0))

    def test_targets_pac_position_when_stationary(self):
        pac = self._pac(5, 4, 0, 0)
        ai = main.make_pinky_ai(pac)
        self.assertEqual(ai(5.0, 4.0), (5.0, 4.0))

    def test_reads_live_pac_direction(self):
        # ai_fn reads pac.dx/dy at call time, not capture time
        pac = self._pac(5, 4, 1, 0)
        ai = main.make_pinky_ai(pac)
        pac.dx, pac.dy = -1, 0
        self.assertEqual(ai(5.0, 4.0), (1.0, 4.0))


class TestInkyAI(unittest.TestCase):
    def _setup(self, pac_tx, pac_ty, pac_dx, pac_dy, blinky_tx, blinky_ty):
        pac = main.Pacman()
        pac.tile_x = pac_tx
        pac.tile_y = pac_ty
        pac.dx = pac_dx
        pac.dy = pac_dy
        pac.progress = 0.0
        blinky = main.Ghost(0)
        blinky.tile_x = blinky_tx
        blinky.tile_y = blinky_ty
        blinky.progress = 0.0
        return main.make_inky_ai(pac, blinky)

    def test_doubles_vector_from_blinky_to_pivot(self):
        # pac at (5,4) moving right, blinky at (3,4)
        # pivot = (7,4), target = 2*(7,4) - (3,4) = (11,4)
        ai = self._setup(5, 4, 1, 0, 3, 4)
        self.assertEqual(ai(5.0, 4.0), (11.0, 4.0))

    def test_blinky_behind_pac_extends_target_far(self):
        # pac at (8,4) moving right, blinky at (4,4)
        # pivot = (10,4), target = 2*(10,4) - (4,4) = (16,4)
        ai = self._setup(8, 4, 1, 0, 4, 4)
        self.assertEqual(ai(8.0, 4.0), (16.0, 4.0))

    def test_reads_live_blinky_position(self):
        pac = main.Pacman()
        pac.tile_x, pac.tile_y, pac.dx, pac.dy = 5, 4, 1, 0
        pac.progress = 0.0
        blinky = main.Ghost(0)
        blinky.tile_x, blinky.tile_y = 3, 4
        blinky.progress = 0.0
        ai = main.make_inky_ai(pac, blinky)
        blinky.tile_x = 1  # blinky moves; pivot still (7,4), target = 2*7-1=13
        self.assertEqual(ai(5.0, 4.0), (13.0, 4.0))


class TestClydeAI(unittest.TestCase):
    CORNER = (1.0, float(main.ROWS - 2))

    def _clyde_at(self, tx, ty):
        g = main.Ghost(3)
        g.tile_x = tx
        g.tile_y = ty
        g.progress = 0.0
        return g

    def test_chases_when_far(self):
        # dist(1,4 → 10,4) = 9 > 8 → target = Pac-Man
        clyde = self._clyde_at(1, 4)
        ai = main.make_clyde_ai(clyde, *self.CORNER)
        self.assertEqual(ai(10.0, 4.0), (10.0, 4.0))

    def test_retreats_to_corner_when_close(self):
        # dist(9,4 → 10,4) = 1 ≤ 8 → target = corner
        clyde = self._clyde_at(9, 4)
        ai = main.make_clyde_ai(clyde, *self.CORNER)
        self.assertEqual(ai(10.0, 4.0), self.CORNER)

    def test_threshold_is_exactly_8_tiles(self):
        # dist = exactly 8 → corner (not strictly greater)
        clyde = self._clyde_at(2, 4)
        ai = main.make_clyde_ai(clyde, *self.CORNER)
        self.assertEqual(ai(10.0, 4.0), self.CORNER)

    def test_reads_live_clyde_position(self):
        clyde = self._clyde_at(9, 4)   # starts close → corner
        ai = main.make_clyde_ai(clyde, *self.CORNER)
        clyde.tile_x = 1               # moves far → should now chase
        self.assertEqual(ai(10.0, 4.0), (10.0, 4.0))


class TestTunnelMazeStructure(unittest.TestCase):
    """Verify the maze is correctly laid out for tunnel rows."""

    TUNNEL_ROWS = [6, 9]

    def test_tunnel_left_edge_is_not_wall(self):
        for ty in self.TUNNEL_ROWS:
            self.assertFalse(main.is_wall(0, ty),
                             f"Row {ty}: col 0 should be open (tunnel entrance)")

    def test_tunnel_right_edge_is_not_wall(self):
        for ty in self.TUNNEL_ROWS:
            self.assertFalse(main.is_wall(main.COLS - 1, ty),
                             f"Row {ty}: col {main.COLS - 1} should be open (tunnel entrance)")

    def test_non_tunnel_rows_have_wall_edges(self):
        for ty in range(main.ROWS):
            if ty not in self.TUNNEL_ROWS:
                self.assertTrue(main.is_wall(0, ty),
                                f"Row {ty}: col 0 should be a wall")
                self.assertTrue(main.is_wall(main.COLS - 1, ty),
                                f"Row {ty}: col {main.COLS - 1} should be a wall")


class TestTunnelTraversal(unittest.TestCase):
    """Verify that entities can exit and wrap through tunnel tiles."""

    TUNNEL_ROW = 6

    def _pac(self, tx, ty, dx, dy):
        pyxel_stub.btn = MagicMock(side_effect=no_input)
        pac = main.Pacman()
        pac.tile_x = int(tx)
        pac.tile_y = int(ty)
        pac.dx = dx
        pac.dy = dy
        pac.next_dx = dx
        pac.next_dy = dy
        pac.progress = 0.0
        return pac

    # --- pick_direction ---

    def test_pick_direction_allows_right_exit_at_right_tunnel_tile(self):
        # Ghost at the rightmost tunnel tile moving right: ntx=COLS is OOB,
        # tile_at handles it via tunnel wrapping → not a wall.
        result = main.pick_direction(
            main.COLS - 1, self.TUNNEL_ROW,
            dx=1, dy=0,
            target_x=float(main.COLS + 5), target_y=float(self.TUNNEL_ROW),
        )
        self.assertEqual(result, (1, 0),
                         "pick_direction should allow rightward exit at right tunnel tile")

    def test_pick_direction_allows_left_exit_at_left_tunnel_tile(self):
        # Ghost at the leftmost tunnel tile moving left: ntx=-1 is OOB.
        result = main.pick_direction(
            0, self.TUNNEL_ROW,
            dx=-1, dy=0,
            target_x=-5.0, target_y=float(self.TUNNEL_ROW),
        )
        self.assertEqual(result, (-1, 0),
                         "pick_direction should allow leftward exit at left tunnel tile")

    # --- end-to-end traversal ---

    def test_pacman_traverses_right_tunnel(self):
        # Pac-Man at the rightmost tunnel tile moving right wraps to the left side.
        pac = self._pac(main.COLS - 1, self.TUNNEL_ROW, dx=1, dy=0)
        for _ in range(PAC_TILE_FRAMES + 5):
            pac.update({})
        self.assertLess(
            pac.tx, float(main.COLS) / 2,
            f"Pac-Man should wrap to left side of tunnel (tx={pac.tx:.2f})"
        )

    def test_pacman_traverses_left_tunnel(self):
        # Pac-Man at the leftmost tunnel tile moving left wraps to the right side.
        pac = self._pac(0, self.TUNNEL_ROW, dx=-1, dy=0)
        for _ in range(PAC_TILE_FRAMES + 5):
            pac.update({})
        self.assertNotEqual(
            pac.dx, 0,
            f"Pac-Man should still be moving after traversing the left tunnel (tx={pac.tx:.2f})"
        )

    def test_pacman_tunnel_row_9_traverses_right(self):
        pac = self._pac(main.COLS - 1, 9, dx=1, dy=0)
        for _ in range(PAC_TILE_FRAMES + 5):
            pac.update({})
        self.assertLess(
            pac.tx, float(main.COLS) / 2,
            f"Row-9 tunnel: Pac-Man should wrap to left side (tx={pac.tx:.2f})"
        )


class TestGhostTunnelRestriction(unittest.TestCase):
    """Ghosts must not pass through tunnels — only Pac-Man can use them."""

    TUNNEL_ROW = 6

    def _ghost_at(self, tx, ty, dx, dy):
        g = main.Ghost(0)
        g.tile_x = tx
        g.tile_y = ty
        g.dx = dx
        g.dy = dy
        g.progress = 0.0
        g.ai_fn = lambda pac_tx, pac_ty: (float(tx), float(ty))
        return g

    def test_pick_direction_blocks_right_exit_for_ghost(self):
        # At the rightmost tunnel tile moving right, allow_tunnel=False must block exit.
        result = main.pick_direction(
            main.COLS - 1, self.TUNNEL_ROW,
            dx=1, dy=0,
            target_x=float(main.COLS + 5), target_y=float(self.TUNNEL_ROW),
            allow_tunnel=False,
        )
        self.assertNotEqual(result, (1, 0),
                            "Ghost should not be allowed to exit right tunnel")

    def test_pick_direction_blocks_left_exit_for_ghost(self):
        # At the leftmost tunnel tile moving left, allow_tunnel=False must block exit.
        result = main.pick_direction(
            0, self.TUNNEL_ROW,
            dx=-1, dy=0,
            target_x=-5.0, target_y=float(self.TUNNEL_ROW),
            allow_tunnel=False,
        )
        self.assertNotEqual(result, (-1, 0),
                            "Ghost should not be allowed to exit left tunnel")

    def test_ghost_does_not_traverse_right_tunnel(self):
        # Ghost heading into the right tunnel exit must not wrap to the left side.
        g = self._ghost_at(main.COLS - 2, self.TUNNEL_ROW, dx=1, dy=0)
        prev_tx = g.tile_x
        for _ in range(GHOST_TILE_FRAMES * 4):
            g.update(float(main.COLS), float(self.TUNNEL_ROW))
            if prev_tx == main.COLS - 1 and g.tile_x == 0:
                self.fail("Ghost wrapped through right tunnel (tile_x jumped COLS-1 → 0)")
            prev_tx = g.tile_x

    def test_ghost_does_not_traverse_left_tunnel(self):
        # Ghost heading into the left tunnel exit must not wrap to the right side.
        g = self._ghost_at(1, self.TUNNEL_ROW, dx=-1, dy=0)
        prev_tx = g.tile_x
        for _ in range(GHOST_TILE_FRAMES * 4):
            g.update(0.0, float(self.TUNNEL_ROW))
            if prev_tx == 0 and g.tile_x == main.COLS - 1:
                self.fail("Ghost wrapped through left tunnel (tile_x jumped 0 → COLS-1)")
            prev_tx = g.tile_x


class TestTileProgressMovement(unittest.TestCase):
    """Verify key properties of the tile-progress movement model."""

    def setUp(self):
        pyxel_stub.btn = MagicMock(side_effect=no_input)

    # --- Ghost ---

    def test_ghost_direction_only_changes_at_tile_boundary(self):
        # Ghost moving right through row 4 toward pac at (12,4).
        # Direction must not change mid-tile — only after progress overflows.
        g = main.Ghost(0)
        g.tile_x = 6
        g.tile_y = 4
        g.dx, g.dy = 1, 0
        g.progress = 0.0
        initial_dx = g.dx
        # Fewer frames than a full tile — direction should be unchanged
        for _ in range(GHOST_TILE_FRAMES - 2):
            g.update(12.0, 4.0)
        self.assertEqual(g.dx, initial_dx, "Direction changed before tile boundary")
        # Complete the tile traversal — pick_direction fires at arrival
        for _ in range(4):
            g.update(12.0, 4.0)
        self.assertEqual(g.dx, 1)  # continues right toward pac at col 12

    def test_ghost_no_wall_clip(self):
        # In the tile-progress model, turns always happen at exact tile boundaries.
        # The ghost's body can never clip into adjacent walls.
        g = main.Ghost(0)  # starts at valid spawn with a valid direction
        for _ in range(200):
            g.update(6.0, 14.0)
            self.assertFalse(
                main.is_wall(g.tile_x, g.tile_y),
                f"Ghost occupies wall tile ({g.tile_x},{g.tile_y})"
            )

    # --- Pacman ---

    def test_pacman_queued_direction_applied_at_tile_boundary(self):
        # Row 4 col 4 → down to col (4,5): MAZE[5][4]='2', valid.
        # Pac moving right from (3,4); queued direction: down.
        pac = main.Pacman()
        pac.tile_x = 3
        pac.tile_y = 4
        pac.dx, pac.dy = 1, 0
        pac.next_dx, pac.next_dy = 0, 1
        pac.progress = 0.0
        for _ in range(PAC_TILE_FRAMES):
            pac.update({})
        self.assertEqual(pac.dy, 1, "Pac-Man should have turned down at tile boundary")
        self.assertEqual(pac.dx, 0)

    def test_pacman_stops_when_wall_ahead_and_no_queue(self):
        # Row 1 col 5→6: col 7 is wall. Both current and queued direction right → stop.
        pac = main.Pacman()
        pac.tile_x = 5
        pac.tile_y = 1
        pac.dx, pac.dy = 1, 0
        pac.next_dx, pac.next_dy = 1, 0
        pac.progress = 0.0
        for _ in range(PAC_TILE_FRAMES):
            pac.update({})
        self.assertEqual(pac.dx, 0)
        self.assertEqual(pac.dy, 0)

    def test_pacman_continues_if_queue_blocked_but_forward_clear(self):
        # Row 4 col 4→5: queued up leads to (5,3) which is a wall.
        # Forward (right) is clear at (6,4) → continue right.
        pac = main.Pacman()
        pac.tile_x = 4
        pac.tile_y = 4
        pac.dx, pac.dy = 1, 0
        pac.next_dx, pac.next_dy = 0, -1  # up: MAZE[3][5]='1', blocked
        pac.progress = 0.0
        for _ in range(PAC_TILE_FRAMES):
            pac.update({})
        self.assertEqual(pac.dx, 1, "Pac-Man should continue right when queued up is blocked")
        self.assertEqual(pac.dy, 0)


if __name__ == "__main__":
    unittest.main()
