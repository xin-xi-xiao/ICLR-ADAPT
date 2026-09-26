#!/usr/bin/env python3
"""Display archived ALIGN phases; does not pretend stock ALIGN reproduces Formal35."""
import argparse,json,shlex,tarfile
from pathlib import Path
import dataset

def main():
 p=argparse.ArgumentParser();p.add_argument('--sample-id',required=True);a=p.parse_args()
 matches=[r for r in dataset.rows() if r['sample_id']==a.sample_id]
 if len(matches)!=1:raise ValueError('Unknown sample')
 r=matches[0]
 with tarfile.open(dataset.ROOT/r['archive'],'r:gz') as tf:record=json.loads(dataset.get(tf,r['sample_member']))
 print('READ-ONLY EXECUTION RECIPE; interleaved binding is required. No command is executed.')
 print('Required native SHA256:',record['runtime_hash'])
 for phase in record['phase_schedule']:
  print('\n'+phase['phase']+'; timeout_s='+str(phase['timeout_s']))
  print(shlex.join(phase['command']))
  print('native environment:',json.dumps(phase['native_environment'],sort_keys=True))
 print('\nBinding / baseline / effective configuration: sample.json')
 print('Historical drivers and metric source: common/align_scripts.tar.gz')
 print('A matching native binary and environment are required. Fresh-host full replay is not validated by this archive.')
if __name__=='__main__':main()
