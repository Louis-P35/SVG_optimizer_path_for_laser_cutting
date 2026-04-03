# SVG Optimizer for Laser Cutting

A Python tool that optimizes SVG files for laser cutting by reordering paths to minimize laser head movements (jumps). This reduces cutting time and wear on the machine.

## Features

- **Path reordering**: Reorganizes SVG paths using a nearest-neighbor algorithm to minimize non-cutting movements
- **Path reversal**: Automatically reverses path directions when it creates better continuity
- **Supports all SVG path commands**: M, L, H, V, C, S, Q, T, A, Z (and relative variants)
- **Preserves SVG structure**: Keeps groups, styles, text, and other elements intact
- **No dependencies**: Uses only Python standard library

## Installation

No installation required. Just clone the repository:

```bash
git clone https://github.com/Louis-P35/SVG_optimizer_path_for_laser_cutting.git
cd SVG_optimizer_path_for_laser_cutting
```

Requires Python 3.7+

## Usage

```bash
python svg_optimizer.py <input_file.svg>
```

The optimized file will be saved as `<input_file>_optimized.svg` in the same directory.

### Example

```bash
python svg_optimizer.py my_design.svg
```

Output:
```
Found 35 paths in the SVG
Initial stats: 31 jumps, total jump distance: 49543.02
Optimized stats: 9 jumps, total jump distance: 45481.80
Reversed 9 paths for better continuity

Optimized SVG saved to: my_design_optimized.svg

Optimization complete!
```

## How It Works

1. **Parse**: Extracts all `<path>` elements from the SVG file
2. **Analyze**: Calculates start and end points for each path by parsing the `d` attribute
3. **Optimize**: Uses a greedy nearest-neighbor algorithm:
   - Starts at origin (0,0)
   - Selects the path whose start (or end, if reversed) is closest to current position
   - Repeats until all paths are ordered
4. **Reverse**: Inverts paths when connecting to the end point is shorter than the start
5. **Output**: Writes the reordered paths to a new SVG file

## Supported Path Commands

| Command | Description |
|---------|-------------|
| M/m | Move to |
| L/l | Line to |
| H/h | Horizontal line |
| V/v | Vertical line |
| C/c | Cubic Bezier curve |
| S/s | Smooth cubic Bezier |
| Q/q | Quadratic Bezier curve |
| T/t | Smooth quadratic Bezier |
| A/a | Elliptical arc |
| Z/z | Close path |

## Limitations

- Closed paths (ending with Z) are not reversed
- The algorithm is greedy (nearest-neighbor), not globally optimal (TSP would be better but slower)
- Very large SVG files may take longer to process

## License

MIT License
