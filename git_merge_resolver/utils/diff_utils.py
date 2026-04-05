"""
Diff and similarity utilities for comparing code resolutions against ground truth.

Used by the reward computation and grading systems to measure how close
an agent's resolution is to the expected ground truth.
"""

from __future__ import annotations

import ast
import re
import tokenize
import io
from difflib import SequenceMatcher
from typing import Set


def normalize_whitespace(text: str) -> str:
    """
    Normalize a code string for comparison purposes.

    Strips leading/trailing whitespace from each line, removes blank lines,
    and normalizes internal runs of whitespace.
    """
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return "\n".join(non_empty)


def sequence_similarity(a: str, b: str) -> float:
    """
    Compute normalized sequence similarity between two strings.

    Uses difflib.SequenceMatcher with whitespace normalization.
    Returns a value in [0.0, 1.0].
    """
    norm_a = normalize_whitespace(a)
    norm_b = normalize_whitespace(b)
    if not norm_a and not norm_b:
        return 1.0
    if not norm_a or not norm_b:
        return 0.0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def is_python_file(file_path: str) -> bool:
    """Return True if the file path indicates a Python source file."""
    return file_path.endswith(".py")


def is_syntax_valid(code: str) -> bool:
    """
    Check whether the given Python code is syntactically valid.

    Attempts to parse the code with ast.parse(). Returns True on success.
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def is_partially_syntactically_valid(code: str) -> bool:
    """
    Heuristic check for partial syntactic validity.

    Returns True if the code has no obvious structural errors even if
    it cannot be parsed standalone (e.g., it's a snippet missing imports).
    This checks that:
    - Indentation is consistent (no IndentationError on tokenization)
    - No unclosed brackets/parentheses/braces
    """
    # Check bracket balance
    opens = code.count("(") + code.count("[") + code.count("{")
    closes = code.count(")") + code.count("]") + code.count("}")
    if abs(opens - closes) > 2:
        return False

    # Check tokenization doesn't raise IndentationError
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
        return True
    except tokenize.TokenError:
        return False
    except IndentationError:
        return False


def extract_identifiers(code: str) -> Set[str]:
    """
    Extract all identifier names from Python code using the AST.

    Falls back to regex-based extraction if parsing fails.
    """
    try:
        tree = ast.parse(code)
        return {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        } | {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        } | {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        }
    except SyntaxError:
        # Fallback: regex-based identifier extraction
        return set(re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", code))


def extract_key_elements(ground_truth: str) -> Set[str]:
    """
    Extract key semantic elements from ground truth code.

    Returns a set of identifiers that are semantically significant —
    function names, class names, variable names — filtering out Python
    keywords and very short identifiers.
    """
    import keyword

    all_identifiers = extract_identifiers(ground_truth)
    # Filter out Python keywords and short/common names
    stop_words = set(keyword.kwlist) | {
        "self", "cls", "args", "kwargs", "None", "True", "False",
        "i", "j", "k", "n", "x", "y", "e", "f", "s", "v",
        "str", "int", "float", "bool", "list", "dict", "set", "tuple",
        "len", "range", "print", "type", "object",
    }
    return {
        ident
        for ident in all_identifiers
        if len(ident) > 2 and ident not in stop_words
    }


def contains_conflict_markers(text: str) -> bool:
    """Return True if the text contains any Git conflict markers."""
    return (
        "<<<<<<<" in text
        or "=======" in text
        or ">>>>>>>" in text
    )


def line_overlap_ratio(a: str, b: str) -> float:
    """
    Compute the fraction of lines in `b` that also appear in `a`.

    Useful for checking if key lines from ground truth are present in the resolution.
    """
    lines_b = set(normalize_whitespace(line) for line in b.splitlines() if line.strip())
    lines_a = set(normalize_whitespace(line) for line in a.splitlines() if line.strip())
    if not lines_b:
        return 1.0
    return len(lines_a & lines_b) / len(lines_b)
