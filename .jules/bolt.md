## 2024-07-05 - Markdown Parsing String Iteration
**Learning:** In Python, iterating line-by-line using a `while` loop and `.find('\n')` to search for a delimiter like `---` can be extremely slow on large files without the delimiter (worst-case scenario), resulting in millions of unnecessary string slices. Standard regex `re.MULTILINE` is faster but can still backtrack heavily.
**Action:** Use `str.find('---', start_index)` to jump directly to candidate matches, then use `rfind('\n')` and `find('\n')` around that index to isolate the specific line for exact checking. This drastically reduces the number of string allocations and loops, dropping worst-case execution time from O(N lines) down to a fraction of a second.
## 2026-08-10 - Replace rglob with os.walk for faster directory traversal
**Learning:** `pathlib.Path.rglob()` causes severe performance penalties when scanning directories containing large ignored folders (like `.venv` and `node_modules`) because it traverses them completely, even if the result is filtered later.
**Action:** Prefer `os.walk` with in-place directory pruning (`dirnames[:] = [...]`) to skip unneeded large directories before they are traversed.
