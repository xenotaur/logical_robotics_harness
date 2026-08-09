## 2024-07-05 - Markdown Parsing String Iteration
**Learning:** In Python, iterating line-by-line using a `while` loop and `.find('\n')` to search for a delimiter like `---` can be extremely slow on large files without the delimiter (worst-case scenario), resulting in millions of unnecessary string slices. Standard regex `re.MULTILINE` is faster but can still backtrack heavily.
**Action:** Use `str.find('---', start_index)` to jump directly to candidate matches, then use `rfind('\n')` and `find('\n')` around that index to isolate the specific line for exact checking. This drastically reduces the number of string allocations and loops, dropping worst-case execution time from O(N lines) down to a fraction of a second.

## 2024-07-28 - Fast File Traversal with os.walk
**Learning:** `pathlib.Path.rglob()` is slow for large directories because it unconditionally traverses ignored directories (like `.venv`, `node_modules`, `.git`) and forces filtering after the fact. This can result in significant performance penalties in large codebases.
**Action:** Use `os.walk` with in-place directory pruning (`dirnames[:] = [d for d in dirnames if d not in skip_dirs]`) to avoid traversing ignored paths completely, providing drastic speedups over `rglob()`.
