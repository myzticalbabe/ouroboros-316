#!/usr/bin/env python3
"""
COMPILE_BCC_990_JSON.PY — Research Data -> Structured Financial JSON
=====================================================================
Compiles all BCC financial data from FUNDING_REVIEW.html research into
structured JSON that the Azazael worm pipeline can ingest.

Data is hardcoded from verified FUNDING_REVIEW.html research (IRS Form 990,
FY2021-FY2025 via ProPublica Nonprofit Explorer). All amounts cross-referenced.

Output: filings/BCC_Complaint/bcc_990_fy2021_2025.json
        filings/BCC_Complaint/bcc_board_conflicts.json
        filings/BCC_Complaint/bcc_hud_grants.json

This is the CRITICAL MISSING PIECE — without this JSON, zero worms
can activate. Once built, DataPipelineWorm -> FeatureEngineer ->
RLTrainLoop -> DashboardGen pipeline runs end-to-end.

Stdlib only — no external dependencies.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path.home() / "Desktop" / "Libra" / "filings" / "BCC_Complaint"
OUTPUT_990 = OUTPUT_DIR / "bcc_990_fy2021_2025.json"
OUTPUT_CONFLICTS = OUTPUT_DIR / "bcc_board_conflicts.json"
OUTPUT_HUD = OUTPUT_DIR / "bcc_hud_grants.json"
OUTPUT_LAWSUIT = OUTPUT_DIR / "bcc_lawsuit.json"


# ---------------------------------------------------------------------------
# MAIN COMPILATION
# ---------------------------------------------------------------------------
def compile_990_data() -> dict:
    """Compile all 990 financial data from verified FUNDING_REVIEW.html research.
    
    All amounts cross-referenced against IRS Form 990 (FY2021-FY2025)
    as published on ProPublica Nonprofit Explorer (EIN 23-2043478).
    Schedule B (major donors) is redacted in public filings.
    """
    
    # =====================================================================
    # 5-YEAR REVENUE TABLE (FY2021-FY2025)
    # =====================================================================
    print("[1/6] Compiling 5-year revenue data...")
    
    fy_data = {
        "FY2025": {"revenue": 12494569, "program_service": 11778182, "contributions": 204333,
                    "investment_income": 446033, "net_income": -796924, "total_assets": 19800000,
                    "expenses": 13291493},
        "FY2024": {"revenue": 13641565, "program_service": 12369645, "contributions": 844835,
                    "investment_income": 412569, "net_income": 1352167},
        "FY2023": {"revenue": 13904040, "program_service": 13222659, "contributions": 401527,
                    "investment_income": 263459, "net_income": 1653195},
        "FY2022": {"revenue": 13462400, "program_service": 13131132, "contributions": 81297,
                    "investment_income": 119723, "net_income": None},
        "FY2021": {"revenue": 15171755, "program_service": 15084073, "contributions": 3615,
                    "investment_income": 40067, "net_income": None},
    }
    
    print(f"   Compiled {len(fy_data)} fiscal years")
    for fy, data in fy_data.items():
        print(f"   {fy}: Revenue=${data['revenue']:,}  Net=${data['net_income'] or 'N/A'}")

    # =====================================================================
    # FUNDING SOURCE BREAKDOWN
    # =====================================================================
    print("[2/6] Compiling funding source breakdown...")
    
    funding_sources = {
        "medicaid_medicare_insurance": {
            "fy2025": 11778182, "fy2024": 12369645, "fy2023": 13222659,
            "percent_of_total": 94.3,
            "risk": "EXTREME single-payer concentration",
            "note": "90-95% of all revenue from government health programs"
        },
        "samhsa_ccbhc_grant": {
            "grant_number": "H79SM088878",
            "total_obligation": 3944396,
            "initial_award": 982780,
            "growth_pct": 301,
            "cfda": "93.696",
            "awarded": "2023-09-30",
            "expires": "2027-09-29",
            "risk": "2-year grant cliff after Sept 2027"
        },
        "investment_income": {
            "fy2025": 446033, "fy2024": 412569, "fy2023": 263459,
            "fy2022": 119723, "fy2021": 40067,
            "growth_4yr": "11.14x",
            "risk": "Anomalous growth for behavioral health nonprofit"
        },
        "private_contributions": {
            "fy2025": 204333, "fy2024": 844835, "fy2023": 401527,
            "fy2022": 81297, "fy2021": 3615,
            "volatility": "23,228% swing (FY2021→FY2024)",
            "risk": "Schedule B redacted — major donors unknown"
        },
        "berks_county_hs": {
            "total_budget": 16200000,
            "breakdown": {
                "mental_health": 10100000,
                "developmental_disabilities": 3390000,
                "behavioral_health_drug_alcohol": 1840000,
                "homeless_hsdf": 900000
            },
            "bcc_share": "NOT PUBLICLY ITEMIZED",
            "residents_served": 15000
        },
        "hud_continuum_of_care": {
            "annual_estimated": 500000,
            "property_count": 8,
            "risk": "Grants span 2021-2024 — gaps between renewals possible"
        }
    }
    
    print(f"   Compiled {len(funding_sources)} funding sources")

    # =====================================================================
    # HUD PROPERTIES
    # =====================================================================
    print("[3/6] Compiling HUD property data...")
    
    hud_properties = [
        {"name": "1135/37 Franklin St.", "latest_grant": 288274, "year": 2024, "type": "PSH"},
        {"name": "BCC Leasing 1", "latest_grant": 203168, "year": 2021, "type": "Leasing"},
        {"name": "BCC Leasing 2", "latest_grant": 193072, "year": 2022, "type": "Leasing"},
        {"name": "New Hope PSH", "latest_grant": 204220, "year": 2021, "type": "PSH"},
        {"name": "13 S. 10th St.", "latest_grant": 87534, "year": 2021, "type": "PSH"},
        {"name": "239 S. 5th St.", "latest_grant": 123524, "year": 2021, "type": "PSH"},
        {"name": "PS Recovery Housing", "latest_grant": 105511, "year": 2021, "type": "Recovery"},
        {"name": "Phoenix House", "latest_grant": 59716, "year": 2021, "type": "PSH"},
    ]
    
    total_hud = sum(p["latest_grant"] for p in hud_properties)
    print(f"   Compiled {len(hud_properties)} HUD properties (${total_hud:,} total)")

    # =====================================================================
    # BOARD CONFLICTS
    # =====================================================================
    print("[4/6] Compiling board conflict data...")
    
    conflicts = [
        {
            "person": "Missy Orlando",
            "bcc_role": "Board Director",
            "external_org": "United Way of Berks County",
            "external_role": "Employee",
            "conflict_type": "FUNDER_EMPLOYMENT",
            "amount_at_stake": 678000,
            "description": "Board member employed by primary private funder ($678K MacKenzie Scott grant)",
            "severity": "HIGH",
            "irs_form_990_disclosure": "Part VI Section B — should be disclosed"
        },
        {
            "person": "Joseph Plageman Jr.",
            "bcc_role": "Board Chair",
            "external_org": "Edward Jones Investments",
            "external_role": "Employee",
            "conflict_type": "INVESTMENT_MANAGER_EMPLOYMENT",
            "amount_at_stake": 19800000,
            "description": "Board Chair works for firm potentially managing BCC's $19.8M portfolio",
            "severity": "CRITICAL",
            "irs_form_990_disclosure": "Schedule D + Part VI — asset management must be disclosed"
        },
        {
            "person": "Linda Krause",
            "bcc_role": "Board Director",
            "external_org": "Edward Jones Investments",
            "external_role": "Employee",
            "conflict_type": "INVESTMENT_MANAGER_EMPLOYMENT",
            "amount_at_stake": 19800000,
            "description": "SECOND board member from same investment firm — dual control concern",
            "severity": "CRITICAL",
            "irs_form_990_disclosure": "Two board members from same firm managing assets = red flag"
        },
        {
            "person": "Marcia Goodman-Hinnershitz",
            "bcc_role": "NOT BCC-AFFILIATED (Reading City Council, Dist 4)",
            "external_org": "Council on Chemical Abuse (COCA)",
            "external_role": "Director of Planning",
            "conflict_type": "OVERSIGHT_FUNDER_EMPLOYMENT",
            "amount_at_stake": None,
            "description": "City Council member works for COCA — a pass-through funder for BCC substance use disorder programs",
            "severity": "MEDIUM",
            "irs_form_990_disclosure": "Not BCC board — but dual oversight/funding role is governance concern"
        },
        {
            "person": "Christine Axford",
            "bcc_role": "CEO",
            "external_org": None,
            "external_role": None,
            "conflict_type": "COMPENSATION_ANOMALY",
            "amount_at_stake": None,
            "description": "CEO compensation LOWER than CFO — rare in nonprofit governance. Suggests unusual comp structure.",
            "severity": "MEDIUM",
            "irs_form_990_disclosure": "Schedule J — compensation must be justified"
        },
    ]
    
    print(f"   Compiled {len(conflicts)} governance conflicts/red flags")

    # =====================================================================
    # LAWSUIT DATA
    # =====================================================================
    print("[5/6] Compiling lawsuit data...")
    
    lawsuit = {
        "case_name": "Berks Counseling Center v. Community Care Behavioral Health Organization",
        "docket": "898 MDA 2017",
        "court": "Pennsylvania Superior Court",
        "year": 2017,
        "trigger": "2015 Fraud, Waste & Abuse (FWA) audit of BCC and Chester County satellite",
        "amount_at_stake": 105000,
        "amount_saved": 81000,
        "alleged_deficiency": "Missing supervisory physician signatures on initial assessments (55 Pa. Code § 1223.52)",
        "ruling": "BCC WON — court ruled CCBH improperly applied unexecuted updated FWA policy",
        "outcome": "CCBH forced to follow original 2011 agreement requiring progressive 'provider education'",
        "open_questions": [
            "Were documentation deficiencies ever resolved or just procedurally dismissed?",
            "Is the Chester County satellite still operating?",
            "Why did NONE of the 5 supervisory agencies catch this before Superior Court?",
            "Does this indicate a pattern of audit non-compliance?"
        ]
    }
    
    print(f"   Compiled 1 lawsuit (BCC v. Community Care, {lawsuit['docket']})")

    # =====================================================================
    # GOVERNANCE DATA
    # =====================================================================
    print("[6/6] Compiling governance metadata...")
    
    governance = {
        "organization": {
            "name": "Berks Counseling Center, Inc.",
            "ein": "23-2043478",
            "doing_business_as": "BCC",
            "address": "645 Penn Street, 2nd Floor, Reading, PA 19601-3543",
            "phone": "610-373-4281",
            "fax": "610-373-0250",
            "website": "berkscc.org",
            "ntee_code": "F32 — Community Mental Health Center",
            "subsection": "501(c)(3)"
        },
        "board": {
            "chair": "Joseph Plageman Jr.",
            "vice_chair": "Crystal Seitz",
            "secretary": None,
            "treasurer": None,
            "total_members": None,
            "independent_members": None,
            "conflicts_disclosed": "UNKNOWN — Schedule B redacted"
        },
        "key_employees": {
            "ceo": {"name": "Christine Axford", "title": "CEO", "email": "caxford@berkscc.org", "email_status": "SMTP_VERIFIED_DELIVERABLE"},
            "cfo": {"name": "Greg Little", "title": "CFO", "email": "glittle@berkscc.org", "email_status": "SMTP_VERIFIED_DELIVERABLE"}
        },
        "oversight_agencies": [
            {"name": "SAMHSA", "role": "CCBHC Grant Oversight", "grant": "H79SM088878", "budget": "~$8.1B", "staffing": "Lean — hiring freezes"},
            {"name": "PA OMHSAS", "role": "State behavioral health oversight", "audit_cycle": "1-3 years"},
            {"name": "Berks County Human Services", "role": "County contract monitoring", "budget": "$16.2M"},
            {"name": "PA Attorney General", "role": "Charitable Trusts & Organizations", "budget": "$174.4M", "caseload": "1,000+ matters"},
            {"name": "United Way of Berks County", "role": "3-year grant monitoring", "grant": "$678K"}
        ]
    }
    
    # =====================================================================
    # ASSEMBLE OUTPUT
    # =====================================================================
    output = {
        "_metadata": {
            "compiled_from": "FUNDING_REVIEW.html (verified research)",
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "compiled_by": "compile_bcc_990_json.py",
            "data_source": "IRS Form 990 (FY2021-FY2025) via ProPublica Nonprofit Explorer",
            "ein": "23-2043478",
            "note": "All amounts cross-referenced against FUNDING_REVIEW.html research. Schedule B (major donors) redacted in public filings."
        },
        "fiscal_years": fy_data,
        "funding_sources": funding_sources,
        "hud_properties": hud_properties,
        "board_conflicts": conflicts,
        "lawsuit": lawsuit,
        "governance": governance
    }
    
    return output


# ---------------------------------------------------------------------------
# WRITE OUTPUT FILES
# ---------------------------------------------------------------------------
def write_json(data: dict, path: Path, label: str):
    """Write JSON to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    size = path.stat().st_size
    print(f"   [{label}] -> {path.name} ({size:,} bytes)")


def main():
    print("=" * 70)
    print("  COMPILE_BCC_990_JSON.PY — Research Data -> Structured JSON")
    print("=" * 70)
    print()
    
    data = compile_990_data()
    
    if not data:
        print("[FATAL] No data extracted.")
        return 1
    
    print()
    print("=" * 70)
    print("  WRITING OUTPUT FILES")
    print("=" * 70)
    
    # Full 990 dataset
    write_json(data, OUTPUT_990, "990_FULL")
    
    # Conflicts subset
    conflicts_data = {
        "_metadata": data["_metadata"],
        "conflicts": data["board_conflicts"]
    }
    write_json(conflicts_data, OUTPUT_CONFLICTS, "CONFLICTS")
    
    # HUD subset
    hud_data = {
        "_metadata": data["_metadata"],
        "properties": data["hud_properties"],
        "total_annual_estimated": sum(p["latest_grant"] for p in data["hud_properties"])
    }
    write_json(hud_data, OUTPUT_HUD, "HUD")
    
    # Lawsuit subset
    lawsuit_data = {
        "_metadata": data["_metadata"],
        "lawsuit": data["lawsuit"]
    }
    write_json(lawsuit_data, OUTPUT_LAWSUIT, "LAWSUIT")
    
    print()
    print("=" * 70)
    print("  COMPILATION COMPLETE")
    print("=" * 70)
    print(f"  {len(data['fiscal_years'])} fiscal years compiled")
    print(f"  {len(data['funding_sources'])} funding sources mapped")
    print(f"  {len(data['hud_properties'])} HUD properties catalogued")
    print(f"  {len(data['board_conflicts'])} governance conflicts flagged")
    print()
    print(f"  OUTPUT: {OUTPUT_990}")
    print()
    print("  NEXT: python activate_bcc_analysis.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
