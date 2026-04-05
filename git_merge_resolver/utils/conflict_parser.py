"""
Utilities for parsing Git conflict markers from file contents.

Handles the standard three-way merge conflict format:
    <<<<<<< ours_branch
    ... ours content ...
    =======
    ... theirs content ...
    >>>>>>> theirs_branch
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


CONFLICT_START = re.compile(r"^<<<<<<< (.+)$", re.MULTILINE)
CONFLICT_SEP = re.compile(r"^=======$", re.MULTILINE)
CONFLICT_END = re.compile(r"^>>>>>>> (.+)$", re.MULTILINE)


@dataclass
class ParsedConflict:
    """A single parsed conflict block extracted from file content."""

    start_line: int
    end_line: int
    ours_branch: str
    theirs_branch: str
    ours_lines: List[str]
    theirs_lines: List[str]
    context_before_lines: List[str]
    context_after_lines: List[str]


def parse_conflicts(file_content: str, context_lines: int = 12) -> List[ParsedConflict]:
    """
    Parse all conflict blocks from a file's content.

    Args:
        file_content: Full file content including conflict markers.
        context_lines: Number of context lines to include before/after each conflict.

    Returns:
        List of ParsedConflict objects, one per conflict block.
    """
    lines = file_content.splitlines()
    conflicts: List[ParsedConflict] = []

    i = 0
    while i < len(lines):
        start_match = CONFLICT_START.match(lines[i])
        if start_match:
            ours_branch = start_match.group(1).strip()
            start_line = i

            # Find separator
            sep_line = None
            j = i + 1
            while j < len(lines):
                if CONFLICT_SEP.match(lines[j]):
                    sep_line = j
                    break
                j += 1

            if sep_line is None:
                i += 1
                continue

            # Find end marker
            end_line = None
            theirs_branch = ""
            k = sep_line + 1
            while k < len(lines):
                end_match = CONFLICT_END.match(lines[k])
                if end_match:
                    end_line = k
                    theirs_branch = end_match.group(1).strip()
                    break
                k += 1

            if end_line is None:
                i += 1
                continue

            ours_lines = lines[start_line + 1 : sep_line]
            theirs_lines = lines[sep_line + 1 : end_line]

            before_start = max(0, start_line - context_lines)
            # Exclude any lines that are part of a previous conflict's region
            context_before = lines[before_start:start_line]

            after_end = min(len(lines), end_line + 1 + context_lines)
            context_after = lines[end_line + 1 : after_end]

            conflicts.append(
                ParsedConflict(
                    start_line=start_line,
                    end_line=end_line,
                    ours_branch=ours_branch,
                    theirs_branch=theirs_branch,
                    ours_lines=ours_lines,
                    theirs_lines=theirs_lines,
                    context_before_lines=context_before,
                    context_after_lines=context_after,
                )
            )
            i = end_line + 1
        else:
            i += 1

    return conflicts


def has_conflict_markers(content: str) -> bool:
    """Return True if the content still contains any conflict markers."""
    return bool(
        CONFLICT_START.search(content)
        or CONFLICT_SEP.search(content)
        or CONFLICT_END.search(content)
    )


def count_conflicts(file_content: str) -> int:
    """Count the number of conflict blocks in a file's content."""
    return len(CONFLICT_START.findall(file_content))


def insert_conflict_markers(
    ours_content: str,
    theirs_content: str,
    ours_branch: str = "HEAD",
    theirs_branch: str = "feature-branch",
) -> str:
    """
    Wrap two content strings in Git conflict marker format.

    Args:
        ours_content: Content from the ours (HEAD) branch.
        theirs_content: Content from the theirs (incoming) branch.
        ours_branch: Name of the ours branch.
        theirs_branch: Name of the theirs branch.

    Returns:
        A string with conflict markers inserted.
    """
    return (
        f"<<<<<<< {ours_branch}\n"
        f"{ours_content}"
        f"=======\n"
        f"{theirs_content}"
        f">>>>>>> {theirs_branch}\n"
    )


def replace_conflict_with_resolution(
    file_content: str,
    conflict: ParsedConflict,
    resolution: str,
) -> str:
    """
    Replace a single conflict block in the file content with the resolved content.

    Args:
        file_content: Full file content with conflict markers.
        conflict: The parsed conflict to replace.
        resolution: The resolved content (without markers).

    Returns:
        Updated file content with the conflict replaced.
    """
    lines = file_content.splitlines(keepends=True)
    before = lines[: conflict.start_line]
    after = lines[conflict.end_line + 1 :]
    resolution_lines = resolution.splitlines(keepends=True)
    if resolution_lines and not resolution_lines[-1].endswith("\n"):
        resolution_lines[-1] += "\n"
    return "".join(before + resolution_lines + after)


def build_conflicted_file(
    base_lines: List[str],
    conflict_positions: List[Tuple[int, str, str, str, str]],
) -> str:
    """
    Build a file string with conflict markers inserted at specified positions.

    Args:
        base_lines: Lines of the base file.
        conflict_positions: List of (line_number, ours_content, theirs_content,
                            ours_branch, theirs_branch) tuples.

    Returns:
        File content string with conflict markers.
    """
    result_lines = list(base_lines)
    # Insert from bottom to top to preserve line numbers
    for line_num, ours, theirs, ours_branch, theirs_branch in sorted(
        conflict_positions, key=lambda x: x[0], reverse=True
    ):
        conflict_block = insert_conflict_markers(ours, theirs, ours_branch, theirs_branch)
        conflict_lines = conflict_block.splitlines(keepends=True)
        result_lines[line_num:line_num] = conflict_lines

    return "".join(result_lines)
