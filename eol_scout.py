#!/usr/bin/env python3
"""Audit line-ending consistency across files and project directories."""

import argparse
import os
from pathlib import Path
import sys


CHUNK_SIZE = 64 * 1024
BOMS = (
    (b"\x00\x00\xfe\xff", "UTF-32 BE"),
    (b"\xff\xfe\x00\x00", "UTF-32 LE"),
    (b"\xef\xbb\xbf", "UTF-8"),
    (b"\xfe\xff", "UTF-16 BE"),
    (b"\xff\xfe", "UTF-16 LE"),
)
VCS_DIRS = {".git", ".hg", ".svn"}


def files_under(inputs, errors, skipped):
    seen = set()

    def add(path):
        key = os.path.normcase(os.path.abspath(os.fspath(path)))
        if key not in seen:
            seen.add(key)
            return True
        return False

    def walk_error(error):
        errors.append(str(error))

    for root in inputs:
        if root.is_symlink():
            skipped.append(root)
        elif root.is_file():
            if add(root):
                yield root
        elif root.is_dir():
            for current, directories, names in os.walk(root, topdown=True, followlinks=False, onerror=walk_error):
                kept = []
                for name in sorted(directories):
                    child = Path(current) / name
                    if name in VCS_DIRS:
                        continue
                    if child.is_symlink():
                        skipped.append(child)
                    else:
                        kept.append(name)
                directories[:] = kept
                for name in sorted(names):
                    path = Path(current) / name
                    if path.is_symlink():
                        skipped.append(path)
                    elif path.is_file() and add(path):
                        yield path
        else:
            errors.append(f"{root}: not a regular file or directory")


def inspect(path):
    byte_count = crlf = lf = cr = 0
    prefix = bytearray()
    previous_cr = False
    nul = False
    with path.open("rb") as source:
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            byte_count += len(chunk)
            if len(prefix) < 4:
                prefix.extend(chunk[:4 - len(prefix)])
            nul = nul or b"\x00" in chunk
            chunk_crlf = chunk.count(b"\r\n")
            chunk_lf = chunk.count(b"\n") - chunk_crlf
            chunk_cr = chunk.count(b"\r") - chunk_crlf
            if previous_cr and chunk.startswith(b"\n"):
                chunk_crlf += 1
                chunk_lf -= 1
                chunk_cr -= 1
            crlf += chunk_crlf
            lf += chunk_lf
            cr += chunk_cr
            previous_cr = chunk.endswith(b"\r")

    bom = next((label for marker, label in BOMS if prefix.startswith(marker)), "none")
    if bom.startswith(("UTF-16", "UTF-32")):
        style = "wide-text"
    elif nul:
        style = "nul-hint"
    else:
        kinds = sum(count > 0 for count in (crlf, lf, cr))
        style = "mixed" if kinds > 1 else next(
            (name for name, count in (("CRLF", crlf), ("LF", lf), ("CR", cr)) if count),
            "no-endings",
        )
    return {
        "bytes": byte_count,
        "crlf": crlf,
        "lf": lf,
        "cr": cr,
        "bom": bom,
        "style": style,
    }


def main():
    parser = argparse.ArgumentParser(description="Recursively audit line-ending styles in files and directories.")
    parser.add_argument("paths", nargs="+", type=Path, help="files or directory trees to inspect")
    args = parser.parse_args()

    counts = {name: 0 for name in ("CRLF", "LF", "CR", "mixed", "no-endings", "wide-text", "nul-hint")}
    boms = {}
    errors = []
    skipped = []
    mixed_files = []
    scanned = 0
    total_bytes = 0
    for path in files_under(args.paths, errors, skipped):
        try:
            result = inspect(path)
        except OSError as error:
            errors.append(f"{path}: {error}")
            continue
        scanned += 1
        total_bytes += result["bytes"]
        counts[result["style"]] += 1
        if result["style"] == "mixed":
            mixed_files.append(path)
        if result["bom"] != "none":
            boms[result["bom"]] = boms.get(result["bom"], 0) + 1

    print(f"Scanned {scanned} file(s), {total_bytes} byte(s).")
    for name, count in counts.items():
        print(f"  {name}: {count}")
    if boms:
        print("BOMs: " + ", ".join(f"{name}={count}" for name, count in sorted(boms.items())))
    if mixed_files:
        print("Files with mixed ASCII line endings:")
        for path in mixed_files:
            print(f"  {path}")
    else:
        print("No files with mixed ASCII line endings.")
    if skipped:
        print(f"Skipped {len(skipped)} symbolic link(s).")
    for error in errors:
        print(f"eol-scout: {error}", file=sys.stderr)
    if errors:
        return 2
    return int(bool(mixed_files))


if __name__ == "__main__":
    raise SystemExit(main())
