import unittest
from calc import add, sub, mul
class TestCalc(unittest.TestCase):
    def test_calc(self):
        self.assertEqual(add(2, 2), 4)
        self.assertEqual(sub(5, 2), 3)
        self.assertEqual(mul(3, 3), 9)
if __name__ == '__main__':
    unittest.main()