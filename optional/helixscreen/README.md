# HelixScreen on KobraNest

The initial package contains the official **v1.1.0-beta.11** `helixscreen-pi32.zip` from prestonbrown/helixscreen, commit `3f4f594092d419f26866995478ba7c54a12378e2`. File content and upstream layout are preserved; no binary aliases are injected. The launcher uses canonical `bin/helix-screen`, with a read-only fallback for older deployments.

Upstream self-updates own `/opt/helixscreen`: a later installed canonical binary is preserved during KobraNest repair, even if the old KobraNest marker disappeared. Repair does not downgrade it to the bundled initial version. KobraNest bookkeeping is outside the upstream tree in `/var/lib/kobranest-display/helixscreen.json`; recognized old markers and our exact compatibility link are archived. The S1 wrapper stays in `/usr/local/sbin/s1-helix`, uses the real root home, and leaves settings in the upstream `config/` directory. No live-device migration is performed by editing these sources.

Official ZIP SHA-256: `f318adc869f20d7adb9a98ab3cb9decca16f3df5ee7c2338ea3531ea5c38a45d`.
Executable SHA-256: `de14865176144462f17625e72f75a59294525e33a0b4a2c0b89060a0712c898c`.
Wrapper/source provenance: `payload/helix-official.json`; reproduce packaging with `source/helixscreen-build/package.py`.

KlipperScreen remains installed with the ACE Pro panel. Both interfaces select local Moonraker when USB forwarding is enabled, otherwise the configured Pi address. [USB details](../../docs/USB.md).

Fresh KobraNest profiles mark per-printer setup complete, use Moonraker's Bauraumlicht power device instead of a fictitious `output_pin caselight`, and acknowledge the reference S1 controller fan and filament sensors. Existing unrelated user settings and custom images are preserved.

Native PWM sound is configured for the verified S1 buzzer, pwmchip0/channel0. Sound and UI sound remain off initially. Enable under Settings → Sound if wanted. This is a buzzer, not a PCM music device. The startup melody is independent.

Framebuffer size 800×480, rotation 180°, lightweight 2D rendering and disabled animations/screensaver remain the S1 defaults. The binary was tested on the reference printer; later ACE changes require separate validation.
