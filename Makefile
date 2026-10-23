.PHONY: gates proofs build-yul talk sweep profile replays replays-fetch replay-resupply replay-bunni replay-balancer replay-balancer-v1 replay-resupply-fetch replay-bunni-fetch replay-balancer-fetch replay-balancer-v1-fetch accrual-submodules accrual-deployed accrual-verify accrual-survey build-fp256 predict-fp256 deploy-fp256-sepolia verify-fp256-sepolia smoke-fp256-sepolia bench-fp256 precision-report-fp256 gen-fp256 vectors-fp256 size-fp256 gen-edges gen-edges-check edges edges-check pi-compare site site-check help gen gen-check gen-wad wad vectors vectors-check build test bench precision-report fetch-baseline size predict deploy-sepolia verify-sepolia smoke-sepolia gen-inputs gen-inputs-check ladder ladder-check predict-ladder deploy-ladder-sepolia verify-ladder-sepolia

PY := uv run

# Deploys send from one account: run them one after another (a parallel make
# collides on the nonce), whatever -j the caller's MAKEFLAGS carry.
ifneq ($(filter deploy-%,$(MAKECMDGOALS)),)
.NOTPARALLEL:
endif

BASELINE_ADDR := 0xfae694D0c2c44181791F838c54Ed64C3151FfE30
SEPOLIA_RPC ?= https://ethereum-sepolia-rpc.publicnode.com

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
	@echo "  make precision-report - Rewrite docs/fp127/precision.md from docs/fp127/precision.json"
	@echo "  make bench            - Gas ladder for every op and form -> docs/benchmarks/gas.json + gas.md"
	@echo "  make talk             - The talk deck, one plot per slide from the data -> docs/talks/dust-is-over.pdf"
	@echo "  make pi-compare       - Ramanujan's series through each library's primitives -> docs/benchmarks/pi.md"
	@echo "  make size             - Print the deployed FP127 runtime size in bytes"
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
	@echo "  make sweep            - random-input accuracy of every FP127/FP256 op vs correctly rounded truth -> docs/benchmarks/sweep.{json,md}"
	@echo "  make sweep OPS=a,b    - only those ops (both libraries, both passes); their rows replace the recorded ones"
	@echo "  make wad              - BlockulatorWad beside Solady and PRBMath on the same inputs: wei error, gas, bytes -> docs/benchmarks/wad.{json,md}"
	@echo "  make gen-wad          - generate contracts/src/wad/BlockulatorWad.sol and ops.json from BlockulatorWad.yul.src (on FP256.yul.src)"
	@echo "  make profile          - where the gas goes: per op gas, fallback rate and per-helper share on the sweep inputs, and the via_ir bench -> docs/benchmarks/profile.{json,md}"
	@echo "  make replays          - four exploits replayed bit-exact from pinned chain data, then in FP127, FP256 and exact -> docs/benchmarks/replay-*.md"
	@echo "  make replays-fetch    - (network, read-only) re-pin scripts/replays/*.json from the attack transactions"
	@echo "  make predict-ladder   - CREATE2 addresses of the ladder adapters and runner"
	@echo "  make site             - Build the Zola site into public/ (pinned Zola is downloaded if none is installed)"
	@echo "  make site-check       - zola check, the symlinked data test, and deno task test"
	@echo "  make og               - Redraw static/og.png, the link-preview card (scripts/og/og.py)"
	@echo "  make deploy-ladder-sepolia - Deploy them (reads DEPLOYER_KEY), then record"
	@echo "  make verify-ladder-sepolia - Verify them on Sourcify (and Etherscan if ETHERSCAN_API_KEY is set)"
	@echo "  make fetch-baseline   - Re-fetch the legacy Huff runtime bytecode from Sepolia"
	@echo "  make predict          - Print the CREATE2 address of the current FP127 object"
	@echo "  make predict-fp256 / predict-fp256e / predict-fp256h / predict-fp256s - CREATE2 addresses of FP256's four objects (the number, elementary, hyperbolic, special)"
	@echo "  make deploy-fp256-sepolia / deploy-fp256e-sepolia / -fp256h- / -fp256s- - Deploy them (reads DEPLOYER_KEY; DEPLOY_GAS, default 40M)"
	@echo "  make verify-fp256-sepolia / verify-fp256e-sepolia / -fp256h- / -fp256s- - Prove runtime = artifact, verify on Sourcify + Blockscout"
	@echo "  make smoke-fp256-sepolia - Every committed FP256 vector against the live objects"
	@echo "  make size-fp256       - FP256, FP256E, FP256H and FP256S runtime sizes"
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
	@test ! -f contracts/src/fp256/FP256.yul.src || $(PY) scripts/fp127/gen.py --lib fp256 --check
	@test ! -f contracts/src/wad/BlockulatorWad.yul.src || $(PY) scripts/fp127/gen.py --lib wad --check

gen-fp256:
	@$(PY) scripts/fp127/gen.py --lib fp256

gen-wad:
	@$(PY) scripts/fp127/gen.py --lib wad

# BlockulatorWad beside Solady and PRBMath on the same inputs: wei error, gas, bytes
wad: build
	@$(PY) scripts/sweep/wad.py

vectors:
	@$(PY) scripts/fp127/oracle.py vectors

vectors-check:
	@$(PY) scripts/fp127/oracle.py check
	@test ! -f scripts/fp256/vector_spec.json || $(PY) scripts/fp256/oracle.py check

vectors-fp256:
	@$(PY) scripts/fp256/oracle.py vectors

build: gen-check gen-inputs-check
	@forge build
	@$(MAKE) -s build-yul

# Every deployed Yul object is compiled by solc directly (stdjson.py: solc
# 0.8.38, evm osaka, 0.8.24's optimizer sequence pinned); the artifact has the
# Foundry shape. forge builds no Yul (foundry.toml skip).
build-yul:
	@set -e; for o in $(OBJECTS); do FP_LIB=$$o $(PY) scripts/fp127/stdjson.py artifact; done
build-fp256:
	@set -e; for o in $(FP256_OBJECTS); do FP_LIB=$$o $(PY) scripts/fp127/stdjson.py artifact; done

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

test: gen-check vectors-check
	@forge test --match-path "test/fp127/*"
	@forge test --match-path "test/fp256/*"
	@forge test --match-path "test/ladder/*" -q
	@forge test --match-path "test/replays/*" -q
	@forge test --match-path "test/examples/*" -q
	@forge test --match-path "test/objects/*"
	@forge test --match-path "test/wad/*"

size-fp256: build
	@$(DEPLOY) size $(FP256_OBJECTS)


ladder: build
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py

ladder-check: build ladder-selftest
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py --check

precision-report:
	@$(PY) scripts/fp127/precision_report.py

precision-report-fp256:
	@$(PY) scripts/fp127/precision_report.py --lib fp256

size: build
	@$(DEPLOY) size $(FP127_OBJECTS)

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

# Replays. Each exploit's deployed arithmetic, bit-exact from integers pinned out of
# the attack transaction (scripts/replays/*.json), then the same step under the
# protocol's own fix, FP127, FP256 and exact rationals. Offline; *-fetch re-pins.
replays: replay-resupply replay-bunni replay-balancer replay-balancer-v1
replays-fetch: replay-resupply-fetch replay-bunni-fetch replay-balancer-fetch replay-balancer-v1-fetch

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
# each object stem <o> (fp127 fp256 fp256e fp256h fp256s, `gen.py --objects`):
# predict-<o>, deploy-<o>-sepolia, verify-<o>-sepolia; predict, deploy-sepolia
# and verify-sepolia are FP127's, as before. deploy-* go through Arachnid's
# CREATE2 proxy and read DEPLOYER_KEY. The objects use CLZ (EIP-7939): every
# deploy first asks the RPC for clz(1) and refuses to send unless it answers
# 255, since the code would deploy fine on a chain without CLZ and every call
# would then fail. Sepolia charges about 1,550 gas per byte of deposited code,
# so the transaction carries an explicit DEPLOY_GAS.

OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects)
FP127_OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects fp127)
FP256_OBJECTS := $(shell $(PY) scripts/fp127/gen.py --objects fp256)
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

# does the chain at RPC (default Sepolia) have CLZ? exit 1 if not
probe-clz:
	@$(DEPLOY) probe $(or $(RPC),$(SEPOLIA_RPC))

smoke-sepolia: build
	@forge test --match-contract Deployed --fork-url $(SEPOLIA_RPC) -vv

# every object: every committed vector against FP256.json's address and, when
# they exist, FP256E.json's, FP256H.json's and FP256S.json's
smoke-fp256-sepolia: build
	@forge test --match-contract Deployed256 --fork-url $(SEPOLIA_RPC) -vv

bench-fp256: build
	@forge test --match-contract "^GasLadder256$$" -vv | $(PY) scripts/fp127/gas_to_json.py --lib fp256

predict-ladder: build
	@$(PY) scripts/ladder/deploy.py predict $(SEPOLIA_RPC)

deploy-ladder-sepolia: build
	@test -n "$$DEPLOYER_KEY" || (echo "DEPLOYER_KEY is not set" && exit 1)
	@$(PY) scripts/ladder/deploy.py deploy $(SEPOLIA_RPC)
	@$(PY) scripts/ladder/deploy.py record $(SEPOLIA_RPC)

verify-ladder-sepolia: build
	@set -e; for c in LadderFP127 LadderFP127Lib LadderABDK LadderSolady LadderPRB LadderQuad LadderBalancer LadderAave LadderMorpho LadderMaker LadderFP256; do \
		A=$$($(PY) python -c "import json;print(json.load(open('contracts/deployments/Ladder.json'))['contracts']['$$c']['address'])"); \
		echo "== $$c $$A"; \
		forge verify-contract --chain sepolia --verifier sourcify --watch $$A contracts/src/ladder/$$c.sol:$$c || true; \
		test -z "$$ETHERSCAN_API_KEY" || forge verify-contract --chain sepolia --verifier etherscan --watch $$A contracts/src/ladder/$$c.sol:$$c || true; \
	done; \
	A=$$($(PY) python -c "import json;print(json.load(open('contracts/deployments/Ladder.json'))['contracts']['LadderRunner']['address'])"); \
	ARGS=$$($(PY) python -c "import json;d=json.load(open('contracts/deployments/Ladder.json'))['contracts']['LadderRunner']['constructorArgs'];print('[' + ','.join(d) + ']')"); \
	ENC=$$(cast abi-encode "f(address[11])" $$ARGS); \
	echo "== LadderRunner $$A"; \
	forge verify-contract --chain sepolia --verifier sourcify --watch --constructor-args $$ENC $$A contracts/src/ladder/LadderRunner.sol:LadderRunner || true; \
	test -z "$$ETHERSCAN_API_KEY" || forge verify-contract --chain sepolia --verifier etherscan --watch --constructor-args $$ENC $$A contracts/src/ladder/LadderRunner.sol:LadderRunner || true; \
	E=$$($(PY) python -c "import json;print(json.load(open('contracts/deployments/Ladder.json'))['contracts']['EdgeRunner']['address'])"); \
	echo "== EdgeRunner $$E"; \
	forge verify-contract --chain sepolia --verifier sourcify --watch --constructor-args $$ENC $$E contracts/src/ladder/EdgeRunner.sol:EdgeRunner || true; \
	test -z "$$ETHERSCAN_API_KEY" || forge verify-contract --chain sepolia --verifier etherscan --watch --constructor-args $$ENC $$E contracts/src/ladder/EdgeRunner.sol:EdgeRunner || true

# ---- site ------------------------------------------------------------------

site:
	@./build.sh

site-check: site
	@test -f public/data/ladder.json && test -f public/data/ops.json
	@test -f public/contracts/build/abis/badge-factory-v2.json && test -f public/contracts/src/identity/badge.vy
	@(test -x ./zola && ./zola check --skip-external-links) || zola check --skip-external-links
	@deno task test

og:
	$(PY) --with pillow python scripts/og/og.py
