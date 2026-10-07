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


if __name__ == "__main__":
    unittest.main()
