# eol-scout

Count CRLF, LF, and CR line endings, report common byte-order marks, and flag mixed newline styles without printing file contents.

```sh
python eol_scout.py README.md data.csv
```

Files are scanned in fixed-size chunks, so memory use stays bounded for large inputs. A NUL-byte indicator can help spot binary data; it is only a hint. The tool does not decode, convert, or modify files and has no third-party dependencies.

## License

MIT
