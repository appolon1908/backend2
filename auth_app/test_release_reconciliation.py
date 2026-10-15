"""PR23: preserve main-only recovery and tracing without regressing deployed safeguards."""
from unittest.mock import Mock, patch
from uuid import UUID

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from auth_app import tasks
from auth_app.models import Visitor
from helpers.middleware_client import submit_contact

CONFIG = dict(MIDDLEWARE_BASE_URL="https://middleware.example", MIDDLEWARE_ACCESS_TOKEN="synthetic-test-token", MIDDLEWARE_TENANT_ID="codestra")


class RecoveryReconciliationTests(APITestCase):
    def recovery(self, **kwargs):
        task = getattr(tasks, "enqueue_pending_signup_syncs", None)
        self.assertTrue(callable(task), "The Celery beat recovery entry must resolve to a registered task")
        return task.apply(kwargs=kwargs).get()

    def user(self, name, **kwargs):
        values = {"email": f"{name}@example.invalid", "crm_sync_payload": {"email": f"{name}@example.invalid", "source": "codestra-signup"}}
        values.update(kwargs)
        return get_user_model().objects.create_user(**values)

    @override_settings(**CONFIG)
    @patch("auth_app.tasks.queue_signup_sync", return_value=True)
    def test_recovery_selects_only_unbound_durable_intents(self, queue):
        pending = self.user("pending")
        failed = self.user("failed", crm_sync_status="failed")
        self.user("legacy", crm_sync_payload={})
        self.user("linked", odoo_id=12)
        self.user("accepted", crm_sync_operation_id="253141aa-1578-48e3-b5f1-148ba27cc9f6")
        self.user("submitted", crm_sync_status="submitted")
        result = self.recovery(limit=100)
        self.assertEqual(result, {"eligible": 2, "queued": 2})
        self.assertEqual([call.args[0] for call in queue.call_args_list], [pending.pk, failed.pk])

    @override_settings(**CONFIG)
    @patch("auth_app.tasks.queue_signup_sync", return_value=True)
    def test_recovery_respects_batch_limit(self, queue):
        first = self.user("first")
        self.user("second")
        self.assertEqual(self.recovery(limit=1), {"eligible": 1, "queued": 1})
        queue.assert_called_once_with(first.pk)

    @override_settings(**CONFIG)
    @patch("auth_app.tasks.queue_signup_sync", side_effect=[False, True])
    def test_recovery_reports_actual_enqueue_outcomes(self, queue):
        self.user("broker-down")
        self.user("broker-up")
        self.assertEqual(self.recovery(limit=2), {"eligible": 2, "queued": 1})
        self.assertEqual(queue.call_count, 2)

    @override_settings(MIDDLEWARE_BASE_URL="", MIDDLEWARE_ACCESS_TOKEN="", MIDDLEWARE_TENANT_ID="")
    @patch("auth_app.tasks.queue_signup_sync")
    def test_unconfigured_recovery_never_queues(self, queue):
        self.user("unconfigured")
        self.assertEqual(self.recovery(), {"eligible": 0, "queued": 0})
        queue.assert_not_called()

    def test_invalid_limits_fail_before_scanning(self):
        task = getattr(tasks, "enqueue_pending_signup_syncs", None)
        self.assertTrue(callable(task), "Recovery task must exist")
        for limit in (0, -1, 1001, True, "100"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                task.apply(kwargs={"limit": limit}).get()

    @patch("auth_app.tasks.queue_signup_sync", return_value=False)
    def test_existing_enqueue_entrypoint_preserves_guarded_queue(self, queue):
        enqueue = getattr(tasks, "enqueue_signup_sync", None)
        self.assertTrue(callable(enqueue), "Preserve the enqueue API introduced on main")
        self.assertFalse(enqueue("synthetic-user-id"))
        queue.assert_called_once_with("synthetic-user-id")

    @patch("auth_app.views.queue_signup_sync", side_effect=RuntimeError("synthetic callback failure"))
    def test_signup_keeps_durable_intent_when_post_commit_enqueue_raises(self, queue):
        try:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/api/auth/signup/", {
                    "email": "callback@example.invalid", "password": "StrongPass123!",
                    "first_name": "Callback", "last_name": "Recovery",
                }, format="json")
        except RuntimeError:
            self.fail("An enqueue callback must not turn a committed signup into a failed response")
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="callback@example.invalid")
        self.assertEqual(user.crm_sync_status, "pending")
        self.assertEqual(user.crm_sync_payload["email"], user.email)
        queue.assert_called_once_with(user.pk)

    def test_visitor_task_returns_persisted_record(self):
        result = tasks.log_visitor_details.apply(args=[{
            "ip_address": "192.0.2.1", "page": "https://example.invalid/healthz/", "device": "test",
            "browser": "test", "os": "test", "method": "GET", "visited_at": timezone.now(),
        }]).get()
        self.assertIsInstance(result, dict, "Preserve main's structured visitor task result")
        self.assertEqual(result["status"], "saved")
        self.assertTrue(Visitor.objects.filter(pk=result["visitor_id"]).exists())

    def test_beat_schedule_names_the_registered_recovery_task(self):
        from CORE.celery_app import app
        self.assertIn("recover_pending_signup_syncs", app.conf.beat_schedule)
        task_name = app.conf.beat_schedule["recover_pending_signup_syncs"]["task"]
        task = getattr(tasks, "enqueue_pending_signup_syncs", None)
        self.assertIsNotNone(task, "The preserved beat entry must not call a missing task")
        self.assertEqual(task_name, task.name)


@override_settings(**CONFIG)
class CorrelationReconciliationTests(APITestCase):
    @patch("helpers.middleware_client.requests.post")
    def test_correlation_is_valid_stable_and_distinct_per_intent(self, post):
        post.return_value = Mock(json=Mock(return_value={"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}), raise_for_status=Mock())
        for key in ("same-intent", "same-intent", "other-intent"):
            submit_contact({"email": "trace@example.invalid"}, idempotency_key=key)
        first, second, third = [call.kwargs["headers"] for call in post.call_args_list]
        self.assertIn("X-Correlation-ID", first, "Preserve main's request tracing header")
        self.assertEqual(str(UUID(first["X-Correlation-ID"])), first["X-Correlation-ID"])
        self.assertEqual(first, second, "Retry envelope must remain immutable")
        self.assertNotEqual(first["X-Correlation-ID"], third["X-Correlation-ID"])

    @patch("helpers.middleware_client.requests.post")
    def test_correlation_is_tenant_scoped(self, post):
        post.return_value = Mock(json=Mock(return_value={"operation_id": "253141aa-1578-48e3-b5f1-148ba27cc9f6", "state": "ACCEPTED"}), raise_for_status=Mock())
        for tenant in ("codestra", "another-tenant"):
            with override_settings(MIDDLEWARE_TENANT_ID=tenant):
                submit_contact({"email": "trace@example.invalid"}, idempotency_key="same-intent")
        first, second = [call.kwargs["headers"] for call in post.call_args_list]
        self.assertIn("X-Correlation-ID", first, "Preserve main's request tracing header")
        self.assertNotEqual(first["X-Correlation-ID"], second["X-Correlation-ID"])
