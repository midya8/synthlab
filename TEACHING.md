# Exact target-distinguishing sets

[Teaching-set inspector](https://midya8.github.io/synthlab/teaching.html). Exact finite teaching sets supplement the original CEGIS replay.

## Correctness is not unique identification

A CEGIS learner selects the cheapest function fitting current examples. The verifier then checks that chosen function against the complete supplied target. It can be correct while other grammar functions fit every current example. The learner's cost preference is extra information. A teaching set instead requires **every** function consistent with its labeled examples to be the target.

For the Boolean zero target in the and/xor cost3 grammar, CEGIS immediately verifies constant0 with no examples. Seven rival functions still fit the empty sample. The minimum target-distinguishing set has3 rows, with3 tied minima. For two-bit XOR in the full cost5 grammar, CEGIS finishes with4 examples, but3 rival functions remain. The unrestricted teaching minimum also has4 rows, with182 tied minima. Equal cardinality does not mean equal identification power.

## Scope and definitions

Requests use the base `bits,operators,max_cost,target,seeds` schema, restricted to1..2 bits. The complete x-major x/y domain has4 or16 rows. The target must be representable in the grammar through the bound. An unrealizable target is rejected, not described as a uniquely taught member of the class. The complete bounded semantic frontier is included and separately verified by raw-tree enumeration as the base contract describes.

The hypothesis class consists of **distinct full-domain functions**, not syntax trees. Every class member has a canonical minimum-cost program witness. The target's labels are fixed by the supplied table. A selected row eliminates exactly those rivals with a different output at that row. A row subset teaches the target precisely when no rival agrees with every selected label. No learner coding convention, preference order or extra information is assumed.

A teaching set for the target is a cover of all rival functions by row-disagreement sets. This established relationship is credited to Goldman and Kearns. The original Boolean concept definition is extended here explicitly to finite word-valued labels by exact equality. The program computes a **target-specific** minimum, not the maximum of these minima over the entire class, so it does not report class-wide teaching dimension. It is not recursive/preference-based teaching, PAC sample complexity, active-query complexity or a human-teaching experiment.

## Exhaustive atlas

Every row subset is checked:16 or65,536 subsets. Mask bitj selects input rowj; row0 is the low bit. For each mask the report records cardinality, remaining-rival count and whether it teaches. The objective is cardinality only. All minimum masks are retained in numeric order; the smallest numeric mask is the canonical display default, not a second quality objective. An unrestricted optimum can omit original seed examples.

The seed-constrained problem retains every original seed and minimizes total sample cardinality. Since seed cardinality is fixed, this also minimizes the number of additional examples. All tied seed-constrained minimum masks are retained. It is not the same optimization as replacing the seeds with any teaching set.

For each row in the canonical unrestricted optimum, deletion witnesses identify the first rival agreeing on all remaining selected rows. These show irredundancy of that chosen set; they are not the proof of global minimum cardinality. The exhaustive subset atlas supplies the latter. The final CEGIS sample records all remaining rival IDs separately. A correct selected candidate is never promoted to a teaching-set claim merely because its verifier succeeds.

## Independent verifier

The generator computes per-row agreement bitsets and builds subset survivor bitsets using a least-significant-bit recurrence. JavaScript uses BigInt for function sets because there can be more than32 rivals. Row masks use ordinary integers because there are at most16 rows. BigInts never leak into JSON.

The verifier calls the base independent raw-tree certificate verifier, but never calls the atlas generator or its subset helpers. It reconstructs disagreement **sets**, directly visits every subset and rival with set intersection, checks all per-subset fields, all minimum ties, every seed constraint, deletion witness, CEGIS ambiguity and summary. Strict equality rejects extra fields and bool-as-integer substitutions. Bounds keep this exponential audit feasible; no scalable optimization claim is made.

## Reproduce offline

```bash
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m synthlab.teaching_cli request.json --output teaching.json
python -m synthlab.teaching_cli teaching.json --verify
pip install .
synthlab-teaching request.json --output teaching.json
synthlab-teaching teaching.json --verify
python -m http.server 8000 --directory docs
# Open teaching.html
```

Strict CLI transport reuses the base64KiB request and8MiB certificate caps, duplicate-key/nonfinite/depth rejection and atomic output. The largest selected two-bit control is about6.8MB with CLI pretty printing and fits the verification cap. Browser exports compact JSON. CLI and console reproduction run outside checkout against installed modules.

Tests preserve all base synthesis controls. New native checks cover every realizable Boolean function in every one of32 operator subsets, all16 seed masks, full two-bit65,536-subset exactness, forgery, disabled-generator independence, unrealizable/large-domain rejection and CLI round-trip/atomic rejection. Two new Node checks compare41 full atlases and independently verify them. Actual Chrome at320/390/1280 checks five controls,15 complete reports,1,203 subset selections and597 rival truth-table selections, including every tiny-domain subset, every tied unrestricted minimum for large controls, all rival signatures at the CEGIS sample, selected labels, witness rows, seed-preserving/CEGIS shortcuts, invalid-selection clearing, certificate export and stale request clearing.

## Sources and attribution

- Goldman and Kearns, *On the Complexity of Teaching*, original technical report dated1992, later JCSS1995: formal unique-consistent-concept definition and Theorem8 cover equivalence. https://www.cis.upenn.edu/~mkearns/papers/teaching.pdf
- Columbia COMS6998 lecture notes,2017: target minimum versus class-wide maximum distinction. https://www.cs.columbia.edu/~djhsu/coms6998-f17/student-work/scribe-notes/teaching_dimension.pdf
- Princeton interactive-learning lecture notes,2017: version-space singleton constraint and separate target/class quantities. https://www.cs.princeton.edu/courses/archive/fall17/cos597A/lecnotes/machineteaching.pdf
- Khan, Mutlu and Zhu, *How Do Humans Teach: On Curriculum Learning and Teaching Dimension*, NeurIPS2011: teaching-set/class definitions and the distinction between formal teaching predictions and human experiments. No human-behavior result is claimed for SynthLab. https://proceedings.neurips.cc/paper_files/paper/2011/file/f9028faec74be6ec9b852b0a542e2f39-Paper.pdf
- Zhu's machine-teaching project bibliography: broader teaching literature and variants, not an implementation specification. https://pages.cs.wisc.edu/~jerryzhu/machineteaching/
- Zhu, Singla, Zilles and Rafferty, *An Overview of Machine Teaching*,2018: singleton version-space teaching objective and distinction from preference-based/recursive models. https://arxiv.org/pdf/1801.05927
- Base synthesis research and fixed-width semantics are attributed in [CONTRACT.md](CONTRACT.md).

No new teaching algorithm, unbounded guarantee, class-wide teaching dimension, generalization result, speedup or human-learning evidence is claimed. All controls are synthetic and project-defined.
