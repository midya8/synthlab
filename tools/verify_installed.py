import json,subprocess,sys,tempfile
from pathlib import Path
import synthlab,synthlab.core,synthlab.__main__
from synthlab.core import synthesize,verify
for module in [synthlab,synthlab.core,synthlab.__main__]:assert 'site-packages'in str(Path(module.__file__).resolve())
controls=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory()as td:
 for c in controls:
  p=Path(td)/'request.json';p.write_text(json.dumps(c['input']));expected=synthesize(c['input']);assert verify(expected)
  for cmd in [[sys.executable,'-m','synthlab'],[sys.argv[2]]]:
   out=Path(td)/'report.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected;assert subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True).stdout=='valid\n'
print(f'Installed: {len(controls)} controls, both generation/verification entry points, three site-packages origins, outside checkout')
