# Flip Blocks Rule Snapshot

Source: `original/批次04-0519.md` and the Bloxorz reference in `original/批次05-0521.md`.

Abstracted rules:
- The board is a grid of usable tiles and missing tiles.
- The block is a 2x1 rectangle.
- The block starts upright on one tile.
- A move rolls the block one step up, down, left, or right.
- The block can be upright or lying on two adjacent tiles.
- Any state that overlaps a missing tile or leaves the board is invalid.
- The goal is to end upright on the goal hole.

Playable implementation:
- `vendor/flip_blocks/game.py`
- `script/flip_blocks_game.py`

VQA policy:
- Render only the board, the block, and the goal hole.
- Do not place the question text inside the image.
- Use binary yes/no reachability questions for the first version.
