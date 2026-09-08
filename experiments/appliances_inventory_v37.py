"""Zero-fit source inventory. Run on private cloud CPU only."""
import csv,hashlib,json,math,urllib.request,time
from pathlib import Path
from datetime import datetime,timedelta
from collections import Counter
URL='https://raw.githubusercontent.com/LuisM78/Appliances-energy-prediction-data/e3e4c27a4ae2b41b21f84b4c9ac2d822d3d0ace1/energydata_complete.csv'
CAP=16*1024*1024
out=Path('/kaggle/working/appliances_v37');out.mkdir(exist_ok=False)
report={'status':'started','fits':0,'cash':0,'url':URL,'max_download_bytes':CAP}
t0=time.monotonic()
try:
 with urllib.request.urlopen(URL,timeout=45) as response:
  raw=response.read(CAP+1)
 if len(raw)>CAP:raise ValueError('download_size_exceeded')
 (out/'energydata_complete.csv').write_bytes(raw)
 report['csv_sha256']=hashlib.sha256(raw).hexdigest();report['csv_bytes']=len(raw)
 times=[];bad=0
 import io
 for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
  times.append(datetime.strptime(row['date'],'%Y-%m-%d %H:%M:%S'))
  try:bad+=not math.isfinite(float(row['Appliances']))
  except (ValueError,TypeError):bad+=1
 if not times:raise ValueError('empty_source')
 delta=Counter(int((b-a).total_seconds()) for a,b in zip(times,times[1:]))
 report.update(rows=len(times),first=times[0].isoformat(),last=times[-1].isoformat(),duplicate_timestamps=len(times)-len(set(times)),interval_seconds=dict(delta),nonfinite_targets=bad)
 firstday=times[0].replace(hour=0,minute=0,second=0)
 if times[0]!=firstday:firstday+=timedelta(days=1)
 origin=firstday+timedelta(days=7)
 episodes=[]
 for i in range(5):
  start=origin+timedelta(days=21*i);end=start+timedelta(days=21)
  count=sum(start<=t<end for t in times)
  episodes.append({'episode':i,'start':start.isoformat(),'end_exclusive':end.isoformat(),'rows':count,'expected_rows':21*144})
 report['episodes']=episodes
 report['coverage_pass']=len(times)==19735 and bad==0 and report['duplicate_timestamps']==0 and set(delta)=={600} and all(e['rows']==e['expected_rows'] for e in episodes)
 report['status']='complete';report['scientific_validity_pass']=False
except Exception as e:
 report['status']='failed';report['error_type']=type(e).__name__;report['error']=str(e)
finally:
 report['seconds']=time.monotonic()-t0
 (out/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False))
 print(json.dumps(report,allow_nan=False))
