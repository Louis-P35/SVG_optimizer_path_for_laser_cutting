#!/usr/bin/env python3
"""
SVG Optimizer for Laser Cutting

This script optimizes SVG files for laser cutting by reordering paths
to minimize laser jumps (non-cutting movements). It can also reverse
path directions when needed to create continuous cutting lines.

Usage: python svg_optimizer.py <input_file.svg>
Output: <input_file>_optimized.svg
"""

import sys
import re
import math
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class PathSegment:
    """Represents a path element from the SVG with its endpoints."""
    original_line: str
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    path_data: str
    reversed_path_data: Optional[str] = None
    is_reversed: bool = False
    is_closed: bool = False


def tokenize_path(d: str) -> List[str]:
    """
    Tokenize SVG path data into commands and numbers.
    Handles cases like "M10,20" or "M 10 20" or "M10-20" (negative numbers).
    """
    pattern = r'([MmZzLlHhVvCcSsQqTtAa])|([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)'
    tokens = []
    for match in re.finditer(pattern, d):
        if match.group(1):
            tokens.append(match.group(1))
        elif match.group(2):
            tokens.append(match.group(2))
    return tokens


def parse_path_endpoints(d: str) -> Tuple[Tuple[float, float], Tuple[float, float], bool]:
    """
    Parse SVG path data and extract start and end points.
    Returns (start_point, end_point, is_closed).
    """
    tokens = tokenize_path(d)
    if not tokens:
        return (0, 0), (0, 0), False

    current_x, current_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    first_point_set = False
    subpath_start_x, subpath_start_y = 0.0, 0.0
    is_closed = False

    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        if cmd in 'Mm':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'm':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

                if not first_point_set:
                    start_x, start_y = current_x, current_y
                    first_point_set = True

                subpath_start_x, subpath_start_y = current_x, current_y

                while i + 1 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    i += 2
                    if cmd == 'm':
                        current_x += x
                        current_y += y
                    else:
                        current_x, current_y = x, y

        elif cmd in 'Ll':
            while i + 1 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'l':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Hh':
            while i < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x = float(tokens[i])
                i += 1
                if cmd == 'h':
                    current_x += x
                else:
                    current_x = x

        elif cmd in 'Vv':
            while i < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                y = float(tokens[i])
                i += 1
                if cmd == 'v':
                    current_y += y
                else:
                    current_y = y

        elif cmd in 'Cc':
            while i + 5 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                i += 4
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'c':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Ss':
            while i + 3 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                i += 2
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 's':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Qq':
            while i + 3 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                i += 2
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'q':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Tt':
            while i + 1 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 't':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Aa':
            while i + 6 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                i += 5
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'a':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y

        elif cmd in 'Zz':
            current_x, current_y = subpath_start_x, subpath_start_y
            is_closed = True

    return (start_x, start_y), (current_x, current_y), is_closed


def reverse_path(d: str) -> str:
    """
    Reverse an SVG path so it goes from end to start.
    """
    tokens = tokenize_path(d)
    if not tokens:
        return d

    points = []
    current_x, current_y = 0.0, 0.0
    subpath_start = (0.0, 0.0)

    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        i += 1

        if cmd in 'Mm':
            if i + 1 < len(tokens):
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'm':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                points.append(('M', current_x, current_y))
                subpath_start = (current_x, current_y)

                while i + 1 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    i += 2
                    if cmd == 'm':
                        current_x += x
                        current_y += y
                    else:
                        current_x, current_y = x, y
                    points.append(('L', current_x, current_y))

        elif cmd in 'Ll':
            while i + 1 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x, y = float(tokens[i]), float(tokens[i + 1])
                i += 2
                if cmd == 'l':
                    current_x += x
                    current_y += y
                else:
                    current_x, current_y = x, y
                points.append(('L', current_x, current_y))

        elif cmd in 'Hh':
            while i < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x = float(tokens[i])
                i += 1
                if cmd == 'h':
                    current_x += x
                else:
                    current_x = x
                points.append(('L', current_x, current_y))

        elif cmd in 'Vv':
            while i < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                y = float(tokens[i])
                i += 1
                if cmd == 'v':
                    current_y += y
                else:
                    current_y = y
                points.append(('L', current_x, current_y))

        elif cmd in 'Cc':
            while i + 5 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
                x, y = float(tokens[i + 4]), float(tokens[i + 5])
                i += 6
                if cmd == 'c':
                    x1 += current_x
                    y1 += current_y
                    x2 += current_x
                    y2 += current_y
                    x += current_x
                    y += current_y
                points.append(('C', current_x, current_y, x1, y1, x2, y2, x, y))
                current_x, current_y = x, y

        elif cmd in 'Qq':
            while i + 3 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                x1, y1 = float(tokens[i]), float(tokens[i + 1])
                x, y = float(tokens[i + 2]), float(tokens[i + 3])
                i += 4
                if cmd == 'q':
                    x1 += current_x
                    y1 += current_y
                    x += current_x
                    y += current_y
                points.append(('Q', current_x, current_y, x1, y1, x, y))
                current_x, current_y = x, y

        elif cmd in 'Aa':
            while i + 6 < len(tokens) and tokens[i] not in 'MmZzLlHhVvCcSsQqTtAa':
                rx = float(tokens[i])
                ry = float(tokens[i + 1])
                rotation = float(tokens[i + 2])
                large_arc = int(float(tokens[i + 3]))
                sweep = int(float(tokens[i + 4]))
                x, y = float(tokens[i + 5]), float(tokens[i + 6])
                i += 7
                if cmd == 'a':
                    x += current_x
                    y += current_y
                points.append(('A', current_x, current_y, rx, ry, rotation, large_arc, sweep, x, y))
                current_x, current_y = x, y

        elif cmd in 'Zz':
            points.append(('Z', subpath_start[0], subpath_start[1]))
            current_x, current_y = subpath_start

    if not points:
        return d

    last_point = points[-1]
    if last_point[0] == 'Z':
        for p in points:
            if p[0] == 'M':
                end_x, end_y = p[1], p[2]
                break
    else:
        end_x, end_y = get_endpoint(last_point)

    reversed_parts = [f"M {end_x},{end_y}"]

    for i in range(len(points) - 1, 0, -1):
        current = points[i]
        prev = points[i - 1]

        prev_end_x, prev_end_y = get_endpoint(prev)

        if current[0] == 'M':
            continue
        elif current[0] == 'L':
            reversed_parts.append(f"L {prev_end_x},{prev_end_y}")
        elif current[0] == 'C':
            _, start_x, start_y, x1, y1, x2, y2, end_x, end_y = current
            reversed_parts.append(f"C {x2},{y2} {x1},{y1} {prev_end_x},{prev_end_y}")
        elif current[0] == 'Q':
            _, start_x, start_y, x1, y1, end_x, end_y = current
            reversed_parts.append(f"Q {x1},{y1} {prev_end_x},{prev_end_y}")
        elif current[0] == 'A':
            _, start_x, start_y, rx, ry, rotation, large_arc, sweep, end_x, end_y = current
            new_sweep = 1 - sweep
            reversed_parts.append(f"A {rx},{ry} {rotation} {large_arc} {new_sweep} {prev_end_x},{prev_end_y}")
        elif current[0] == 'Z':
            reversed_parts.append(f"L {prev_end_x},{prev_end_y}")

    return " ".join(reversed_parts)


def get_endpoint(point_data: tuple) -> Tuple[float, float]:
    """Get the endpoint coordinates from a point data tuple."""
    cmd = point_data[0]
    if cmd in ('M', 'L'):
        return point_data[1], point_data[2]
    elif cmd == 'C':
        return point_data[7], point_data[8]
    elif cmd == 'Q':
        return point_data[5], point_data[6]
    elif cmd == 'A':
        return point_data[8], point_data[9]
    elif cmd == 'Z':
        return point_data[1], point_data[2]
    return 0, 0


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def extract_path_data(line: str) -> Optional[str]:
    """Extract the 'd' attribute from a path element line."""
    # Match d="..." or d='...'
    match = re.search(r'\bd\s*=\s*["\']([^"\']*)["\']', line)
    if match:
        return match.group(1)
    return None


def update_path_data(line: str, new_d: str) -> str:
    """Update the 'd' attribute in a path element line."""
    return re.sub(r'(\bd\s*=\s*["\'])([^"\']*)(["\'"])', f'\\1{new_d}\\3', line)


def extract_paths_from_svg(content: str) -> Tuple[List[str], List[PathSegment], List[int]]:
    """
    Extract all path elements from SVG content.
    Returns (all_lines, path_segments, path_line_indices).
    """
    lines = content.split('\n')
    paths = []
    path_indices = []

    # Handle multi-line path elements
    current_path_lines = []
    current_path_start_idx = -1
    in_path = False

    for i, line in enumerate(lines):
        # Check if this line starts a path element
        if '<path' in line and not in_path:
            in_path = True
            current_path_start_idx = i
            current_path_lines = [line]

            # Check if path ends on same line
            if '/>' in line or '</path>' in line:
                full_path = '\n'.join(current_path_lines)
                d = extract_path_data(full_path)
                if d:
                    start, end, is_closed = parse_path_endpoints(d)
                    reversed_d = reverse_path(d) if not is_closed else None
                    paths.append(PathSegment(
                        original_line=full_path,
                        start_point=start,
                        end_point=end,
                        path_data=d,
                        reversed_path_data=reversed_d,
                        is_closed=is_closed
                    ))
                    path_indices.append(current_path_start_idx)
                in_path = False
                current_path_lines = []
        elif in_path:
            current_path_lines.append(line)
            if '/>' in line or '</path>' in line:
                full_path = '\n'.join(current_path_lines)
                d = extract_path_data(full_path)
                if d:
                    start, end, is_closed = parse_path_endpoints(d)
                    reversed_d = reverse_path(d) if not is_closed else None
                    paths.append(PathSegment(
                        original_line=full_path,
                        start_point=start,
                        end_point=end,
                        path_data=d,
                        reversed_path_data=reversed_d,
                        is_closed=is_closed
                    ))
                    path_indices.append(current_path_start_idx)
                in_path = False
                current_path_lines = []

    return lines, paths, path_indices


def optimize_path_order(paths: List[PathSegment]) -> List[PathSegment]:
    """
    Optimize the order of paths to minimize laser jumps.
    Uses a greedy nearest-neighbor algorithm.
    """
    if not paths:
        return paths

    current_pos = (0.0, 0.0)
    remaining = paths.copy()
    optimized = []

    while remaining:
        best_idx = -1
        best_distance = float('inf')
        best_reversed = False

        for i, path in enumerate(remaining):
            d_start = distance(current_pos, path.start_point)
            if d_start < best_distance:
                best_distance = d_start
                best_idx = i
                best_reversed = False

            if not path.is_closed and path.reversed_path_data:
                d_end = distance(current_pos, path.end_point)
                if d_end < best_distance:
                    best_distance = d_end
                    best_idx = i
                    best_reversed = True

        best_path = remaining.pop(best_idx)

        if best_reversed:
            best_path.is_reversed = True
            best_path.original_line = update_path_data(best_path.original_line, best_path.reversed_path_data)
            best_path.start_point, best_path.end_point = best_path.end_point, best_path.start_point

        optimized.append(best_path)
        current_pos = best_path.end_point

    return optimized


def calculate_stats(paths: List[PathSegment]) -> dict:
    """Calculate statistics about path continuity."""
    if not paths:
        return {'total_paths': 0, 'total_jumps': 0, 'total_jump_distance': 0}

    total_jump_distance = 0
    jumps = 0
    current_pos = (0.0, 0.0)

    for path in paths:
        d = distance(current_pos, path.start_point)
        if d > 0.01:
            jumps += 1
            total_jump_distance += d
        current_pos = path.end_point

    return {
        'total_paths': len(paths),
        'total_jumps': jumps,
        'total_jump_distance': total_jump_distance
    }


def optimize_svg(input_path: str) -> str:
    """
    Main function to optimize an SVG file for laser cutting.
    Returns the output file path.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.suffix.lower() == '.svg':
        raise ValueError("Input file must be an SVG file")

    # Read the SVG content
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract paths
    lines, paths, path_indices = extract_paths_from_svg(content)
    print(f"Found {len(paths)} paths in the SVG")

    if not paths:
        print("No paths found to optimize.")
        return input_path

    # Calculate initial stats
    initial_stats = calculate_stats(paths)
    print(f"Initial stats: {initial_stats['total_jumps']} jumps, "
          f"total jump distance: {initial_stats['total_jump_distance']:.2f}")

    # Optimize path order
    optimized_paths = optimize_path_order(paths)

    # Calculate optimized stats
    optimized_stats = calculate_stats(optimized_paths)
    print(f"Optimized stats: {optimized_stats['total_jumps']} jumps, "
          f"total jump distance: {optimized_stats['total_jump_distance']:.2f}")

    # Count reversed paths
    reversed_count = sum(1 for p in optimized_paths if p.is_reversed)
    print(f"Reversed {reversed_count} paths for better continuity")

    # Rebuild the SVG content
    # First, mark all original path lines for removal
    lines_to_remove = set()
    for idx in path_indices:
        # Find the end of this path element
        j = idx
        while j < len(lines):
            lines_to_remove.add(j)
            if '/>' in lines[j] or '</path>' in lines[j]:
                break
            j += 1

    # Find where to insert the optimized paths (at the first path location)
    insert_idx = min(path_indices) if path_indices else len(lines) - 1

    # Build the new content
    new_lines = []
    paths_inserted = False

    for i, line in enumerate(lines):
        if i in lines_to_remove:
            if not paths_inserted and i == insert_idx:
                # Insert all optimized paths here
                for p in optimized_paths:
                    new_lines.append(p.original_line)
                paths_inserted = True
        else:
            new_lines.append(line)

    # If paths weren't inserted yet (shouldn't happen), append them
    if not paths_inserted and optimized_paths:
        # Find closing tag
        for i in range(len(new_lines) - 1, -1, -1):
            if '</svg>' in new_lines[i] or '</g>' in new_lines[i]:
                for p in optimized_paths:
                    new_lines.insert(i, p.original_line)
                break

    # Generate output filename
    output_path = input_file.parent / f"{input_file.stem}_optimized{input_file.suffix}"

    # Write the optimized SVG
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"\nOptimized SVG saved to: {output_path}")
    return str(output_path)


def main():
    if len(sys.argv) != 2:
        print("Usage: python svg_optimizer.py <input_file.svg>")
        print("Example: python svg_optimizer.py drawing.svg")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        output_file = optimize_svg(input_file)
        print(f"\nOptimization complete!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
