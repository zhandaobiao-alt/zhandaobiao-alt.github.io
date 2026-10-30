"""Create/update the requested homepage using existing Git credential storage.

Credentials are obtained through Git Credential Manager and used in memory;
neither tokens nor credential subprocess output are printed or written to disk.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'zhandaobiao-alt'
REPO = OWNER+'.github.io'
GIT = shutil.which('git') or r'D:\Program Files\Git\cmd\git.exe'

def git(*args, capture=False, check=True):
    return subprocess.run([GIT,*args],cwd=ROOT,text=True,encoding='utf-8',capture_output=capture,check=check,
                          env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'})

def credential():
    result = subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\nusername='+OWNER+'\n\n',
                            text=True,encoding='utf-8',capture_output=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'Never'})
    fields = dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not fields.get('password'):
        raise RuntimeError('GitHub login is required in Git Credential Manager')
    return fields['password']

def api(method, route, token, payload=None, allow_missing=False):
    body = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request('https://api.github.com'+route,data=body,method=method,
              headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                       'X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json',
                       'User-Agent':'research-homepage-publisher'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                data = response.read()
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as error:
            if error.code==404 and allow_missing:
                return None
            if error.code>=500 and attempt<2:
                time.sleep(attempt+1)
                continue
            try: detail = json.loads(error.read()).get('message','GitHub API error')
            except Exception: detail = 'GitHub API error'
            raise RuntimeError('GitHub '+method+' '+route+' returned '+str(error.code)+': '+detail) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempt==2:
                raise RuntimeError('Network interrupted during GitHub '+method+' '+route+'; retry publication') from None
            time.sleep(attempt+1)

def publish_with_api(route, token):
    # HTTPS Git transport is unreliable on this host. The official Git Data API
    # publishes one reviewed tree without exposing credentials or force-pushing.
    branch=api('GET',route+'/branches/main',token,allow_missing=True)
    if branch is None:
        api('PUT',route+'/contents/README.md',token,{
            'message':'Initialize research homepage', 'branch':'main',
            'content':base64.b64encode((ROOT/'README.md').read_bytes()).decode('ascii')})
    pages=api('GET',route+'/pages',token,allow_missing=True)
    if pages is None:
        pages=api('POST',route+'/pages',token,{'build_type':'workflow'})
    elif pages.get('build_type')!='workflow':
        pages=api('PUT',route+'/pages',token,{'build_type':'workflow'})
    head=api('GET',route+'/git/ref/heads/main',token)['object']['sha']
    commit=api('GET',route+'/git/commits/'+head,token)
    names=git('ls-files','-z',capture=True).stdout.split('\0')
    tree=[]
    for name in names:
        if not name:
            continue
        tree.append({'path':name,'mode':'100644','type':'blob',
                     'content':(ROOT/name).read_text(encoding='utf-8')})
    newtree=api('POST',route+'/git/trees',token,{'base_tree':commit['tree']['sha'],'tree':tree})
    if newtree['sha']==commit['tree']['sha']:
        return head,pages
    newcommit=api('POST',route+'/git/commits',token,{
        'message':'Update validated research homepage and publishing workflow',
        'tree':newtree['sha'],'parents':[head]})
    current=api('GET',route+'/git/ref/heads/main',token)['object']['sha']
    if current!=head:
        raise RuntimeError('Remote branch changed during publication; no force push performed')
    api('PATCH',route+'/git/refs/heads/main',token,{'sha':newcommit['sha'],'force':False})
    return newcommit['sha'],pages

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--status',action='store_true')
    args=parser.parse_args()
    if not args.status:
        from build import build
        build()
    token=credential()
    user=api('GET','/user',token)
    if user['login'].lower()!=OWNER:
        raise RuntimeError('Authenticated account does not match the requested homepage owner')
    route='/repos/'+OWNER+'/'+REPO
    if args.status:
        result={'repo':api('GET',route,token,allow_missing=True),
                'pages':api('GET',route+'/pages',token,allow_missing=True),
                'actions':api('GET',route+'/actions/runs?per_page=3',token,allow_missing=True)}
        # A selected metadata view only, never HTTP headers or credentials.
        print(json.dumps({'repository':result['repo'].get('html_url') if result['repo'] else None,
                          'pages':result['pages'], 'runs':[
                              {key:run.get(key) for key in ('id','status','conclusion','html_url','head_sha')}
                              for run in (result['actions'] or {}).get('workflow_runs',[])]},indent=2))
        return
    repository=api('GET',route,token,allow_missing=True)
    if repository is None:
        repository=api('POST','/user/repos',token,{'name':REPO,'private':False,
                         'description':'移动巡检机器人研究进度与可追溯实验摘要','auto_init':False})
    if not (ROOT/'.git').exists():
        git('init','-b','main')
        git('config','user.name',OWNER)
        git('config','user.email',str(user['id'])+'+'+OWNER+'@users.noreply.github.com')
        git('remote','add','origin',repository['clone_url'])
    git('add','--','README.md','AGENTS.md','.gitignore','.github','web','scripts','tests','public',
        '更新并发布主页.cmd')
    pending=git('diff','--cached','--quiet',capture=True,check=False)
    if pending.returncode:
        git('commit','-m','Update validated research homepage and publishing workflow')
    remote_commit,pages=publish_with_api(route,token)
    try:
        api('POST',route+'/actions/workflows/pages.yml/dispatches',token,{'ref':'main'})
        dispatch='requested'
    except RuntimeError:
        # The just-pushed workflow may not yet be indexed. Push still triggers it.
        dispatch='push_trigger_pending'
    result={'repository':repository['html_url'],'homepage':pages.get('html_url', 'https://'+OWNER+'.github.io/'),
            'workflow_dispatch':dispatch,'local_commit':git('rev-parse','HEAD',capture=True).stdout.strip(),
            'remote_commit':remote_commit,'transport':'GitHub Git Data API'}
    (ROOT/'publish_status.local.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
