"""Verify the deployed HTML, public evidence and referenced assets over HTTPS."""
import json
from pathlib import Path
import re
import time
import urllib.request

root=Path(__file__).resolve().parents[1]
url='https://zhandaobiao-alt.github.io/'
headers={'User-Agent':'research-homepage-verifier','Cache-Control':'no-cache'}
def fetch(target):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(target,headers=headers),timeout=15) as response:
                return response.status,response.read()
        except (OSError,TimeoutError):
            if attempt==2: raise
            time.sleep(attempt+1)
status,body=fetch(url)
html=body.decode('utf-8')
assert status==200 and '移动巡检机器人' in html
match=re.search(r'<script id="research-data" type="application/json">(.*?)</script>',html,re.S)
assert match,'No published research payload'
data=json.loads(match.group(1))
local=json.loads((root/'public/research.json').read_text(encoding='utf-8'))
assert data==local,'Published payload does not yet match the latest local evidence summary'
assets={}
for name in ('styles.css','app.js'):
    asset_status,content=fetch(url+name)
    assert asset_status==200 and len(content)>200
    assets[name]=len(content)
report={'homepage':url,'http_status':status,'public_payload_matches':True,
        'milestones':len(data['milestones']),'requests':data['acceptance']['requests'],
        'independent_vehicle_trials':data['acceptance']['independent_vehicle_trials'],
        'assets':assets,'visual_browser_check':'not available in this session'}
(root/'live_check.local.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
