.PHONY: build-fp256 predict-fp256 deploy-fp256-sepolia verify-fp256-sepolia smoke-fp256-sepolia bench-fp256 precision-report-fp256 gen-fp256 vectors-fp256 size-fp256 gen-edges gen-edges-check edges edges-check pi-compare site site-check help gen gen-check vectors vectors-check build test bench precision-report fetch-baseline size predict deploy-sepolia verify-sepolia smoke-sepolia gen-inputs gen-inputs-check ladder ladder-check predict-ladder deploy-ladder-sepolia verify-ladder-sepolia

PY := uv run
BASELINE_ADDR := 0xfae694D0c2c44181791F838c54Ed64C3151FfE30
SEPOLIA_RPC ?= https://ethereum-sepolia-rpc.publicnode.com

help:
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
	@echo "  make predict-ladder   - CREATE2 addresses of the ladder adapters and runner"
	@echo "  make site             - Build the Zola site into public/ (pinned Zola is downloaded if none is installed)"
	@echo "  make site-check       - zola check, the symlinked data test, and deno task test"
	@echo "  make deploy-ladder-sepolia - Deploy them (reads DEPLOYER_KEY), then record"
	@echo "  make verify-ladder-sepolia - Verify them on Sourcify (and Etherscan if ETHERSCAN_API_KEY is set)"
	@echo "  make fetch-baseline   - Re-fetch the legacy Huff runtime bytecode from Sepolia"
	@echo "  make predict          - Print the CREATE2 address of the current FP127 object"
	@echo "  make deploy-sepolia   - Deploy via the CREATE2 proxy (reads DEPLOYER_KEY)"
	@echo "  make verify-sepolia   - Prove the live runtime equals the artifact, then verify on Sourcify + Blockscout"
	@echo "  make smoke-sepolia    - Run every committed vector against the live Sepolia contract"
	@echo ""

gen:
	@$(PY) scripts/fp127/gen.py

gen-check:
	@$(PY) scripts/fp127/gen.py --check
	@test ! -f contracts/src/fp256/FP256.yul.src || $(PY) scripts/fp127/gen.py --lib fp256 --check

gen-fp256:
	@$(PY) scripts/fp127/gen.py --lib fp256

vectors:
	@$(PY) scripts/fp127/oracle.py vectors

vectors-check:
	@$(PY) scripts/fp127/oracle.py check
	@test ! -f scripts/fp256/vector_spec.json || $(PY) scripts/fp256/oracle.py check

vectors-fp256:
	@$(PY) scripts/fp256/oracle.py vectors

build: gen-check gen-inputs-check
	@forge build
	@$(MAKE) -s build-fp256

# FP256.yul is compiled by solc directly (Foundry 1.8 batches Yul sources,
# and Yul mode takes one file); the artifact has the Foundry shape.
build-fp256:
	@test ! -f contracts/src/fp256/FP256.yul || FP_LIB=fp256 $(PY) scripts/fp127/stdjson.py artifact

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

size-fp256: build
	@$(PY) python -c "import json;b=json.load(open('out/FP256.yul/FP256.json'))['deployedBytecode']['object'];print('FP256 runtime:', (len(b)-2)//2, 'bytes of 24576')"

ladder: build
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py

ladder-check: build ladder-selftest
	@forge test --match-contract "^Ladder$$" -vv | $(PY) scripts/ladder/ladder.py --check

precision-report:
	@$(PY) scripts/fp127/precision_report.py

precision-report-fp256:
	@$(PY) scripts/fp127/precision_report.py --lib fp256

size: build
	@$(PY) python -c "import json;d=json.load(open('out/FP127.yul/FP127.json'));b=d['deployedBytecode']['object'];print('FP127 runtime:', (len(b)-2)//2, 'bytes of 24576')"

bench: build
	@forge test --match-contract "^GasLadder$$" -vv | $(PY) scripts/fp127/gas_to_json.py

pi-compare: build
	@forge test --match-contract PiCompare -vv | $(PY) scripts/fp127/pi_compare.py

fetch-baseline:
	@mkdir -p contracts/archive/huff
	@cast code $(BASELINE_ADDR) --rpc-url $(SEPOLIA_RPC) | tr -d "\n" > contracts/archive/huff/fp127.sepolia.runtime.hex
	@echo "fetched at block $$(cast block-number --rpc-url $(SEPOLIA_RPC))"
	@cast keccak "$$(cat contracts/archive/huff/fp127.sepolia.runtime.hex)"

# ---- deployment ------------------------------------------------------------

DEPLOY_SCRIPT := script/DeployFP127.s.sol
CREATE2_PROXY := 0x4e59b44847b379578588920cA78FbF26c0B4956C
SALT := 0x4650313237207634000000000000000000000000000000000000000000000000
# Sepolia (Amsterdam fork) charges about 1,550 gas per byte of deposited code,
# not 200: the node estimates ~10.45M gas for this deployment where forge
# 1.7.1's local EVM says 1.46M, so the transaction is sent with an explicit limit.
DEPLOY_GAS ?= 20000000

predict: build
	@forge script $(DEPLOY_SCRIPT) --sig "predict()" --rpc-url $(SEPOLIA_RPC) 2>&1 | grep -E "deployer|salt|hash|keccak|bytes|address|deployed"

deploy-sepolia: build
	@test -n "$$DEPLOYER_KEY" || (echo "DEPLOYER_KEY is not set" && exit 1)
	@$(PY) scripts/fp127/stdjson.py check
	@set -e; \
	ADDR=$$(forge script $(DEPLOY_SCRIPT) --sig "predict()" --rpc-url $(SEPOLIA_RPC) 2>&1 | grep -E '^\s+address' | awk '{print $$2}'); \
	echo "address $$ADDR"; \
	if [ "$$(cast code $$ADDR --rpc-url $(SEPOLIA_RPC))" != "0x" ]; then echo "already deployed"; exit 0; fi; \
	INIT=$$($(PY) python -c "import json;print(json.load(open('out/FP127.yul/FP127.json'))['bytecode']['object'][2:])"); \
	cast send $(CREATE2_PROXY) "$(SALT)$$INIT" --rpc-url $(SEPOLIA_RPC) --private-key "$$DEPLOYER_KEY" --gas-limit $(DEPLOY_GAS) --json \
		| tee contracts/deployments/FP127.sepolia.receipt.json \
		| $(PY) python -c "import json,sys;r=json.load(sys.stdin);print('status',r['status'],'tx',r['transactionHash'],'block',int(r['blockNumber'],16),'gasUsed',int(r['gasUsed'],16))"; \
	echo "code at $$ADDR: $$(( ($$(cast code $$ADDR --rpc-url $(SEPOLIA_RPC) | wc -c) - 3) / 2 )) bytes"

verify-sepolia: build
	@$(PY) scripts/fp127/stdjson.py check
	@$(PY) scripts/fp127/stdjson.py onchain $(SEPOLIA_RPC) $$($(PY) python -c "import json;print(json.load(open('contracts/deployments/FP127.json'))['address'])")
	@$(PY) scripts/fp127/verify.py 11155111 $$($(PY) python -c "import json;print(json.load(open('contracts/deployments/FP127.json'))['address'])")

smoke-sepolia: build
	@forge test --match-contract Deployed --fork-url $(SEPOLIA_RPC) -vv

# ---- FP256 (the second ruler): same procedure, its own artifact, salt and record

DEPLOY_SCRIPT256 := script/DeployFP256.s.sol
SALT256 := 0x4650323536207633000000000000000000000000000000000000000000000000

predict-fp256: build
	@forge script $(DEPLOY_SCRIPT256) --sig "predict()" --rpc-url $(SEPOLIA_RPC) 2>&1 | grep -E "deployer|salt|hash|keccak|bytes|address|deployed"

deploy-fp256-sepolia: build
	@test -n "$$DEPLOYER_KEY" || (echo "DEPLOYER_KEY is not set" && exit 1)
	@FP_LIB=fp256 $(PY) scripts/fp127/stdjson.py check
	@set -e; \
	ADDR=$$(forge script $(DEPLOY_SCRIPT256) --sig "predict()" --rpc-url $(SEPOLIA_RPC) 2>&1 | grep -E '^\s+address' | awk '{print $$2}'); \
	echo "address $$ADDR"; \
	if [ "$$(cast code $$ADDR --rpc-url $(SEPOLIA_RPC))" != "0x" ]; then echo "already deployed"; exit 0; fi; \
	INIT=$$($(PY) python -c "import json;print(json.load(open('out/FP256.yul/FP256.json'))['bytecode']['object'][2:])"); \
	cast send $(CREATE2_PROXY) "$(SALT256)$$INIT" --rpc-url $(SEPOLIA_RPC) --private-key "$$DEPLOYER_KEY" --gas-limit $(DEPLOY_GAS) --json \
		| tee contracts/deployments/FP256.sepolia.receipt.json \
		| $(PY) python -c "import json,sys;r=json.load(sys.stdin);print('status',r['status'],'tx',r['transactionHash'],'block',int(r['blockNumber'],16),'gasUsed',int(r['gasUsed'],16))"; \
	echo "code at $$ADDR: $$(( ($$(cast code $$ADDR --rpc-url $(SEPOLIA_RPC) | wc -c) - 3) / 2 )) bytes"

verify-fp256-sepolia: build
	@FP_LIB=fp256 $(PY) scripts/fp127/stdjson.py check
	@FP_LIB=fp256 $(PY) scripts/fp127/stdjson.py onchain $(SEPOLIA_RPC) $$($(PY) python -c "import json;print(json.load(open('contracts/deployments/FP256.json'))['address'])")
	@FP_LIB=fp256 $(PY) scripts/fp127/verify.py 11155111 $$($(PY) python -c "import json;print(json.load(open('contracts/deployments/FP256.json'))['address'])")

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
