import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_build', ROOT/'scripts/build.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PublicBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'public/research.json').read_text(encoding='utf-8'))
    def test_real_export_is_valid(self):
        module.validate(self.data)
    def test_private_path_is_rejected(self):
        for value in ('D:/private/work', '/home/someone/secret', '192.168.152.129'):
            data = copy.deepcopy(self.data); data['current_stage'] = value
            with self.assertRaises(ValueError): module.validate(data)
    def test_replay_is_not_silently_relabelled_as_vehicle_trials(self):
        data = copy.deepcopy(self.data); data['acceptance']['independent_vehicle_trials'] = 6
        with self.assertRaises(ValueError): module.validate(data)
    def test_request_denominator_is_checked(self):
        data = copy.deepcopy(self.data); data['acceptance']['requests'] += 1
        with self.assertRaises(ValueError): module.validate(data)
    def test_evidence_digest_is_required(self):
        data = copy.deepcopy(self.data); data['evidence_sha256'] = ''
        with self.assertRaises(ValueError): module.validate(data)
    def test_unknown_export_fields_are_rejected(self):
        data = copy.deepcopy(self.data); data['raw_log'] = 'not allowed'
        with self.assertRaises(ValueError): module.validate(data)

if __name__=='__main__': unittest.main()
