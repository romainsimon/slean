"""Build scientific records without running their source or claiming verification.

The bundled validator is generated from the canonical reference checker.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import tempfile

from . import contract
import rfc8785

from .quantities import PROFILE as QUANTITY, _validate as validate_scalar, check_scalar

RESEARCH = "slean-research/0.1-draft.1"
LEAN = "slean-lean/0.1-draft.1"
KNOWN_PROFILES = {QUANTITY, RESEARCH, LEAN}


def _walk(value):
    """Visit core fields and supported annotations; unknown annotations are data."""
    if isinstance(value, dict):
        yield value
        for key, child in value.items():
            if key == "value" and value.get("profile") not in KNOWN_PROFILES and "profile" in value:
                continue
            if key == "arguments" and "predicate" in value and not (
                (value.get("profile") == LEAN and value["predicate"] == "proposition") or
                (value.get("profile") == QUANTITY and value["predicate"] in {"quantity", "range", "equals", "applicability"})
            ):
                continue
            if key == "annotations":
                for profile, annotation in child.items():
                    if profile in KNOWN_PROFILES:
                        yield from _walk(annotation)
            else:
                yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _requirements(tree):
    contract.schema(tree, 'module', 'requirement')
    ids = set()
    def visit(node):
        if node['id'] in ids:
            raise ValueError('Duplicate requirement ID: ' + node['id'])
        ids.add(node['id'])
        for child in node.get('all', node.get('any', [])):
            visit(child)
    visit(tree)
    return ids


def qualify_requirements(tree, module):
    """Bind supported producer-local leaf references to their exact revision."""
    tree = deepcopy(tree)
    def visit(node):
        if "leaf" not in node:
            for child in node.get("all", node.get("any", [])):
                visit(child)
            return
        leaf = node["leaf"]
        predicate, profile, arguments = leaf["predicate"], leaf["profile"], leaf["arguments"]
        if (profile, predicate) in {(LEAN, "proposition"), (QUANTITY, "applicability")}:
            arguments["claim"].setdefault("module", module)
        elif profile == QUANTITY and predicate == "equals":
            expected = arguments["expected"]
            for field in ("ref", "artifact"):
                if field in expected:
                    expected[field].setdefault("module", module)
            typed = expected.get("typed", {})
            if typed.get("profile") == QUANTITY and typed.get("value", {}).get("kind") == "table":
                typed["value"]["artifact"].setdefault("module", module)
        # Unknown arguments are opaque bytes. Their owner remains the exact
        # component revision; do not guess reference shapes inside them.
    visit(tree)
    return tree


class Author:
    def __init__(self, *, payloads=None, dependencies=(), profiles=()):
        self._records, self._families, self._payloads, self._dependencies = {}, {}, {}, {}
        self._profiles = {row["id"]: deepcopy(row) for row in profiles}
        for path, data in (payloads or {}).items():
            self.payload(path, data)
        for directory in dependencies:
            path = Path(directory)
            manifest = contract.load((path / 'slean-module.json').read_text())
            contract.check(manifest, path)
            self._dependencies[manifest['id']] = deepcopy(manifest)

    def payload(self, path, data):
        contract.schema({"path": path}, "module", "artifact")
        if not isinstance(data, bytes):
            raise TypeError("Payloads must be explicit immutable bytes")
        if path in self._payloads:
            raise ValueError("Payload already registered: " + path)
        self._payloads[path] = data
        return {"path": path}

    def _add(self, family, record):
        if record["id"] in self._records:
            raise ValueError("Duplicate record ID: " + record["id"])
        if family == "questions":
            contract.schema({"questions": [record], "alternatives": []}, "research", "module")
        else:
            contract.schema(record, "module", 'evidence' if family == 'evidence' else family[:-1])
        self._records[record["id"]] = deepcopy(record)
        self._families[record["id"]] = family
        return {"id": record["id"]}

    def _record(self, reference, family):
        contract.schema(reference, "module", "ref")
        if "module" in reference:
            manifest = self._dependencies.get(reference["module"])
            if manifest is None:
                raise ValueError("Missing exact dependency module")
            records = manifest.get(family, [])
            matches = [r for r in records if r["id"] == reference["id"]]
            if len(matches) != 1:
                raise ValueError("Missing dependency record or wrong family")
            return deepcopy(matches[0])
        if self._families.get(reference["id"]) != family:
            raise ValueError("Missing local record or wrong family")
        return deepcopy(self._records[reference["id"]])

    def component(self, *, id, kind, name, interface, requires, sources, license, supersedes=(), annotations=None):
        record = {"id": id, "kind": kind, "name": name, "interface": deepcopy(interface),
                  "requires": deepcopy(requires), "sources": list(sources), "license": license}
        if supersedes:
            record["supersedes"] = list(supersedes)
        if annotations:
            record["annotations"] = deepcopy(annotations)
        _requirements(requires)
        return self._add("components", record)

    def question(self, *, id, wording, source, targets=(), motivated_by=None):
        record = {"id": id, "wording": wording, "source": source, "targets": list(targets)}
        if motivated_by is not None:
            record["motivated_by"] = motivated_by
        return self._add("questions", record)

    def plan(self, component, *, id, bindings, context, extra_requirements=None):
        producer = self._record(component, "components")
        required = producer["requires"]
        if "module" in component:
            required = qualify_requirements(required, component["module"])
        if extra_requirements is not None:
            used = _requirements(required) | _requirements(extra_requirements)
            suffix = 0
            while f"slean-extra-{suffix}" in used:
                suffix += 1
            required = {"id": f"slean-extra-{suffix}", "all": [required, deepcopy(extra_requirements)]}
        _requirements(required)
        return self._add("applications", {"id": id, "component": component, "phase": "planned",
            "bindings": deepcopy(bindings), "context": deepcopy(context), "requires": required})

    def plan_test(self, component, *, id, question, bindings, context, prediction, bound, observation_id, observable=None):
        if prediction['profile'] != QUANTITY or bound['profile'] != QUANTITY:
            raise ValueError("Unsupported prediction or bound profile")
        expected, limit = validate_scalar(prediction['value']), validate_scalar(bound['value'])
        if expected['value'] is None or limit['value'] is None:
            raise ValueError("A test needs an explicit prediction and evaluation bound")
        if expected['dimension'] != limit['dimension'] or Decimal(limit['value']) < 0:
            raise ValueError('The evaluation bound must be nonnegative and dimensionally compatible')
        if limit['dimension'] == 'temperature':
            raise ValueError('Temperature-difference bounds are unsupported in the initial profile')
        producer = self._record(component, "components")
        if producer['interface']['profile'] != QUANTITY:
            raise ValueError('Scalar prediction requires a supported quantity interface')
        outputs = producer['interface']['value'].get('outputs', {})
        if observable is None:
            if len(outputs) != 1:
                raise ValueError("Select an observable for a method with multiple outputs")
            observable = next(iter(outputs))
        if observable not in outputs:
            raise ValueError("The observable is not a declared output")
        for value in (expected, limit):
            diagnostic = check_scalar(value, outputs[observable])
            if diagnostic['status'] != 'satisfied':
                raise ValueError('Unsupported or incompatible prediction/bound: ' + diagnostic['reason'])
        reference = self.plan(component, id=id, bindings=bindings, context=context)
        self._records[id]['annotations'] = {RESEARCH: {'role': 'test-plan', 'question': deepcopy(question),
            'prediction': {'observable': observable, 'expected': expected, 'comparison': 'absolute_difference',
                           'bound': limit, 'observation': observation_id}}}
        return reference

    def record_execution(self, plan, *, id, outputs):
        previous = self._record(plan, 'applications')
        if previous['phase'] != 'planned':
            raise ValueError("Execution must refer to a planned application")
        record = {key: previous[key] for key in ('component', 'bindings', 'context', 'requires')}
        if 'module' in plan:
            record['requires'] = qualify_requirements(record['requires'], plan['module'])
            for node in _walk(record):
                if set(node) in ({'id'}, {'path'}):
                    node['module'] = plan['module']
        record.update(id=id, phase='executed', outputs=deepcopy(outputs), plan=deepcopy(plan))
        if previous.get('annotations', {}).get(RESEARCH, {}).get('role') == 'test-plan':
            record['annotations'] = {RESEARCH: {'role': 'test-execution'}}
        return self._add('applications', record)

    def record_evidence(self, *, id, kind, subject, context, policy, implementation, artifacts, result):
        return self._add('evidence', {'id': id, 'kind': kind, 'subject': subject, 'context': deepcopy(context),
            'method': {'policy': policy, 'implementation': implementation}, 'artifacts': list(artifacts), 'result': result})

    def record_attempt(self, application, *, question, attempt_of, previous_attempt, contributions, obstacles):
        if 'module' in application:
            raise ValueError("Annotate an owned local attempt")
        record = self._record(application, 'applications')
        if RESEARCH in record.get('annotations', {}):
            raise ValueError('Preserve the existing research record; author a separate reuse attempt')
        value = {'role': 'reuse-attempt', 'question': question, 'attempt_of': attempt_of,
                 'contributions': list(contributions), 'obstacles': [
                     {key: obstacle[key] for key in ('requirement', 'status', 'reason')} for obstacle in obstacles]}
        if previous_attempt is not None:
            value['previous_attempt'] = previous_attempt
        contract.schema(value, 'research', 'application')
        record.setdefault('annotations', {})[RESEARCH] = deepcopy(value)
        self._records[application['id']] = record

    def pack(self, destination, *, publishable, alternatives=()):
        destination = Path(destination)
        if destination.exists() or destination.is_symlink():
            raise ValueError("Publication destination already exists")
        ids = []
        for reference in publishable:
            contract.schema(reference, 'module', 'ref')
            if 'module' in reference or reference['id'] not in self._records:
                raise ValueError("Select only explicitly owned local records")
            if reference['id'] in ids:
                raise ValueError("Duplicate publication selection")
            ids.append(reference['id'])
        selected = [deepcopy(self._records[id]) for id in ids]
        manifest = {'format': contract.FORMAT, 'profiles': [], 'dependencies': [], 'payloads': [],
                    'components': [], 'applications': [], 'evidence': []}
        questions = []
        for record in selected:
            family = self._families[record['id']]
            (questions if family == 'questions' else manifest[family]).append(record)
        if questions or alternatives:
            manifest['annotations'] = {RESEARCH: {'questions': questions, 'alternatives': deepcopy(list(alternatives))}}
        profiles, dependencies, payloads = {}, set(), set()
        for node in _walk(manifest):
            if 'profile' in node and isinstance(node['profile'], str):
                profiles[node['profile']] = self._profiles.get(node['profile'], {'id': node['profile'], 'required': True})
            for profile in node.get('annotations', {}):
                profiles[profile] = self._profiles.get(profile, {'id': profile, 'required': profile in KNOWN_PROFILES})
            if set(node) in ({'id', 'module'}, {'path', 'module'}):
                dependencies.add(node['module'])
            if set(node) == {'path'}:
                payloads.add(node['path'])
        manifest['profiles'] = sorted(profiles.values(), key=lambda row: row['id'])
        manifest['dependencies'] = sorted(dependencies)
        for path in sorted(payloads):
            if path not in self._payloads:
                raise ValueError("Missing explicitly registered payload: " + path)
            data = self._payloads[path]
            manifest['payloads'].append({'path': path, 'size': str(len(data)), 'sha256': hashlib.sha256(data).hexdigest()})
        manifest['id'] = contract.identity(manifest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='slean-publication-', dir=destination.parent) as temporary:
            stage = Path(temporary) / 'module'
            stage.mkdir()
            for item in manifest['payloads']:
                path = stage / item['path']
                # The wire path syntax is checked before any filesystem write.
                contract.schema({'path': item['path']}, 'module', 'artifact')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(self._payloads[item['path']])
            contract.check(manifest, stage)
            (stage / 'slean-module.json').write_bytes(rfc8785.dumps(manifest) + b'\n')
            if destination.exists() or destination.is_symlink():
                raise ValueError("Publication destination appeared during preparation")
            stage.rename(destination)
        return manifest['id']
