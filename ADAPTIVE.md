# Exact adaptive identification

This contract covers adaptive identification. Base synthesis and target-specific teaching retain their separate versioned certificate formats.

## Model and scope

The complete semantic grammar frontier is the hypothesis class. Initial observations are exactly the request's `seeds` and their supplied target labels, not CEGIS's later examples. Filtering on those labels creates the initial version space. No arbitrary hypothesis subset is selected to make the task easier. The target must be representable; the bit width must be one or two; and at most ten functions may remain after initial observations. Larger spaces are rejected with an instruction to add initial observations, never silently truncated.

Every future query asks the output at one input row. It has unit cost, returns an exact label, and may have up to four outcomes. The policy must identify any function in the initial space. Future labels are simulated from the supplied complete function tables. This is an inspectable offline policy experiment, not a connection to a hidden oracle.

Initial observations and further queries are reported separately. The objective is deterministic worst-case remaining query count. There is no probability prior, expected-depth objective, cost weighting, noise model, PAC guarantee, or claim about identifying source syntax. Equivalent grammar expressions are one semantic function.

## Exact recurrence

Local bit `j` represents `initial_ids[j]`, which is a grammar ID. Every nonempty local mask has a state record. These include subsets not necessarily reachable from a sequence of queries; auditing them closes the recurrence and permits arbitrary version-space inspection.

For a singleton, `D(V) = 0`. Every query partitions `V` by output label. A non-splitting query is listed with a null score and cannot improve a policy. For splitting queries:

```
D(V) = min_row (1 + max_label D(V restricted to that row and label))
```

Each nonempty branch is a proper submask. Numeric mask order is therefore topological. All rows attaining the exact minimum are retained. The canonical policy uses the smallest row index at every state. This is a reproducibility tie-break, not a second quality objective. Every possible target has a complete canonical-policy trace to its own leaf, and the longest trace equals `D` at the root.

A separate verifier first checks the embedded base certificate by raw ordered grammar-tree enumeration. It then reconstructs explicit members and every label partition independently, checking every state, query score, minimax tie list, balanced-policy bound, canonical tree, target trace and summary. It does not call the adaptive generator, its partition construction, or its dynamic program. Native tests also independently enumerate depth-bounded decision policies to show that each reported depth is feasible and the preceding depth is not.

## Fair comparisons

A passive separating set is one fixed set of rows whose label signatures differ for every pair of initial hypotheses. Every row subset is considered, and every minimum-cardinality passive mask is retained in ascending numeric order. This is class separation, not a target-specific teaching set. The passive verifier independently projects full output tuples and checks their distinctness.

The most-balanced heuristic minimizes the largest immediate branch cardinality. It is not generally equivalent to minimizing total worst-case depth. All immediate balance ties are retained. Two further recurrences report the best and worst worst-case depths obtainable over all balanced tie resolutions at every future state. The baseline is not weakened by picking an unlucky tie and calling it representative. The minimum of the balanced-policy depths cannot beat exact minimax.

## A real seeded grammar control

Use the full two-bit grammar with all five operators through AST node cost five. The target is `(not (neg y))`; initial rows are 7 and 12. Those two labels leave ten functions, with grammar IDs 19, 22, 24, 50, 51, 64, 67, 71, 112 and 113. The atlas audits all 1,023 nonempty version spaces.

Two more adaptive queries suffice in the worst case. Every fixed passive separating set requires three rows; there are 30 tied minima. Root minimax query rows are 2 and 10. Most-balanced root rows are 1, 2 and 11, and complete balanced-policy tie choices can require two or three further queries. Thus a balanced split can be optimal, but immediate balance alone does not settle the policy objective. These are exact finite counts for a synthetic control, not production-model performance.

Other controls cover a Boolean class without initial observations, a multiway word-valued query, an already identified singleton and Boolean XOR after one observation. No claim is made that adaptivity always helps.

## Certificate and CLI

`synthlab-adaptive-v1` contains `synthesis`, `initial_ids`, `states`, `passive`, `policy`, `traces` and `summary`, plus `schema`. Existing synthesis and teaching schemas are unchanged.

```
python -m synthlab.adaptive_cli request.json --output policy.json
python -m synthlab.adaptive_cli policy.json --verify
synthlab-adaptive request.json --output policy.json
synthlab-adaptive policy.json --verify
```

Generation accepts at most 64 KiB of strict JSON. Adaptive verification accepts at most 32 MiB because the certificate lists every query partition in every version space. The largest control's pretty-printed report is 5,713,035 bytes, including its terminal newline. Existing base and teaching verification retain their 8 MiB defaults. Duplicate keys, nonfinite numbers, excess depth, invalid caps and malformed certificates are rejected; file output is atomic. Browser exports use compact JSON.

## Attribution and sources

The implementation is an educational exhaustive finite decision-tree dynamic program, not a new active-learning algorithm. It differs from greedy generalized binary search by solving the tiny remaining minimax problem exactly. The word-valued extension groups each query's outputs by equality rather than forcing binary labels. The worst-case objective is explicitly distinct from average or probability-weighted objectives.

- Robert Nowak, *The Geometry of Generalized Binary Search*: finite unique hypotheses, version-space splits and greedy balance; distinguishes worst-case from average tree depth. https://nowak.ece.wisc.edu/GBS_arxiv_v3.pdf
- Sanjoy Dasgupta, *Analysis of a greedy active learning strategy*: greedy balance can be approximate rather than exactly optimal; probability-weighted and expected-query objectives differ from this contract. https://cseweb.ucsd.edu/~dasgupta/papers/greedy.pdf
- *Generalized Binary Search for Split-Neighborly Problems*: finite identifiable classes and worst-case sequential query evaluation. https://arxiv.org/pdf/1802.09751v1.pdf
- *Query Learning with Exponential Query Costs*: historical exact exponential dynamic programming and distinctions among expected and worst-case objectives. https://ar5iv.labs.arxiv.org/html/1002.4019
- Azad et al., *Decision Trees with Hypotheses for Recognition of Monotone Boolean Functions and for Sorting*: depth as maximum query-path length and exact decision-table dynamic programming. This implementation uses attribute queries only, not equivalence/hypothesis queries. https://ar5iv.labs.arxiv.org/html/2203.08894
- Jeff Erickson, decision-tree notes: adaptive next queries, deterministic minimax tree depth and its distinction from randomized and average-case complexity. https://jeffe.cs.illinois.edu/teaching/497/01-decision-trees.pdf
- Goldman and Kearns, teaching dimension: helpful target-directed examples are a different setup from identifying every unknown function by an adaptive policy. https://www.cis.upenn.edu/~mkearns/papers/teaching.pdf
