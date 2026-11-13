#!/usr/bin/env python3
"""
Decode a Token Status List (TSL) JWT per
draft-ietf-oauth-status-list (https://datatracker.ietf.org/doc/draft-ietf-oauth-status-list/)

The `lst` field is base64url-encoded ZLIB-compressed bytes (RFC 1950/1951).
Each entry uses `bits` bits (1, 2, 4 or 8), packed LSB-first within each byte.

Usage:
    python3 decode_status_list.py <jwt> [idx] [--quiet|-q]

    No idx   → full summary
    With idx → check that credential index
    --quiet  → silent mode, useful in scripts

Exit codes (quiet mode with idx):
    0 = VALID
    1 = INVALID
    2 = SUSPENDED
    3 = APPLICATION_SPECIFIC
    4 = out of range / error
"""

import base64
import json
import sys
import zlib


def decode_jwt(token: str) -> tuple[dict, dict, list[str]]:
    """Decode a JWT, returning (header, payload, parts).
    Accepts partial JWTs (header.payload only)."""
    parts = token.split(".")
    if len(parts) < 2:
        raise ValueError("Not a valid JWT (expected header.payload[.signature])")

    def b64url_decode(s: str) -> bytes:
        s = s.replace("-", "+").replace("_", "/")
        s += "=" * (4 - len(s) % 4) if len(s) % 4 else ""
        return base64.b64decode(s)

    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))
    return header, payload, parts


def unpack_statuses(raw: bytes, bits: int) -> list[int]:
    """Unpack status values from already-decompressed bytes."""
    bytes_per_status = 8 // bits
    bit_mask = (1 << bits) - 1

    statuses = []
    total_statuses = len(raw) * bytes_per_status

    for i in range(total_statuses):
        byte_idx = (i * bits) // 8
        bit_offset = (i * bits) % 8
        val = (raw[byte_idx] >> bit_offset) & bit_mask
        statuses.append(val)

    return statuses


STATUS_NAMES: dict[int, str] = {
    0: "VALID",
    1: "INVALID",
    2: "SUSPENDED",
    3: "APPLICATION_SPECIFIC",
}


def status_label(value: int, bits: int) -> str:
    name = STATUS_NAMES.get(value)
    if name:
        return f"0x{value:0{bits // 4 + 1}x} ({name})"
    return f"0x{value:0{bits // 4 + 1}x}"


def try_decompress(lst_raw: bytes) -> bytes | None:
    """Try to decompress ZLIB data, with fallbacks for truncated streams."""
    try:
        return zlib.decompress(lst_raw)
    except zlib.error:
        pass

    try:
        d = zlib.decompressobj()
        result = d.decompress(lst_raw)
        if d.unused_data:
            return result
        return result
    except zlib.error:
        pass

    try:
        return zlib.decompress(lst_raw, -15)
    except zlib.error:
        pass

    for strip in range(4, 256, 4):
        if len(lst_raw) < strip:
            break
        try:
            return zlib.decompress(lst_raw[:-strip])
        except zlib.error:
            continue

    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Example: python3 decode_status_list.py <jwt_token>")
        print("Example: python3 decode_status_list.py <jwt_token> 42  # check entry 42")
        print("Example: python3 decode_status_list.py <jwt_token> 42 --quiet  # silent: exit 0=VALID, 1=INVALID")
        sys.exit(1)

    quiet = "--quiet" in sys.argv or "-q" in sys.argv
    token = sys.argv[1]
    args = [a for a in sys.argv[1:] if a not in ("--quiet", "-q")]
    idx_filter: int | None = None
    if len(args) > 1:
        idx_filter = int(args[1])

    # --- Decode JWT ---
    header, payload, jwt_parts = decode_jwt(token)

    sub = payload.get("sub", "(no sub)")
    iat = payload.get("iat", "?")
    exp = payload.get("exp", None)
    status_list = payload["status_list"]
    bits = status_list["bits"]
    lst_b64 = status_list["lst"]

    if not quiet:
        jwt_part_count = len(jwt_parts)
        print("=" * 60)
        print("Token Status List (TSL) — Decoded")
        print("=" * 60)
        print(f"  JWT parts : {jwt_part_count}/3 {'(missing signature, decoding anyway)' if jwt_part_count < 3 else '(full)'}")
        print(f"  algorithm : {header.get('alg', '?')}")
        print(f"  subject   : {sub}")
        print(f"  issued at : {iat}  ({iat_to_date(iat)})")
        print(f"  expires   : {exp_to(exp)}")
        print(f"  bits/entry: {bits}  →  {1 << bits} possible values")
        print()

    # --- Decode lst ---
    lst_raw = b64url_decode(lst_b64)

    if not quiet:
        print(f"  lst b64url chars : {len(lst_b64)}")
        print(f"  lst raw bytes    : {len(lst_raw)}")
        print(f"  raw header       : {lst_raw[:8].hex()}")
        expected_header = "78da"
        if lst_raw[:2].hex() == expected_header:
            print(f"  ✓ Valid ZLIB header ({expected_header})")
        else:
            print(f"  ✗ Unexpected header (expected {expected_header})")

    # --- Decompress ---
    decompressed = try_decompress(lst_raw)

    if decompressed is None:
        if quiet:
            print("ERROR: ZLIB decompression failed", file=sys.stderr)
        else:
            print("\n  ✗ ZLIB decompression failed completely.")
            print("  Possible causes:")
            print("    1. The lst value was truncated")
            print("    2. The data is corrupted")
            print("    3. Non-standard compression was used")
        sys.exit(1)

    if not quiet:
        print()
        print(f"  ✓ Decompressed: {len(decompressed)} bytes")

    # --- Unpack ---
    statuses = unpack_statuses(decompressed, bits)
    total_entries = len(statuses)

    if not quiet:
        print(f"  total entries    : {total_entries:,}")
        print(f"  bytes per entry  : {8 // bits}")
        print()

    if idx_filter is not None:
        if 0 <= idx_filter < total_entries:
            val = statuses[idx_filter]
            label = STATUS_NAMES.get(val, f"unknown({val})")
            print(f"Entry #{idx_filter}: {label}")
            sys.exit(0 if val == 0 else (4 if val not in STATUS_NAMES else val))
        else:
            if quiet:
                print(f"ERROR: entry {idx_filter} out of range (0..{total_entries - 1})", file=sys.stderr)
            else:
                print(f"Entry #{idx_filter} is out of range (0..{total_entries - 1})")
            sys.exit(4)
        return

    # --- Summary ---
    if not quiet:
        counts: dict[int, int] = {}
        for s in statuses:
            counts[s] = counts.get(s, 0) + 1

        print("--- Summary ---")
        for val in sorted(counts):
            label = status_label(val, bits)
            pct = 100 * counts[val] / total_entries if total_entries else 0
            print(f"  {label:30s}: {counts[val]:>12,}  ({pct:.2f}%)")
        print()

        def show_range(label: str, start: int, end: int):
            print(f"--- {label} ---")
            for i in range(start, end):
                print(f"  [{i:>6d}] {status_label(statuses[i], bits)}")
            print()

        if total_entries <= 200:
            show_range("All entries", 0, total_entries)
        else:
            show_range("First 50 entries", 0, 50)
            show_range("Last 50 entries", total_entries - 50, total_entries)


def b64url_decode(s: str) -> bytes:
    """Base64url decode with proper padding."""
    s = s.replace("-", "+").replace("_", "/")
    s += "=" * (4 - len(s) % 4) if len(s) % 4 else ""
    return base64.b64decode(s)


def iat_to_date(ts: int) -> str:
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(ts)


def exp_to(exp: int | None) -> str:
    if exp is None:
        return "(not set)"
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(exp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return str(exp)


if __name__ == "__main__":
    main()
