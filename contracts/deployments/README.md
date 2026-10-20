# Deployment records

Everything in this directory is served at blockulator.com/contracts/deployments/.

- `FP127.md`, `FP127.json`: the FP127 object on Sepolia, CREATE2 through the
  deterministic proxy with salt "FP127 v4" (v1 to v3 recorded below it), the
  verification recipe and the smoke test. Deploy a new version with
  `make deploy-sepolia`, `make verify-sepolia`, `make smoke-sepolia`.
- `FP256.md`, `FP256.json`: the FP256 object, salt "FP256 v3", the same way
  with the `-fp256` targets.
- `Ladder.md`, `Ladder.json`: the eleven ladder adapters, `LadderRunner` and
  `EdgeRunner`, salt "FP127 ladder v8". `make deploy-ladder-sepolia`,
  `make verify-ladder-sepolia`.
- `RELEASE.md`, `RELEASE.json`: every address in Blockulator 2.0.
- `FP127.sepolia.receipt.json`: the raw receipt of the FP127 deployment.

The badge, game, calculator and market contracts were deployed by hand in
the Huff era; their addresses live in
`static/js/legacy/infrastructure/config/contract-registry.js`, the game
modules, and `/.well-known/agent.json`.
