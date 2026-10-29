.PHONY: rates-verify home-data gates proofs build-yul talk sweep profile replays replays-fetch replay-resupply replay-bunni replay-balancer replay-balancer-v1 replay-thetanuts replay-resupply-fetch replay-bunni-fetch replay-balancer-fetch replay-balancer-v1-fetch replay-thetanuts-fetch accrual-submodules accrual-deployed accrual-verify accrual-survey build-fp19 predict-fp19 deploy-fp19-sepolia verify-fp19-sepolia smoke-fp19-sepolia bench-fp19 precision-report-fp19 gen-fp19 vectors-fp19 size-fp19 gen-edges gen-edges-check edges edges-check pi-compare site site-check readme-assets readme-check help gen gen-check gen-wad wad vectors vectors-check build test bench precision-report fetch-baseline size predict deploy-sepolia verify-sepolia smoke-sepolia gen-inputs gen-inputs-check ladder ladder-check predict-ladder deploy-ladder-sepolia verify-ladder-sepolia size-inline size-inline-check build-vyper

PY := uv run

# Deploys send from one account: run them one after another (a parallel make
# collides on the nonce), whatever -j the caller's MAKEFLAGS carry.
ifneq ($(filter deploy-%,$(MAKECMDGOALS)),)
.NOTPARALLEL:
endif

BASELINE_ADDR := 0xfae694D0c2c44181791F838c54Ed64C3151FfE30
SEPOLIA_RPC ?= https://ethereum-sepolia-rpc.publicnode.com
MAINNET_RPC ?= https://ethereum-rpc.publicnode.com

help:
	@echo "  make gates            - Run every merge gate and print one line each (OPS=a,b sweeps only those ops; QUICK=1 skips the sweep); logs in cache/gates/"
	@echo "  make proofs           - Halmos proofs of the core arithmetic and directed rounding, lemmas, fuzz (CI subset; PROOFS_FULL=1 runs all and rewrites docs/benchmarks/proofs.json); docs/proofs.md"
	@echo "Blockulator / FP127"
	@echo ""
	@echo "  make gen              - generate FP127.yul, FP127Lib.sol, IFP127.sol, abi.json, ops.json from FP127.yul.src"
	@echo "  make gen-check        - Fail if the generated files are stale"
	@echo "  make vectors          - Regenerate test/fp127/vectors/*.json from the mpmath oracle"
	@echo "  make vectors-check    - Fail if the vectors are stale"
	@echo "  make build            - gen-check + forge build"
	@echo "  make test             - gen-check + vectors-check + equivalence, behaviour and precision suites"
	@echo "  make typed            - The typed API (FP127Type, FP19Type) against the raw libraries: same results and reverts, gas both ways, default profile and via_ir"
	@echo "  make precision-report - Rewrite docs/fp127/precision.md from docs/fp127/precision.json"
	@echo "  make bench            - Gas ladder for every op and form -> docs/benchmarks/gas.json + gas.md"
	@echo "  make talk             - The talk deck, one plot per slide from the data -> docs/talks/dust-is-over.pdf"
	@echo "  make pi-compare       - Ramanujan's series through each library's primitives -> docs/benchmarks/pi.md"
	@echo "  make size             - Print the deployed FP127 runtime size in bytes"
	@echo "  make size-inline      - Bytecode each op adds inlined through FP127Lib / FP19Lib, legacy and via_ir -> docs/benchmarks/size.{json,md}"
	@echo "  make size-inline-check - Fail if size.json / size.md are stale"
	@echo "  make gen-inputs       - Generate scripts/ladder/inputs.json (every input floored into each representation) from scenarios.json"
	@echo "  make gen-inputs-check - Fail if inputs.json is stale"
	@echo "  make ladder           - Terminal-precision ladder: every scenario x input x library x N -> docs/benchmarks/ladder.json + ladder.md"
	@echo "  make ladder-check     - Fail if ladder.json is stale (gas within 2%)"
	@echo "  make ladder-selftest  - Unit checks of the ladder's metric definitions"
	@echo "  make gen-edges        - Generate scripts/ladder/edge-inputs.json from edges.json"
	@echo "  make edges            - Edges dataset: every probe x library, one call each -> docs/benchmarks/edges.json + edges.md"
	@echo "  make edges-check      - Fail if edges.json is stale"
	@echo "  make accrual-deployed - Aave v3 / Morpho Blue accrual as deployed vs a 200-digit truth -> docs/benchmarks/accrual-deployed.{json,md}"
	@echo "  make accrual-verify   - (network) recompile the pinned Aave/Morpho sources, compare runtime bytecode to mainnet"
	@echo "  make accrual-survey   - (network) refresh scripts/accrual/survey.json from mainnet at the current block"
	@echo "  make rates-verify     - (network) LadderFraxlend / LadderEuler against the deployed rate models, on a mainnet fork"
	@echo "  make sweep            - random-input accuracy of every FP127/FP19 op vs correctly rounded truth -> docs/benchmarks/sweep.{json,md}"
	@echo "  make sweep OPS=a,b    - only those ops (both libraries, both passes); their rows replace the recorded ones"
	@echo "  make wad              - BlockulatorWad beside Solady and PRBMath on the same inputs: wei error, gas, bytes -> docs/benchmarks/wad.{json,md}"
	@echo "  make gen-wad          - generate contracts/src/wad/BlockulatorWad.sol and ops.json from BlockulatorWad.yul.src (on FP19.yul.src)"
	@echo "  make profile          - where the gas goes: per op gas, fallback rate and per-helper share on the sweep inputs, and the via_ir bench -> docs/benchmarks/profile.{json,md}"
	@echo "  make replays          - five exploits replayed bit-exact from pinned chain data, then in FP127, FP19 and exact -> docs/benchmarks/replay-*.md"
	@echo "  make replays-fetch    - (network, read-only) re-pin scripts/replays/*.json from the attack transactions"
	@echo "  make predict-ladder   - CREATE2 addresses of the ladder adapters and runner"
	@echo "  make site             - Build the Zola site into public/ (pinned Zola is downloaded if none is installed)"
	@echo "  make home-data        - static/data/home.json, the home page's tables and charts, from the datasets"
	@echo "  make site-check       - zola check, the symlinked data test, and deno task test"
	@echo "  make readme-assets    - regenerate the README chart, badges and tables from the datasets"
	@echo "  make pack             - Stage the npm/Soldeer package in dist/contracts/ and check both dry runs' file lists (publishes nothing)"
	@echo "  make og               - Redraw static/og.png, the link-preview card (scripts/og/og.py)"
	@echo "  make deploy-ladder-sepolia - Deploy them (reads DEPLOYER_KEY), then record"
	@echo "  make cdf              - The normal CDF and erfc of every on-chain implementation against mpmath -> docs/benchmarks/cdf.{json,md}"
	@echo "  make predict-mainnet  - Every release object's CREATE2 address on Ethereum mainnet, and whether it is there"
	@echo "  make deploy-mainnet-dry - The mainnet bundle on an anvil fork: addresses, runtimes, gas and the ETH to fund"
	@echo "  make deploy-mainnet   - Funding + deploys as one Flashbots bundle (FUNDER_KEY pays, DEPLOYER_KEY deploys)"
	@echo "  make verify-mainnet   - Live runtime equals the artifact; Sourcify and Blockscout"
	@echo "  make smoke-mainnet    - Every committed vector against the mainnet addresses (fork)"
	@echo "  make verify-ladder-sepolia - Verify them on Sourcify (and Etherscan if ETHERSCAN_API_KEY is set)"
	@echo "  make fetch-baseline   - Re-fetch the legacy Huff runtime bytecode from Sepolia"
	@echo "  make predict          - Print the CREATE2 address of the current FP127 object"
	@echo "  make predict-fp19 / predict-fp19e / predict-fp19h / predict-fp19n / predict-fp19s - CREATE2 addresses of FP19's five objects (the number, elementary, hyperbolic, normal, Lambert W)"
	@echo "  make deploy-fp19-sepolia / deploy-fp19e-sepolia / -fp19h- / -fp19n- / -fp19s- - Deploy them (reads DEPLOYER_KEY; DEPLOY_GAS, default 40M)"
	@echo "  make verify-fp19-sepolia / verify-fp19e-sepolia / -fp19h- / -fp19n- / -fp19s- - Prove runtime = artifact, verify on Sourcify + Blockscout"
	@echo "  make smoke-fp19-sepolia - Every committed FP19 vector against the live objects"
	@echo "  make size-fp19       - FP19, FP19E, FP19H, FP19N and FP19S runtime sizes"
	@echo "  make build-yul        - Compile every deployed Yul object with the pinned solc (stdjson.py) -> out/<Object>.yul/"
	@echo "  make probe-clz [RPC=] - Does the chain have CLZ (EIP-7939)? Every deploy runs this first"
	@echo "  make deploy-sepolia   - Deploy via the CREATE2 proxy (reads DEPLOYER_KEY)"
	@echo "  make verify-sepolia   - Prove the live runtime equals the artifact, then verify on Sourcify + Blockscout"
	@echo "  make smoke-sepolia    - Run every committed vector against the live Sepolia contract"
	@echo ""

gen:
	@$(PY) scripts/fp127/gen.py

gen-check:
	@$(PY) scripts/fp127/gen.py --check
	@test ! -f contracts/src/fp19/FP19.yul.src || $(PY) scripts/fp127/gen.py --lib fp19 --check
	@test ! -f contracts/src/wad/BlockulatorWad.yul.src || $(PY) scripts/fp127/gen.py --lib wad --check

gen-fp19:
	@$(PY) scripts/fp127/gen.py --lib fp19

gen-wad:
	@$(PY) scripts/fp127/gen.py --lib wad

# BlockulatorWad beside Solady and PRBMath on the same inputs: wei error, gas, bytes
wad: build
	@$(PY) scripts/sweep/wad.py

vectors:
	@$(PY) scripts/fp127/oracle.py vectors

vectors-check:
	@$(PY) scripts/fp127/oracle.py check
	@test ! -f scripts/fp19/vector_spec.json || $(PY) scripts/fp19/oracle.py check

vectors-fp19:
	@$(PY) scripts/fp19/oracle.py vectors

build: gen-check gen-inputs-check
	@forge build
	@$(MAKE) -s build-yul
	@$(PY) scripts/ladder/vyper.py

# Every deployed Yul object is compiled by solc directly (stdjson.py: solc
# 0.8.38, evm osaka, 0.8.24's optimizer sequence pinned); the artifact has the
# Foundry shape. forge builds no Yul (foundry.toml skip).
build-yul:
	@set -e; for o in $(OBJECTS); do FP_LIB=$$o $(PY) scripts/fp127/stdjson.py artifact; done
# The comparison's Vyper contracts (snekmate), each with the compiler its
# library pins, through uvx -> out/vyper/<Name>.json. forge skips *.vy.
build-vyper:
	@$(PY) scripts/ladder/vyper.py

build-fp19:
	@set -e; for o in $(FP19_OBJECTS); do FP_LIB=$$o $(PY) scripts/fp127/stdjson.py artifact; done

gen-inputs:
	@$(PY) scripts/ladder/gen_inputs.py

gen-inputs-check:
	@$(PY) scripts/ladder/gen_inputs.py --check

ladder-selftest:
	@$(PY) scripts/ladder/ladder.py --selftest

gen-edges:
	@$(PY) scripts/ladder/gen_edges.py

gen-edges-check:
	@$(PY) scripts/ladder/gen_edges.py --check

edges: build
	@forge test --match-contract "^Edges$$" -vv | $(PY) scripts/ladder/edges.py

edges-check: build gen-edges-check
	@forge test --match-contract "^Edges$$" -vv | $(PY) scripts/ladder/edges.py --check

# the normal CDF and erfc, every on-chain implementation (test/cdf/Cdf.t.sol) -> docs/benchmarks/cdf.{json,md}
cdf: build
	@forge test --match-contract "^Cdf$$" -vv | $(PY) scripts/cdf/cdf.py

cdf-check: build
	@forge test --match-contract "^Cdf$$" -vv | $(PY) scripts/cdf/cdf.py --check

test: gen-check vectors-check
	@forge test --match-path "test/fp127/*"
	@forge test --match-path "test/fp19/*"
	@forge test --match-path "test/ladder/*" -q
	@forge test --match-path "test/replays/*" -q
	@forge test --match-path "test/examples/*" -q
	@forge test --match-path "test/objects/*"
	@forge test --match-path "test/wad/*"
	@$(MAKE) -s typed

# The typed API (FP127Type.sol, FP19Type.sol) against the raw libraries: the
# same words and reverts under fuzzing, and each op's gas both ways, under the
# default profile and again through the IR, where no difference is allowed.
# The IR pass sets src to test/typed, and forge >= 1.8 then auto-remaps
# forge-std/ to lib/forge-std/test/typed/, so its remapping is explicit.
.PHONY: typed
typed:
	@mkdir -p cache/typed-ir
	@forge test --match-path "test/typed/*" -vv > cache/typed-ir/default.log || { cat cache/typed-ir/default.log; exit 1; }
	@grep -E "TYPED\|.*\|worst|Suite result" cache/typed-ir/default.log
	@TYPED_GAS_TOL=0 FOUNDRY_SRC=test/typed FOUNDRY_TEST=test/typed FOUNDRY_SCRIPT=test/typed \
		FOUNDRY_OUT=cache/typed-ir/out FOUNDRY_CACHE_PATH=cache/typed-ir/cache FOUNDRY_VIA_IR=true \
		forge test --match-test test_gas -vv --remappings forge-std/=lib/forge-std/src/ > cache/typed-ir/via-ir.log || { cat cache/typed-ir/via-ir.log; exit 1; }
	@grep -E "TYPED\|.*\|worst|Suite result" cache/typed-ir/via-ir.log

size-fp19: build
	@$(DEPLOY) size $(FP19_OBJECTS)


ladder: build
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py

ladder-check: build ladder-selftest
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py --check

precision-report:
	@$(PY) scripts/fp127/precision_report.py

precision-report-fp19:
	@$(PY) scripts/fp127/precision_report.py --lib fp19

size: build
	@$(DEPLOY) size $(FP127_OBJECTS)

# The bytecode each op adds when inlined through FP127Lib / FP19Lib, legacy and
# via_ir: one throwaway contract per op (in a temp dir) against a baseline, by
# solc directly. Needs only solc 0.8.38 (forge build installs it).
size-inline:
	@$(PY) scripts/size/inline.py
size-inline-check:
	@$(PY) scripts/size/inline.py --check

bench: build
	@forge test --match-contract "^GasLadder$$" -vv | $(PY) scripts/fp127/gas_to_json.py

# Deployed accrual. The submodules lib/aave-v3-origin (v3.7.0), lib/morpho-blue
# (v1.0.0) and lib/morpho-blue-irm (v1.0.0) are the mainnet code; accrual-verify
# proves it byte for byte. accrual-deployed is offline once solc 0.8.19 is cached.
accrual-submodules:
	@git submodule update --init --checkout --recursive lib/aave-v3-origin lib/morpho-blue lib/morpho-blue-irm

accrual-deployed: build accrual-submodules
	@$(PY) scripts/accrual/verify_deployed.py build
	@$(PY) scripts/accrual/accrual.py

accrual-verify: accrual-submodules
	@$(PY) scripts/accrual/verify_deployed.py check

accrual-survey:
	@$(PY) scripts/accrual/survey.py

# (network) LadderFraxlend and LadderEuler against the deployed FraxLend rate
# contract and pair and an Euler v2 IRMAdaptiveCurve, on a mainnet fork
rates-verify: build
	@forge test --match-contract "^DeployedRates$$" --fork-url $(MAINNET_RPC) -vv

# Replays. Each exploit's deployed arithmetic, bit-exact from integers pinned out of
# the attack transaction (scripts/replays/*.json), then the same step under the
# protocol's own fix, FP127, FP19 and exact rationals. Offline; *-fetch re-pins.
replays: replay-resupply replay-bunni replay-balancer replay-balancer-v1 replay-thetanuts
replays-fetch: replay-resupply-fetch replay-bunni-fetch replay-balancer-fetch replay-balancer-v1-fetch replay-thetanuts-fetch

replay-resupply: build
	@$(PY) scripts/replays/resupply.py
replay-resupply-fetch:
	@$(PY) scripts/replays/resupply.py fetch
replay-bunni:
	@$(PY) scripts/replays/bunni.py
replay-bunni-fetch:
	@$(PY) scripts/replays/bunni.py fetch
replay-balancer:
	@$(PY) scripts/replays/balancer.py
replay-balancer-fetch:
	@$(PY) scripts/replays/balancer.py fetch
replay-balancer-v1:
	@$(PY) scripts/replays/balancer_v1.py score
replay-balancer-v1-fetch:
	@$(PY) scripts/replays/balancer_v1.py fetch
replay-thetanuts:
	@$(PY) scripts/replays/thetanuts.py
replay-thetanuts-fetch:
	@$(PY) scripts/replays/thetanuts.py fetch

gates:
	@$(PY) scripts/gates.py $(if $(OPS),--ops $(OPS)) $(if $(QUICK),--quick) $(if $(ONLY),--only $(ONLY))

# The formal proofs (docs/proofs.md): needs halmos 0.3.3 (uv tool install
# halmos==0.3.3), which downloads bitwuzla on first use. PROOFS_FULL=1 runs
# every check and records the result; ONLY=<regex> runs the matching checks.
proofs:
	@HALMOS_ALLOW_DOWNLOAD=1 python3 test/proofs/run.py $(if $(ONLY),--only $(ONLY))

sweep: build
	@$(PY) scripts/sweep/sweep.py $(if $(OPS),--ops $(OPS))
profile: build
	@$(PY) scripts/sweep/gasprofile.py
talk:
	@uv run --with matplotlib --with weasyprint --with mpmath python scripts/talk/deck.py

pi-compare: build
	@forge test --match-contract PiCompare -vv | $(PY) scripts/fp127/pi_compare.py

fetch-baseline:
	@mkdir -p contracts/archive/huff
	@cast code $(BASELINE_ADDR) --rpc-url $(SEPOLIA_RPC) | tr -d "\n" > contracts/archive/huff/fp127.sepolia.runtime.hex
	@echo "fetched at block $$(cast block-number --rpc-url $(SEPOLIA_RPC))"
	@cast keccak "$$(cat contracts/archive/huff/fp127.sepolia.runtime.hex)"

# ---- deployment ------------------------------------------------------------
# Every deployed object from the one objects table in scripts/fp127/gen.py
# (LIBS[...]["objects"]: name, library, salt). The targets are static pattern
# rules over that list, so a re-layout or a new salt edits only the table. For
# each object stem <o> (fp127 fp19 fp19e fp19h fp19n fp19s, `gen.py --objects`):
# predict-<o>, deploy-<o>-sepolia, verify-<o>-sepolia; predict, deploy-sepolia
# and verify-sepolia are FP127's, as before. deploy-* go through Arachnid's
# CREATE2 proxy and read DEPLOYER_KEY. The objects use CLZ (EIP-7939): every
# deploy first asks the RPC for clz(1) and refuses to send unless it answers
# 255, since the code would deploy fine on a chain without CLZ and every call
# would then fail. Sepolia charges about 1,550 gas per byte of deposited code,
# so the transaction carries an explicit DEPLOY_GAS.

OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects)
FP127_OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects fp127)
FP19_OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects fp19)
DEPLOY := $(PY) scripts/fp127/deploy.py
DEPLOY_GAS ?= 40000000
export DEPLOY_GAS

.PHONY: $(OBJECTS:%=predict-%) $(OBJECTS:%=deploy-%-sepolia) $(OBJECTS:%=verify-%-sepolia) probe-clz

predict: predict-fp127
deploy-sepolia: deploy-fp127-sepolia
verify-sepolia: verify-fp127-sepolia

$(OBJECTS:%=predict-%): predict-%: build
	@$(DEPLOY) predict $* $(SEPOLIA_RPC)

$(OBJECTS:%=deploy-%-sepolia): deploy-%-sepolia: build
	@$(DEPLOY) deploy $* $(SEPOLIA_RPC)

$(OBJECTS:%=verify-%-sepolia): verify-%-sepolia: build
	@FP_LIB=$* $(PY) scripts/fp127/stdjson.py check
	@FP_LIB=$* $(PY) scripts/fp127/stdjson.py onchain $(SEPOLIA_RPC) $$($(DEPLOY) address $*)
	@FP_LIB=$* $(PY) scripts/fp127/verify.py 11155111 $$($(DEPLOY) address $*)

# Ethereum mainnet: the library objects only (the ladder stays on Sepolia). The deployer key is public, so the funding
# and every deploy go out as one Flashbots bundle (scripts/fp127/bundle.py): FUNDER_KEY pays, DEPLOYER_KEY deploys.
# deploy-mainnet-dry runs the identical transactions on an anvil fork first and needs no keys.
MAINNET_RPC ?= https://ethereum-rpc.publicnode.com
RELEASE_OBJECTS ?= $(OBJECTS)
.PHONY: predict-mainnet deploy-mainnet-dry deploy-mainnet verify-mainnet smoke-mainnet

predict-mainnet: build
	@set -e; for o in $(RELEASE_OBJECTS); do echo "== $$o"; $(DEPLOY) predict $$o $(MAINNET_RPC); done

deploy-mainnet-dry: build
	@$(DEPLOY) bundle --dry-run $(MAINNET_RPC) $(RELEASE_OBJECTS)

deploy-mainnet: build
	@test -n "$$FUNDER_KEY" || (echo "FUNDER_KEY is not set (the account that pays)" && exit 1)
	@test -n "$$DEPLOYER_KEY" || (echo "DEPLOYER_KEY is not set" && exit 1)
	@$(DEPLOY) bundle $(MAINNET_RPC) $(RELEASE_OBJECTS)

verify-mainnet: build
	@set -e; for o in $(RELEASE_OBJECTS); do echo "== $$o"; A=$$($(DEPLOY) address $$o); \
		FP_LIB=$$o $(PY) scripts/fp127/stdjson.py onchain $(MAINNET_RPC) $$A; FP_LIB=$$o $(PY) scripts/fp127/verify.py 1 $$A; done

smoke-mainnet: build
	@forge test --match-contract "^Deployed(19)?$$" --fork-url $(MAINNET_RPC) -vv

# does the chain at RPC (default Sepolia) have CLZ? exit 1 if not
probe-clz:
	@$(DEPLOY) probe $(or $(RPC),$(SEPOLIA_RPC))

smoke-sepolia: build
	@forge test --match-contract Deployed --fork-url $(SEPOLIA_RPC) -vv

# every object: every committed vector against FP19.json's address and, when
# they exist, FP19E.json's, FP19H.json's, FP19N.json's and FP19S.json's
smoke-fp19-sepolia: build
	@forge test --match-contract Deployed19 --fork-url $(SEPOLIA_RPC) -vv

bench-fp19: build
	@forge test --match-contract "^GasLadder19$$" -vv | $(PY) scripts/fp127/gas_to_json.py --lib fp19

predict-ladder: build
	@$(PY) scripts/ladder/deploy.py predict $(SEPOLIA_RPC)

deploy-ladder-sepolia: build
	@test -n "$$DEPLOYER_KEY" || (echo "DEPLOYER_KEY is not set" && exit 1)
	@$(PY) scripts/ladder/deploy.py deploy $(SEPOLIA_RPC)
	@$(PY) scripts/ladder/deploy.py record $(SEPOLIA_RPC)

verify-ladder-sepolia: build
	@$(PY) scripts/ladder/verify.py 11155111

# ---- site ------------------------------------------------------------------

site:
	@./build.sh

# The home page's tables and charts, one small file from the measured datasets (scripts/site/home.py)
home-data:
	@$(PY) python scripts/site/home.py

site-check: site
	@$(PY) python scripts/site/home.py --check
	@test -f public/data/ladder.json && test -f public/data/ops.json
	@test -f public/contracts/build/abis/badge-factory-v2.json && test -f public/contracts/src/identity/badge.vy
	@(test -x ./zola && ./zola check --skip-external-links) || zola check --skip-external-links
	@deno task test

# The README's chart (docs/img/digits-*.svg), badges and tables, from the committed datasets
readme-assets:
	@$(PY) python scripts/readme/assets.py

readme-check:
	@$(PY) python scripts/readme/assets.py --check

# ---- packages ----------------------------------------------------------------
# @blockulator/contracts on npm and blockulator on Soldeer, from one staged tree
# (scripts/pack/pack.py). Publishing is manual: docs/DEVELOPING.md, "Packages".

.PHONY: pack
pack:
	@$(PY) scripts/pack/pack.py

og:
	$(PY) --with pillow python scripts/og/og.py
