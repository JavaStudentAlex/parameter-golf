#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path


def verify_log(log_path: Path, require_wallclock_cap: bool = False) -> bool:
    if not log_path.exists():
        print(f"Error: Log file not found at {log_path}")
        return False

    content = log_path.read_text()

    # 1. Verify final_int8_zlib_roundtrip_exact
    roundtrip_match = re.search(r"final_int8_zlib_roundtrip_exact\s+val_loss:([\d\.]+)\s+val_bpb:([\d\.]+)", content)
    if not roundtrip_match:
        print("Error: Missing 'final_int8_zlib_roundtrip_exact' line.")
        return False
    val_loss = float(roundtrip_match.group(1))
    val_bpb = float(roundtrip_match.group(2))
    print(f"✅ Found roundtrip metric: val_loss={val_loss}, val_bpb={val_bpb}")

    # 2. Verify Total submission size int8+zlib
    # Match "Total submission size int8+zlib: 15863489 bytes" or "Total submission size: 67272625 bytes"
    # We prefer the int8+zlib one if available
    size_matches = re.findall(r"Total submission size(?: int8\+zlib)?:\s+(\d+)\s+bytes", content)
    if not size_matches:
        print("Error: Missing 'Total submission size' line.")
        return False
    
    # Check if any of the sizes are within limit (prioritizing compressed if multiple)
    sizes = [int(s) for s in size_matches]
    total_size = min(sizes) # For verification, the smallest claimed size is the "total submission size" in the compressed path
    
    MAX_SIZE = 16_000_000
    if total_size > MAX_SIZE:
        print(f"❌ Total submission size {total_size} exceeds limit of {MAX_SIZE} bytes.")
        return False
    print(f"✅ Total submission size: {total_size} bytes (within 16MB limit)")

    # 3. Optional: Verify wallclock-cap proof
    if require_wallclock_cap:
        wallclock_match = re.search(r"stopping_early: wallclock_cap", content)
        if not wallclock_match:
            print("Error: Missing 'stopping_early: wallclock_cap' line (required by --require-wallclock-cap).")
            return False
        print("✅ Found wallclock-cap proof.")

    return True


def main():
    parser = argparse.ArgumentParser(description="Verify training log for challenge compliance.")
    parser.add_argument("log_file", type=Path, help="Path to the training log file.")
    parser.add_argument("--require-wallclock-cap", action="store_true", help="Require proof of wallclock cap early stop.")

    args = parser.parse_args()

    if verify_log(args.log_file, args.require_wallclock_cap):
        print("🚀 Log verification PASSED.")
        sys.exit(0)
    else:
        print("❌ Log verification FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
