## 2024-07-05 - Markdown Parsing String Iteration
**Learning:** In Python, iterating line-by-line using a `while` loop and `.find('\n')` to search for a delimiter like `---` can be extremely slow on large files without the delimiter (worst-case scenario), resulting in millions of unnecessary string slices. Standard regex `re.MULTILINE` is faster but can still backtrack heavily.
**Action:** Use `str.find('---', start_index)` to jump directly to candidate matches, then use `rfind('\n')` and `find('\n')` around that index to isolate the specific line for exact checking. This drastically reduces the number of string allocations and loops, dropping worst-case execution time from O(N lines) down to a fraction of a second.

## 2024-07-08 - File traversal performance with large ignored directories
**Learning:** `pathlib.Path.rglob` doesn't prune directories before traversing them, leading to severe performance penalties in codebases with large ignored folders like `.venv` or `node_modules` during static analysis scans (like `sourcetree_surveyor.py`).
**Action:** Prefer `os.walk` with in-place directory pruning (`dirnames[:] = [d for d in dirnames if d not in skip_dirs]`) over `pathlib.Path.rglob()` to avoid traversing into ignored trees entirely, and yield `pathlib.Path` objects to maintain API compatibility.
