import os

# ── Custom exception ──────────────────────────────────────────────────────────


class MazeInputError(Exception):
    pass


# ── Constants ─────────────────────────────────────────────────────────────────

ROWS = 12
COLS = 12
VALID_CELLS = {"W", "P", "M", "T", "D"}

# Cardinal directions in clockwise order (used for turning)
DIRECTIONS_CW = ["N", "E", "S", "W"]

# Row/col deltas for each cardinal direction
DELTA = {
    "N": (-1, 0),
    "E": (0, 1),
    "S": (1, 0),
    "W": (0, -1),
}

# ── Helpers ───────────────────────────────────────────────────────────────────


def turn_left(facing: str) -> str:
    """Return the direction after a 90° counter-clockwise (left) turn."""
    idx = DIRECTIONS_CW.index(facing)
    return DIRECTIONS_CW[(idx - 1) % 4]


def turn_right(facing: str) -> str:
    """Return the direction after a 90° clockwise (right) turn."""
    idx = DIRECTIONS_CW.index(facing)
    return DIRECTIONS_CW[(idx + 1) % 4]


def cell_ahead(row: int, col: int, facing: str):
    """Return (r, c) of the cell directly ahead."""
    dr, dc = DELTA[facing]
    return row + dr, col + dc


# ── Maze loading & validation ─────────────────────────────────────────────────


def load_maze(path: str):
    """Load the maze from *path* and return a 12×12 list of strings."""
    if not os.path.isfile(path):
        raise MazeInputError(f"Maze file not found: {path}")

    with open(path, "r") as fh:
        raw_lines = fh.readlines()

    # Strip trailing newline / whitespace from each line but preserve content
    lines = [line.rstrip("\n") for line in raw_lines]

    # Remove completely blank lines (e.g. trailing newline produces one)
    lines = [l for l in lines if l.strip() != ""]

    if len(lines) != ROWS:
        raise MazeInputError(
            f"Maze must have {ROWS} rows, but {len(lines)} were found."
        )

    maze = []
    for row_idx, line in enumerate(lines):
        tokens = line.split(" ")
        if len(tokens) != COLS:
            raise MazeInputError(
                f"Row {row_idx} has {len(tokens)} columns; expected {COLS}."
            )
        for col_idx, cell in enumerate(tokens):
            if cell not in VALID_CELLS:
                raise MazeInputError(
                    f"Invalid cell '{cell}' at [{row_idx}, {col_idx}]."
                )
        maze.append(tokens)

    return maze


def validate_maze(maze):
    """Validate special-cell counts and border walls; return positions."""
    counts = {ch: 0 for ch in ("M", "T", "D")}
    positions = {}

    for r in range(ROWS):
        for c in range(COLS):
            cell = maze[r][c]
            if cell in counts:
                counts[cell] += 1
                positions[cell] = [r, c]

    for ch in ("M", "T", "D"):
        if counts[ch] != 1:
            raise MazeInputError(
                f"Maze must contain exactly one '{ch}', found {counts[ch]}."
            )

    # Border cells must all be W or D
    for c in range(COLS):
        if maze[0][c] not in ("W",):
            raise MazeInputError(f"Border cell [0, {c}] is not a wall.")
        if maze[ROWS - 1][c] not in ("W", "D"):
            raise MazeInputError(
                f"Border cell [{ROWS - 1}, {c}] is not a wall or door."
            )
    for r in range(ROWS):
        if maze[r][0] not in ("W", "D"):
            raise MazeInputError(f"Border cell [{r}, 0] is not a wall or door.")
        if maze[r][COLS - 1] not in ("W", "D"):
            raise MazeInputError(
                f"Border cell [{r}, {COLS - 1}] is not a wall or door."
            )

    return positions


# ── Always-turn-left strategy ─────────────────────────────────────────────────


def is_passable(maze, r: int, c: int) -> bool:
    """Return True if the cell is a path, the door, or Theseus's start."""
    # Theseus can move onto P, D cells (T is where he starts, treated as P)
    return maze[r][c] in ("P", "D", "T")


def solve_left_hand(maze, start: list) -> tuple:
    """
    Navigate the maze using the always-turn-left (left-hand-on-wall) rule.

    Returns (steps, directions) where directions is a list of cardinal
    direction strings ('N','E','S','W') for each move taken.
    """
    r, c = start
    facing = "S"  # Theseus always starts facing South
    directions = []

    # Safety cap: a generous upper bound to avoid infinite loops on bad mazes
    max_steps = ROWS * COLS * 4 * 4 + 1000

    for _ in range(max_steps):
        # Step 1: turn left
        facing = turn_left(facing)

        # Try to move forward; if blocked, rotate clockwise up to 3 more times
        moved = False
        for _ in range(4):  # at most 4 rotations to try all directions
            nr, nc = cell_ahead(r, c, facing)
            if 0 <= nr < ROWS and 0 <= nc < COLS and is_passable(maze, nr, nc):
                # Move forward
                r, c = nr, nc
                directions.append(facing)
                moved = True
                break
            else:
                facing = turn_right(facing)

        if not moved:
            raise MazeInputError(
                "Theseus is completely surrounded by walls — unsolvable maze."
            )

        # Check for escape
        if maze[r][c] == "D":
            break

    else:
        raise MazeInputError(
            "Always-turn-left strategy exceeded step limit — maze may be unsolvable."
        )

    return len(directions), directions


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    # Build file paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Expected layout: Lab J/src/lab_j.py  →  data/maze.txt, ../maze_solution.json
    data_path = os.path.join(script_dir, "..", "data", "maze.txt")
    output_path = os.path.join(script_dir, "..", "maze_solution.json")

    # Normalise paths
    data_path = os.path.normpath(data_path)
    output_path = os.path.normpath(output_path)

    # Load & validate
    maze = load_maze(data_path)
    positions = validate_maze(maze)

    theseus_start = positions["T"]

    # Solve
    steps, directions = solve_left_hand(maze, theseus_start)

    # Build output manually (no json module)
    dirs_str = ", ".join('"' + d + '"' for d in directions)
    output = (
        '{"theseus_start": ' + str(theseus_start) + ",\n"
        ' "left_steps": ' + str(steps) + ",\n"
        ' "directions": [' + dirs_str + "]}"
    )

    with open(output_path, "w") as fh:
        fh.write(output)

    print(f"Solution written to: {output_path}")
    print(f"Theseus starts at:   {theseus_start}")
    print(f"Steps required:      {steps}")
    print(f"Directions:          {directions}")


if __name__ == "__main__":
    main()
