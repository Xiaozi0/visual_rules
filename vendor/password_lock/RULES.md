# Password Lock Rule Snapshot

Source: `original/批次6-0522.md`, row `解开密码锁`.

Reference image:
- `original/assets/batch6_0522/lock_q1.png`

Rule abstraction:
- The hidden code has three distinct digits.
- Each clue shows a three-digit guess.
- `in_place` is the number of digits that are correct and in the same position.
- `misplaced` is the number of digits that are in the hidden code but in a different position.
- The answer is the unique three-digit code satisfying all clues.

Rendering:
- The image shows only guesses and clue markers.
- Blue filled dots encode `in_place`.
- Gray outlined dots encode `misplaced`.
- The question text explains the marker semantics; the image does not contain the question or answer.

