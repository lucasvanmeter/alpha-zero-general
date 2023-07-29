import sys
sys.path.append('..')
import unittest
import QuoridorLogic as ql

class TestGetBoardVec(unittest.TestCase):
    """Tests for sums.running_sum."""
    
    def test_get_board_vec_initial(self):
        """Test an initial board."""
        expected = [10,10]+[(4,0),(4,8)]+64*[0]
        b = ql.Board()
        actual = b.getBoardVec()
        self.assertEqual(expected, actual, "Initial board vec")
        
unittest.main()