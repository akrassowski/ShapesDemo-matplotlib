#!/usr/bin/env python 

import unittest
#from ShapesDemo.Shape import Shape
from Shape import Shape

class Test(unittest.TestCase):

    limit = 250

    def setUp(self):
 
        self.circle = Shape(
            seq=71, which="C",
            limit_xy=(240, 270),
            color="GREEN",
            xy=(33,33), size=33,
            angle=45, fill=0
        )
        self.square = Shape(
            seq=72, which="S",
            limit_xy=(240, 270),
            color="RED",
            xy=(30,30), size=30,
            angle=0, fill=0
        )
        self.triangle = Shape(
            seq=73, which="T",
            limit_xy=(240, 270),
            color="YELLOW",
            xy=(30,30), size=30,
            angle=0, fill=0
        )
        self.limit_y = self.circle.limit_xy[1]

    def test_reverse_if_wall_horizontal(self):
        self.square.xy = 100, 100
        delta_xy = 200, 0
        self.assertTrue(delta_xy[0] > 0)
        new_xy, new_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertTrue(new_delta_xy[0] < 0)

    def test_reverse_if_wall_vertical(self):
        xy = 100, 100
        delta_xy = 0, 200
        self.assertTrue(delta_xy[1] > 0)
        new_xy, new_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertTrue(new_delta_xy[1] < 0)

    def test_reverse_if_wall_edge_pos(self):
        edge = self.square.size = 30  # we depend on size, so set it
        # start a few pixels from the edge
        diff_x, diff_y = 2, 3
        self.square.xy = (self.square.limit_xy[0] - diff_x, self.square.limit_xy[1] - diff_y)
        # ensure we'll hit the wall by choosing a delta larger than the diff
        delta_xy = 9, 10
        out_xy, out_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertEqual(out_xy[0], self.square.limit_xy[0] - edge)
        self.assertEqual(out_xy[1], self.square.limit_xy[1] - edge)
        self.assertEqual(out_delta_xy[0], -delta_xy[0])
        self.assertEqual(out_delta_xy[1], -delta_xy[1])
        
    def test_reverse_if_wall_edge_neg(self):
        edge = self.square.size = 30  # we depend on size, so set it
        # start a few pixels from the edge
        diff_x, diff_y = 2, 3
        self.square.xy = (diff_x, diff_y)
        # ensure we'll hit the wall by choosing a delta larger than the diff
        delta_xy = -9, -10
        out_xy, out_delta_xy = self.square.reverse_if_wall(delta_xy)
        self.assertEqual(out_xy[0], edge)
        self.assertEqual(out_xy[1], edge)
        self.assertEqual(out_delta_xy[0], -delta_xy[0])
        self.assertEqual(out_delta_xy[1], -delta_xy[1])
        
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
        print(start)
        self.square.angle = 90
        end = sorted(self.square.get_points())
        print(end)
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
        #obj.angle = 0
        start = obj.get_points()
        for n in range(0, 361, 30):
            obj.angle = n
            end = obj.get_points()
            print(f'{n=}: {sorted(end)=}')

        self.assertEqual(sorted(start), sorted(end))

    def test_reverse(self):
        mpl = 100
        sd = Shape.mpl2sd(mpl, self.limit)
        new_mpl = Shape.sd2mpl(sd, self.limit)
        self.assertEqual(mpl, new_mpl)

    def test_mpl2sd_0(self):
        mpl = 0
        sd = Shape.mpl2sd(mpl, self.limit)
        self.assertEqual(sd, self.limit)

    def test_mpl2sd_10(self):
        mpl = 10
        sd = Shape.mpl2sd(mpl, self.limit)
        self.assertEqual(sd, 240)

    def test_sd2mpl_10(self):
        mpl = Shape.sd2mpl(240, self.limit)
        self.assertEqual(mpl, 10)

    def test_get_points_circle(self):
        self.circle.xy = 5, 5
        points = self.circle.get_points()
        self.assertEqual(points, (5, 5))



if __name__ == '__main__':
    unittest.main()

