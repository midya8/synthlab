# SynthLab

SynthLab implements counterexample-guided inductive synthesis for tiny unsigned bit-vector expressions. A learner selects a minimum-cost program fitting current examples; an exact finite verifier returns the first wrong input until the program is correct or the bounded grammar is exhausted. Every candidate, counterexample, eliminated function and full-domain output signature is replayable.

[Live inspector](https://midya8.github.io/synthlab/) | [Exact grammar, certificate and sources](CONTRACT.md)

## Choose a question

- **Synthesis:** find a minimum-node expression fitting examples, then check it on the entire supplied finite domain.
- **Teaching sets:** find the smallest example sets that distinguish a representable target from every rival function in the grammar.
- **Adaptive identification:** find a minimax query policy for identifying any function consistent with the initial observations.

Correctness on the finite domain, unique identification from examples and grammar-relative
minimum expression cost are different claims. The inspectors retain each boundary.

## Grammar and verification

A constant can fit the first XOR example. A variable can fit several more. Neither implements XOR. Bitwise complement is not modular negation. A grammar missing an operator and a bound missing one node can both exclude a solution, without proving that no program exists.

SynthLab separates three claims: fits known examples, is correct on every supplied finite input, and has minimum AST node cost within the declared grammar. A full-domain semantic quotient keeps the cheapest canonical representative of each function. This quotient does not depend on target values or examples. An independent verifier enumerates **every raw grammar tree** through the cost bound, without semantic pruning or calling the generator's evaluator/frontier/text functions. That gives a separate check of grammar completeness and canonical minimum cost.

## Run offline

```bash
python -m unittest discover -s tests -v
npm test                      # Node 22+ and actual Chrome
bash tools/check_wheel.sh      # installed, outside-checkout reproduction
python -m http.server 8000 --directory docs
python -m synthlab request.json --output certificate.json
python -m synthlab certificate.json --verify
pip install .
synthlab request.json --output certificate.json
```

No model, API key, runtime dependency, private data or paid service. The browser needs no network after local assets load.

## Evidence and scope

The original eight native tests include all 512 Boolean target/operator-subset combinations (16 functions × 32 grammars), independent raw-tree minimum-cost checks and all 2,764 raw trees in the largest grammar through node cost 5 at each of three bit widths. Eighty complete native/browser-engine reports match and independently verify. Actual Chrome at 320/390/1280 replays 90 iterations, 903 candidate signatures and 3,420 expression probes across 30 reports, including full truth tables, evaluation-tree values, exports and stale-state clearing. The installed wheel reproduces all ten controls through module/console generation and verification outside the checkout.

Bounds are 1..3-bit unsigned x/y, constants 0/1, a selected subset of add/and/neg/not/xor and maximum AST node cost 1..5. The complete target table is supplied. Exact verification is possible because the domain has at most 64 rows. These are synthetic controls, not SyGuS competition benchmarks or production coding tasks. No runtime-optimality, novel algorithm, unbounded synthesis, solver-integration or unknown-service claim.

CEGIS is credited to Solar-Lezama and colleagues; grammar-guided enumerative search and semantic equivalence are established ideas. This is an original bounded implementation and inspector, not SKETCH, cvc5, an e-graph implementation or a new synthesis method. MIT licensed. [Full attribution and conventions](CONTRACT.md).


## Exact teaching-set atlas

`teaching.html` separates verified correctness from unique identification by examples. Every subset of a 1..2-bit input domain is checked against every rival function. Inspect all minimum teaching sets, seed-preserving extensions and deletion witnesses, plus the CEGIS examples that may still leave rivals. The target must be representable in the explicit grammar. [Exact contract and established teaching-set attribution](TEACHING.md).

```bash
python -m synthlab.teaching_cli request.json --output teaching.json
python -m synthlab.teaching_cli teaching.json --verify
synthlab-teaching request.json --output teaching.json
```

The teaching release checked fifteen combined native tests on Python 3.10-3.13. Seven combined Node/actual-Chrome checks preserved the base and added 15 teaching reports, 1,203 subset selections and 597 rival selections at 320/390/1280. Installed outside-checkout reproduction covers both certificate families. The atlas checks every subset in its explicit finite domain; no class-wide teaching-dimension or generalization claim.

## Exact adaptive identification

The adaptive atlas finds the exact worst-case number of further input queries needed to identify any function still fitting the initial observations. It audits every nonempty version space, every label partition, all minimax ties, the best and worst balanced-heuristic tie resolutions, an exact passive baseline and every canonical target path. No arbitrary easy hypothesis subset is selected. A full seeded grammar control needs two further adaptive queries versus three fixed passive rows.

See [the adaptive contract](ADAPTIVE.md) and `docs/adaptive.html`. Reproduce with `python -m synthlab.adaptive_cli request.json --output policy.json`, then verify with `python -m synthlab.adaptive_cli policy.json --verify`. Existing synthesis and teaching formats remain unchanged.
