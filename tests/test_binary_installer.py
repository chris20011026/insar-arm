import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('binary_installer', Path(__file__).resolve().parents[1]/'packaging/install_binary.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class BinaryInstallerTests(unittest.TestCase):
    def test_existing_environment_is_never_touched(self):
        with tempfile.TemporaryDirectory() as d, patch.object(module.subprocess, 'run') as run:
            marker = Path(d)/'research.txt'
            marker.write_text('keep')
            with self.assertRaisesRegex(RuntimeError, 'not be overwritten'):
                module.install('conda', Path(d))
            run.assert_not_called()
            self.assertEqual(marker.read_text(), 'keep')

    def test_unexpected_download_destination_rejected_before_conda(self):
        with tempfile.TemporaryDirectory() as d, patch.object(module.subprocess, 'run') as run:
            lock = Path(d)/'lock'
            lock.write_text('@EXPLICIT\nhttps://unexpected.example/pkg.conda#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n')
            with self.assertRaisesRegex(RuntimeError, 'unexpected'):
                module.install('conda', Path(d)/'new', lock)
            run.assert_not_called()

    def test_failed_create_does_not_start_validation(self):
        with tempfile.TemporaryDirectory() as d:
            lock = Path(d)/'lock'
            lock.write_text('@EXPLICIT\nhttps://conda.anaconda.org/conda-forge/osx-arm64/pkg.conda#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n')
            with patch.object(module.subprocess, 'run', side_effect=module.subprocess.CalledProcessError(1, 'conda')) as run:
                with self.assertRaises(module.subprocess.CalledProcessError):
                    module.install('conda', Path(d)/'new', lock)
                self.assertEqual(run.call_count, 1)
