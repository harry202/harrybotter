import unittest
from src.harrybotter import HarryBotter
from test.mocks import StockModMock

FAILURE = 'incorrect value'
PASS    = 'test passed'

class HarryPotterTest(unittest.TestCase):
    def setUp(self):
        self.bot = HarryBotter()
        self.bot.install_mods(StockModMock())

    def test_cmd_report(self):
        value = self.bot.action_user("harry report","test","test")
        self.assertEqual(value, "建设中", FAILURE)

    def test_cmd_list(self):
        value = self.bot.action_user("harry list","test","test")
        self.assertEqual(value, PASS, FAILURE)

if __name__ == '__main__':
    import xmlrunner

    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        failfast=False,
        buffer=False,
        catchbreak=False)