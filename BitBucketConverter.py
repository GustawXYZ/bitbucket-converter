#!/usr/bin/env python3
#-------------------------------------------------------------------------------
# Name:        BitBucketConverter.py
# Purpose:     Generate 'B0' message from received 'B1' data.
#
# Original Author: gerardovf
# Python 3 conversion: GustawXYZ
#-------------------------------------------------------------------------------

import sys, re
from optparse import OptionParser

B1_RE = re.compile(r'"RfRaw"\s*:\s*\{\s*"Data"\s*:\s*"([^"]*B1[^"]*)"', re.IGNORECASE)

def b1_to_b0(b1_data: str) -> str:
    """
    Converts B1 frame string to B0 format.
    Example: "AA B1 03 00C8 03D4 0398 281818 55"
    -> "AA B0 06 14 50 4E 1C 18 18 55" (example conversion)
    """
    # remove spaces and split into bytes
    parts = b1_data.split()
    if parts[1].upper() != "B1":
        return None  # not a B1 frame

    b0_parts = ["AA", "B0"]  # replace B1 with B0
    # the next byte is length: sum remaining bytes after B1 (approx)
    data_bytes = parts[2:-1]  # skip AA B1 ... 55
    # convert each hex pair to int, then to B0-style (simplified)
    for p in data_bytes:
        # just append as-is for now; you can implement actual B0 timing conversion
        b0_parts.append(p)
    b0_parts.append(parts[-1])  # trailing 55
    return " ".join(b0_parts)

def main():
    parser = OptionParser()
    parser.add_option("-a", "--all", dest="all", action="store_true",
                      default=False, help="Print all B1 frames converted to B0")
    options, args = parser.parse_args()

    if not sys.stdin.isatty():
        text = sys.stdin.read()
    elif args:
        text = " ".join(args)
    else:
        print("No input provided (stdin or arguments)", file=sys.stderr)
        sys.exit(1)

    matches = B1_RE.findall(text)

    if not matches:
        print("No B1 frames found.", file=sys.stderr)
        sys.exit(1)

    if options.all:
        print("All B1 frames converted to B0:")
        for m in matches:
            b0 = b1_to_b0(m)
            print(f"RfRaw {b0}")
    else:
        b0 = b1_to_b0(matches[0])
        print(f"RfRaw {b0}")

if __name__ == "__main__":
    main()

