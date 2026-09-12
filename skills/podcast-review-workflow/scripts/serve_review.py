#!/usr/bin/env python3
"""Serve local review files with HTTP byte-range support."""
from __future__ import annotations

import argparse
import os
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class RangeRequestHandler(SimpleHTTPRequestHandler):
    byte_range: tuple[int, int] | None = None

    def send_head(self):
        self.byte_range = None
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            source = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None
        stat, size = os.fstat(source.fileno()), os.fstat(source.fileno()).st_size
        start, end, status = 0, size - 1, 200
        header = self.headers.get("Range")
        if header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
            if not match:
                source.close(); self.send_error(416, "Invalid byte range"); return None
            first, last = match.groups()
            if first:
                start, end = int(first), min(int(last), size - 1) if last else size - 1
            elif last:
                start = max(0, size - int(last))
            if start > end or start >= size:
                source.close(); self.send_response(416); self.send_header("Content-Range", f"bytes */{size}"); self.end_headers(); return None
            status, self.byte_range = 206, (start, end)
        self.send_response(status)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Last-Modified", self.date_time_string(stat.st_mtime))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        return source

    def copyfile(self, source, outputfile):
        try:
            if self.byte_range is None:
                return super().copyfile(source, outputfile)
            start, end = self.byte_range
            source.seek(start)
            remaining = end - start + 1
            while remaining:
                chunk = source.read(min(256 * 1024, remaining))
                if not chunk: break
                outputfile.write(chunk); remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir(): raise NotADirectoryError(root)
    handler = partial(RangeRequestHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {root} at http://{args.host}:{args.port}/")
    print("Press Control-C to stop")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__":
    main()
