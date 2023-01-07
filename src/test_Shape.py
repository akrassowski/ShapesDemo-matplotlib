#!/usr/bin/env python
"""Tests for Shape"""
import unittest
from unittest.mock import MagicMock
from Shape import Shape, COLOR_MAP

# pylint: disable=missing-function-docstring, too-many-public-methods
class Test(unittest.TestCase):
    """Tests for Shape"""

    def setUp(self):
        matplotlib = MagicMock()  # only mock the values that matter
        #matplotlib.args.graph_xy = (240, 270)
        #matplotlib.args.figure_xy = (2, 3)
        matplotlib.axes.get_xlim.return_value = (0, 240)
        matplotlib.axes.get_ylim.return_value = (0, 270)

        self.circle = Shape(
            matplotlib=matplotlib, seq=71, which="C",
            color="GREEN",
            xy=(33, 33), size=33,
            angle=45, fill=0
        )
        self.square = Shape(
            matplotlib=matplotlib, seq=72, which="S",
            color="RED",
            xy=(30, 30), size=30,
        )
        self.triangle = Shape(
            matplotlib=matplotlib, seq=73, which="T",
            color="YELLOW",
            xy=(30, 30), size=30,
        )
        self.limit_y = self.circle.limit_xy[1]

    def test_reverse_if_wall_horizontal(self):
        self.square.xy = 100, 100
        delta_xy = [200, 0]
        self.assertTrue(delta_xy[0] > 0)
        _, new_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertTrue(new_delta_xy[0] < 0)

    def test_reverse_if_wall_vertical(self):
        self.square.xy = 100, 100
        delta_xy = [0, 200]
        self.assertTrue(delta_xy[1] > 0)
        _, new_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertTrue(new_delta_xy[1] < 0)

    def test_reverse_if_wall_edge_pos(self):
        edge = self.square.size = 30  # we depend on size, so set it
        # start a few pixels from the edge
        size, diff_x, diff_y = self.square.size, 2, 3
        self.square.xy = (self.square.limit_xy[0] - diff_x - size,
                          self.square.limit_xy[1] - diff_y - size)
        # ensure we'll hit the wall by choosing a delta larger than the diff
        orig_xy, delta_xy = [9, 10], [9, 10]
        out_xy, out_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertEqual(out_xy[0], self.square.limit_xy[0] - edge)
        self.assertEqual(out_xy[1], self.square.limit_xy[1] - edge)
        self.assertEqual(out_delta_xy[0], -orig_xy[0])
        self.assertEqual(out_delta_xy[1], -orig_xy[1])

    def test_reverse_if_wall_edge_neg(self):
        edge = self.square.size = 30  # we depend on size, so set it
        # start a few pixels from the edge
        diff_x, diff_y = 2, 3
        self.square.xy = (self.square.size + diff_x, self.square.size + diff_y)
        # ensure we'll hit the wall by choosing a delta larger than the diff
        orig_xy, delta_xy = [-9, -10], [-9, -10]
        out_xy, out_delta_xy = self.square.reverse_if_wall(delta_xy)
        #print(f'{out_xy=} {out_delta_xy=}')
        self.assertEqual(out_xy[0], edge)
        self.assertEqual(out_xy[1], edge)
        self.assertEqual(out_delta_xy[0], -orig_xy[0])
        self.assertEqual(out_delta_xy[1], -orig_xy[1])

    def test_get_points_square_0(self):
        self.square.xy = 0, 0
        self.square.size = 15
        self.square.angle = 0
        points = self.square.get_points()
        self.assertEqual(points[0], (-15, -15))
        self.assertEqual(points[1], (-15, 15))
        self.assertEqual(points[2], (15, 15))
        self.assertEqual(points[3], (15, -15))

    def test_get_points_square_360(self):
        self.square.xy = 0, 0
        self.square.size = 15
        self.square.angle = 360
        points = self.square.get_points()
        self.assertEqual(points[0], (-15, -15))
        self.assertEqual(points[1], (-15, 15))
        self.assertEqual(points[2], (15, 15))
        self.assertEqual(points[3], (15, -15))

    def test_get_points_square_45(self):
        self.square.xy = 0, 0
        self.square.size = 15
        self.square.angle = 45
        points = self.square.get_points()
        self.assertEqual(points[0], (-21, 0))
        self.assertEqual(points[1], (0, 21))
        self.assertEqual(points[2], (21, 0))
        self.assertEqual(points[3], (0, -21))

    def test_get_points_square_0_90(self):
        self.square.size = 15
        self.square.angle = 0
        start = sorted(self.square.get_points())
        #self.assertEqual(start[
        self.square.angle = 90
        end = sorted(self.square.get_points())
        #print(end)
        self.assertEqual(start, end)

    def test_get_points_square_45x2(self):
        self.square.size = 15
        self.square.angle = 45
        start = self.square.get_points()
        self.square.angle = 3 * 45
        end = self.square.get_points()
        self.assertEqual(sorted(start), sorted(end))

    def test_get_points_square_90(self):
        self.square.xy = 0, 0
        self.square.size = 15
        self.square.angle = 90
        points = self.square.get_points()
        self.assertEqual(points[3], (-15, -15))
        self.assertEqual(points[0], (-15, 15))
        self.assertEqual(points[1], (15, 15))
        self.assertEqual(points[2], (15, -15))

    def test_get_points_triangle_180(self):
        obj = self.triangle
        obj.xy = 0, 0
        obj.size = 15
        start = obj.get_points()
        for obj.angle in range(0, 361, 30):
            end = obj.get_points()
            #print(f'{n=}: {sorted(end)=}')

        self.assertEqual(sorted(start), sorted(end))

    def test_get_points_circle(self):
        self.circle.xy = 5, 5
        points = self.circle.get_points()
        self.assertEqual(points, (5, 5))

    def test_example_colors(self):
        fcolor, ecolor = self.circle.face_and_edge_color_code(self.circle.fill, self.circle.color)
        self.assertEqual(fcolor, COLOR_MAP['GREEN'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])
        fcolor, ecolor = self.square.face_and_edge_color_code(self.square.fill, self.square.color)
        self.assertEqual(fcolor, COLOR_MAP['RED'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])
        fcolor, ecolor = self.triangle.face_and_edge_color_code(
            self.triangle.fill,
            self.triangle.color
        )
        self.assertEqual(fcolor, COLOR_MAP['YELLOW'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])


    def test_color_fill0_blue(self):
        fcolor, ecolor = Shape.face_and_edge_color_code(0, 'BLUE')
        self.assertEqual(fcolor, COLOR_MAP['BLUE'])
        self.assertEqual(ecolor, COLOR_MAP['RED'])

    def test_color_fill1_blue(self):
        fcolor, ecolor = Shape.face_and_edge_color_code(1, 'BLUE')
        self.assertEqual(fcolor, COLOR_MAP['WHITE'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])

    def test_color_fill2_blue(self):
        fcolor, ecolor = Shape.face_and_edge_color_code(2, 'BLUE')
        self.assertEqual(fcolor, COLOR_MAP['WHITE'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])

    def test_color_compute_blue(self):
        fcolor, ecolor = Shape.face_and_edge_color_code(0, 'BLUE')
        self.assertEqual(fcolor, COLOR_MAP['BLUE'])
        self.assertEqual(ecolor, COLOR_MAP['RED'])

    def test_color_compute_green(self):
        fcolor, ecolor = Shape.face_and_edge_color_code(0, 'GREEN')
        self.assertEqual(fcolor, COLOR_MAP['GREEN'])
        self.assertEqual(ecolor, COLOR_MAP['BLUE'])


if __name__ == '__main__':
    unittest.main()
    Test()
