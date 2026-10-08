"""Typed dependency-map snapshots for LRH Console views.

A view declaration (``project/views/dependency_maps/<name>.md``) names ordered
lanes and phases by canonical ID. ``snapshot.build_snapshot`` projects the
project's work items through it into a versioned ``DependencyMapSnapshot``
that every renderer consumes. See ``PROP-LRH-CONSOLE-LOCAL-DOGFOOD`` §5–§6 and
the Revision 2 status model in ``PROP-LRH-CONSOLE-VISUAL-LANGUAGE``.
"""
