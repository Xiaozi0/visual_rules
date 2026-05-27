# Haimian Flip Rule Snapshot

Source: `original/批次04-0519.md` (`海绵宝宝-翻木块`) and `original/haimian_gemini`.

Abstracted rules:
- The puzzle uses a single 1x1x1 cube on a square grid board.
- The cube has six distinct SpongeBob-themed faces:
  - `head` (top at the start)
  - `foot` (bottom at the start)
  - `face` (front at the start)
  - `body` (back at the start)
  - `left` (left side at the start)
  - `right` (right side at the start)
- A move rolls the cube by one tile in one of four directions: up, down, left, right.
- Rolling changes both the cube position and which face is on top/front/left.
- The board image can show the arrow path, the start tile, the finish tile, and a target face card.
- The image must not contain the natural-language question itself.

VQA policy for this version:
- Use one static square image.
- Show the cube in its starting orientation.
- Show a deterministic arrow path from the green start tile to the red finish tile.
- Show one target face icon on a side card.
- Ask a yes/no question: after following the arrows, will the target face be on top?

Playable / reusable implementation:
- `vendor/haimian_flip/game.py`

Generator:
- `generator/haimian_flip_vqa_generator.py`
