#!/usr/bin/env python3
"""Count line endings and inspect byte-order marks without printing file contents."""

import argparse
from pathlib import Path
import sys


BOMS = (
    (b"\x00\x00\xfe\xff", "UTF-32 BE"),
    (b"\xff\xfe\x00\x00", "UTF-32 LE"),
    (b"\xef\xbb\xbf", "UTF-8"),
    (b"\xfe\xff", "UTF-16 BE"),
    (b"\xff\xfe", "UTF-16 LE"),
)


def inspect(path):
    total = crlf = lf = cr = 0
    prefix = bytearray()
    last = None
    pending_cr = False
    nul = False
    with path.open("rb") as source:
        while True:
            block = source.read(65536)
            if not block:
                break
            total += len(block)
            if len(prefix) < 4:
                prefix.extend(block[:4 - len(prefix)])
            nul = nul or b"\x00" in block
            index = 0
            if pending_cr:
                if block[0] == 10:
                    crlf += 1
                    index = 1
                else:
                    cr += 1
                pending_cr = False
            while index < len(block):
                if block[index] != 13:
                    if block[index] == 10:
                        lf += 1
                    index += 1
                elif index + 1 == len(block):
                    pending_cr = True
                    index += 1
                elif block[index + 1] == 10:
                    crlf += 1
                    index += 2
                else:
                    cr += 1
                    index += 1
            last = block[-1]
    if pending_cr:
        cr += 1

    bom = next((label for marker, label in BOMS if prefix.startswith(marker)), "none")
    endings = sum(count > 0 for count in (crlf, lf, cr))
    lines = [f"{path}: {total} bytes; BOM: {bom}; NUL present: {'yes' if nul else 'no'}"]
    lines.append(f"  CRLF: {crlf}; LF: {lf}; CR: {cr}; mixed endings: {'yes' if endings > 1 else 'no'}")
    if last is None:
        lines.append("  Ends with line break: n/a (empty file)")
    else:
        lines.append(f"  Ends with line break: {'yes' if last in (10, 13) else 'no'}")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Inspect line endings and BOMs in local files.")
    parser.add_argument("files", nargs="+", type=Path, help="files to scan")
    args = parser.parse_args()
    failed = False
    for path in args.files:
        try:
            if not path.is_file():
                raise OSError("not a file")
            print("\n".join(inspect(path)))
        except OSError as error:
            print(f"eol-scout: {path}: {error}", file=sys.stderr)
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
