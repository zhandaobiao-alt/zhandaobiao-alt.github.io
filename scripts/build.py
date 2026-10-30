"""Validate an allowlisted public summary and build without external packages."""
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]

def validate(data):
    serialized = json.dumps(data, ensure_ascii=False)
    forbidden = [r'[A-Za-z]:[\\/]', r'/home/', r'/Users/', r'192\.168\.',
                 r'BEGIN .*PRIVATE KEY', r'gh[pousr]_[A-Za-z0-9]', r'github_pat_',
                 r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}']
    if any(re.search(pattern, serialized) for pattern in forbidden):
        raise ValueError('Public summary contains private paths, connection data or credentials')
    if set(data) != {'updated_on','current_stage','milestones','acceptance','evidence_sha256'}:
        raise ValueError('Unexpected public summary fields')
    if not re.fullmatch(r'[a-f0-9]{64}', data['evidence_sha256']):
        raise ValueError('Missing evidence digest')
    acceptance = data['acceptance']
    if acceptance['requests'] != sum(route['requests'] for route in acceptance['routes']):
        raise ValueError('Request denominator mismatch')
    if acceptance['unit'] != 'same_stationary_bag_requests':
        raise ValueError('Do not relabel replay requests as independent trials')
    if acceptance['independent_vehicle_trials'] != 0:
        raise ValueError('Independent vehicle trials require a separately reviewed publication schema')
    if len({task['id'] for task in data['milestones']}) != len(data['milestones']):
        raise ValueError('Duplicate task IDs')
    if any(task['phase'] not in ('done','active','todo') for task in data['milestones']):
        raise ValueError('Unknown task phase')
    return data

def build():
    data = validate(json.loads((ROOT/'public/research.json').read_text(encoding='utf-8')))
    output = ROOT/'site'
    output.mkdir(exist_ok=True)
    text = (ROOT/'web/index.html').read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    (output/'index.html').write_text(text.replace('__RESEARCH_JSON__',payload),encoding='utf-8')
    for name in ('styles.css','app.js'):
        shutil.copyfile(ROOT/'web'/name,output/name)
    (output/'research.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'.nojekyll').touch()
    print('Built homepage from validated public summary')

if __name__ == '__main__':
    build()
