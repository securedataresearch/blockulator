# Blockulator

FP127, a signed 127.128 fixed-point math library for the EVM, and the site
that measures it against ABDKMath64x64, Solady and PRBMath:
[blockulator.com](https://blockulator.com).

One Yul source, `contracts/src/fp127/FP127.yul.src`, generates two forms
that are proven to agree bit for bit:

- a **deployed object** (`FP127.yul`) that any contract can `staticcall`,
  at a CREATE2 address with a published salt:
  `0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1` on Sepolia
  ([deployment record](contracts/deployments/FP127.md));
- an **inline library** (`FP127Lib.sol`) with the same bodies in
  `memory-safe` assembly blocks, for contracts that want no external call.

49 operations: `add`, `sub`, `mul`, `div`, `exp`, `exp2`, `exp10`, `ln`,
`log2`, `log10`, `sqrt`, `cbrt`, `pow`, `powu`, `compound`, `log1p`, `expm1`,
`sinh`, `cosh`, `tanh`, `atanh`, `erf`, `erfc`, `normCdf`, `lambertW0`,
`lambertWm1`, `pi` by Ramanujan's series, and the usual rounding, comparison
and conversion ops. Every argument and result is an `int256` holding
`value * 2^128`.

- 128 fractional bits, about 38 decimal digits, against 18 for WAD libraries
- Integer and rounding ops bit-exact; `ln`, `log2`, `log10` within one ULP;
  `exp`, `exp2`, `exp10` 146 bits or better, against mpmath at 200 decimal places ([`docs/fp127/precision.md`](docs/fp127/precision.md))
- Checked: out-of-domain inputs revert with `Overflow()`, `DivisionByZero()`
  or `OutOfRange()`
- Gas ladder against ABDKMath64x64, Solady and PRBMath for every op
  ([`docs/benchmarks/gas.md`](docs/benchmarks/gas.md))
- Terminal precision: thirteen iterated scenarios, N from 1 to 10,000, every
  cell against exact arithmetic and re-runnable on chain through
  `LadderRunner` ([`docs/benchmarks/ladder.md`](docs/benchmarks/ladder.md),
  [record](contracts/deployments/Ladder.md))
- The edges: 139 one-shot probes at the ends of each library's domain, where
  a result goes to zero, reverts or runs out of digits, re-runnable through
  `EdgeRunner` ([`docs/benchmarks/edges.md`](docs/benchmarks/edges.md))

**Site:** the [demo](https://blockulator.com/demo/) is the argument, the
[why](https://blockulator.com/why/) page is the mechanism, the
[library](https://blockulator.com/library/) page is how to use it, and the
[write-up](https://blockulator.com/writeup/) is the story.
**Library README:** [`contracts/src/fp127/README.md`](contracts/src/fp127/README.md)
(layout, source rules, rounding policy, what changed from the Huff).
**History:** [`docs/fp127/HISTORY.md`](docs/fp127/HISTORY.md).
**EthCC[9] talk:** https://www.youtube.com/watch?v=a_tL99NY-yc

## Use it

Inline, from Foundry:

```bash
forge install securedataresearch/blockulator
echo "fp127/=lib/blockulator/contracts/src/fp127/" >> remappings.txt
```

```solidity
import {FP127Lib} from "fp127/FP127Lib.sol";
int256 b = FP127Lib.mul(FP127Lib.fromFixed18(1.5e18), FP127Lib.exp(FP127Lib.ONE));
```

Deployed, through the interface: `import {IFP127} from "fp127/IFP127.sol";`
and `IFP127(0x6cFbCB928Ac068E84Ef793Dd1DFce4f8e9Cac1d1).ln(x)`. Both
examples are compiled and tested in [`test/examples/`](test/examples/).

For agents and scripts, every op is a free `eth_call`:
[`/llms.txt`](https://blockulator.com/llms.txt),
[`/.well-known/agent.json`](https://blockulator.com/.well-known/agent.json).

## Layout

```
blockulator/
├── contracts/src/fp127/        FP127.yul.src and the five generated files (make gen)
├── contracts/src/ladder/       LadderRunner and the per-library adapters behind the demo
├── contracts/src/{identity,games,market,tools,content}/  Vyper: badges, and the archived apps
├── contracts/archive/huff/     the Huff implementation and its Sepolia bytecode (the equivalence baseline)
├── contracts/deployments/      CREATE2 records: FP127.{md,json}, Ladder.{md,json}
├── contracts/build/abis/       ABIs the site fetches at runtime for the Vyper contracts
├── script/DeployFP127.s.sol    CREATE2 deploy script
├── scripts/fp127/              generator, mpmath oracle, verification, gas report
├── scripts/ladder/             scenario params, ladder dataset, deploy and live-cap tooling
├── test/fp127/                 equivalence, behaviour, precision, gas ladder
├── test/ladder/                the ladder harness
├── test/examples/              the two snippets on the library page, compiled and tested
├── docs/fp127/                 precision tables, history
├── docs/benchmarks/            gas and ladder datasets and reports
├── config.toml, build.sh       the Zola site
├── content/, templates/        pages (Markdown) and templates; tables are Tera components
├── static/css/site.css         synced from securedataresearch.net (scripts/sync-sdr.sh)
├── static/js/islands/          the live parts: ladder verify, badges, archive
├── static/{js,css}/legacy/     the previous SPA's code, run inside the islands
└── static/data/, static/contracts/   symlinks into docs/ and contracts/, served as /data and /contracts
```

## Build and test

Needs `forge` (solc 0.8.24 is installed on first build), `uv`, `deno`, and
`zola` 0.23 for the site (`build.sh` downloads it when absent). No Huff
toolchain, no Node.

```bash
git submodule update --init --recursive   # solady, prb-math, abdk, forge-std
uv sync                                   # mpmath + keccak for the oracle and generator

make gen           # regenerate FP127.yul, FP127Lib.sol, IFP127.sol, abi.json, ops.json
make test          # gen-check + vectors-check + equivalence, behaviour, precision, ladder suites
make bench         # gas ladder -> docs/benchmarks/gas.{json,md}
make ladder        # terminal-precision ladder -> docs/benchmarks/ladder.{json,md}
make size          # runtime bytes against the 24,576 limit
make site          # zola build -> public/
make site-check    # zola check, the symlink test, deno task test
```

`zola serve` previews the site at http://127.0.0.1:1111. Colour literals
are allowed only in `static/css/site.css` and the two legacy token files;
`scripts/check-sdr-colors.mjs` (run by `deno task test`) rejects the rest.

Deploying a new FP127: `make deploy-sepolia`, `make verify-sepolia`,
`make smoke-sepolia`; the procedure is in
[`contracts/deployments/FP127.md`](contracts/deployments/FP127.md). The
ladder contracts: `make deploy-ladder-sepolia`, `make verify-ladder-sepolia`.
The site deploys from `master` through DigitalOcean App Platform with the
spec in `.do/app.yaml`, which must be applied with `doctl apps update`
after it changes.

## License

MIT.
