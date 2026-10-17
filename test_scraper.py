#!/usr/bin/env python3
"""
Automated Test Suite for Sijilat Commercial Registration Scraper
"""

import unittest
from sijilat_scraper import (
    SijilatClient,
    classify_field,
    extract_cr_record,
    ProvenanceStatus
)


class TestSijilatScraper(unittest.TestCase):
    """Test suite for Sijilat data extraction and classification."""

    def setUp(self):
        self.client = SijilatClient()

    def test_field_provenance_classification(self):
        """Verify field classification into RETRIEVED vs ABSENT_FROM_SOURCE."""
        # Non-empty strings
        retrieved_str = classify_field("BAPCO")
        self.assertEqual(retrieved_str["value"], "BAPCO")
        self.assertEqual(retrieved_str["provenance"], ProvenanceStatus.RETRIEVED)

        # Null / None
        null_res = classify_field(None)
        self.assertIsNone(null_res["value"])
        self.assertEqual(null_res["provenance"], ProvenanceStatus.ABSENT_FROM_SOURCE)

        # Empty or whitespace string
        empty_res = classify_field("   ")
        self.assertIsNone(empty_res["value"])
        self.assertEqual(empty_res["provenance"], ProvenanceStatus.ABSENT_FROM_SOURCE)

        # Placeholders
        na_res = classify_field("N/A")
        self.assertIsNone(na_res["value"])
        self.assertEqual(na_res["provenance"], ProvenanceStatus.ABSENT_FROM_SOURCE)

        dash_res = classify_field("-")
        self.assertIsNone(dash_res["value"])
        self.assertEqual(dash_res["provenance"], ProvenanceStatus.ABSENT_FROM_SOURCE)

    def test_client_token_acquisition(self):
        """Verify public client authentication and JWT retrieval from Sijilat API."""
        token = self.client.get_public_token()
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)
        self.assertTrue(token.startswith("eyJ"))

    def test_live_extraction_cr_48602(self):
        """Verify live extraction for target business: BAPCO REFINING (CR 48602)."""
        result = extract_cr_record(self.client, cr_no="48602", requested_branch="1")
        meta = result.get("metadata", {})
        self.assertEqual(meta.get("processing_outcome"), "SUCCESS")
        self.assertEqual(meta.get("cr_number"), "48602")
        self.assertFalse(meta.get("is_simulated"))
        self.assertEqual(meta.get("branches_found_count"), 13)

        # Check Branch Details
        branches = result.get("branches", [])
        self.assertEqual(len(branches), 1)
        b1 = branches[0]

        # Commercial Name
        name_en = b1["commercial_name"]["english"]
        self.assertEqual(name_en["value"], "BAPCO REFINING B.S.C CLOSED")
        self.assertEqual(name_en["provenance"], ProvenanceStatus.RETRIEVED)

        # Status
        status = b1["registration_status"]["status"]
        self.assertEqual(status["value"], "UNDER MORTGAGE")
        self.assertEqual(status["provenance"], ProvenanceStatus.RETRIEVED)

        # Address
        addr = b1["commercial_address"]
        self.assertEqual(addr["building"]["value"], "245")
        self.assertEqual(addr["town"]["value"], "AWALI")
        self.assertEqual(addr["po_box"]["provenance"], ProvenanceStatus.ABSENT_FROM_SOURCE)

        # Business Activities
        acts = b1["business_activities"]
        self.assertEqual(acts["count"], 3)
        self.assertEqual(acts["provenance"], ProvenanceStatus.RETRIEVED)
        self.assertTrue(any("4661-5" in a["isic4_code"] for a in acts["value"]))

    def test_not_found_live_query(self):
        """Verify handling of non-existent CR number (negative case)."""
        result = extract_cr_record(self.client, cr_no="999999999", requested_branch="1")
        meta = result.get("metadata", {})
        self.assertEqual(meta.get("processing_outcome"), "NOT_FOUND")
        self.assertEqual(len(result.get("branches", [])), 0)

    def test_simulated_failure_case(self):
        """Verify handling and clear metadata tagging of simulated failure."""
        result = extract_cr_record(self.client, cr_no="48602", simulate_failure=True)
        meta = result.get("metadata", {})
        self.assertEqual(meta.get("processing_outcome"), "SIMULATED_FAILURE")
        self.assertTrue(meta.get("is_simulated"))
        self.assertIn("error_details", result)
        self.assertEqual(result["error_details"]["provenance"], ProvenanceStatus.EXTRACTION_ERROR)

    def test_repeat_run_consistency(self):
        """Verify that repeat runs yield identical business data (idempotency)."""
        res1 = extract_cr_record(self.client, cr_no="48602", requested_branch="1")
        res2 = extract_cr_record(self.client, cr_no="48602", requested_branch="1")

        self.assertEqual(res1["branches"], res2["branches"])
        self.assertEqual(res1["branch_catalog"], res2["branch_catalog"])


if __name__ == "__main__":
    unittest.main()
