# VHS tape for the flagship demo GIF: docs/media/denied-proposal.gif
#
# Regenerate with: vhs docs/media/denied-proposal.tape
# (run from the repo root; requires vhs -- https://github.com/charmbracelet/vhs)
#
# Records the exact command documented in examples/denied-proposal/README.md
# under "Run it with no backend at all" -- this is not staged text, it is
# the real emitter's real stdout.

Output docs/media/denied-proposal.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 560
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 40ms

Type "cd examples/denied-proposal"
Enter
Sleep 500ms

Type "uv run --project ../../py --group examples python run.py"
Sleep 500ms
Enter

Sleep 6s
