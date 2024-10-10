import unittest
import sys

from tools import (MyTextTestRunner, MyTestLoader, get_cloud_cmd_print, MyTestCase)


class TestTempate(MyTestCase):
    def test_template1(self):
        """test template1"""
        pass


if __name__ == '__main__':
    help_info = """
       使用方法：
           1、python test_template_simple.py
       """
    if '-h' in sys.argv or '--help' in sys.argv:
        print(help_info)
        sys.exit(0)
    unittest.main(testLoader=MyTestLoader(), testRunner=MyTextTestRunner, verbosity=2)
