import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.package_release import package


class Release(unittest.TestCase):
    def test_release_is_repeatable_and_excludes_local_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=package(Path(tmp))
            first=hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertLess(archive.stat().st_size,500_000)
            with zipfile.ZipFile(archive) as z:
                names=z.namelist()
                self.assertTrue(any(n.endswith('/install.sh') for n in names))
                self.assertTrue(any(n.endswith('/locks/sources.json') for n in names))
                self.assertFalse(any('/.work/' in n or '/__pycache__/' in n or n.endswith('.pyc') for n in names))
                self.assertIsNone(z.testzip())
            second=hashlib.sha256(package(Path(tmp)).read_bytes()).hexdigest()
            self.assertEqual(first,second)
