# Developing Blockulator

The repository layout, the build and the make targets. The project overview is in the [README](../README.md).

## Layout

```
blockulator/
├── contracts/src/fp127/        FP127.yul.src and its five generated files (make gen)
├── contracts/src/fp19/        FP19.yul.src and its fourteen generated files, four objects (make gen-fp19)
├── contracts/src/ladder/       LadderRunner, EdgeRunner, one adapter per library, vendor/ (Balancer; the rest transcribed)
├── contracts/src/{identity,games,market,tools,content}/  Vyper: badges, and the archived apps
├── contracts/archive/huff/     the Huff implementation and its Sepolia bytecode (FP127's equivalence baseline)
├── contracts/deployments/      CREATE2 records: FP127, FP19, Ladder
├── scripts/fp127/              generator (both libraries), FP127 oracle, verification, gas report
├── scripts/fp19/              FP19 oracle, vector spec, kernel models and bounds.py
├── scripts/ladder/             scenarios, edges, inputs, datasets, deploy and live-check tooling
├── test/fp127/, test/fp19/    equivalence, behaviour, precision, gas ladder, fork smoke tests
├── test/ladder/                the ladder and edges harnesses
├── test/examples/              the snippets on the library page, compiled and tested
├── docs/fp127/, docs/fp19/    precision tables; docs/fp127/HISTORY.md
├── docs/benchmarks/            gas, ladder, edges and pi datasets and reports
├── docs/talks/                 the talk
├── config.toml, build.sh       the Zola site
├── content/, templates/        pages and templates; tables and charts are Tera components
├── static/css/site.css         the theme: colour tokens (light, dark), background, glass
├── static/js/islands/          scenario tabs; the badges and archive islands
└── static/data/                symlinks into docs/ and contracts/, served as /data
```

## Build and test

Needs `forge` (solc 0.8.38 is installed on first build; everything targets
evm osaka, since the libraries use the CLZ opcode), `uv`, `deno`, and
`zola` 0.23 for the site (`build.sh` downloads it when absent).

```bash
git submodule update --init --recursive   # solady, prb-math, abdk, forge-std
uv sync                                   # mpmath, keccak

make gen gen-fp19       # regenerate each library's generated files from its .yul.src
make build               # forge build; FP19.yul is compiled by solc standard-json (make build-fp19)
make test                # gen-check, vectors-check, every suite under test/fp127, test/fp19, test/ladder, test/replays, test/examples
make bench bench-fp19   # gas ladders -> docs/benchmarks/gas.{json,md}, gas19.{json,md}
make ladder              # terminal-precision ladder -> docs/benchmarks/ladder.{json,md}
make edges               # the edges -> docs/benchmarks/edges.{json,md}
make pi-compare          # docs/benchmarks/pi.md
make precision-report precision-report-fp19
make size size-fp19     # runtime bytes against the 24,576 limit (FP127; FP19, FP19E, FP19H, FP19N, FP19S)
make sweep               # random inputs through every op, both stages -> docs/benchmarks/sweep.{json,md}
make site site-check     # zola build -> public/; zola check, the symlink test, deno task test
```

`make *-check` targets fail when a committed dataset no longer matches the
code; CI runs them all. Deploying follows the records: `make predict`,
`deploy-sepolia`, `verify-sepolia`, `smoke-sepolia` for FP127, the `-fp19`,
`-fp19e`, `-fp19h`, `-fp19n` and `-fp19s` variants for FP19's five objects (one
pattern rule each over the objects table in `scripts/fp127/gen.py`), and `predict-ladder` / `deploy-ladder-sepolia` /
`verify-ladder-sepolia` then `scripts/ladder/livecap.py` and `liveedges.py`
for the runners. The deployer key is read from `DEPLOYER_KEY` and never
stored.

Before a merge, `make gates` runs every gate and prints one line each (`OPS=a,b` sweeps only those ops, `QUICK=1` skips the sweep); full logs go to `cache/gates/`.

## Packages

`make pack` stages `@blockulator/contracts` (npm) and `blockulator` (Soldeer)
in `dist/contracts/` from one tree: `packages/contracts/` (package.json, the
package README), the LICENSE, and `fp127/`, `fp19/`, `wad/` (the `.sol` and
`.yul` sources and the ABIs from `contracts/src/`) plus `deployments/` (the
JSON records). It runs `npm pack --dry-run` and `forge soldeer push --dry-run`
and fails unless both list exactly the staged files, with no tests, cache or
secrets and every Solidity import relative. CI runs it. Publishing is manual,
after the version in `packages/contracts/package.json` is set:

```bash
make pack
cd dist/contracts
npm login
npm publish --access public
forge soldeer login
forge soldeer push blockulator~<version>
```
