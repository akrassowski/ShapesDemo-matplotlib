#!/usr/bin/env python
"""tests for ConnextSubscriber"""

from io import StringIO
import logging
from pprint import pprint
import unittest
from parameterized import parameterized

from ConfigParser import ConfigParser
from ShapesDemo import DEFAULT_DIC
from ConnextPublisher import ConnextPublisher

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

TRIANGLE_CONFIG_FILENAME = 'test_pub_t.cfg'

# pylint: disable=missing-function-docstring
class Test(unittest.TestCase):
    """tests for ConnextSubscriber"""
    def setUp(self):
        self.parser = ConfigParser(DEFAULT_DIC)
        self.config = """{
        "pub1": {
          "square": {
             "color": "color1", "xy": [27, 37],
             "angle": 45, "delta_angle": 2.0,
             "delta_xy": [1,2], "size": 50
           }
        },
        "pub2": {
           "square": {
             "color": "color2", "xy": [47, 57],
             "angle": 90, "delta_angle": 3.0,
             "delta_xy": [2,4], "size": 55
           }
        }}"""
        self.config_multi = """{
          "square": {
             "color": "green", "xy": [27, 37],
             "angle": 45, "delta_angle": 2.0,
             "delta_xy": [1,2], "size": 50
           },
           "square": {
             "color": "red", "xy": [47, 57],
             "angle": 90, "delta_angle": 3.0,
             "delta_xy": [2,4], "size": 55
           },
           "square": {
             "xy": [97, 97],
             "angle": 99, "delta_angle": 9.0,
             "delta_xy": [9,9], "size": 99
           }
        }"""

    def test_normalize_pub_config(self):
        config = self.parser.json_to_config(StringIO(self.config_multi))
        self.parser.normalize_pub_config(config)
        self.assertTrue('S' in self.parser.pub_list[0])
        self.assertEqual('GREEN', self.parser.pub_list[0]['S']['color'], pprint(self.parser.pub_list))
        self.assertTrue('S' in self.parser.pub_list[1])
        self.assertEqual('RED', self.parser.pub_list[1]['S']['color'], pprint(self.parser.pub_list))
        self.assertTrue('S' in self.parser.pub_list[2])
        self.assertIsNone(self.parser.pub_list[2]['S'].get('color'), pprint(self.parser.pub_list))

    def test_json_to_config(self):
        cfg = self.parser.json_to_config(StringIO(self.config_multi))
        self.assertEqual(len(cfg), 3)

    def old_test_fixup(self):
        color = 'GREEN'
        key_unknown = ConnextPublisher.form_pub_key('S', 'UNKNOWN')
        self.parser.pub_dic[key_unknown] = self.parser.pub_default_dic
        #pprint(self.parser.pub_default_dic)
        self.parser.pub_dic[key_unknown]['color'] = color
        #pprint(self.parser.pub_dic)
        self.parser.fixup_unknown('S', color)
        #pprint(self.parser.pub_dic)
        key = ConnextPublisher.form_pub_key('S', color)
        self.assertEqual(self.parser.pub_dic[key]['color'], color)
        attr_lis = ['angle', 'delta_angle', 'xy', 'delta_xy', 'fillKind', 'shapesize']
        self.assertIsNone(self.parser.pub_dic.get(key_unknown))
        for attr in attr_lis:
            self.assertIsNotNone(self.parser.pub_dic[key][attr])

    def test_init_does_not_populate_sub_or_pub(self):
        self.assertFalse(self.parser.pub_list)
        self.assertFalse(self.parser.sub_dic)
        ###self.assertFalse(self.parser.sub_list)

    def test_init_populates_defaults(self):
        self.assertTrue(self.parser.pub_default_dic)
        self.assertTrue(self.parser.pub_help_dic)
        self.assertTrue(self.parser.sub_default_dic)
        self.assertTrue(self.parser.sub_help_dic)

    def test_parse_sub_and_pub_no_file(self):
        self.parser.parse()
        self.assertFalse(self.parser.get_sub_config())
        self.assertFalse(self.parser.get_pub_config())

    def check_config_triangle(self):
        self.assertEqual(self.parser.pub_list[0]['T']['fillKind'], 3, self.parser.pub_list)
        self.assertIsNone(self.parser.pub_list[0].get('C'))
        self.assertIsNone(self.parser.pub_list[0].get('S'))

        self.assertIsNone(self.parser.sub_dic.get('C'))
        self.assertIsNone(self.parser.sub_dic.get('S'))
        self.assertIsNone(self.parser.sub_dic.get('T'))

    def test_config_triangle(self):
        self.parser.parse(TRIANGLE_CONFIG_FILENAME)
        self.check_config_triangle()

    def test_config_triangle_from_stream(self):
        with open(TRIANGLE_CONFIG_FILENAME, "r", encoding='utf-8') as cfg_file:
            contents = cfg_file.read()
        stream = StringIO(contents)
        self.parser.parse(stream)
        self.check_config_triangle()

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
        self.assertEqual(len(self.parser.pub_list), 1)
        key = 'S'
        self.assertIsNotNone(self.parser.pub_list[0].get(key))
        self.assertEqual(self.parser.pub_list[0][key]['color'], "YELLOW")
        self.assertEqual(self.parser.pub_list[0][key]['xy'], [27, 37])
        self.assertEqual(self.parser.pub_list[0][key]['angle'], 45.0)
        self.assertEqual(self.parser.pub_list[0][key]['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_list[0][key]['delta_xy'], [1, 2])
        self.assertEqual(self.parser.pub_list[0][key]['shapesize'], 50)

    def test_minimal(self):
        config = """{"pub": { "square": {
            "size": 33
        }}}"""
        self.parser.parse(StringIO(config))
        key = 'S'
        self.assertIsNotNone(self.parser.pub_list[0].get(key), f'{key=} {self.parser.pub_list[0]=}')
        self.assertEqual(self.parser.pub_list[0][key]['shapesize'], 33)
        self.assertIsNone(self.parser.pub_list[0][key].get('color'))
        self.assertIsNone(self.parser.pub_list[0][key].get('xy'))

    def test_config_pub_square2(self):
        color1, color2 = 'Yellow', 'Green'
        config = self.config.replace("color1", color1).replace("color2", color2)
        self.parser.parse(StringIO(config))
        self.assertEqual(len(self.parser.pub_list), 2)
        #print(f'{self.parser.pub_dic=}')
        key = 'S'
        #print(f'{key=}')
        self.assertIsNotNone(self.parser.pub_list[0].get(key))
        self.assertEqual(self.parser.pub_list[0][key]['angle'], 45.0)
        self.assertEqual(self.parser.pub_list[0][key]['color'], color1.upper())
        self.assertEqual(self.parser.pub_list[0][key]['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_list[0][key]['delta_xy'], [1, 2])
        self.assertEqual(self.parser.pub_list[0][key]['shapesize'], 50)
        self.assertEqual(self.parser.pub_list[0][key]['xy'], [27, 37])

        self.assertIsNotNone(self.parser.pub_list[1].get(key))
        self.assertEqual(self.parser.pub_list[1][key]['angle'], 90.0)
        self.assertEqual(self.parser.pub_list[1][key]['color'], color2.upper())
        self.assertEqual(self.parser.pub_list[1][key]['delta_angle'], 3.0)
        self.assertEqual(self.parser.pub_list[1][key]['delta_xy'], [2, 4])
        self.assertEqual(self.parser.pub_list[1][key]['shapesize'], 55)
        self.assertEqual(self.parser.pub_list[1][key]['xy'], [47, 57])

    def test_config_pub_square_dup(self):
        color1, color2 = 'Yellow', 'Green'
        config = self.config.replace("color1", color1).replace("color2", color2)
        config = config.replace("pub1", "pub").replace("pub2", "pub")
        #pprint(config)
        self.parser.parse(StringIO(config))
        self.assertEqual(len(self.parser.pub_list), 2)
        key = 'S'
        self.assertIsNotNone(self.parser.pub_list[0].get(key))
        self.assertEqual(self.parser.pub_list[0][key]['angle'], 45.0)
        self.assertEqual(self.parser.pub_list[0][key]['color'], color1.upper())
        self.assertEqual(self.parser.pub_list[0][key]['delta_angle'], 2.0)
        self.assertEqual(self.parser.pub_list[0][key]['delta_xy'], [1, 2])
        self.assertEqual(self.parser.pub_list[0][key]['shapesize'], 50)
        self.assertEqual(self.parser.pub_list[0][key]['xy'], [27, 37])

        self.assertEqual(self.parser.pub_list[1][key]['angle'], 90.0)
        self.assertEqual(self.parser.pub_list[1][key]['color'], color2.upper())
        self.assertEqual(self.parser.pub_list[1][key]['delta_angle'], 3.0)
        self.assertEqual(self.parser.pub_list[1][key]['delta_xy'], [2, 4])
        self.assertEqual(self.parser.pub_list[1][key]['shapesize'], 55)
        self.assertEqual(self.parser.pub_list[1][key]['xy'], [47, 57])

    def check_case_and_length(self, default, help_text):
        #print(f'{default=} {help_text=}')
        for key, text in help_text.items():
            self.assertTrue(key[0].islower())
            self.assertTrue(text[0].isupper())
        for key in default.keys():
            self.assertTrue(key[0].islower())
        self.assertEqual(len(default), len(help_text))

    def test_get_pub_config(self):
        self.parser.parse(TRIANGLE_CONFIG_FILENAME)
        pub_cfg_list = self.parser.get_pub_config()
        self.assertEqual(pub_cfg_list[0]['T']['color'], 'RED') #, pprint(pub_cfg_list))

    def test_get_sub_config(self):
        config = """{"sub": { "circle": {}, "square": {}}}"""
        config = """{"sub": { "circle": {}}, "sub": {"square": {}}}"""
        self.parser.parse(StringIO(config))
        sub_cfg = self.parser.get_sub_config()
        return
        pprint(sub_cfg)
        #print(f'{sub_cfg_list=}')
        #self.assertEqual(len(sub_cfg_list), 1)
        #sub_cfg = sub_cfg_list[0]
        self.assertIsNotNone(sub_cfg.get('C'))
        square_config = sub_cfg.get('S')
        self.assertIsNotNone(square_config)
        self.assertTrue('content_filter' in square_config)
        self.assertIsNone(sub_cfg.get('T'))

    def test_get_pub_config_defaults(self):
        default, help_text = self.parser.get_pub_config(True)
        self.check_case_and_length(default, help_text)

    def test_get_sub_config_defaults(self):
        default, help_text = self.parser.get_sub_config(True)
        self.check_case_and_length(default, help_text)

    def test_normalize_xy_too_few(self):
        with self.assertRaises(ValueError):
            _ = self.parser.normalize_xy('too_few', (1, ))

    def test_normalize_xy_too_many(self):
        with self.assertRaises(ValueError):
            _ = self.parser.normalize_xy('too_many', (1, 2, 3))

class Test_normalize_shape(unittest.TestCase):
    """Parameter test for normalize_shape functions"""
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
    """Parameter test for normalize_xy functions"""
    def setUp(self):
        self.parser = ConfigParser(DEFAULT_DIC)

    @parameterized.expand([
        [(7.0, 9.0), [7,9]],
        [(7.1, 9.2), [7,9]]
    ])

    def test_normalize_xy(self, xy, result):
        xy = self.parser.normalize_xy('float', xy)
        self.assertEqual(result, xy)

if __name__ == '__main__':
    unittest.main()
    Test()
    Test_normalize_shape()
    Test_normalize_xy()
