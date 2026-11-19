# Blockulator: rules for anyone working in this repository

## What the product is

Two libraries, and nothing else:

- **BL127**: signed 127.128 fixed point in one `int256` (`contracts/src/bl127/`).
- **BL19**: a 256-bit binary float in one `int256` (`contracts/src/bl19/`).

Blockulator is a ruler first: the reference its author, an auditor, measures the rest of the industry's
math against. Use inside production contracts is the second step. Everything else in the repository is
evidence that the two libraries are right (tests, proofs, sweeps) or a comparison of them with other
libraries (the ladder, edges, replays, benchmarks).

## What needs the owner's explicit approval

Do not add any of these on your own initiative, however useful it looks:

- a new library, contract, wrapper or compatibility layer;
- a new entry in the published package (`scripts/pack/pack.py` holds the list of what ships);
- a new page or section on the site, or a new headline claim;
- a new public name.

If a task seems to need one, stop and ask, in plain words, one decision at a time.

## Comparisons

When a comparison needs an "ours" column, it is BL19 and BL127 called through their own public API.
List them first, BL19 then BL127, then the other libraries. Publish what is measured, including the
rows where another library does better.

## Claims

- Every number in public copy comes from a committed dataset, and a claim is scoped to the ops it was
  measured on.
- The libraries are on Sepolia only and have had no third-party audit. Their assurance is the formal
  proofs, the sweeps and the fact that every measurement can be rerun. Say so where it matters.
- They need the CLZ opcode (EIP-7939). There is one build, for chains that have it.

## Names

BL127 and BL19 everywhere. The only place the old names appear is a deployed object's salt or on-chain
verified name ("FP127 v9", "FP19 v6"), quoted, until the next deployment.

## Before judging the state of the repository

`git fetch` and compare with `origin/master` first. A local checkout can be many commits behind.
