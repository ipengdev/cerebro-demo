import unittest

from queue_management.qms_utils import estimated_wait_minutes, normalize_rating_to_five_scale


class TestQMSUtils(unittest.TestCase):
	def test_normalize_rating_accepts_five_point_scale(self):
		self.assertEqual(normalize_rating_to_five_scale(5), 5)
		self.assertEqual(normalize_rating_to_five_scale(3), 3)

	def test_normalize_rating_converts_legacy_unit_scale(self):
		self.assertEqual(normalize_rating_to_five_scale(1), 5)
		self.assertEqual(normalize_rating_to_five_scale(0.6), 3)
		self.assertEqual(normalize_rating_to_five_scale(0.2), 1)

	def test_estimated_wait_uses_people_ahead_only(self):
		self.assertEqual(estimated_wait_minutes(0, 10), 0)
		self.assertEqual(estimated_wait_minutes(1, 10), 0)
		self.assertEqual(estimated_wait_minutes(4, 10), 30)

	def test_estimated_wait_divides_by_counters(self):
		# 10th in line, 10 min service, 3 counters → (9*10)/3 = 30
		self.assertEqual(estimated_wait_minutes(10, 10, 3), 30)
		# 7th in line, 10 min service, 3 counters → (6*10)/3 = 20
		self.assertEqual(estimated_wait_minutes(7, 10, 3), 20)
		# single counter (default) unchanged
		self.assertEqual(estimated_wait_minutes(4, 10, 1), 30)

	def test_estimated_wait_counters_floor_to_one(self):
		# 0 or None counters should be treated as 1
		self.assertEqual(estimated_wait_minutes(4, 10, 0), 30)
		self.assertEqual(estimated_wait_minutes(4, 10, None), 30)


if __name__ == "__main__":
	unittest.main()