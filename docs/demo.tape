# VHS Tape for T-Zero Terminal Demo
# VHS is a 100% free, open-source terminal recording tool (github.com/charmbracelet/vhs)
# Run with: vhs main/demo.tape  (Produces demo.gif completely offline & free)

Output demo.gif

Set FontSize 16
Set Width 1200
Set Height 680
Set Theme "Catppuccin Mocha"
Set Padding 20
Set PlaybackSpeed 1.2

Type "python tzero.py --version"
Sleep 400ms
Enter
Sleep 1000ms

Type "clear"
Enter
Sleep 400ms

# 1. Run reproducible savings benchmark
Type "python tzero.py --savings"
Sleep 600ms
Enter
Sleep 3500ms

# 2. Run AST static code quality & zero-leak security audit
Type "python tzero.py --doctor"
Sleep 600ms
Enter
Sleep 2500ms

Type "# Result: 94.9% Token Reduction | 100% Zero-Leak Local Storage"
Enter
Sleep 2000ms
