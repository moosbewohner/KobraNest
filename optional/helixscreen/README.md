# HelixScreen on KobraNest

The initial package contains the official **v1.1.0** `helixscreen-pi32.zip` from prestonbrown/helixscreen, commit `e82a1bb844794153f8c9d3f5f590a3f930463cb4`. File content and upstream layout are preserved; no binary aliases are injected. The launcher uses canonical `bin/helix-screen`, with a read-only fallback for older deployments.

Upstream self-updates own `/opt/helixscreen`: a later installed canonical binary is preserved during KobraNest repair, even if the old KobraNest marker disappeared. Repair does not downgrade it to the bundled initial version. KobraNest bookkeeping is outside the upstream tree in `/var/lib/kobranest-display/helixscreen.json`; recognized old markers and our exact compatibility link are archived. The S1 wrapper stays in `/usr/local/sbin/s1-helix`, uses the real root home, and leaves settings in the upstream `config/` directory. No live-device migration is performed by editing these sources.

Official ZIP SHA-256: `831b9e4c80e9b79f8c8b454cb7b46a381192c8e9d7ac53010ac14ba6054a2e0b`.
Executable SHA-256: `68f923405013c09f77756848f76579a5a3fd2fd2f150dfb507073acd825f0041`.
Wrapper/source provenance: `payload/helix-official.json`; reproduce packaging with `source/helixscreen-build/package.py`.

KlipperScreen remains installed with the ACE Pro panel. Both interfaces select local Moonraker when USB forwarding is enabled, otherwise the configured Pi address. [USB details](../../docs/USB.md).

Fresh KobraNest profiles mark per-printer setup complete, use Moonraker's Bauraumlicht power device instead of a fictitious `output_pin caselight`, and acknowledge the reference S1 controller fan and filament sensors. Existing unrelated user settings and custom images are preserved.

Native PWM sound is configured for the verified S1 buzzer, pwmchip0/channel0. Sound and UI sound remain off initially. Enable under Settings → Sound if wanted. This is a buzzer, not a PCM music device. The startup melody is independent.

Framebuffer size 800×480, rotation 180°, lightweight 2D rendering and disabled animations/screensaver remain the S1 defaults. The binary was tested on the reference printer; later ACE changes require separate validation.
