"""공개 참고 이미지의 실제 Git 인덱스·해시·치수·참조 문서 검사."""
from pathlib import Path
import json,hashlib,struct,subprocess,sys,re,posixpath
root=Path(__file__).resolve().parent.parent
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
entries={line.split('\t',1)[1]:line.split()[1] for line in git('ls-files','--stage').decode().splitlines()}
def read(p):return git('cat-file','blob',entries[p])
manifest=json.loads(read('manifest.json'));images=set();total=0
for a in manifest['assets']:
 p=a['path'];assert p.startswith('design-system/asset-packs/starter-r1/') and '..' not in p
 d=read(p);assert d[:8]==b'\x89PNG\r\n\x1a\n';assert hashlib.sha256(d).hexdigest()==a['sha256'],p
 assert len(d)==a['bytes'] and len(d)<=5*1024**2,p
 assert list(struct.unpack('>II',d[16:24]))==[a['width'],a['height']],p
 assert a['rawUrl']=='https://raw.githubusercontent.com/imakerjun/yesjun-image-references/main/'+p
 assert a['referenceUse'] and a['reviewStatus'] and a['source']
 images.add(p);total+=len(d)
assert images=={p for p in entries if p.endswith('.png')},'등록되지 않은 이미지'
for p in entries:
 assert not any(v in p for v in ['workspace.local','.env','__pycache__']),p
 assert not p.lower().endswith(('.mp4','.mov','.prproj','.psd','.wav','.mp3','.zip')),p
 if p.endswith('.json'):json.loads(read(p))
 if p.endswith('.md'):
  text=read(p).decode();assert '/Users/' not in text and '/Volumes/' not in text,p
  for target in re.findall(r'\]\(([^)]+)\)',text):
   if not target.startswith(('https:','http:','#')):
    target=posixpath.normpath(posixpath.join(posixpath.dirname(p),target.rstrip('/')));assert target in entries or any(x.startswith(target+'/')for x in entries),(p,target)
if '--history' in sys.argv:
 for line in git('rev-list','--objects','--all').decode().splitlines():
  oid,_,name=line.partition(' ')
  if name and git('cat-file','-t',oid).strip()==b'blob':assert len(git('cat-file','blob',oid))<=5*1024**2,name
print(json.dumps({'ok':True,'images':len(images),'imageBytes':total,'indexFiles':len(entries),'historyChecked':'--history' in sys.argv},ensure_ascii=False))
