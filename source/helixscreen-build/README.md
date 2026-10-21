# KobraNest HelixScreen build

Source: https://github.com/Kobra-S1/helixscreen/tree/kobrian
Pinned commit: 67ecd2597f63d29b727a74d679ffcb3dbc848fd3
Upstream version: 1.1.0-beta.10 (branch build, not the upstream stable release).
Target: pi32-fbdev, ARMv7 armhf, Debian trixie (KobraNest), plain framebuffer.

Build on an ARM64 or AMD64 Linux host with Docker:

```sh
git clone --branch kobrian --recurse-submodules https://github.com/Kobra-S1/helixscreen.git source
cd source
git checkout 67ecd2597f63d29b727a74d679ffcb3dbc848fd3
git submodule update --init --recursive
cd ..
docker build -t kobranest/helix-armhf:trixie .
docker run --rm -v "$PWD/source":/src -w /src kobranest/helix-armhf:trixie sh -c 'make PLATFORM_TARGET=pi32-fbdev HELIX_PACKAGING=1 SKIP_OPTIONAL_DEPS=1 && make PLATFORM_TARGET=pi32-fbdev HELIX_PACKAGING=1 SKIP_OPTIONAL_DEPS=1 gen-images gen-splash-3d-pi32 gen-printer-images release-pi32-fbdev'
```

Run while the build host is idle, with sufficient memory and disk space. The Makefile selects compilation parallelism. This Dockerfile supports native ARM64/AMD64 build hosts and adapts the target runtime to Debian trixie; it is not a general replacement for the upstream Bullseye cross toolchain.

The KobraNest archive retains the upstream release files and adds a bin/helix-screen-fbdev symlink to bin/helix-screen for the existing S1 supervisor, plus kobranest-build.json. No upstream C++ sources are modified. The matching source archive includes submodule sources and upstream patches. Runtime startup sets HELIX_DIAGNOSTIC_UPLOADS=0; fresh settings disable telemetry, animation, screensaver and application sounds. The independent KobraNest startup melody remains unchanged.

Use KobraNest's display installer, not the upstream installer, for the BusyBox-based S1 system. The KobraNest installer preserves existing settings and backs up a recognized old release under /var/backups/kobrian-display before upgrading. Unknown releases and missing runtime libraries are rejected.

Upstream code remains GPL-3.0-or-later with its original notices and third-party licenses. See the included upstream LICENSE and source tree.
