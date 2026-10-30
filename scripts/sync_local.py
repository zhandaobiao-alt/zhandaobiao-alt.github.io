"""Export selected facts only; never copy raw local state or logs to GitHub."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from build import validate

parser = argparse.ArgumentParser()
parser.add_argument('--state',type=Path,required=True)
args = parser.parse_args()
state = json.loads(args.state.read_text(encoding='utf-8'))
source = Path(state['tasks'][0]['evidence'])
acceptance = json.loads(source.read_text(encoding='utf-8'))
if acceptance.get('status') != 'INPUT_TRIGGER_REPLAY_ACCEPTANCE_PASSED':
    raise RuntimeError('The expected acceptance record is not passed')
labels = {'rgbd':'RGB-D直接输入','pointcloud':'受控单帧彩色点云','legacy_pointcloud':'原C++单帧点云'}
routes = [{'label':labels[record['mode']],'requests':record['request_count'],'status':'通过'}
          for record in acceptance['modes'] if record['status']=='PASSED']
manifest = json.loads(Path(state['bridge_manifest']).read_text(encoding='utf-8'))
unchanged = all((Path(state['bridge_root'])/relative).is_file() and
                hashlib.sha256((Path(state['bridge_root'])/relative).read_bytes()).hexdigest()==digest
                for relative,digest in manifest['files'].items())
milestones = [
    {'id':'T01','title':'观测输入与单次触发','phase':'done' if unchanged else 'active',
     'description':'三条输入链路完成静止录包验收。'+('当前代码与验收版本一致。' if unchanged else '当前代码已有后续修改，正在补充回归验收。')},
    {'id':'T02','title':'几何证据约束与方法对照','phase':'active','description':'已有离线候选结果，在线接入及统一条件对照待完成。'},
    {'id':'T03','title':'真实足迹与近场连接','phase':'active','description':'整理已有测量及坐标记录，核验真实车体条件。'},
    {'id':'T04','title':'独立场景验证','phase':'todo','description':'冻结方法后，在未用于调参的地点或条件下评价。'},
    {'id':'T05','title':'真实任务与检测验证','phase':'todo','description':'实际到达、误差和失败回合需要独立任务记录。'},
    {'id':'T06','title':'方法与实验正文','phase':'active','description':'已有方法及部分实验内容稿，随证据更新；全篇与排版待完成。'},
]
data = {'updated_on':datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d'),
        'current_stage':'局部导航方法与系统验证', 'milestones':milestones,
        'acceptance':{'routes':routes,'requests':sum(route['requests'] for route in routes),
                      'independent_vehicle_trials':0,'unit':'same_stationary_bag_requests',
                      'scope':'三条链路的六次请求来自同一个静止录包，用于接口验收；不作为独立导航实验或泛化精度。'},
        'evidence_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
validate(data)
target = Path(__file__).resolve().parents[1]/'public/research.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('Exported allowlisted public research summary; no local paths or raw records copied')
