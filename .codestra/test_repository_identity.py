#!/usr/bin/env python3
"""Behavioral regressions for the two explicitly authorized repository transfers."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = runpy.run_path(str(ROOT / ".codestra/validate-production-orchestrator-contract.py"), run_name="identity_regression_validator")
IDENTITIES = {1319808791: "appolon1908/codestra", 1319903950: "appolon1908/backend2"}


class RepositoryIdentityTests(unittest.TestCase):
    def setUp(self):
        self.contract = VALIDATOR["load_contract"]()
        self.repository = IDENTITIES[self.contract["repository_id"]]
        self.environment = patch.dict(os.environ, {
            "GITHUB_REPOSITORY": self.repository,
            "GITHUB_REPOSITORY_ID": str(self.contract["repository_id"]),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def reject(self, contract, reason):
        with self.assertRaisesRegex(VALIDATOR["ContractError"], reason):
            VALIDATOR["validate"](contract)

    def test_canonical_repository_keeps_complete_contract_validation(self):
        VALIDATOR["validate"](self.contract)

    def test_former_owner_cannot_reclaim_the_transferred_identity(self):
        old = self.repository.replace("appolon1908/", "appolon1908-hue/")
        contract = deepcopy(self.contract)
        contract["repository"] = old
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": old}):
            self.reject(contract, "outside the protected catalog identity map")

    def test_unregistered_owner_cannot_reuse_the_stable_id(self):
        contract = deepcopy(self.contract)
        contract["repository"] = "unapproved-owner/" + self.repository.split("/")[1]
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": contract["repository"]}):
            self.reject(contract, "outside the protected catalog identity map")

    def test_contract_name_must_match_github_event(self):
        contract = deepcopy(self.contract)
        contract["repository"] = self.repository.replace("appolon1908/", "appolon1908-hue/")
        self.reject(contract, "repository identity mismatch")

    def test_swapped_application_id_is_rejected(self):
        wrong_id = next(identity for identity in IDENTITIES if identity != self.contract["repository_id"])
        contract = deepcopy(self.contract)
        contract["repository_id"] = wrong_id
        self.reject(contract, "stable repository ID mismatch")

    def test_github_event_id_must_match_contract(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY_ID": "1"}):
            self.reject(self.contract, "stable repository ID mismatch")

    def test_transfer_does_not_grant_runtime_mutation(self):
        contract = deepcopy(self.contract)
        contract["runtime_mutation_authority"] = True
        self.reject(contract, "runtime mutation authority contradicts")

    def test_transfer_does_not_enable_live_effects(self):
        contract = deepcopy(self.contract)
        contract["safety"]["live_email_delivery"] = True
        self.reject(contract, "every external/live effect must remain disabled")

    def test_transfer_does_not_unbind_required_checks(self):
        contract = deepcopy(self.contract)
        contract["required_check_app_id"] = 1
        self.reject(contract, "required checks must be bound to GitHub Actions")

    def test_repository_transfer_does_not_implicitly_transfer_image_authority(self):
        contract = deepcopy(self.contract)
        contract["artifact_policy"]["image_repositories"] = ["ghcr.io/" + self.repository]
        self.reject(contract, "artifact image policy contradicts")


class BackendPostgresFixtureTests(unittest.TestCase):
    """Only the exact, isolated CI service fixture receives a configuration pin."""
    path = ".github/workflows/backend-postgres.yml"

    def setUp(self):
        self.workflow = (ROOT / self.path).read_text(encoding="utf-8")
        self.environment = patch.dict(os.environ, {"GITHUB_REPOSITORY": "appolon1908/backend2"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_exact_fixture_is_bound_and_has_no_runtime_commands(self):
        self.assertTrue(VALIDATOR["job_executable_configuration_approved"](self.workflow, self.path))
        self.assertFalse(VALIDATOR["workflow_has_runtime_mutation"](self.workflow, self.path))

    def test_any_fixture_byte_change_loses_the_configuration_pin(self):
        self.assertFalse(VALIDATOR["job_executable_configuration_approved"](self.workflow + "\n# drift\n", self.path))
        self.assertTrue(VALIDATOR["workflow_has_runtime_mutation"](self.workflow + "\n# drift\n", self.path))

    def test_image_change_is_rejected(self):
        changed = self.workflow.replace("image: postgres:16-alpine", "image: unreviewed.example/postgres:latest")
        self.assertNotEqual(changed, self.workflow)
        self.assertTrue(VALIDATOR["workflow_has_runtime_mutation"](changed, self.path))

    def test_runner_authority_change_is_rejected(self):
        changed = self.workflow.replace("runs-on: ubuntu-24.04", "runs-on: self-hosted")
        self.assertTrue(VALIDATOR["workflow_has_runtime_mutation"](changed, self.path))

    def test_configuration_pin_does_not_transfer_to_another_repository(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "appolon1908/codestra"}):
            self.assertFalse(VALIDATOR["job_executable_configuration_approved"](self.workflow, self.path))
            self.assertTrue(VALIDATOR["workflow_has_runtime_mutation"](self.workflow, self.path))

    def test_configuration_pin_does_not_transfer_to_another_path(self):
        self.assertFalse(VALIDATOR["job_executable_configuration_approved"](self.workflow, ".github/workflows/unreviewed.yml"))
        self.assertTrue(VALIDATOR["workflow_has_runtime_mutation"](self.workflow, ".github/workflows/unreviewed.yml"))

    def test_fixture_is_hosted_read_only_synthetic_and_not_activated(self):
        parsed = VALIDATOR["yaml"].safe_load(self.workflow)
        self.assertEqual(parsed["permissions"], {"contents": "read"})
        job = parsed["jobs"]["postgres-regression"]
        self.assertEqual(job["runs-on"], "ubuntu-24.04")
        self.assertEqual(job["env"]["DJANGO_SETTINGS_MODULE"], "CORE.leadconnector_pg_test_settings")
        self.assertEqual(job["env"]["LEADCONNECTOR_ENABLED"], "false")
        self.assertEqual(job["env"]["LC_PG_HOST"], "localhost")
        self.assertNotIn("environment", job)
        self.assertNotIn("secrets.", self.workflow)
        self.assertNotIn("volumes", job["services"]["postgres"])


if __name__ == "__main__":
    unittest.main()
