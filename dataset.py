#!/usr/bin/env python3
"""Read, verify, or materialize an archived G+ observation (Python stdlib only)."""
import argparse,csv,hashlib,json,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent

def digest(b):return hashlib.sha256(b).hexdigest()
def rows():
 with (ROOT/'index.csv').open(newline='') as f:return list(csv.DictReader(f))
def safe(name):
 p=PurePosixPath(name)
 if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('Unsafe archive member')
 return p

def get(tf,name):
 safe(name);m=tf.getmember(name)
 if not m.isfile():raise ValueError('Only regular files are supported')
 return tf.extractfile(m).read()

def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 s.add_parser('summary');s.add_parser('verify')
 x=s.add_parser('extract');x.add_argument('--sample-id',required=True);x.add_argument('--output',type=Path,required=True)
 a=p.parse_args();data=rows()
 if a.cmd=='summary':
  print(json.dumps({'circuits':len({r['case_id'] for r in data}),'pairs':len({r['pair_id'] for r in data}),'G':len(data),'C':sum(r['C']=='true' for r in data),'L':sum(r['L']=='true' for r in data)},indent=2));return
 if a.cmd=='verify':
  manifest=json.loads((ROOT/'manifest.json').read_text())
  for name,want in manifest['files'].items():
   safe(name);b=(ROOT/name).read_bytes()
   if digest(b)!=want['sha256'] or len(b)!=want['bytes']:raise ValueError('Hash mismatch: '+name)
  assert len(data)==3760 and len({r['sample_id'] for r in data})==3760
  for r in data:
   assert r['G']=='true'
   assert r['C']!='true' or r['OPEN']==r['SHORT']==r['checker_unknown']=='0'
   assert r['L']!='true' or r['C']=='true' and r['DRC_total']=='0'
   for k in ('requested35','executed35','normalized35'):assert len(json.loads(r[k]))==35
  print('File hashes, 3760 logical identities, quality labels and action dimensions verified.');return
 matches=[r for r in data if r['sample_id']==a.sample_id]
 if len(matches)!=1:raise ValueError('Unknown or duplicate sample ID')
 r=matches[0];safe(r['archive']);a.output.mkdir(parents=True,exist_ok=False)
 with tarfile.open(ROOT/r['archive'],'r:gz') as tf:
  sample=get(tf,r['sample_member']);layout=get(tf,r['layout_member'])
  assert digest(sample)==r['sample_sha256'] and digest(layout)==r['layout_sha256']
  record=json.loads(sample);(a.output/'sample.json').write_bytes(sample);(a.output/'layout.gds').write_bytes(layout)
  (a.output/'pair.json').write_bytes(get(tf,'pair.json'))
  for name,entry in record['input_files'].items():
   b=get(tf,entry['path']);assert digest(b)==entry['sha256']
   q=a.output/'input'/str(safe(name));q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 with tarfile.open(ROOT/record['pdk_base_archive'],'r:gz') as tf:
  for member in tf:
   safe(member.name)
   if not member.isfile():raise ValueError('Unexpected PDK member')
   q=a.output/'pdk'/member.name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(get(tf,member.name))
 (a.output/'pdk/layers.json').write_text(json.dumps(record['pdk_layers'],indent=2)+'\n')
 print('Materialized archived layout, metadata, PDK and available inputs in',a.output)
 if not record['input_included']:print('Circuit inputs are not included: see pair.json upstream acquisition information.')
 print('No ALIGN run was started. Inspect phase_schedule and historical scripts before attempting replay.')
if __name__=='__main__':main()
