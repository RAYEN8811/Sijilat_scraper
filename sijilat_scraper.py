#!/usr/bin/env python3
"""
Bahrain Sijilat Commercial Registration (CR) Scraper Prototype
Author: Autonomous Prototype Engineer (Pair Programming with User)
Registry: Ministry of Industry and Commerce (MOIC) - Sijilat (sijilat.bh)

Collects structured business information for Bahraini commercial entities,
including commercial name (EN/AR), CR number & branch identifiers, registration
status, business activities (ISIC), and commercial address.

Strictly distinguishes between fields absent from the source and fields that
could not be extracted/retrieved.
"""

import sys
import json
import time
import hmac
import hashlib
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

# Sijilat Official Endpoints and Public Client Auth Constants
DEFAULT_PORTAL_BASE = "https://www.sijilat.bh"
DEFAULT_API_BASE = "https://api.sijilat.bh"
DEFAULT_TOKEN_URL = f"{DEFAULT_API_BASE}/token"
DEFAULT_DETAILS_URL = f"{DEFAULT_API_BASE}/api/CRdetails/CompleteCRDetails"

# Public Client Credentials from Sijilat Frontend (config.js)
CLIENT_USERNAME = "sijilat"
CLIENT_SECRET_KEY = b"UHxNtYMRYwvfpO1dS5pWLKL0M2DgOj40EbN4SoBWgfc"
CLIENT_PASSWORD_SEED = b"sijilat_test"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


class ProvenanceStatus:
    RETRIEVED = "RETRIEVED"
    ABSENT_FROM_SOURCE = "ABSENT_FROM_SOURCE"
    EXTRACTION_ERROR = "EXTRACTION_ERROR"


def classify_field(value: Any) -> Dict[str, Any]:
    """
    Classifies a data field according to whether it was present with data,
    or absent from the source payload (null or empty string).
    """
    if value is None:
        return {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE}
    
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned or cleaned.upper() == "N/A" or cleaned == "-":
            return {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE}
        return {"value": cleaned, "provenance": ProvenanceStatus.RETRIEVED}
    
    if isinstance(value, (list, dict)):
        if not value:
            return {"value": value, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE}
        return {"value": value, "provenance": ProvenanceStatus.RETRIEVED}

    return {"value": value, "provenance": ProvenanceStatus.RETRIEVED}


class SijilatClient:
    """Client for interacting with the Kingdom of Bahrain's Sijilat public registry."""

    def __init__(self, api_base: str = DEFAULT_API_BASE, timeout: int = 15):
        self.api_base = api_base.rstrip("/")
        self.token_url = f"{self.api_base}/token"
        self.details_url = f"{self.api_base}/api/CRdetails/CompleteCRDetails"
        self.timeout = timeout
        self._cached_token: Optional[str] = None
        self._token_expiry_timestamp: float = 0.0

    def get_public_token(self) -> str:
        """
        Obtains a public client JWT access token via client password grant.
        Credentials are authenticated using HMAC-SHA256 as required by Sijilat API.
        """
        current_time = time.time()
        if self._cached_token and current_time < self._token_expiry_timestamp - 30:
            return self._cached_token

        # Compute HMAC-SHA256 signature
        encrypted_pass = hmac.new(CLIENT_SECRET_KEY, CLIENT_PASSWORD_SEED, hashlib.sha256).hexdigest()

        data = urllib.parse.urlencode({
            "username": CLIENT_USERNAME,
            "password": encrypted_pass,
            "grant_type": "password"
        }).encode("utf-8")

        req = urllib.request.Request(
            self.token_url,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": USER_AGENT,
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            token = body.get("access_token")
            expires_in = body.get("expires_in", 3600)
            if not token:
                raise ValueError("Authentication response did not contain access_token.")
            self._cached_token = token
            self._token_expiry_timestamp = current_time + expires_in
            return token

    def fetch_raw_cr_details(self, cr_no: str, branch_no: str = "1", lang: str = "EN") -> Dict[str, Any]:
        """
        Directly queries the CompleteCRDetails endpoint for a given CR number and branch number.
        """
        token = self.get_public_token()

        payload = {
            "cr_no": str(cr_no).strip(),
            "branch_no": str(branch_no).strip(),
            "cult_lang": lang.upper()
        }

        req = urllib.request.Request(
            self.details_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "*/*",
                "Authorization": f"Bearer {token}",
                "User-Agent": USER_AGENT
            }
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data


def parse_commercial_address(addr_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extracts and normalizes commercial address fields with provenance tracking."""
    if not addr_data or not isinstance(addr_data, dict):
        # Commercial address section completely missing or null in source
        return {
            "flat_or_shop": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "building": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "road": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "road_name": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "block": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "town": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "po_box": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "email": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "mobile_phone": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "telephone": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "fax": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "website": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "estore_url": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE},
            "full_formatted_address": {"value": None, "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE}
        }

    flat = classify_field(addr_data.get("CR_FLAT"))
    building = classify_field(addr_data.get("CR_BULD"))
    road = classify_field(addr_data.get("CR_ROAD"))
    road_nm = classify_field(addr_data.get("CR_ROAD_NM"))
    block = classify_field(addr_data.get("CR_BLOCK"))
    town = classify_field(addr_data.get("CR_TOWN_NM"))
    po_box = classify_field(addr_data.get("CR_PBOX"))
    email = classify_field(addr_data.get("CR_EMAIL"))
    mobile = classify_field(addr_data.get("CR_NAT_MOBILE"))
    tel = classify_field(addr_data.get("CR_NAT_PHONE_BIS"))
    fax = classify_field(addr_data.get("CR_NAT_FAX"))
    website = classify_field(addr_data.get("CR_URL"))
    estore = classify_field(addr_data.get("ESTORE_URL"))

    # Synthesize human-readable address line
    parts = []
    if building["value"]:
        parts.append(f"Building {building['value']}")
    if flat["value"] and flat["value"] != "0":
        parts.append(f"Flat/Shop {flat['value']}")
    if road["value"]:
        parts.append(f"Road {road['value']}" + (f" ({road_nm['value']})" if road_nm['value'] else ""))
    if block["value"]:
        parts.append(f"Block {block['value']}")
    if town["value"]:
        parts.append(town["value"])

    full_addr = ", ".join(parts) if parts else None

    return {
        "flat_or_shop": flat,
        "building": building,
        "road": road,
        "road_name": road_nm,
        "block": block,
        "town": town,
        "po_box": po_box,
        "email": email,
        "mobile_phone": mobile,
        "telephone": tel,
        "fax": fax,
        "website": website,
        "estore_url": estore,
        "full_formatted_address": classify_field(full_addr)
    }


def parse_business_activities(act_list: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Extracts and formats registered business activities and ISIC classifications."""
    if act_list is None:
        return {"value": [], "provenance": ProvenanceStatus.ABSENT_FROM_SOURCE, "count": 0}

    normalized = []
    for item in act_list:
        normalized.append({
            "activity_code": item.get("ACT_CD"),
            "isic4_code": item.get("ISIC4_CD"),
            "isic4_parent_code": item.get("ISIC4_ORI_CD"),
            "activity_name": item.get("ISIC4_NM"),
            "activity_description": (item.get("ISIC4_DETL") or "").strip()
        })

    provenance = ProvenanceStatus.RETRIEVED if normalized else ProvenanceStatus.ABSENT_FROM_SOURCE
    return {
        "value": normalized,
        "provenance": provenance,
        "count": len(normalized)
    }


def parse_branch_detail(
    cr_no: str,
    branch_no: str,
    raw_json_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parses a single branch details response from CompleteCRDetails.
    """
    summary = raw_json_data.get("company_summary") or {}
    addr_raw = raw_json_data.get("commercialAddress")
    activities_raw = raw_json_data.get("businessActivities")

    # Commercial Names
    cr_lnm = classify_field(summary.get("CR_LNM"))
    cr_anm = classify_field(summary.get("CR_ANM"))
    cr_group_lnm = classify_field(summary.get("CR_GRP_LNM"))
    cr_group_anm = classify_field(summary.get("CR_GRP_ANM"))

    # Status
    status = classify_field(summary.get("STATUS"))
    status_color = classify_field(summary.get("STATUS_COLOR"))
    reg_date = classify_field(summary.get("REG_DATE"))
    expire_date = classify_field(summary.get("EXPIRE_DATE"))
    company_type = classify_field(summary.get("CM_TYP_DESC"))
    company_type_code = classify_field(summary.get("CM_TYP_CD"))
    bcci_expire_date = classify_field(summary.get("BCCI_EXPIRE_DATE"))

    # Capital & Financial
    fin_year_end = classify_field(summary.get("FN_YEAR_END"))
    nationality = classify_field(summary.get("CR_NAT"))

    return {
        "cr_number": cr_no,
        "branch_identifier": branch_no,
        "commercial_name": {
            "english": cr_lnm,
            "arabic": cr_anm,
            "group_english": cr_group_lnm,
            "group_arabic": cr_group_anm
        },
        "legal_form": {
            "type_description": company_type,
            "type_code": company_type_code,
            "nationality": nationality
        },
        "registration_status": {
            "status": status,
            "status_color": status_color,
            "registration_date": reg_date,
            "expiry_date": expire_date,
            "bcci_expiry_date": bcci_expire_date,
            "financial_year_end": fin_year_end
        },
        "commercial_address": parse_commercial_address(addr_raw),
        "business_activities": parse_business_activities(activities_raw)
    }


def extract_cr_record(
    client: SijilatClient,
    cr_no: str,
    requested_branch: Optional[str] = None,
    collect_all_branches: bool = False,
    simulate_failure: bool = False
) -> Dict[str, Any]:
    """
    Main extraction coordinator:
    - Queries Sijilat for the target business.
    - Discovers all associated branches and keeps each identifiable.
    - Captures timestamp, source URL, and processing outcome.
    - Distinguishes absent source data from extraction/retrieval failures.
    """
    start_time = time.time()
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    source_url = f"{DEFAULT_PORTAL_BASE}/public-search-cr/search-cr-3.aspx?cr_no={cr_no}&branch_no={requested_branch or '1'}"

    # Handle explicitly simulated failure case
    if simulate_failure:
        elapsed = round(time.time() - start_time, 4)
        return {
            "metadata": {
                "cr_number": str(cr_no),
                "requested_branch": requested_branch,
                "source_url": source_url,
                "api_endpoint": client.details_url,
                "collection_timestamp_utc": timestamp_utc,
                "processing_outcome": "SIMULATED_FAILURE",
                "is_simulated": True,
                "simulation_notes": "Explicitly simulated network connection timeout/server error for testing resilience.",
                "branches_found_count": 0,
                "branches_extracted_count": 0,
                "elapsed_seconds": elapsed
            },
            "error_details": {
                "error_type": "SimulatedUpstreamTimeout",
                "error_message": "SIMULATED: Connection to https://api.sijilat.bh timed out after 15.0s",
                "provenance": ProvenanceStatus.EXTRACTION_ERROR
            },
            "branches": []
        }

    try:
        # Fetch initial branch (default 1)
        initial_branch = requested_branch or "1"
        raw_res = client.fetch_raw_cr_details(cr_no=cr_no, branch_no=initial_branch)

        # Check for "No Data Found"
        if raw_res.get("Code") == "S001" or not raw_res.get("jsonData"):
            elapsed = round(time.time() - start_time, 4)
            return {
                "metadata": {
                    "cr_number": str(cr_no),
                    "requested_branch": requested_branch,
                    "source_url": source_url,
                    "api_endpoint": client.details_url,
                    "collection_timestamp_utc": timestamp_utc,
                    "processing_outcome": "NOT_FOUND",
                    "is_simulated": False,
                    "branches_found_count": 0,
                    "branches_extracted_count": 0,
                    "elapsed_seconds": elapsed
                },
                "branches": []
            }

        json_data = raw_res.get("jsonData", {})
        all_branches_raw = json_data.get("otherbranchlist") or []
        total_branches_count = len(all_branches_raw) if all_branches_raw else 1

        # Catalog of all identified branches
        branch_catalog = []
        for b in all_branches_raw:
            branch_catalog.append({
                "cr_number": b.get("CR_NO"),
                "branch_identifier": b.get("BRANCH_NO"),
                "branch_name": b.get("CR_NAME"),
                "status": b.get("STATUS"),
                "registration_date": b.get("REG_DATE"),
                "expiry_date": b.get("EXPIRE_DATE")
            })

        extracted_branches = []

        # Parse the initial branch details
        branch_1_detail = parse_branch_detail(cr_no, initial_branch, json_data)
        extracted_branches.append(branch_1_detail)

        # If user requested all branches, fetch remaining branches
        if collect_all_branches and all_branches_raw:
            for b_info in all_branches_raw:
                b_num = str(b_info.get("BRANCH_NO", "")).strip()
                if not b_num or b_num == initial_branch:
                    continue
                try:
                    b_raw = client.fetch_raw_cr_details(cr_no=cr_no, branch_no=b_num)
                    b_json = b_raw.get("jsonData", {})
                    if b_json:
                        b_detail = parse_branch_detail(cr_no, b_num, b_json)
                        extracted_branches.append(b_detail)
                except Exception as b_err:
                    # Incomplete data on individual branch is tracked gracefully
                    extracted_branches.append({
                        "cr_number": cr_no,
                        "branch_identifier": b_num,
                        "extraction_status": ProvenanceStatus.EXTRACTION_ERROR,
                        "error_message": str(b_err)
                    })

        elapsed = round(time.time() - start_time, 4)
        return {
            "metadata": {
                "cr_number": str(cr_no),
                "requested_branch": requested_branch,
                "source_url": source_url,
                "api_endpoint": client.details_url,
                "collection_timestamp_utc": timestamp_utc,
                "processing_outcome": "SUCCESS",
                "is_simulated": False,
                "branches_found_count": total_branches_count,
                "branches_extracted_count": len(extracted_branches),
                "elapsed_seconds": elapsed
            },
            "branch_catalog": branch_catalog,
            "branches": extracted_branches
        }

    except urllib.error.HTTPError as http_err:
        elapsed = round(time.time() - start_time, 4)
        return {
            "metadata": {
                "cr_number": str(cr_no),
                "requested_branch": requested_branch,
                "source_url": source_url,
                "api_endpoint": client.details_url,
                "collection_timestamp_utc": timestamp_utc,
                "processing_outcome": "FAILED",
                "is_simulated": False,
                "branches_found_count": 0,
                "branches_extracted_count": 0,
                "elapsed_seconds": elapsed
            },
            "error_details": {
                "error_type": "HTTPError",
                "http_status": http_err.code,
                "error_message": str(http_err),
                "provenance": ProvenanceStatus.EXTRACTION_ERROR
            },
            "branches": []
        }
    except Exception as exc:
        elapsed = round(time.time() - start_time, 4)
        return {
            "metadata": {
                "cr_number": str(cr_no),
                "requested_branch": requested_branch,
                "source_url": source_url,
                "api_endpoint": client.details_url,
                "collection_timestamp_utc": timestamp_utc,
                "processing_outcome": "FAILED",
                "is_simulated": False,
                "branches_found_count": 0,
                "branches_extracted_count": 0,
                "elapsed_seconds": elapsed
            },
            "error_details": {
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "provenance": ProvenanceStatus.EXTRACTION_ERROR
            },
            "branches": []
        }


def main():
    parser = argparse.ArgumentParser(
        description="Bahrain Commercial Registration (Sijilat) Data Collection Prototype"
    )
    parser.add_argument(
        "--cr",
        type=str,
        default="48602",
        help="Commercial Registration Number (default: 48602 - BAPCO REFINING B.S.C CLOSED)"
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="1",
        help="Specific Branch Identifier (default: 1)"
    )
    parser.add_argument(
        "--all-branches",
        action="store_true",
        help="Collect complete details for all discovered branches of the CR"
    )
    parser.add_argument(
        "--simulate-failure",
        action="store_true",
        help="Simulate an upstream network or extraction failure for testing"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional file path to save output JSON"
    )

    args = parser.parse_args()

    client = SijilatClient()
    result = extract_cr_record(
        client=client,
        cr_no=args.cr,
        requested_branch=args.branch,
        collect_all_branches=args.all_branches,
        simulate_failure=args.simulate_failure
    )

    formatted_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        import os
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_json)
        print(f"[OK] Extracted data saved to: {args.output}")
        print(f"     CR: {result['metadata']['cr_number']} | Outcome: {result['metadata']['processing_outcome']} | Branches: {result['metadata']['branches_extracted_count']}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(formatted_json)


if __name__ == "__main__":
    main()
