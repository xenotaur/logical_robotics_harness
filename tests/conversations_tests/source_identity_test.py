"""Unit tests for the shared export source-identity reader."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lrh.conversations import source_identity


class TestReadBytesWithIdentity(unittest.TestCase):
    def test_returns_bytes_and_identity_of_the_file_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "src.txt"
            path.write_bytes(b"hello")

            data, identity = source_identity.read_bytes_with_identity(path)

            self.assertEqual(data, b"hello")
            self.assertTrue(os.path.samestat(identity, path.stat()))

    def test_identity_still_describes_original_after_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "src.txt"
            moved = Path(temp_dir) / "moved.txt"
            path.write_bytes(b"hello")

            _, identity = source_identity.read_bytes_with_identity(path)
            os.rename(path, moved)

            self.assertTrue(os.path.samestat(identity, moved.stat()))
            self.assertFalse(path.exists())

    def test_identity_still_describes_original_after_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "src.txt"
            moved = Path(temp_dir) / "moved.txt"
            path.write_bytes(b"hello")

            _, identity = source_identity.read_bytes_with_identity(path)
            os.rename(path, moved)
            path.write_bytes(b"replacement")

            self.assertTrue(os.path.samestat(identity, moved.stat()))
            self.assertFalse(os.path.samestat(identity, path.stat()))

    def test_missing_file_raises_oserror(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(OSError):
                source_identity.read_bytes_with_identity(Path(temp_dir) / "absent")

    def test_descriptor_is_closed_after_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "src.txt"
            path.write_bytes(b"hello")
            opened: list[int] = []
            real_open = os.open

            def recording_open(*args: object, **kwargs: object) -> int:
                fd = real_open(*args, **kwargs)
                opened.append(fd)
                return fd

            with mock.patch("os.open", side_effect=recording_open):
                source_identity.read_bytes_with_identity(path)

            self.assertEqual(len(opened), 1)
            with self.assertRaises(OSError):
                os.fstat(opened[0])


if __name__ == "__main__":
    unittest.main()
