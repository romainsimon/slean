"""Compact laws: short expressions that compute a world's rule.

Mirrors ``Slean/Law.lean`` exactly. A law is JSON:

    {"op": "cell", "j": 2}                      the cell at position j of the neighbourhood
    {"op": "const", "c": 3}
    {"op": "add" | "sub" | "mul", "a": LAW, "b": LAW}
    {"op": "sum", "args": [LAW, ...]}            shorthand for nested "add"
    {"op": "mod", "a": LAW, "m": 4}              non-negative remainder
    {"op": "lookup", "table": [ints], "a": LAW}  table[value], 0 outside the table

Its description length counts one per node plus one per table entry. A law is
accepted only when it is much shorter than the rule table itself.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_NODES = 2000


class LawError(ValueError):
    pass


@dataclass(frozen=True)
class Node:
    op: str
    j: int = 0
    c: int = 0
    m: int = 0
    table: tuple[int, ...] = ()
    a: "Node | None" = None
    b: "Node | None" = None


def parse(obj, _count=None) -> Node:
    count = _count if _count is not None else [0]
    count[0] += 1
    if count[0] > MAX_NODES:
        raise LawError("law too large")
    if not isinstance(obj, dict) or "op" not in obj:
        raise LawError("each node needs an 'op'")
    op = obj["op"]
    try:
        if op == "cell":
            j = int(obj["j"])
            if j < 0:
                raise LawError("cell index must be >= 0")
            return Node("cell", j=j)
        if op == "const":
            return Node("const", c=int(obj["c"]))
        if op in ("add", "sub", "mul"):
            return Node(op, a=parse(obj["a"], count), b=parse(obj["b"], count))
        if op == "sum":
            args = [parse(x, count) for x in obj["args"]]
            if not args:
                return Node("const", c=0)
            node = args[0]
            for nxt in args[1:]:
                node = Node("add", a=node, b=nxt)
            return node
        if op == "mod":
            m = int(obj["m"])
            if m <= 0:
                raise LawError("mod needs m > 0")
            return Node("mod", m=m, a=parse(obj["a"], count))
        if op == "lookup":
            table = tuple(int(v) for v in obj["table"])
            return Node("lookup", table=table, a=parse(obj["a"], count))
    except (KeyError, TypeError) as exc:
        raise LawError(f"malformed '{op}' node: {exc}") from exc
    raise LawError(f"unknown op {op!r}")


def evaluate(node: Node, cells) -> int:
    op = node.op
    if op == "cell":
        return cells[node.j] if node.j < len(cells) else 0
    if op == "const":
        return node.c
    if op == "add":
        return evaluate(node.a, cells) + evaluate(node.b, cells)
    if op == "sub":
        return evaluate(node.a, cells) - evaluate(node.b, cells)
    if op == "mul":
        return evaluate(node.a, cells) * evaluate(node.b, cells)
    if op == "mod":
        return evaluate(node.a, cells) % node.m  # Python % = Lean Int.emod for m > 0
    if op == "lookup":
        idx = max(0, evaluate(node.a, cells))  # Lean Int.toNat
        return node.table[idx] if idx < len(node.table) else 0
    raise LawError(op)


def description_length(node: Node) -> int:
    size = 1 + len(node.table)
    for child in (node.a, node.b):
        if child is not None:
            size += description_length(child)
    return size


def lean_term(node: Node) -> str:
    op = node.op
    if op == "cell":
        return f"(.cell {node.j})"
    if op == "const":
        return f"(.const ({node.c}))"
    if op in ("add", "sub", "mul"):
        return f"(.{op} {lean_term(node.a)} {lean_term(node.b)})"
    if op == "mod":
        return f"(.mod {lean_term(node.a)} {node.m})"
    if op == "lookup":
        entries = ", ".join(f"({v})" for v in node.table)
        return f"(.lookup [{entries}] {lean_term(node.a)})"
    raise LawError(op)


def to_json(node: Node) -> dict:
    op = node.op
    if op == "cell":
        return {"op": "cell", "j": node.j}
    if op == "const":
        return {"op": "const", "c": node.c}
    if op in ("add", "sub", "mul"):
        return {"op": op, "a": to_json(node.a), "b": to_json(node.b)}
    if op == "mod":
        return {"op": "mod", "a": to_json(node.a), "m": node.m}
    return {"op": "lookup", "table": list(node.table), "a": to_json(node.a)}


def compactness_limit(table_size: int) -> int:
    """A law must be at most a quarter of the rule table it replaces."""
    return table_size // 4
