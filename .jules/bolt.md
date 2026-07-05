## 2024-07-05 - Markdown Parsing String Iteration
**Learning:** In Python, iterating line-by-line using a `while` loop and `.find('\n')` to search for a delimiter like `---` can be extremely slow on large files without the delimiter (worst-case scenario), resulting in millions of unnecessary string slices. Standard regex `re.MULTILINE` is faster but can still backtrack heavily.
**Action:** Use `str.find('---', start_index)` to jump directly to candidate matches, then use `rfind('\n')` and `find('\n')` around that index to isolate the specific line for exact checking. This drastically reduces the number of string allocations and loops, dropping worst-case execution time from O(N lines) down to a fraction of a second.

## 2024-07-05 - Avoid Quadratic Text Scanning Traps
**Learning:** Advancing scanning indices by a static offset (e.g. `start = idx + 3`) after finding a false candidate (like `---` inside a longer string) can lead to quadratic performance drops if there are many overlapping candidates on a single long line, causing repeated line boundaries checks for the same line.
**Action:** When evaluating line-based delimiter boundaries using string jump searches, advance the search offset past the entire evaluated line (`start = line_end + 1`) rather than just past the match, to ensure each long line is evaluated at most once.
