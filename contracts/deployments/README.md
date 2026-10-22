# Deployment records

Everything in this directory is served at blockulator.com/contracts/deployments/.

- `FP127.md`, `FP127.json`: the FP127 object on Sepolia, CREATE2 through the
  deterministic proxy with salt "FP127 v5" (v1 to v4 recorded below it), the
  verification recipe and the smoke test. Deploy a new version with
  `make deploy-sepolia`, `make verify-sepolia`, `make smoke-sepolia`.
- `FP256.md`, `FP256.json`, `FP256X.json`, `FP256X2.json`, `FP256X3.json`:
  FP256 release four, four objects from one source (salts "FP256 v4",
  "FP256X v4", "FP256X2 v4", "FP256X3 v4"; releases one to three recorded
  below them), the same way with the `-fp256`, `-fp256x`, `-fp256x2` and
  `-fp256x3` targets. One record covers the four objects, as `Ladder.md`
  covers its thirteen contracts.
- `Ladder.md`, `Ladder.json`: the eleven ladder adapters, `LadderRunner` and
  `EdgeRunner`, salt "FP127 ladder v9". `make deploy-ladder-sepolia`,
  `make verify-ladder-sepolia`.
- `RELEASE.md`, `RELEASE.json`: every address in Blockulator 2.1.
- `*.sepolia.receipt.json`: the raw receipt of each object's deployment.

The badge, game, calculator and market contracts were deployed by hand in
the Huff era; their addresses live in
`static/js/legacy/infrastructure/config/contract-registry.js`, the game
modules, and `/.well-known/agent.json`.
