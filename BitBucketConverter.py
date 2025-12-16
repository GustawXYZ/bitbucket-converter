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
from optparse import OptionParser
from collections import Counter

B1_RE = re.compile(r'"RfRaw"\s*:\s*\{\s*"Data"\s*:\s*"([^"]*B1[^"]*)"', re.IGNORECASE)

def b1_to_b0(b1_data: str, repeat_val: int = 20) -> tuple:
    """
    Converts B1 frame string to B0 format and generates A8 command.
    Returns tuple: (b0_command, a8_command, debug_info)
    """
    parts = b1_data.split()
    
    if len(parts) < 4 or parts[1].upper() != "B1":
        return None, None, "Not a valid B1 frame"
    
    # Extract components
    num_buckets = int(parts[2], 16)
    
    # Build B0 command
    b0_parts = ["AA", "B0", "xx", parts[2]]  # xx is placeholder for length
    b0_parts.append(f"{repeat_val:02X}")
    
    # Add buckets
    for i in range(num_buckets):
        b0_parts.append(parts[3 + i])
    
    # Add data section
    data_section = parts[3 + num_buckets]
    b0_parts.append(data_section)
    b0_parts.append(parts[3 + num_buckets + 1])  # trailing part
    
    # Calculate length (total bytes / 2 - 4 for header/footer)
    b0_str = "".join(b0_parts)
    length = len(b0_str) // 2 - 4
    b0_str = b0_str.replace("xx", f"{length:02X}")
    
    # Format B0 with spaces
    b0_formatted = " ".join([b0_str[i:i+2] for i in range(0, len(b0_str), 2)])
    
    # Parse data section for A8 command
    data_len = len(data_section)
    str_first = data_section[0]
    str_last = data_section[-1]
    str_middle = data_section[1:-1]
    
    # Extract nibble pairs
    nibbles = [str_middle[i:i+2] for i in range(0, len(str_middle), 2)]
    
    # Decode bits (12 = 0, 21 = 1)
    bits = []
    for nibble in nibbles:
        if nibble == "12":
            bits.append("0")
        elif nibble == "21":
            bits.append("1")
    
    # Convert bits to hex digits (groups of 4)
    hex_data = ""
    for i in range(0, len(bits), 4):
        if i + 3 < len(bits):
            bit_group = "".join(bits[i:i+4])
            hex_data += f"{int(bit_group, 2):X}"
    
    # Build A8 command
    sync_high = parts[3 + 3]  # bucket 3
    sync_low = parts[3]        # bucket 0
    bit_high_time = parts[3 + 2]  # bucket 2
    bit_low_time = parts[3 + 1]   # bucket 1
    
    # Calculate duty cycles
    high_val = int(bit_high_time, 16)
    low_val = int(bit_low_time, 16)
    total = high_val + low_val
    
    if total > 0:
        bit_high_duty = f"{int((high_val / total) * 100):02X}"
        bit_low_duty = f"{int((low_val / total) * 100):02X}"
    else:
        bit_high_duty = "32"
        bit_low_duty = "32"
    
    sync_bit_count = 0
    bit_count = len(bits) + sync_bit_count
    bit_count_hex = f"{bit_count:02X}"
    
    # Assemble A8 data
    a8_data = [
        "7F",
        sync_high,
        sync_low,
        bit_high_time,
        bit_high_duty,
        bit_low_time,
        bit_low_duty,
        bit_count_hex,
        hex_data
    ]
    
    a8_str = "".join(a8_data)
    a8_len = len(a8_str) // 2
    a8_formatted = " ".join(a8_data)
    a8_command = f"AA A8 {a8_len:02X} {a8_formatted} 55"
    
    # Debug info
    debug_info = {
        "sync": f"{str_last}{str_first}",
        "data_nibbles": " ".join(nibbles),
        "bits": "".join(bits),
        "hex_data": hex_data,
        "sync_high": sync_high,
        "sync_low": sync_low,
        "bit_high_time": bit_high_time,
        "bit_high_duty": f"{bit_high_duty} ({int(bit_high_duty, 16)}%)",
        "bit_low_time": bit_low_time,
        "bit_low_duty": f"{bit_low_duty} ({int(bit_low_duty, 16)}%)",
        "bit_count": f"{bit_count_hex} ({bit_count})"
    }
    
    return b0_formatted, a8_command, debug_info

def main():
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 0.3")
    parser.add_option("-a", "--all", dest="all", action="store_true",
                      default=False, help="Print all B1 frames converted to B0")
    parser.add_option("-r", "--repeat", dest="repeat", type="int",
                      default=20, help="number of times to repeat (default: 20)")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
                      default=False, help="show debug info")
    
    options, args = parser.parse_args()

    # Read input
    if not sys.stdin.isatty():
        text = sys.stdin.read()
    elif args:
        text = " ".join(args)
    else:
        print("No input provided (stdin or arguments)", file=sys.stderr)
        print("Usage: cat log.txt | python3 BitBucketConverter.py", file=sys.stderr)
        print("   or: python3 BitBucketConverter.py 'AA B1 05 ...'", file=sys.stderr)
        sys.exit(1)

    # Find all B1 frames
    matches = B1_RE.findall(text)

    if not matches:
        print("No B1 frames found.", file=sys.stderr)
        sys.exit(1)

    if options.all:
        # Print all frames
        print(f"Found {len(matches)} B1 frame(s)\n")
        for idx, m in enumerate(matches, 1):
            b0, a8, debug = b1_to_b0(m, options.repeat)
            if b0:
                print(f"Frame {idx}:")
                print(f"RfRaw {b0}")
                if options.debug:
                    print(f"\nDebug info:")
                    for key, val in debug.items():
                        print(f"  {key}: {val}")
                print(f"\n{a8}\n")
                print("-" * 60)
    else:
        # Find most common Data section (everything after buckets)
        data_sections = []
        for m in matches:
            parts = m.split()
            if len(parts) >= 4 and parts[1].upper() == "B1":
                num_buckets = int(parts[2], 16)
                if len(parts) > 3 + num_buckets:
                    # Extract data section (the long hex string)
                    data_sections.append(parts[3 + num_buckets])
        
        if data_sections:
            # Count occurrences
            counter = Counter(data_sections)
            most_common_data, count = counter.most_common(1)[0]
            
            # Find first frame with this data
            for m in matches:
                parts = m.split()
                if len(parts) >= 4:
                    num_buckets = int(parts[2], 16)
                    if len(parts) > 3 + num_buckets:
                        if parts[3 + num_buckets] == most_common_data:
                            print(f"Most common data pattern (appeared {count} time(s)):\n")
                            b0, a8, debug = b1_to_b0(m, options.repeat)
                            if b0:
                                print(f"RfRaw {b0}")
                                if options.debug:
                                    print(f"\nDebug info:")
                                    for key, val in debug.items():
                                        print(f"  {key}: {val}")
                                print(f"\n{a8}")
                            break
        else:
            # Fallback to first frame
            b0, a8, debug = b1_to_b0(matches[0], options.repeat)
            if b0:
                print(f"RfRaw {b0}")
                if options.debug:
                    print(f"\nDebug info:")
                    for key, val in debug.items():
                        print(f"  {key}: {val}")
                print(f"\n{a8}")

if __name__ == "__main__":
    main()