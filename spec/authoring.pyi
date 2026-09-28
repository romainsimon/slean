"""Draft signatures only. No runtime SDK or verification implementation is supplied here."""

from collections.abc import Mapping, Sequence
from typing import Literal, NotRequired, Protocol, TypedDict

type Json = None | bool | int | float | str | list[Json] | dict[str, Json]
type ComponentKind = Literal["claim", "model", "method", "data"]
type LeafStatus = Literal["satisfied", "violated", "unresolved", "unsupported"]
type Compatibility = Literal["compatible", "conditional", "incompatible", "unsupported"]

class Ref(TypedDict):
    id: str
    module: NotRequired[str]

class Artifact(TypedDict):
    path: str
    module: NotRequired[str]

class ProfileValue(TypedDict):
    profile: str
    value: dict[str, Json]

class Requirement(TypedDict):
    id: str
    # Exactly one operator is permitted; the wire schema enforces this union.
    all: NotRequired[list[Requirement]]
    any: NotRequired[list[Requirement]]
    leaf: NotRequired[dict[str, Json]]

class Binding(TypedDict):
    # Exactly one source member; `output` optionally selects an executed application's port.
    literal: NotRequired[str | bool | None]
    ref: NotRequired[Ref]
    output: NotRequired[str]
    artifact: NotRequired[Artifact]
    typed: NotRequired[ProfileValue]

class Obligation(TypedDict):
    requirement: str
    status: LeafStatus
    reason: str
    witnesses: list[Ref]

class ApplicationPlan(TypedDict):
    application: Ref
    compatibility: Compatibility
    obligations: list[Obligation]
    selections: dict[str, str]

class VerificationReport(TypedDict):
    module: str
    subject: Ref
    policy: str
    layer: Literal["integrity", "interface", "formal", "computation", "empirical"]
    outcome: str
    artifacts: list[Artifact]
    diagnostics: list[str]

class Author(Protocol):
    def component(self, *, id: str, kind: ComponentKind, name: str,
                  interface: ProfileValue, requires: Requirement,
                  sources: Sequence[Artifact], license: str,
                  supersedes: Sequence[Ref] = ()) -> Ref: ...
    def question(self, *, id: str, wording: str, source: str,
                 targets: Sequence[Ref] = (), motivated_by: Ref | None = None) -> Ref: ...
    def plan(self, component: Ref, *, id: str, bindings: Mapping[str, Binding],
             context: Mapping[str, Binding], extra_requirements: Requirement | None = None) -> Ref: ...
    def plan_test(self, component: Ref, *, id: str, question: Ref,
                  bindings: Mapping[str, Binding], context: Mapping[str, Binding],
                  prediction: ProfileValue, bound: ProfileValue, observation_id: str) -> Ref: ...
    def record_execution(self, plan: Ref, *, id: str, outputs: Mapping[str, Binding]) -> Ref: ...
    def record_evidence(self, *, id: str, kind: Literal["formal", "computation", "empirical", "assertion"],
                        subject: Ref, context: Mapping[str, Binding], policy: str,
                        implementation: Artifact, artifacts: Sequence[Artifact], result: ProfileValue) -> Ref: ...
    def record_attempt(self, application: Ref, *, question: Ref, attempt_of: str,
                       previous_attempt: Ref | None, contributions: Sequence[Ref],
                       obstacles: Sequence[Obligation]) -> None: ...
    def pack(self, destination: str, *, publishable: Sequence[Ref]) -> str: ...

class Reader(Protocol):
    def inspect(self, component: Ref) -> Mapping[str, Json]: ...
    def apply(self, component: Ref, *, bindings: Mapping[str, Binding],
              context: Mapping[str, Binding], policy: str) -> ApplicationPlan: ...
    def verify(self, subject: Ref, *, policy: str) -> VerificationReport: ...
    def uses(self, subject: Ref) -> Sequence[Ref]: ...
