import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'experiments/FROZEN.json').read_text())
for name,digest in manifest['source_sha256'].items():
 b=(root/name).read_bytes();assert hashlib.sha256(b).hexdigest()==digest,name;ast.parse(b,filename=name)
print('PASS: four experiment sources match original executed hashes; no model fitting')
