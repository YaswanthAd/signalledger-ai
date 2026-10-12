"""Publish this new project to the explicitly intended GitHub account.

Requires GitHub CLI and an authenticated session. Refuses an existing repo.
No credentials are read or written by this script.
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OWNER='YaswanthAd'
REPO='signalledger-ai'

def run(*args,check=True):
    return subprocess.run(args,cwd=ROOT,check=check,text=True,capture_output=True)

def main():
    if not shutil.which('gh'):
        raise SystemExit('Install GitHub CLI from https://cli.github.com/ and run gh auth login first.')
    user=json.loads(run('gh','api','user').stdout)
    if user['login'].lower()!=OWNER.lower():
        raise SystemExit('The authenticated GitHub account does not match YaswanthAd. Nothing was published.')
    existing=run('gh','repo','view',OWNER+'/'+REPO,'--json','name',check=False)
    if existing.returncode==0:
        raise SystemExit('The repository already exists. Refusing to overwrite or attach it automatically.')
    # gh repo create itself remains authoritative for availability/permissions.
    if not (ROOT/'.git').exists():
        run('git','init','-b','main')
    if run('git','remote',check=False).stdout.strip():
        raise SystemExit('A remote is already configured. Review it before publishing.')
    run('git','add','.')
    if run('git','diff','--cached','--quiet',check=False).returncode!=0:
        email=str(user['id'])+'+'+user['login']+'@users.noreply.github.com'
        run('git','-c','user.name='+user['login'],'-c','user.email='+email,'commit','-m','Build signalledger local AI workbench, architecture and tests')
    result=run('gh','repo','create',OWNER+'/'+REPO,'--public','--source','.','--push','--description','Evidence-grounded AI incident investigations for data platforms: lineage, anomaly scoring, citations and a local workbench.')
    print(result.stdout.strip())
    verify=json.loads(run('gh','repo','view',OWNER+'/'+REPO,'--json','url,isPrivate').stdout)
    if verify['isPrivate']:
        raise SystemExit('Repository exists but is not public; inspect visibility.')
    print('Published:',verify['url'])

if __name__=='__main__':main()
