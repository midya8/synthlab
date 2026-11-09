import json,subprocess,sys,tempfile
from pathlib import Path
import synthlab.adaptive,synthlab.adaptive_cli
from synthlab.adaptive import adaptive_atlas,verify_adaptive
for module in [synthlab.adaptive,synthlab.adaptive_cli]:assert 'site-packages'in str(Path(module.__file__).resolve())
controls=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory()as td:
 for c in controls:
  p=Path(td)/'request.json';p.write_text(json.dumps(c['input']));expected=adaptive_atlas(c['input']);assert verify_adaptive(expected)
  for cmd in [[sys.executable,'-m','synthlab.adaptive_cli'],[sys.argv[2]]]:
   out=Path(td)/'report.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected;assert subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True).stdout=='valid\n'
print(f'Installed adaptive: {len(controls)} controls, module+console generation/verification, two added site-packages origins, outside checkout')
