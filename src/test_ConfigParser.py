#!/usr/bin/env python 

from io import StringIO
from parameterized import parameterized
import unittest

from ConfigParser import ConfigParser
from ShapesDemo import DEFAULT_DIC

TRIANGLE_CONFIG_FILENAME = 'pub_t.cfg'

class Test(unittest.TestCase):

    def setUp(self):
        self.parser = ConfigParser(DEFAULT_DIC)


    def test_init_does_not_populate_sub_or_pub(self):
        self.assertFalse(self.parser.pub_dic)
        self.assertFalse(self.parser.sub_dic)

    def test_init_populates_defaults(self):
        self.assertTrue(self.parser.pub_dic_default)
        self.assertTrue(self.parser.pub_dic_help)
        self.assertTrue(self.parser.sub_dic_default)
        self.assertTrue(self.parser.sub_dic_help)

    def test_parse_sub_and_pub_no_file(self):
        self.parser.parse()
        self.assertFalse(self.parser.sub_dic)
        self.assertFalse(self.parser.pub_dic)

    def check_config_triangle(self):
        self.assertEqual(self.parser.pub_dic['T']['color'], "RED")
        self.assertIsNone(self.parser.pub_dic.get('C'))
        self.assertIsNone(self.parser.pub_dic.get('S'))

        self.assertIsNone(self.parser.sub_dic.get('C'))
        self.assertIsNone(self.parser.sub_dic.get('S'))
        self.assertIsNone(self.parser.sub_dic.get('T'))

    def test_config_triangle(self):
        self.parser.parse(TRIANGLE_CONFIG_FILENAME)
        self.check_config_triangle()

    def test_config_triangle_from_stream(self):
        with open(TRIANGLE_CONFIG_FILENAME, "r") as cfg_file:
            contents = cfg_file.read()
        stream = StringIO(contents)
        self.parser.parse(stream)

    def test_config_pub_square(self):
        config = """{"pub": { "square": {
           "color": "yellow",
           "xy": [27, 37],
           "angle": 45,
           "delta_angle": 2.0,
           "delta_xy": [1,2],
           "size": 50
        }}}"""
        self.parser.parse(StringIO(config))
        self.assertIsNotNone(self.parser.pub_dic.get('S'))
        self.assertEqual(self.parser.pub_dic['S']['color'], "YELLOW")
        self.assertEqual(self.parser.pub_dic['S']['xy'], (27, 37))
        self.assertEqual(self.parser.pub_dic['S']['angle'], 45.0)
        self.assertEqual(self.parser.pub_dic['S']['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_dic['S']['delta_xy'], (1,2))
        self.assertEqual(self.parser.pub_dic['S']['shapesize'], 50)

    def todo_test_config_pub_square2(self):
        config = """{
        "pub": { 
          "square": {
             "color": "yellow",
             "xy": [27, 37],
             "angle": 45,
             "delta_angle": 2.0,
             "delta_xy": [1,2],
             "size": 50
           },
           "triangle": {
             "color": "Green",
             "xy": [47, 57],
             "angle": 90,
             "delta_angle": 3.0,
             "delta_xy": [2,4],
             "size": 55
           }
        }}"""
        self.parser.parse(StringIO(config))
        self.assertIsNotNone(self.parser.pub_dic.get('S'))
        self.assertEqual(self.parser.pub_dic['S']['color'], "YELLOW")
        self.assertEqual(self.parser.pub_dic['S']['xy'], (27, 37))
        self.assertEqual(self.parser.pub_dic['S']['angle'], 45.0)
        self.assertEqual(self.parser.pub_dic['S']['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_dic['S']['delta_xy'], (1,2))
        self.assertEqual(self.parser.pub_dic['S']['shapesize'], 50)

        self.assertIsNotNone(self.parser.pub_dic.get('T'))
        self.assertEqual(self.parser.pub_dic['T']['color'], "GREEN")
        self.assertEqual(self.parser.pub_dic['T']['xy'], (27, 37))
        self.assertEqual(self.parser.pub_dic['T']['angle'], 45.0)
        self.assertEqual(self.parser.pub_dic['T']['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_dic['T']['delta_xy'], (1,2))
        self.assertEqual(self.parser.pub_dic['T']['shapesize'], 50)

    def check_case_and_length(self, default, help_text):
        #print(f'{default=} {help_text=}')
        for key, text in help_text.items():
            self.assertTrue(key[0].islower())
            self.assertTrue(text[0].isupper())
        for key in default.keys():
            self.assertTrue(key[0].islower())
        self.assertEqual(len(default), len(help_text))

    def test_get_pub_config(self):
        self.parser.parse('pub_t.cfg')
        pub_cfg = self.parser.get_pub_config()
        sub_cfg = self.parser.get_sub_config()

    def test_get_sub_config(self):
        pass

    def test_get_pub_config_defaults(self):
        default, help_text = self.parser.get_pub_config(True)
        self.check_case_and_length(default, help_text)

    def test_get_sub_config_defaults(self):
        default, help_text = self.parser.get_sub_config(True)
        self.check_case_and_length(default, help_text)
        
    def test_normalize_xy_too_few(self):
        with self.assertRaises(ValueError):
            xy = self.parser.normalize_xy('too_few', (1, ))

    def test_normalize_xy_too_many(self):
        with self.assertRaises(ValueError):
            xy = self.parser.normalize_xy('too_many', (1, 2, 3))

class Test_normalize_shape(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser(DEFAULT_DIC)

    @parameterized.expand([
        ['Circle', 'C'],
        ['Square', 'S'],
        ['triangle', 'T'],
    ])
        
    def test_normalize_shape(self, param, result):
        shape = self.parser.normalize_shape(param)
        self.assertEqual(result, shape)

class Test_normalize_xy(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser(DEFAULT_DIC)

    @parameterized.expand([
        [(7.0, 9.0), (7,9)],
        [(7.1, 9.2), (7,9)]
    ])
        
    def test_normalize_xy(self, xy, result):
        xy = self.parser.normalize_xy('float', xy)
        self.assertEqual(result, xy)

if __name__ == '__main__':
    unittest.main()

