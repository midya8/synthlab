# SynthLab: finite bit-vector synthesis with independent certificates

[Live inspector](https://midya8.github.io/synthlab/). This is an explanatory implementation of established CEGIS and bottom-up enumerative synthesis, not a new algorithm. Exact claims are about a supplied finite truth table and the explicit expression grammar below.

## Request, arithmetic and grammar

Input has exactly `bits`, `operators`, `max_cost`, `target`, `seeds`.

- `bits` is an integer1..3. Inputs x/y and all outputs are unsigned words0..2^bits-1. Every pair is included, ordered by x then y. Row index is x·2^bits+y.
- `operators` is a sorted unique subset of `add`, `and`, `neg`, `not`, `xor`. Empty is allowed. The terminals0,1,x,y are always available.
- `max_cost` is an integer1..5. **Every terminal and operator node costs one.** Cost is AST node count, including repeated subtrees separately. This differs from papers that count only non-nullary operators; do not compare their numeric bounds directly.
- `target` contains exactly4^bits integers in row order. This is the complete specification, not a few training examples, a hidden service or an arbitrary logical formula.
- `seeds` contains sorted unique row indices. These are the examples known to the learner initially. Empty and full-domain seed sets are allowed.

Grammar: `E := 0 | 1 | x | y | (not E) | (neg E) | (add E E) | (and E E) | (xor E E)`, restricted to the selected operators. Ordered binary children are enumerated; no commutativity pruning is assumed. All functions are pure and total, with no loops, conditionals, multiplication, shifts, side effects or external calls.

`not` flips exactly the selected bits. `neg` computes -v modulo2^bits. `add` adds modulo2^bits. `and`/`xor` are fixed-width bitwise operations. No signed comparison, arithmetic overflow trap, saturation or machine-dependent word width is used. The bit-vector semantics follow the relevant SMT-LIB operations, but SynthLab does not implement the SMT-LIB or SyGuS input languages.

## Complete semantic frontier and canonical witnesses

The generator enumerates costs in increasing order. At each cost it forms every grammar production whose retained children have the required total node cost. It evaluates each resulting expression on **every input row**, not only the current examples, and keeps one representative per full-domain signature. The representative has minimum cost, then lexicographically smallest fully parenthesized prefix text using ordinary ASCII ordering. IDs follow cost, then this text. Constants are written0/1, variables x/y, and operator applications such as `(add (and 1 y) x)`.

Why quotienting is safe here: identical full-domain signatures mean identical values for every allowed x/y. Pure total operators are congruent under this equivalence. Replacing a discarded subexpression with its representative preserves every output and cannot increase cost. Equal-cost lexicographically smaller subexpressions preserve or improve the surrounding prefix text. Induction on tree structure therefore preserves at least one cheapest canonical representative of every grammar-definable function through the bound. This argument relies on the single nonterminal, common output sort and compositional total semantics. It would need rechecking for a different grammar, context-sensitive constraints, effects or partial operations.

The frontier depends on bit width, operators and bound, **not target outputs or seed examples**. Full-domain semantic evaluation is explicitly available in this tiny simulator; it is not a black-box query-saving claim. Layer `compositions` counts attempted productions of retained representatives. It is not the number of all raw grammar trees, unique syntactic programs, instructions or elapsed-time work.

## Deterministic CEGIS replay

Each iteration records all examples before the iteration, every eligible function ID, the chosen candidate, the counterexample, every newly eliminated ID, the next example set and status.

1. A function is eligible exactly when its full-domain output vector agrees with the target on every currently known example.
2. Select the first eligible ID, therefore the cheapest/canonical candidate that fits the examples.
3. Compare it against the **entire** target table. The first wrong row in x-major order is the counterexample. It is added to the sorted example set. All currently eligible functions wrong at that row are recorded as eliminated.
4. If no wrong row exists, status is `solved`. If no eligible function remains, status is `exhausted-in-bound`.

A counterexample is necessarily new and eliminates at least the chosen candidate. There are at most domain-size counterexamples. A solved program agrees with every finite input. It has minimum cost within the declared grammar: any cheaper correct function would have remained eligible at every iteration and been chosen first. An exhausted result proves absence only through the stated bound. It does not prove the target has no implementation or that no larger grammar expression works.

## Certificate and genuinely separate checks

`synthlab-v1` contains the normalized request, complete input rows, every minimum-cost semantic representative with AST/text/full outputs, layer counts, every CEGIS step, solution ID or null, and a derived summary.

The native verifier does **not** call synthesis, frontier construction, the generator evaluator or text printer. It builds every **raw ordered grammar tree**, without semantic pruning, independently evaluates output vectors and derives the minimum-cost/lexicographic representative map. It then compares the complete pool, independently computes representative-production counts, replays every eligible set/choice/counterexample/elimination and checks all summary fields with strict keys and types. This bounded exhaustive verification is not a machine-checked proof of a general synthesis theorem.

The largest allowed grammar through node cost5 has2764 raw trees: counts4,8,64,320,2368 at costs1..5. Cost limits are intentional; raw enumeration would grow quickly with larger bounds. Small bounds make a separate exhaustive verifier practical, not a scalable industrial solver claim.

CLI generation reads at most64KiB; verification at most8MiB. Duplicate decoded JSON keys, nonfinite values and nesting beyond64 levels are rejected. Output files replace atomically only after successful generation/verification. Browser parsing additionally rejects decimal/exponent numeric literals instead of silently coercing them to integers. Browser editing clears old reports/selections and disables stale export.

## Tests and controls

Ten synthetic controls cover XOR learned from too few examples, bitwise AND on64 inputs, width-dependent complement, modular addition, modular negation, composed arithmetic/bitwise grammar, missing operators, too-small cost bound, a fully seeded Boolean task and the largest allowed grammar/domain. These are defined for this project, not copied competition benchmarks. The mathematical operations are standard and no invented task attribution is made.

Eight native tests include all16 Boolean functions ×all32 operator subsets at bound5, with an independent raw-tree/bit-list oracle for representability and minimum cost. Another check enumerates all2764 largest-grammar trees at each of three widths and compares the exact canonical signature map. Eighty seeded finite targets/costs, ten controls, strict requests, forged certificates, disabled generator dependencies and CLI size/depth/atomicity checks are separate. The frontier is also checked to remain unchanged when only target/seeds change. Tests run on Python3.10-3.13.

Three Node tests compare80 full reports (ten controls+70 seeded), independently verified natively, and check strict parsing and arithmetic distinctions. Actual Chrome runs all controls at320/390/1280:30 complete reports,90 iterations,903 candidate signatures and3420 expression probes. It checks every example/eligible/eliminated set, complete truth-table rows, evaluation-tree values, previous/next controls, export and stale clearing. The four Node/Chrome checks and installed outside-checkout module/console reproduction are part of CI.

## Offline reproduction

```bash
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m http.server 8000 --directory docs
python -m synthlab request.json --output certificate.json
python -m synthlab certificate.json --verify
pip install .
synthlab request.json --output certificate.json
synthlab certificate.json --verify
```

A two-bit XOR request:

```json
{"bits":2,"operators":["xor"],"max_cost":3,"target":[0,1,2,3,1,0,3,2,2,3,0,1,3,2,1,0],"seeds":[0]}
```

## Sources, credit and differences

1. [Solar-Lezama, Tancau, Bodik, Saraswat and Seshia, *Combinatorial Sketching for Finite Programs*, ASPLOS2006](https://people.csail.mit.edu/asolar/papers/asplos06-final.pdf), Section5.4: counterexample-driven synthesize/verify loop. Their SKETCH/SAT system is not implemented here, and none of its cryptography/performance claims apply to SynthLab.
2. [Stanford CS357, *Syntax-Guided Synthesis* lecture](https://web.stanford.edu/class/cs357/lecture15.pdf): syntax/semantic restrictions and enumerative CEGIS background. Our exact finite-table oracle and node-cost convention are stated independently.
3. [Barbosa, Reynolds, Larraz and Tinelli, *Extending enumerative function synthesis via SMT-driven classification*, FMCAD2019](http://theory.stanford.edu/~barrett/fmcad/papers/FMCAD2019_paper_63.pdf): grammar-guided increasing-size enumeration and CEGIS refinement. We do not implement its classification/divide-and-conquer method or borrow its non-nullary-symbol cost definition.
4. [Frankel, Schneider, Steuwer and Polgreen, *Syntax-Guided Synthesis with Counterexample-Guided E-graphs*, SMT2025 work-in-progress](https://ceur-ws.org/Vol-4008/SMT_paper11.pdf): observational equivalence/congruence and counterexample context. SynthLab uses full-domain signatures on a finite space, not e-graphs, CE-graphs or their evaluation claims.
5. [SMT-LIB FixedSizeBitVectors theory](https://smt-lib.org/theories-FixedSizeBitVectors.shtml), page last-updated2025-09-09 when fetched: fixed-width not/and/neg/add semantics. XOR is the usual per-bit exclusive-or; no broader SMT-LIB conformance is claimed.
6. [cvc5 SyGuS grammar example documentation, version1.0.7](https://cvc5.github.io/docs/cvc5-1.0.7/examples/sygus-grammar.html): grammar-constrained synthesis as an existing supported tool capability. SynthLab has no cvc5 dependency, compatible API or solver integration.

Search lead `sygus.org/language/` did not fetch and is not evidence for this implementation. No novel algorithm, neural synthesis, benchmark win, runtime-optimality, unbounded logical verification, real-world coding ability or hidden-service guarantee is claimed.
