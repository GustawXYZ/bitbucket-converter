#!/usr/bin/env python3
#-------------------------------------------------------------------------------
# Name:        BitBucketConverter.py
# Purpose:     Generate 'B0' message from received 'B1' data.
#
# Original Author: gerardovf
# Python 3 conversion: GustawXYZ
#-------------------------------------------------------------------------------

import sys
import re
from collections import Counter
from optparse import OptionParser

RFRAW_RE = re.compile(
    r'"RfRaw"\s*:\s*\{\s*"Data"\s*:\s*"([^"]+)"',
    re.IGNORECASE
)


def extract_rfraw(text):
    return [
        m.group(1).replace(" ", "").upper()
        for m in RFRAW_RE.finditer(text)
    ]


def similarity(a, b):
    return sum(1 for x, y in zip(a, b) if x == y)


def pick_best(candidates):
    counts = Counter(candidates)
    best, freq = counts.most_common(1)[0]
    if freq > 1:
        return best

    scores = {}
    for c in candidates:
        scores[c] = sum(similarity(c, o) for o in candidates if o != c)
    return max(scores, key=scores.get)


def convert_b1_to_b0(b1, repeat):
    elems = b1.split()
    if elems[1] != "B1":
        raise ValueError("Not a B1 frame")

    bucket_count = int(elems[2])
    out = "AAB0xx"
    out += elems[2]
    out += f"{repeat:02X}"

    for i in range(bucket_count):
        out += elems[i + 3]

    out += elems[bucket_count + 3]
    out += elems[bucket_count + 4]

    length = (len(out) // 2) - 4
    return out.replace("xx", f"{length:02X}")


def main():
    usage = "usage: %prog [options] [<tasmota-logs>]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-r", "--repeat",
        dest="repeat",
        type="int",
        default=20,
        help="Repeat count for B0 (default: 20)"
    )

    options, args = parser.parse_args()

    if args:
        text = args[0]
    else:
        text = sys.stdin.read()

    rfraws = extract_rfraw(text)
    if not rfraws:
        print("No RfRaw Data found", file=sys.stderr)
        sys.exit(1)

    # Keep only B1 frames
    b1s = []
    for r in rfraws:
        spaced = " ".join(r[i:i+2] for i in range(0, len(r), 2))
        if " B1 " in f" {spaced} ":
            b1s.append(spaced)

    if not b1s:
        print("No B1 frames found (cannot convert)", file=sys.stderr)
        sys.exit(1)

    best = pick_best(b1s)
    b0 = convert_b1_to_b0(best, options.repeat)

    print(f"RfRaw {b0}")


if __name__ == "__main__":
    main()

