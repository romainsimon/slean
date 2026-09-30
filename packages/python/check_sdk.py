"""Validate the bounded SDK and an installed wheel outside the checkout."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# Only the candidate wheel and the pinned third-party environment are available
# to this child. No source checkout is put on its import path.
SMOKE = '''
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import slean
from slean import Author, Reader, INTERFACE_POLICY, INTEGRITY_POLICY, scalar, scalar_port, equals_requirement
assert Path(slean.__file__).is_relative_to(Path(sys.argv[1]))
assert importlib.util.find_spec("conformance") is None
profile = "slean-quantity/0.1-draft.1"
def value(text):
    return {"typed": {"profile": profile, "value": scalar(text, dimension="voltage", unit="millivolt", uncertainty={"kind": "unknown"})}}
producer = Author(payloads={"method.py": b'raise AssertionError("Do not execute during authoring or planning")\\n'})
condition = equals_requirement("sensor", location="context", field="sensor", expected={"literal": "sensor-A"})
component = producer.component(id="inverse", kind="method", name="Declared sensor method", interface={"profile": profile, "value": {"inputs": {"reading": scalar_port(dimension="voltage", unit="volt")}, "outputs": {}, "entrypoint": {"artifact": {"path": "method.py"}, "symbol": "inverse"}}}, requires=condition, sources=[{"path": "method.py"}], license="unknown")
revision = producer.pack("producer", publishable=[component])
reader = Reader("producer")
report = reader.apply(component, bindings={"reading": value("8500")}, context={"sensor": {"literal": "sensor-A"}}, policy=INTERFACE_POLICY)
assert report["compatibility"] == "compatible", report
assert report["obligations"][0]["value"]["value"] == "8.500"
assert report["computational_reproduction"] == "not_performed"
assert reader.apply(component, bindings={"reading": value("8500")}, context={"sensor": {"literal": "sensor-B"}}, policy=INTERFACE_POLICY)["compatibility"] == "incompatible"
consumer = Author(dependencies=["producer"])
plan = consumer.plan({"module": revision, **component}, id="reuse", bindings={"reading": value("8500")}, context={"sensor": {"literal": "sensor-A"}})
consumer_revision = consumer.pack("consumer", publishable=[plan])
second_reader = Reader("consumer", dependencies=["producer"])
assert second_reader.inspect(plan)["record"]["component"]["module"] == revision
assert second_reader.uses({"module": revision, **component}) == [{"module": consumer_revision, **plan}]
assert second_reader.verify(plan, policy=INTEGRITY_POLICY)["outcome"] == "valid"
assert second_reader.verify(plan, policy="unknown-computation")["outcome"] == "unsupported"
from slean.execution import Executor, POLICY
import hashlib
source = b'from decimal import Decimal\\nimport pint\\nUNITS=pint.UnitRegistry(non_int_type=Decimal)\\ndef inverse(reading):\\n return {"distance":UNITS.Quantity((reading.to("volt").magnitude-Decimal("0.5"))/Decimal("2"),"millimeter")}\\n'
author = Author(payloads={"method.py": source})
method = author.component(id="inverse", kind="method", name="Installed call test", interface={"profile": profile,"value":{"inputs":{"reading":scalar_port(dimension="voltage",unit="volt")},"outputs":{"distance":scalar_port(dimension="length",unit="millimeter")},"entrypoint":{"artifact":{"path":"method.py"},"symbol":"inverse"}}}, requires={"id":"conditions","all":[]}, sources=[{"path":"method.py"}],license="unknown")
call = author.plan(method,id="call",bindings={"reading":value("8500")},context={})
call_revision=author.pack("call",publishable=[method,call])
result=Executor(Reader("call")).run(call,policy=POLICY,expected_component={"module":call_revision,**method},reviewed_source_sha256=hashlib.sha256(source).hexdigest())
assert result["outcome"] == "executed", result
assert result["outputs"]["distance"]["typed"]["value"]["value"] == "4.000"
from slean.authoring import RESEARCH
from slean.research import Research, POLICY as RESEARCH_POLICY
def voltage(text):
 return scalar(text,dimension="voltage",unit="volt",uncertainty={"kind":"unknown"})
observation_bytes=json.dumps({"id":"observation","context":{},"voltage":voltage("1.1")}).encode()
research_author=Author(payloads={"observation.json":observation_bytes})
model=research_author.component(id="model",kind="model",name="Installed finite-check model",interface={"profile":profile,"value":{"inputs":{},"outputs":{"voltage":scalar_port(dimension="voltage",unit="volt")}}},requires={"id":"conditions","all":[]},sources=[],license="unknown")
question=research_author.question(id="question",wording="Does this prediction match?",source="Owned installed-package check")
test=research_author.plan_test(model,id="test",question=question,bindings={},context={},prediction={"profile":profile,"value":voltage("1")},bound={"profile":profile,"value":voltage("0.02")},observation_id="observation")
run=research_author.record_execution(test,id="run",outputs={"voltage":{"typed":{"profile":profile,"value":voltage("1")}}})
observation=research_author.component(id="observation",kind="data",name="Installed observation",interface={"profile":profile,"value":{"inputs":{},"outputs":{}}},requires={"id":"conditions","all":[]},sources=[{"path":"observation.json"}],license="unknown",annotations={RESEARCH:{"role":"observation"}})
research_revision=research_author.pack("research",publishable=[model,question,test,run,observation])
finite=Research(Reader("research")).assess(run,observation,expected_plan={"module":research_revision,**test},policy=RESEARCH_POLICY)
assert finite["outcome"] == "failed_prediction",finite
assert finite["prediction_reproduction"] == "not_performed"
print(json.dumps({"status": "passed", "producer": revision, "consumer": consumer_revision, "outside_checkout": True, "inspection_executed_candidate": False, "explicit_reviewed_execution": "passed", "explicit_finite_comparison":"passed"}))
'''


def run(command, *, cwd):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Command failed: '+repr(command)+'\n'+result.stdout+result.stderr)
    return result.stdout


def check():
    started = time.monotonic()
    run([sys.executable, str(HERE/'generate_runtime.py')], cwd=ROOT)
    suite = unittest.defaultTestLoader.discover(str(HERE/'tests'))
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun != 44 or result.skipped:
        raise RuntimeError('Expected all 44 SDK test groups to pass without skipped execution checks')
    with tempfile.TemporaryDirectory(prefix='slean-installed-sdk-') as temporary:
        directory = Path(temporary)
        wheels = directory/'wheels'; wheels.mkdir()
        run([sys.executable, '-m', 'pip', 'wheel', '--no-build-isolation', '--no-deps', str(HERE), '-w', str(wheels)], cwd=directory)
        wheel, = wheels.glob('*.whl')
        site = directory/'site'
        run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--target', str(site), str(wheel)], cwd=directory)
        empty = directory/'empty'; empty.mkdir()
        smoke = json.loads(run([sys.executable, '-I', '-c', SMOKE, str(site)], cwd=empty))
        wheel_report = {'filename': wheel.name, 'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(), 'size': wheel.stat().st_size, **smoke}
    frozen = json.loads((ROOT/'examples/reuse/frozen-baseline.json').read_text())
    hashes = frozen['sha256']
    changed = [path for path, expected in hashes.items() if hashlib.sha256((ROOT/'examples/reuse'/path).read_bytes()).hexdigest() != expected]
    if changed: raise RuntimeError('Frozen direct-tool files changed: '+repr(changed))
    paths = [HERE/name for name in ('README.md', 'EXECUTION.md', 'RESEARCH.md', 'check_sdk.py', 'generate_runtime.py', 'pyproject.toml', 'requirements.lock', 'build-requirements.lock')]
    paths += sorted((HERE/'slean').glob('*.py')) + sorted((HERE/'slean/data').glob('*.json')) + sorted((HERE/'tests').glob('test_*.py'))
    paths += [ROOT/'conformance/contract.py', ROOT/'spec/module.schema.json', ROOT/'spec/authoring.pyi', ROOT/'packages/lean/verification/boundary.py', *sorted((ROOT/'profiles').glob('*.schema.json')), ROOT/'profiles/quantity-map.json']
    return {'status': 'passed', 'observed_date': datetime.date.today().isoformat(), 'scope': 'SR-T07 authoring/interface and SR-T08 numerical execution plus finite research-cycle checkpoint; conditional formal bridge, full negative-case acceptance and Gate U remain open',
        'python': platform.python_version(), 'test_groups': result.testsRun, 'negative_vectors': 41, 'requirement_vectors': 34, 'positive_modules': 3,
        'installed_wheel': wheel_report, 'frozen_files_unchanged': len(hashes), 'seconds': round(time.monotonic()-started, 3),
        'source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2, sort_keys=True))
