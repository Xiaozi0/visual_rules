# Sokoban Rule Snapshot

Source: Invent with Python, Sokoban clone.

Rules abstracted for VQA generation:
- The game is played on a grid board consisting of walls, empty spaces, and targets.
- There are boxes and one player on the board.
- The player can move orthogonally to empty spaces or targets.
- If the player moves into a box, the box is pushed one square in that direction, provided the square behind the box is empty or a target (not a wall or another box).
- A box is "on a target" if its position matches a target's position.
- A "deadlock" occurs when a box is pushed into a corner (surrounded by walls in two orthogonal directions) and it is not on a target, making it impossible to ever push again.

VQA Questions:
- Count the number of boxes currently on targets.
- Determine whether pushing a specific box in a specified direction is a legal move.
