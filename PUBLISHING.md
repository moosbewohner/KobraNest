# GitHub upload checklist

## Source repository

Suggested repository name: **KobraNest**. Original project code is licensed GPL-3.0-only. The repository is intentionally source-only; runtime archives and Windows executables are excluded.

1. Create an empty GitHub repository named KobraNest in your own account.
2. Use this directory as the local repository. Configure your own Git author identity before making the initial commit.
3. Inspect staged files, commit, add the exact GitHub repository URL as origin and push main.
4. Keep private backups, device settings and SSH keys outside Git.

## Binary release

The separate `KobraNest-S1-v0.1.8.zip` is the complete installation package tested on the reference device. The `.sha256` alongside it verifies the download. GitHub's automatic source ZIP is not that installer.

Track corresponding-source and license provisioning for redistributed Debian packages and statically linked dependencies. `docs/BUILD.md` and THIRD_PARTY.md describe existing provenance and the remaining gap. Do not describe it as a broad hardware-certified stable release; the project has been tested on one reference printer.

Known runtime limitation: ECM enumeration can require a printer restart after rebooting only the Pi. The project remains tested on a reference S1; this is not broad hardware certification.

Public repository: https://github.com/moosbewohner/KobraNest

The complete installer and signed update/setup assets are published together as release v0.1.8. The source-provisioning gap above remains documented; publishing the preview does not resolve it.

Signed releases: build optional/updater/build.py, then build_complete.py. Never commit private signing keys. The workflow creates drafts and requires an explicitly configured signing secret. The Windows executable must be rebuilt whenever assistant.py/installer.py/recovery.py change. Publish the complete installer, complete setup ZIP, both TARs, hashes and signed catalog together.
