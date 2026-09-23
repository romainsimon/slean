import Verso
import VersoManual
import VersoBlueprint
import Slean

open Verso.Genre
open Verso.Genre.Manual
open Informal

#doc (Manual) "Synthetic Slean case" =>

This is a manual Blueprint rendering of `examples/valid.json` in Slean. Every number and event is synthetic. Blueprint labels make the decision path navigable; Slean validates the JSON journal.

:::definition "claim-1"
The synthetic claim says that the stated metric exceeds `0.001` on the stated input. This is an experiment claim, not a Lean theorem.
:::

:::definition "protocol-1"
Event 1 freezes protocol `protocol-1` for {uses "claim-1"}[the claim]: evaluator `synthetic-evaluator-v1`, metric `synthetic_delta`, unit `ratio`, threshold strictly greater than `0.001`, and a `10.00 cpu_s` cap.
:::

:::definition "run-1"
Event 2 starts `run-1` on synthetic input A with seed 7 under {uses "protocol-1"}[the frozen protocol].
:::

:::definition "artifact-1"
Event 3 registers the synthetic JSON artifact with a placeholder digest. It is not a hash of a real measurement.
:::

:::definition "observation-1"
Event 4 records `synthetic_delta = 0.002 ratio` for {uses "run-1"}[run-1], citing {uses "artifact-1"}[artifact-1].
:::

:::definition "cost-1"
Event 5 records `2.50 cpu_s` of machine time for {uses "run-1"}[run-1].
:::

:::definition "assessment-1"
Event 6 records `pass` by `exact_v0`, citing {uses "protocol-1"}[protocol-1] and {uses "observation-1"}[observation-1]. This node reports the fixture value; Blueprint does not recalculate the decimal rule.
:::

:::definition "decision-1"
Event 7 records `promote` from {uses "assessment-1"}[assessment-1]. This node reports the fixture value; Blueprint does not validate journal chronology or audience filtering.
:::

:::definition "relation-1"
Event 8 records a support relation from {uses "observation-1"}[observation-1] to {uses "claim-1"}[claim-1].
:::

Events 9 and 10 are an owner-only artifact and observation after the decision. They are deliberately omitted from this agent-facing rendering. Slean's agent projection omits them automatically; this manual Blueprint text must be reviewed before publication because it has no automatic audience projection.

:::theorem "formal-promotion-witness" (lean := "Slean.promotionEvidence_has_frozen_observation")
Slean separately proves a conditional local witness: if promotion evidence exists, it includes a frozen protocol and a linked observation. This theorem does not establish that the synthetic observation or any external experiment is true.
:::
