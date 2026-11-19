# tests

Run with `deno task test` (see `deno.json`), which also runs the colour guard
and the orphan check from `scripts/`.

- `test-digits.js`: the digit-split rule the demo page uses to colour the
  first wrong digit, the same rule as the `cell` component in
  `templates/components.html`, and the raw-word decoder.

Contract tests are Foundry: `make test` (see `test/` at the repository root).
