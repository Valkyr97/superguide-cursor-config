#!/usr/bin/env python3
"""
Bokún sandbox E2E smoke test.

Usage:
    BOKUN_ACCESS_KEY=xxx BOKUN_SECRET_KEY=yyy BOKUN_PRODUCT_ID=418 BOKUN_OPTION_ID=11608 \
        python scripts/bokun_e2e_smoke.py

    BOKUN_ACCESS_KEY=xxx BOKUN_SECRET_KEY=yyy BOKUN_PRODUCT_ID=418 BOKUN_OPTION_ID=11608 \
        python scripts/bokun_e2e_smoke.py --dry-run

Required env vars:
    BOKUN_ACCESS_KEY   32-hex access key (hyphens optional; normalized at runtime)
    BOKUN_SECRET_KEY   32-hex secret key (hyphens optional; normalized at runtime)
    BOKUN_PRODUCT_ID   Numeric Bokún activity ID to test against
    BOKUN_OPTION_ID    Numeric Bokún rate ID to test against

Optional env vars:
    BOKUN_API_URL      Default: https://api.bokuntest.com
    BOKUN_TEST_DATE    YYYY-MM-DD; default: today + 30 days
"""

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Shared-layer path injection — works from any cwd
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "msg-lambda-layers" / "layers" / "shared"))

# ---------------------------------------------------------------------------
# Config from environment
# ---------------------------------------------------------------------------
ACCESS_KEY = os.environ.get("BOKUN_ACCESS_KEY", "")
SECRET_KEY = os.environ.get("BOKUN_SECRET_KEY", "")
API_URL = os.environ.get("BOKUN_API_URL", "https://api.bokuntest.com")
PRODUCT_ID = os.environ.get("BOKUN_PRODUCT_ID", "")
OPTION_ID = os.environ.get("BOKUN_OPTION_ID", "")
TEST_DATE = os.environ.get(
    "BOKUN_TEST_DATE",
    (date.today() + timedelta(days=30)).strftime("%Y-%m-%d"),
)

REQUIRED_VARS = {
    "BOKUN_ACCESS_KEY": ACCESS_KEY,
    "BOKUN_SECRET_KEY": SECRET_KEY,
    "BOKUN_PRODUCT_ID": PRODUCT_ID,
    "BOKUN_OPTION_ID": OPTION_ID,
}

_SEP = "::"  # matches _TOKEN_DELIM in bokun.py


def _pp(label: str, obj) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(json.dumps(obj, indent=2, default=str))


def _check_env() -> None:
    missing = [k for k, v in REQUIRED_VARS.items() if not v]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def _build_api_key() -> str:
    """Pack ACCESS_KEY::SECRET_KEY — mirrors BokunProvider.get_api_key."""
    # Normalize: strip hyphens and lowercase (matches _normalize_bokun_access_key)
    ak = ACCESS_KEY.strip().replace("-", "").lower()
    sk = SECRET_KEY.strip().replace("-", "").lower()
    return f"{ak}{_SEP}{sk}"


# ---------------------------------------------------------------------------
# Smoke steps
# ---------------------------------------------------------------------------

def step1_fetch_availability(provider, api_key: str) -> dict:
    """Fetch availability slots and return the first bookable raw slot."""
    print(f"\n[STEP 1] fetch_availability  product={PRODUCT_ID}  option={OPTION_ID}  date={TEST_DATE}")
    slots = provider.fetch_availability(
        product_id=PRODUCT_ID,
        option_id=OPTION_ID,
        local_date_start=TEST_DATE,
        local_date_end=TEST_DATE,
        api_key=api_key,
        api_url=API_URL,
    )
    print(f"  → {len(slots)} slot(s) returned")
    if not slots:
        print("[WARN] No slots returned for the given date. Try a different BOKUN_TEST_DATE.")
        sys.exit(0)

    first_slot = slots[0]
    _pp("First raw slot", first_slot)

    canonical = provider.map_availability_to_canonical(
        first_slot,
        experience_id="smoke-test-experience",
        experience_option_id=None,
        supplier_id="smoke-test-supplier",
    )
    _pp("Canonical slot", canonical)

    provider_slot_id = canonical.get("provider_slot_id") or first_slot.get("id")
    print(f"\n  → provider_slot_id: {provider_slot_id!r}")
    return first_slot


def _first_pricing_category_id(slot: dict) -> str:
    """Extract the first pricingCategoryId from pricesByRate."""
    prices_by_rate = slot.get("pricesByRate") or []
    if not prices_by_rate:
        # Fall back to OPTION_ID as a numeric category if no price data
        return OPTION_ID
    per_category = prices_by_rate[0].get("pricePerCategoryUnit") or []
    if not per_category:
        return OPTION_ID
    return str(per_category[0].get("id", OPTION_ID))


def step2_create_booking(provider, api_key: str, slot: dict) -> str:
    """Reserve the booking; return confirmationCode."""
    provider_slot_id = slot.get("id", "")
    unit_code = _first_pricing_category_id(slot)
    print(f"\n[STEP 2] create_booking  slot={provider_slot_id!r}  unit_code={unit_code!r}")

    raw_response = provider.create_booking(
        product_id=PRODUCT_ID,
        option_id=OPTION_ID,
        availability_id=provider_slot_id,
        unit_items=[{"unit_code": unit_code, "quantity": 1}],
        api_key=api_key,
        api_url=API_URL,
        contact={
            "firstName": "Smoke",
            "lastName": "Test",
            "email": "smoke@superguide.dev",
            "phoneNumber": "+34600000000",
        },
        answers=[],
    )
    _pp("Raw create_booking response", raw_response)

    canonical = provider.map_booking_to_canonical(raw_response, supplier_id="smoke-test-supplier")
    _pp("Canonical booking", {
        "provider_uuid": canonical.get("provider_uuid"),
        "status": canonical.get("status"),
    })

    confirmation_code = canonical.get("provider_uuid")
    if not confirmation_code:
        raise ValueError("No confirmationCode in create_booking response")
    print(f"\n  → confirmation_code: {confirmation_code!r}")
    return confirmation_code


def step3_get_booking(provider, api_key: str, confirmation_code: str) -> None:
    """Retrieve the booking and print its canonical status."""
    print(f"\n[STEP 3] get_booking  confirmation_code={confirmation_code!r}")
    canonical = provider.get_booking(
        provider_booking_id=confirmation_code,
        api_key=api_key,
        api_url=API_URL,
    )
    print(f"  → status: {canonical.get('status')!r}")
    _pp("Canonical get_booking", {
        "provider_uuid": canonical.get("provider_uuid"),
        "status": canonical.get("status"),
    })


def step4_cancel_booking(provider, api_key: str, confirmation_code: str) -> None:
    """Cancel the booking and print the final status (expect 'cancelled')."""
    print(f"\n[STEP 4] cancel_booking  confirmation_code={confirmation_code!r}")
    canonical = provider.cancel_booking(
        provider_booking_id=confirmation_code,
        api_key=api_key,
        api_url=API_URL,
        reason="Smoke test teardown",
    )
    final_status = canonical.get("status")
    print(f"  → final status: {final_status!r}")
    if final_status != "cancelled":
        print(f"[WARN] Expected 'cancelled' but got {final_status!r}. Verify cancel response shape.")
    else:
        print("  ✓ Booking successfully cancelled")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bokún sandbox E2E smoke test — exercises the full booking lifecycle."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only run Step 1 (availability fetch); skip reserve/get/cancel.",
    )
    args = parser.parse_args()

    _check_env()

    from booking_providers.registry import get_provider  # noqa: PLC0415

    provider = get_provider("bokun")
    if provider is None:
        print("[ERROR] Could not load 'bokun' provider from registry.")
        sys.exit(1)

    api_key = _build_api_key()

    print("=" * 60)
    print("  Bokún E2E Smoke Test")
    print("=" * 60)
    print(f"  api_url    : {API_URL}")
    print(f"  product_id : {PRODUCT_ID}")
    print(f"  option_id  : {OPTION_ID}")
    print(f"  test_date  : {TEST_DATE}")
    print(f"  dry_run    : {args.dry_run}")

    # Step 1: always run
    try:
        slot = step1_fetch_availability(provider, api_key)
    except Exception as exc:
        print(f"\n[FAIL] Step 1 — fetch_availability: {exc}")
        sys.exit(1)

    if args.dry_run:
        print("\n[DRY RUN] Steps 2–4 skipped.")
        sys.exit(0)

    # Step 2: reserve
    try:
        confirmation_code = step2_create_booking(provider, api_key, slot)
    except Exception as exc:
        print(f"\n[FAIL] Step 2 — create_booking: {exc}")
        sys.exit(1)

    # Step 3: get booking (best-effort — don't abort cancel on failure)
    try:
        step3_get_booking(provider, api_key, confirmation_code)
    except Exception as exc:
        print(f"\n[WARN] Step 3 — get_booking failed (will still attempt cancel): {exc}")

    # Step 4: cancel (always attempt to avoid leaving dangling holds in sandbox)
    try:
        step4_cancel_booking(provider, api_key, confirmation_code)
    except Exception as exc:
        print(f"\n[FAIL] Step 4 — cancel_booking: {exc}")
        print(f"  Manually cancel confirmation code {confirmation_code!r} in the Bokún sandbox.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Smoke test PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
