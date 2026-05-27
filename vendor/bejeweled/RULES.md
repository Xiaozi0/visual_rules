# Bejeweled Rule Snapshot

Source: Invent with Python, Bejeweled clone.

Rules abstracted for VQA generation:
- Played on an 8x8 grid filled with colored gems.
- A player swaps two adjacent gems (horizontally or vertically) to create a straight line of 3 or more gems of the same color.
- If a swap results in a match, the matched gems are eliminated.
- If a swap does not result in a match, the move is invalid.
- Static VQA frames show a snapshot of the grid with a highlighted gem.

VQA Questions:
- Determine if swapping the highlighted gem with an adjacent gem is a valid move.
- Count the number of gems that will be matched and eliminated if a specific valid swap is made.
