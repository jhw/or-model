from model.utils import linear_interpolate

import unittest

class UtilsTest(unittest.TestCase):
                
    def test_linear_interpolate(self):
        self.assertEqual(linear_interpolate([(1, 10),
                                             (2, 20),
                                             (3, 30)], 2.1), 21.0)
            
if __name__ == "__main__":
    unittest.main()
