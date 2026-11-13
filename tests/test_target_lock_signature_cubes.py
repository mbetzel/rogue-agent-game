"""Alias test module redirecting to test_target_lock.py per spec section 10."""

from tests.test_target_lock import *

if __name__ == "__main__":
    import unittest
    unittest.main()
