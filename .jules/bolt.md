## 2024-07-05 - Markdown Parsing String Iteration
**Learning:** In Python, iterating line-by-line using a `while` loop and `.find('\n')` to search for a delimiter like `---` can be extremely slow on large files without the delimiter (worst-case scenario), resulting in millions of unnecessary string slices. Standard regex `re.MULTILINE` is faster but can still backtrack heavily.
**Action:** Use `str.find('---', start_index)` to jump directly to candidate matches, then use `rfind('\n')` and `find('\n')` around that index to isolate the specific line for exact checking. This drastically reduces the number of string allocations and loops, dropping worst-case execution time from O(N lines) down to a fraction of a second.

## 2024-05-18 - [Replace rglob with os.walk for faster file tree traversal]
**Learning:** `pathlib.Path.rglob()` is slow when traversing large file trees with significant ignored directories (like `node_modules` or `.venv`) because it cannot prune these directories in-place during the generator step; it iterates through them entirely before we can filter them out.
**Action:** Use `os.walk()` combined with in-place directory pruning (`dirnames[:] = [d for d in dirnames if d not in ignored]`) to aggressively avoid descending into ignored directories, reducing traversal time significantly.
