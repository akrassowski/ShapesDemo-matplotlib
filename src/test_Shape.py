#!/usr/bin/env python 

import unittest
from Shape import Shape
from argparse import Namespace

class Test(unittest.TestCase):

    limit = 250

    def setUp(self):
        args = Namespace(graphy=270)
        
        self.shape_circle = Shape(
            args=args,
            seq=77,
            which="C",
            color="GREEN",
            xy=(33,33),
            size=33,
            angle=45,
            fillKind=0
        )
        self.shape_square = Shape(
            args=args,
            seq=77,
            which="S",
            color="RED",
            xy=(30,30),
            size=30,
            angle=0,
            fillKind=0
        )

    def test_get_points_square_0(self):
        self.shape_square.xy = 0, 0
        self.shape_square.size = 15
        self.shape_square.angle = 0
        points = self.shape_square.get_points()
        self.assertEqual(points[0], (-15, -15))
        self.assertEqual(points[1], (-15, 15))
        self.assertEqual(points[2], (15, 15))
        self.assertEqual(points[3], (15, -15))

    def test_get_points_square_360(self):
        self.shape_square.xy = 0, 0
        self.shape_square.size = 15
        self.shape_square.angle = 360
        points = self.shape_square.get_points()
        self.assertEqual(points[0], (-15, -15))
        self.assertEqual(points[1], (-15, 15))
        self.assertEqual(points[2], (15, 15))
        self.assertEqual(points[3], (15, -15))

    def test_get_points_square_45(self):
        self.shape_square.xy = 0, 0
        self.shape_square.size = 15
        self.shape_square.angle = 45
        points = self.shape_square.get_points()
        self.assertEqual(points[0], (-21, 0))
        self.assertEqual(points[1], (0, 21))
        self.assertEqual(points[2], (21, 0))
        self.assertEqual(points[3], (0, -21))

    def test_get_points_square_45x2(self):
        self.shape_square.size = 15
        self.shape_square.angle = 45
        start = self.shape_square.get_points()
        self.shape_square.angle = 3 * 45
        end = self.shape_square.get_points()
        self.assertEqual(start.sort(), end.sort())

    def test_get_points_square_90(self):
        self.shape_square.xy = 0, 0
        self.shape_square.size = 15
        self.shape_square.angle = 90
        points = self.shape_square.get_points()
        self.assertEqual(points[3], (-15, -15))
        self.assertEqual(points[0], (-15, 15))
        self.assertEqual(points[1], (15, 15))
        self.assertEqual(points[2], (15, -15))

    def test_get_points_triangle_120(self):
        self.shape_square.xy = 0, 0
        self.shape_square.size = 15
        self.shape_square.angle = 0
        start = self.shape_square.get_points()
        self.shape_square.angle = 120
        end = self.shape_square.get_points()
        self.assertEqual(start.sort(), end.sort())

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
        self.shape_circle.xy = 5, 5
        points = self.shape_circle.get_points()
        self.assertEqual(points, (5, 5))



if __name__ == '__main__':
    unittest.main()

