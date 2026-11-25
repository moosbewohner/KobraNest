# Official HelixScreen payload

KobraNest now packages official HelixScreen v1.1.0, commit e82a1bb844794153f8c9d3f5f590a3f930463cb4, rather than compiling a branch snapshot on the Pi.

```sh
python3 source/helixscreen-build/package.py --output /path/to/cache
```

The script verifies the official ZIP, preserves all original file content and the native layout without extra binary aliases, and creates a reproducible wrapper tarball. `tested-build.json` records upstream URL, version, commit and SHA-256 values. The matching upstream source archive is in `payload/helixscreen-kobrian-source.tar.gz` (legacy filename retained). The Dockerfile is retained as an optional cross-compilation environment; it is not used to produce this official binary.

Upstream: https://github.com/prestonbrown/helixscreen/releases/tag/v1.1.0 . Retain upstream license/copyright notices. Source submodules and other component licensing remain governed by upstream and THIRD_PARTY.md.
