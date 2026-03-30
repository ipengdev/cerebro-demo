import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from queue_management import qms_api, qms_call_screen_api


class TestQMSRegressions(unittest.TestCase):
	def test_get_screen_data_uses_shared_call_screen_loader(self):
		expected = {"queue_length": 3, "serving_tickets": []}

		with patch(
			"queue_management.qms_call_screen_api._staff_action_context",
			return_value=nullcontext({"staff_id": "staff-1"}),
		) as action_context:
			with patch(
				"queue_management.qms_display_api.get_call_screen_data",
				return_value=expected,
			) as get_call_screen_data:
				result = qms_call_screen_api.get_screen_data("token-1", "QCTR-1")

		self.assertEqual(result, expected)
		action_context.assert_called_once_with("token-1", "QCTR-1")
		get_call_screen_data.assert_called_once_with("QCTR-1")

	def test_action_start_serving_delegates_under_staff_context(self):
		with patch(
			"queue_management.qms_call_screen_api._staff_action_context",
			return_value=nullcontext({"staff_id": "staff-1"}),
		) as action_context:
			with patch("queue_management.qms_api.start_serving", return_value={"ticket": "QT-1"}) as start_serving:
				result = qms_call_screen_api.action_start_serving("token-1", "QT-1")

		self.assertEqual(result, {"ticket": "QT-1"})
		action_context.assert_called_once_with("token-1")
		start_serving.assert_called_once_with("QT-1")

	def test_mark_no_show_validates_transition_before_update(self):
		rows = [SimpleNamespace(
			name="QT-1",
			status="Completed",
			counter="QCTR-1",
			ticket_number="T001",
			location="LOC-1",
			transferred_from_counter=None,
			no_show_count=0,
		)]
		fake_db = SimpleNamespace()

		with patch.object(qms_api, "_check_qms_role"):
			with patch.object(qms_api, "_require_qms_live_mutation"):
				with patch.object(qms_api.frappe, "db", fake_db):
					with patch.object(fake_db, "sql", side_effect=[rows], create=True) as sql:
						with patch.object(
							qms_api,
							"_validate_status_transition",
							side_effect=RuntimeError("invalid transition"),
						) as validate_transition:
							with self.assertRaisesRegex(RuntimeError, "invalid transition"):
								qms_api.mark_no_show("QT-1")

		validate_transition.assert_called_once_with("Completed", "Waiting")
		self.assertEqual(sql.call_count, 1)

	def test_call_next_ticket_uses_fifo_before_peer_distribution(self):
		counter_doc = SimpleNamespace(
			services=[SimpleNamespace(service="Blood Test")],
			location="LOC-1",
		)
		ticket_doc = SimpleNamespace(name="QT-11", ticket_number="BLD011", service="Blood Test", location="LOC-1")
		fake_db = SimpleNamespace()
		fake_db.sql = MagicMock(side_effect=[
			[
				SimpleNamespace(name="QT-11", counter=""),
				SimpleNamespace(name="QT-12", counter=""),
			],
			None,
			[(1,)],
		])
		fake_db.get_value = MagicMock(side_effect=[None, SimpleNamespace(counter_name="Counter 1", counter_number="1")])

		def fake_get_doc(doctype, name):
			if doctype == "QMS Counter":
				return counter_doc
			if doctype == "QMS Queue Ticket" and name == "QT-11":
				return ticket_doc
			raise AssertionError(f"Unexpected get_doc call: {doctype} {name}")

		with patch.object(qms_api, "_check_qms_role"):
			with patch.object(qms_api, "_require_qms_live_mutation"):
				with patch.object(qms_api, "_check_counter_access"):
					with patch.object(qms_api, "today", return_value="2026-03-29"):
						with patch.object(qms_api, "now_datetime", return_value="2026-03-29 09:00:00"):
							with patch.object(qms_api.frappe, "db", fake_db):
								with patch.object(qms_api.frappe, "get_doc", side_effect=fake_get_doc) as get_doc:
									with patch.object(qms_api.frappe, "session", SimpleNamespace(user="operator@example.com")):
										with patch.object(qms_api, "_refresh_counter_state") as refresh_counter_state:
											with patch.object(qms_api, "_publish_qms_realtime") as publish_realtime:
												with patch.object(qms_api, "_log_qms_action") as log_action:
													result = qms_api.call_next_ticket("CTR-1")

		self.assertEqual(result, {"ticket": "QT-11", "ticket_number": "BLD011"})
		get_doc.assert_any_call("QMS Queue Ticket", "QT-11")
		self.assertEqual(fake_db.sql.call_args_list[1].args[1][-1], "QT-11")
		refresh_counter_state.assert_called_once_with("CTR-1")
		publish_realtime.assert_called_once()
		log_action.assert_called_once()


if __name__ == "__main__":
	unittest.main()