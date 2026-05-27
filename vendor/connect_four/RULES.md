# Connect Four Rule Snapshot

Source: Invent with Python, Connect Four clone.

Rules abstracted for VQA generation:
- Played on a grid of 7 columns and 6 rows.
- Two players (Red and Yellow) take turns dropping their colored discs into any column.
- The disc falls straight down, occupying the lowest available empty space within the column.
- The game is won when a player aligns four of their discs horizontally, vertically, or diagonally.

VQA Questions:
- Determine if dropping a disc in a specific column results in an immediate win for that player.
- Identify the column that a player must drop a disc into to block the opponent from winning on their next turn.
