# Nepal EMSR927 Baseline Fixture

This is a frozen input fixture for the direct-prompt baseline. It contains a cited, curated incident dossier plus explicit synthetic operational constraints and gold action labels.

It is intentionally not a raw CEMS product archive. Iteration 1 adds immutable upstream source snapshots, hashes, licensing metadata, and source-verification behavior. The baseline must use these frozen files only and must not call live services.

`manifest.json` stores SHA-256 checksums for every input file. The loader rejects modified, missing, unknown, or cross-reference-invalid artifacts.

The gold action labels are evaluation expectations, not field instructions. No file in this fixture authorizes an alert, evacuation, dispatch, or real-world action.
