"""Turn certificates into Lean theorems and have the kernel check them."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from .verify import Claim, Verdict
from .worlds.ca import CA

REPO = Path(__file__).resolve().parents[2]


def lean_ident(text: str) -> str:
    ident = re.sub(r"[^A-Za-z0-9_]", "_", text)
    return ident if ident[:1].isalpha() else f"b_{ident}"


def _ints(values) -> str:
    return "[" + ", ".join(str(v) for v in values) + "]"


def travel_theorem(name: str, ca: CA, claim, verdict: Verdict) -> str:
    from .worlds.structures import padded

    world = f"({ca.lean()})"
    cells = _ints(padded(claim.block, claim.q, ca.s, claim.t))
    neg = "" if verdict.status == "certified" else "¬ "
    return f"theorem {name} : {neg}Travels {world} {cells} {claim.t} {claim.d} := by decide +kernel\n"


def theorem(name: str, ca: CA, claim, verdict: Verdict) -> str:
    if getattr(claim, "kind", "") == "structure":
        return travel_theorem(name, ca, claim, verdict)
    world = f"({ca.lean()})"
    density = f"(tableFn {ca.k} {_ints(claim.f)})"
    if verdict.status == "certified":
        current = f"(tableFn {ca.k} {_ints(ca.lift_flux(verdict.flux, claim.w))})"
        return (
            f"theorem {name} : Conserved {world} {density} {claim.w} :=\n"
            f"  conserved_of_fluxCheck _ _ {current} {claim.w} (by decide +kernel)\n"
        )
    if verdict.status == "refuted":
        return (
            f"theorem {name} : ¬ Conserved {world} {density} {claim.w} :=\n"
            f"  not_conserved_of_witness _ _ {claim.w} {_ints(verdict.witness)}"
            f" (by decide) (by decide +kernel) (by decide +kernel)\n"
        )
    raise ValueError(f"no Lean statement for status {verdict.status!r}")


def module(name: str, theorems: list[str], doc: str) -> str:
    header = (
        "import Slean.World.Structures\n\n"
        f"/-! {doc} -/\n\n"
        "set_option maxRecDepth 100000\n\n"
        f"namespace Slean.{name}\n\n"
    )
    return header + "\n".join(theorems) + f"\nend Slean.{name}\n"


def lake() -> str:
    found = shutil.which("lake")
    if found:
        return found
    fallback = Path.home() / ".elan" / "bin" / "lake"
    return str(fallback)


def kernel_check(path: Path, timeout: int = 1800) -> dict:
    """Elaborate a Lean file against the built Slean library."""
    started = time.monotonic()
    proc = subprocess.run(
        [lake(), "env", "lean", str(path)],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "ok": proc.returncode == 0,
        "seconds": round(time.monotonic() - started, 2),
        "output": (proc.stdout + proc.stderr)[-4000:],
    }
