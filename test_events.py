import unittest
from app import Events

class RuleTests(unittest.TestCase):
    def test_persistence_dwell_cooldown(self):
        rules = Events(dwell=10)
        self.assertEqual(rules.update(0, {1}), [])
        self.assertEqual([e[1] for e in rules.update(2, {1})], ['intrusion'])
        self.assertEqual([e[1] for e in rules.update(10, {1})], ['loitering'])
        self.assertEqual(rules.update(11, {1}), [])
        rules.update(12, set())
        self.assertEqual(rules.update(13, {1}), [])

    def test_people_do_not_share_dwell(self):
        rules = Events(dwell=10)
        rules.update(0, {1})
        self.assertEqual(rules.update(20, {2}), [])

if __name__ == '__main__':
    unittest.main()

