# eol-scout

Audit line-ending consistency across files or an entire project directory. It reports style totals and lists files mixing CRLF, LF, and CR line endings without printing file contents.

```sh
python eol_scout.py .
python eol_scout.py src README.md
```

Directory scans are recursive, skip `.git`, `.hg`, and `.svn` metadata directories, and do not follow symbolic links. Files are read in fixed-size chunks. UTF-16/32 BOM files are counted separately because their line breaks are not ASCII byte sequences; NUL-containing files without those BOMs are marked as a binary hint. No files are changed and no third-party packages are needed.

Exit status is `1` when mixed line endings are found, `2` when a path cannot be scanned, and `0` when the scan completes without mixed line endings.

## License

MIT
