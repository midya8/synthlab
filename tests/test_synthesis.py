import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from synthlab import core as c
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/controls.json').read_text())

def raw_programs(ops,bound):
    # Raw ordered ASTs, not quotient representatives.
    costs={1:['0','1','x','y']}
    for n in range(2,bound+1):
        ps=[]
        for op in ops:
            if op in ['neg','not']:ps.extend([op,p]for p in costs[n-1])
            else:
                for left in range(1,n-1):ps.extend([op,a,b]for a in costs[left]for b in costs[n-1-left])
        costs[n]=ps
    return costs

def oracle(p,x,y,bits):
    # Independent fixed-width bit list operations, not the generator evaluator.
    size=2**bits
    if isinstance(p,str):return int(p)if p in ['0','1']else x if p=='x'else y
    a=oracle(p[1],x,y,bits)
    if p[0]=='neg':return(size-a)%size
    if p[0]=='not':return size-1-a
    b=oracle(p[2],x,y,bits)
    if p[0]=='add':return(a+b)%size
    aa=[(a//2**j)%2 for j in range(bits)];bb=[(b//2**j)%2 for j in range(bits)];return sum((u*v if p[0]=='and'else(u+v)%2)*2**j for j,(u,v)in enumerate(zip(aa,bb)))

class SynthesisTests(unittest.TestCase):
 def test_controls_and_independent_semantics(self):
    for control in CONTROLS:
        before=copy.deepcopy(control['input']);r=c.synthesize(before);self.assertEqual(before,control['input']);self.assertTrue(c.verify(r));bits=before['bits'];size=2**bits
        for n in r['pool']:self.assertEqual(n['outputs'],[oracle(n['program'],x,y,bits)for x in range(size)for y in range(size)])
        for step in r['steps']:
            if step['candidate']is not None:
                n=r['pool'][step['candidate']];self.assertTrue(all(n['outputs'][j]==before['target'][j]for j in step['examples']))
            if step['counterexample']is not None:self.assertNotIn(step['counterexample'],step['examples']);self.assertGreater(len(step['eliminated']),0)
    self.assertEqual(c.synthesize(CONTROLS[0]['input'])['summary']['minimum_cost'],3);self.assertEqual(c.synthesize(CONTROLS[6]['input'])['summary']['status'],'exhausted-in-bound')
 def test_all_boolean_targets_and_all_operator_subsets(self):
    total=0
    for mask in range(32):
        ops=[op for j,op in enumerate(c.OPS)if mask>>j&1]
        # Independent raw grammar oracle for solvability and minimum cost.
        representable={}
        for cost,ps in raw_programs(ops,5).items():
            for p in ps:
                out=tuple(oracle(p,x,y,1)for x in range(2)for y in range(2));representable.setdefault(out,cost)
        for target in itertools.product(range(2),repeat=4):
            x={'bits':1,'operators':ops,'max_cost':5,'target':list(target),'seeds':[]};r=c.synthesize(x);self.assertTrue(c.verify(r));self.assertEqual(r['summary']['minimum_cost'],representable.get(target));total+=1
    self.assertEqual(total,512)
 def test_raw_grammar_canonical_minimums_and_quotient(self):
    # Every raw tree at maximum grammar cost 5, all three bit widths.
    for bits in [1,2,3]:
        x={'bits':bits,'operators':c.OPS[:],'max_cost':5,'target':[0]*(4**bits),'seeds':[]};r=c.synthesize(x);best={};raw_count=0
        for cost,ps in raw_programs(c.OPS,5).items():
            for p in ps:
                raw_count+=1;sig=tuple(oracle(p,a,b,bits)for a in range(2**bits)for b in range(2**bits));v=(cost,c.text(p))
                if sig not in best or v<best[sig]:best[sig]=v
        self.assertEqual(raw_count,2764);self.assertEqual({tuple(n['outputs']):(n['cost'],n['text'])for n in r['pool']},best)
 def test_seeded_finite_targets_and_costs(self):
    x=copy.deepcopy(CONTROLS[-1]['input']);before=c.synthesize(x)['pool'];x['target']=[0]*len(x['target']);x['seeds']=[0];self.assertEqual(c.synthesize(x)['pool'],before)
    rng=random.Random(2006)
    for _ in range(80):
        bits=rng.randrange(1,4);side=2**bits;ops=[op for op in c.OPS if rng.randrange(2)];bound=rng.randrange(1,6);target=[rng.randrange(side)for _ in range(side*side)];seeds=sorted(rng.sample(range(side*side),rng.randrange(min(4,side*side)+1)));x={'bits':bits,'operators':ops,'max_cost':bound,'target':target,'seeds':seeds};r=c.synthesize(x);self.assertTrue(c.verify(r));self.assertLessEqual(len(r['steps']),side*side+1)
 def test_verifier_has_no_generator_dependencies(self):
    r=c.synthesize(CONTROLS[-1]['input'])
    with patch.object(c,'synthesize',side_effect=AssertionError),patch.object(c,'frontier',side_effect=AssertionError),patch.object(c,'evaluate',side_effect=AssertionError),patch.object(c,'text',side_effect=AssertionError):self.assertTrue(c.verify(r))
 def test_forged_certificates(self):
    r=c.synthesize(CONTROLS[0]['input'])
    for change in [lambda r:r.update(extra=0),lambda r:r['pool'].pop(),lambda r:r['pool'][0]['outputs'].__setitem__(0,True),lambda r:r['pool'][0].update(program='x'),lambda r:r['layers'][0].update(compositions=3),lambda r:r['steps'][0]['eligible'].pop(),lambda r:r['steps'][0].update(counterexample=2),lambda r:r['steps'][0]['eliminated'].clear(),lambda r:r.update(solution=True),lambda r:r['summary'].update(minimum_cost=1),lambda r:r['inputs'][0].update(x=1)]:
        t=copy.deepcopy(r);change(t);self.assertFalse(c.verify(t))
    for v in [None,{},[],True,{'schema':'synthlab-v1'}]:self.assertFalse(c.verify(v))
 def test_strict_request(self):
    x=CONTROLS[0]['input']
    for k,v in [('bits',True),('bits',2.0),('bits',0),('bits',4),('max_cost',6),('operators',['xor','xor']),('operators',['mul']),('seeds',[0,0]),('seeds',[True]),('target',[0])]:
        t=copy.deepcopy(x);t[k]=v
        with self.assertRaises(ValueError):c.synthesize(t)
    for v in [None,{},[],True,{**x,'extra':0}]:
        with self.assertRaises(ValueError):c.synthesize(v)
 def test_cli_transport_atomicity(self):
    with tempfile.TemporaryDirectory()as td:
        p=Path(td)/'request.json';o=Path(td)/'report.json';p.write_text(json.dumps(CONTROLS[0]['input']));cmd=[sys.executable,'-m','synthlab',str(p),'--output',str(o)];self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0);self.assertTrue(c.verify(json.loads(o.read_text())));self.assertEqual(subprocess.run([sys.executable,'-m','synthlab',str(o),'--verify'],capture_output=True).stdout,b'valid\n');before=o.read_bytes()
        for invalid in ['{}','{"bits":2,"bits":2}','NaN','['*1000+']'*1000,' '*65537]:
            p.write_text(invalid);self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,2);self.assertEqual(o.read_bytes(),before)
        p.write_bytes(b' '*(8*1024*1024+1));self.assertEqual(subprocess.run([sys.executable,'-m','synthlab',str(p),'--verify'],capture_output=True).returncode,2)
