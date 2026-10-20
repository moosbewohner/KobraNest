# GitHub upload checklist

## Source repository

Suggested repository name: **KobraNest**. Original project code is licensed GPL-3.0-only. The repository is intentionally source-only; runtime archives and Windows executables are excluded.

1. Create an empty GitHub repository named KobraNest in your own account.
2. Use this directory as the local repository. Configure your own Git author identity before making the initial commit.
3. Inspect staged files, commit, add the exact GitHub repository URL as origin and push main.
4. Keep private backups, device settings and SSH keys outside Git.

## Binary release candidate

The separate `KobraNest-S1-v0.1.zip` is the complete tested-device installation candidate. The `.sha256` alongside it verifies the download. GitHub's automatic source ZIP is not that installer.

Before attaching the binary candidate publicly, finish the corresponding-source and license provisioning for redistributed Debian packages and statically linked dependencies. `docs/BUILD.md` and THIRD_PARTY.md describe existing provenance and the remaining gap. Do not describe it as a broad hardware-certified stable release; the project has been tested on one reference printer.

Pending hardware confirmation: full cold start after the latest boot-logo and RTL8153B changes. Also track the wireless regulatory database signature warning.

Public repository: https://github.com/moosbewohner/KobraNest

The complete binary preview is published separately as release v0.1.0. The source-provisioning gap above remains documented; publishing the preview does not resolve it.
