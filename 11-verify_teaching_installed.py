import json,subprocess,sys,tempfile
from pathlib import Path
import synthlab.teaching,synthlab.teaching_cli
from synthlab.teaching import teaching_atlas,verify_teaching
for module in [synthlab.teaching,synthlab.teaching_cli]:assert 'site-packages'in str(Path(module.__file__).resolve())
controls=json.loads(Path(sys.argv[1]).read_text())
with tempfile.TemporaryDirectory()as td:
 for c in controls:
  p=Path(td)/'request.json';p.write_text(json.dumps(c['input']));expected=teaching_atlas(c['input']);assert verify_teaching(expected)
  for cmd in [[sys.executable,'-m','synthlab.teaching_cli'],[sys.argv[2]]]:
   out=Path(td)/'report.json';subprocess.run(cmd+[str(p),'--output',str(out)],check=True,capture_output=True);assert json.loads(out.read_text())==expected;assert subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True,text=True).stdout=='valid\n'
print(f'Installed teaching: {len(controls)} controls, module+console generation/verification, two added site-packages origins, outside checkout')
