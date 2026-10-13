"""Conservative non-path slash positions in literal Python shell payloads.

This is not a shell interpreter or a security boundary. Unsupported/expanding
shell forms and invalid Python retain the original path heuristics. Positions,
not string values, keep a harmless occurrence from excusing a later file access.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass


@dataclass
class _Word:
    value: str
    positions: list[int]
    literal: bool = True
    quoted: bool = False


def _word(text: str, start: int) -> tuple[_Word, int]:
    value, positions = [], []
    literal, quoted, quote = True, False, None
    i = start
    while i < len(text):
        char = text[i]
        if quote is None and (char.isspace() or char in ";&|<>()"):
            break
        if char in "'\"" and (quote is None or char == quote):
            quoted = True
            quote = None if quote else char
            i += 1
            continue
        if char == "\\" and quote != "'":
            if i + 1 >= len(text):
                raise ValueError("unfinished shell escape")
            following = text[i + 1]
            # Within double quotes, shell only removes these backslashes.
            if quote is None or following in '$`"\\\n':
                i += 1
                if text[i] == "\n":
                    i += 1
                    continue
                value.append(text[i])
                positions.append(i)
                i += 1
                continue
        if char in "$`" and quote != "'":
            literal = False  # shell expansion/substitution, not literal Python
        value.append(char)
        positions.append(i)
        i += 1
    if quote:
        raise ValueError("unfinished shell quote")
    return _Word("".join(value), positions, literal, quoted), i


def _python_slashes(source: str) -> set[int]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def offset(row, col, *, utf8=False):
        if utf8:
            col = len(lines[row - 1].encode()[:col].decode())
        return starts[row - 1] + col

    def span(node):
        return (offset(node.lineno, node.col_offset, utf8=True),
                offset(node.end_lineno, node.end_col_offset, utf8=True))

    # In a valid division expression, the gap between the operands contains
    # its operator, parentheses, whitespace or comments, never a path operand.
    # AST spans also cover f-string expressions on Python 3.11, whose tokenizer
    # presents the entire f-string as one string token.
    divisions = [(span(node.left)[1], span(node.right)[0]) for node in ast.walk(tree)
                 if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.FloorDiv))]
    safe = {i for a, b in divisions for i in range(a, b) if source[i] == "/"}

    # Only direct builtin print arguments are output context. If the source
    # binds print or uses dynamic namespace/evaluation operations, do not infer
    # that print is still the builtin. All other strings retain the path scan.
    dynamic = {"exec", "eval", "compile", "globals", "locals", "vars", "setattr", "getattr",
               "__import__", "builtins", "__builtins__"}
    for node in ast.walk(tree):
        if ((isinstance(node, ast.Name) and node.id == "print" and not isinstance(node.ctx, ast.Load)) or
            (isinstance(node, ast.arg) and node.arg == "print") or
            (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.ExceptHandler,
                              ast.MatchAs, ast.MatchStar)) and node.name == "print") or
            (isinstance(node, ast.MatchMapping) and node.rest == "print") or
            (isinstance(node, (ast.Global, ast.Nonlocal)) and "print" in node.names) or
            (isinstance(node, ast.alias) and ((node.asname or node.name.split(".")[0]) in ("print", "*") or node.name == "builtins")) or
            (isinstance(node, ast.Attribute) and node.attr == "print" and not isinstance(node.ctx, ast.Load)) or
            (isinstance(node, ast.Name) and node.id in dynamic) or
            (isinstance(node, ast.Constant) and node.value == "builtins")):
            return safe
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"):
            continue
        for argument in node.args:
            if not (isinstance(argument, ast.JoinedStr) or
                    isinstance(argument, ast.Constant) and isinstance(argument.value, str)):
                continue
            start, end = span(argument)
            # AST constants inside f-strings share the whole string span on
            # Python 3.11. Keep every interpolation expression visible, including
            # expressions nested in format specifications. The specification
            # itself is an argument to __format__, not literal printed output.
            expressions = [span(part) for child in ast.walk(argument) if isinstance(child, ast.FormattedValue)
                           for part in (child.value, child.format_spec) if part is not None]
            safe.update(i for i in range(start, end) if source[i] == "/" and
                        not any(a <= i < b for a, b in expressions))
    return safe


def _python_command(words: list[_Word]) -> bool:
    return bool(words) and bool(re.fullmatch(r"(?:python(?:3(?:\.\d+)?)?|/usr/bin/python3)", words[0].value))


def non_path_slashes(command: str, *, _depth=0) -> set[int]:
    """Recognize literal python -c / quoted stdin heredocs, including shell wrappers.

    No exceptions are inferred for file-change events, other languages, shell
    expansions, pipes, output redirections or unquoted heredocs. Output routed
    into another command or file could become a path rather than display text.
    Unrecognized syntax stays conservative.
    """
    if _depth > 4:
        return set()
    safe, words = set(), []
    i = 0
    try:
        while i < len(command):
            char = command[i]
            if char in " \t\r":
                i += 1
                continue
            if char == "#" and not words:
                end = command.find("\n", i)
                i = len(command) if end < 0 else end
                continue
            if command.startswith("<<", i):
                # Consume every heredoc body, even for non-Python commands, so
                # command-looking text within it is never parsed as shell code.
                j = i + 2
                strip_tabs = command[j:j + 1] == "-"
                j += strip_tabs
                while command[j:j + 1] in (" ", "\t"):
                    j += 1
                delimiter, j = _word(command, j)
                newline = command.find("\n", j)
                if (newline < 0 or not re.fullmatch(r"[A-Za-z_]\w*", delimiter.value) or
                        any(c in command[j:newline] for c in "|<>$`")):
                    return set()
                body_start, cursor = newline + 1, newline + 1
                while cursor < len(command):
                    end = command.find("\n", cursor)
                    end = len(command) if end < 0 else end
                    line = command[cursor:end]
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter.value:
                        break
                    cursor = end + 1
                else:
                    return set()
                # Tabs stripped by <<- need a new source-to-command map; retain
                # the conservative scan instead of guessing its positions.
                if (_python_command(words) and
                    all(w.literal and w.value in ("-", "-u", "-I", "-B", "-S") for w in words[1:]) and
                    delimiter.quoted and delimiter.literal and not strip_tabs):
                    source = command[body_start:cursor]
                    safe.update(body_start + p for p in _python_slashes(source))
                words = []
                i = end + 1
                continue
            if char in "|<>":
                return set()
            if char in ";&|()< >\n":
                words = []
                i += 1
                continue
            word, i = _word(command, i)
            if not word.literal:
                return set()
            words.append(word)
            if len(words) < 3:
                continue
            preceding = words[:-1]
            if (_python_command(preceding) and preceding[-1].value == "-c" and
                    all(w.value in ("-u", "-I", "-B", "-S") for w in preceding[1:-1])):
                safe.update(word.positions[p] for p in _python_slashes(word.value))
            elif (len(preceding) == 2 and preceding[0].value in ("sh", "bash", "zsh", "/bin/sh", "/bin/bash", "/bin/zsh")
                  and preceding[1].value in ("-c", "-lc")):
                safe.update(word.positions[p] for p in non_path_slashes(word.value, _depth=_depth + 1))
    except (ValueError, IndexError):
        return set()
    return safe
