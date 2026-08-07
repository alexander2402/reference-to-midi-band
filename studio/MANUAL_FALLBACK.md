# GarageBand manual fallback

Use this only when the automated native-project workflow reports that GarageBand, Accessibility permission, or Screen/Input control is unavailable on a new machine.

## Required environment

- GarageBand 10.4.3 or a deliberately re-verified newer version
- the GarageBand sound library patches named in `studio/project.json`
- Accessibility permission for the terminal or automation host if retrying automation

## Fallback procedure

1. Open `midi/00_full_arrangement.mid` in GarageBand and save it as `Gorodok_Matched.band`.
2. Confirm 77.733 BPM, A minor, 4/4, and all six tracks.
3. Apply the patches and fader values from `garageband.tracks` in `studio/project.json`.
4. Save, close, and reopen the project.
5. Confirm every patch and fader value again. Do not continue if any value reverted.
6. Play from bar 1, then export a WAVE file at 44.1 kHz.
7. Run the comparison and promotion gate. A successful export alone is not acceptance.

The automated workflow remains authoritative whenever it is available. This document is a portability fallback, not the normal production path.
