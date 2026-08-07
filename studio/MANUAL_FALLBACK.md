# GarageBand manual fallback

Use this only when the automated native-project workflow reports that GarageBand, Accessibility permission, Screen/Input control, or a required sound-library patch is unavailable on a new machine.

## Required environment

- the GarageBand version declared by the selected `projects/<track>/project.json`, or a deliberately re-verified newer version;
- the sound-library patches named in that project specification;
- Accessibility permission for the terminal or automation host if retrying automation.

## Fallback procedure

1. Open the selected project's `midi/00_full_arrangement.mid` in GarageBand and save the native project inside the same `projects/<track>/` directory.
2. Confirm the tempo, key, meter, length, and track count from `projects/<track>/project.json`.
3. Apply only the named patches. Never move master volume, master gain, track volume, or track gain.
4. If tonal balance needs correction, use EQ. If EQ is insufficient, revisit arrangement, register, velocity, articulation, density, or patch choice.
5. Save, close, and reopen the project. Confirm every patch again and confirm that track-volume values did not change.
6. Play from bar 1, then export a WAVE file at the required sample rate.
7. Run the full-reference comparison and promotion gate. A successful export alone is not acceptance.

The automated workflow remains authoritative whenever available. Any new UI behavior discovered here must be encoded and regression-tested before the fallback becomes routine.
