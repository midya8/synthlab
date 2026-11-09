import copy,itertools,json,unittest,subprocess,sys,tempfile,random
from pathlib import Path
from unittest.mock import patch
from synthlab import teaching as t
from synthlab.core import synthesize,OPS

class TeachingTests(unittest.TestCase):
 def test_every_boolean_grammar_function(self):
    # All semantic functions in every Boolean operator subset, not random samples.
    total=0
    for mask in range(32):
        ops=[v for j,v in enumerate(OPS)if mask>>j&1];x={'bits':1,'operators':ops,'max_cost':5,'target':[0]*4,'seeds':[]};pool=synthesize(x)['pool']
        for v in pool:
            x['target']=v['outputs'];a=t.teaching_atlas(x);self.assertTrue(t.verify_teaching(a));self.assertEqual(a['summary']['subset_count'],16);self.assertTrue(a['subsets'][-1]['teaches']);total+=1
    self.assertGreater(total,100)
 def test_seed_constraints_and_nonunique_correct_candidate(self):
    x={'bits':1,'operators':['and','xor'],'max_cost':3,'target':[0]*4,'seeds':[]};a=t.teaching_atlas(x);self.assertTrue(t.verify_teaching(a));self.assertFalse(a['cegis']['teaches']);self.assertEqual(a['cegis']['size'],0);self.assertGreater(a['minimum']['size'],0)
    for mask in range(16):
        x['seeds']=[j for j in range(4)if mask>>j&1];a=t.teaching_atlas(x);self.assertTrue(t.verify_teaching(a));self.assertEqual(a['seed_constrained']['chosen_mask']&mask,mask)
 def test_full_two_bit_domain(self):
    x={'bits':2,'operators':OPS,'max_cost':5,'target':[a^b for a in range(4)for b in range(4)],'seeds':[0]};a=t.teaching_atlas(x);self.assertTrue(t.verify_teaching(a));self.assertEqual(len(a['subsets']),65536);self.assertEqual(a['minimum']['size'],min(s['size']for s in a['subsets']if s['teaches']));self.assertEqual(a['minimum']['masks'],sorted(a['minimum']['masks']));self.assertLess(len(json.dumps(a)),8*1024*1024)
 def test_forgery_and_independence(self):
    x={'bits':1,'operators':['xor'],'max_cost':3,'target':[0,1,1,0],'seeds':[0]};a=t.teaching_atlas(x)
    with patch.object(t,'teaching_atlas',side_effect=AssertionError),patch.object(t,'synthesize',side_effect=AssertionError):self.assertTrue(t.verify_teaching(a))
    for change in [lambda r:r['subsets'].pop(),lambda r:r['subsets'][0].update(teaches=True),lambda r:r['row_eliminations'][0].append(999),lambda r:r['minimum'].update(size=True),lambda r:r['minimum']['masks'].pop(),lambda r:r['minimum']['deletion_witnesses'][0].update(surviving_rival=999),lambda r:r['seed_constrained'].update(added_size=-1),lambda r:r['cegis'].update(teaches=not r['cegis']['teaches']),lambda r:r['summary'].update(subset_count=1)]:
        b=copy.deepcopy(a);change(b);self.assertFalse(t.verify_teaching(b))
 def test_unrealizable_and_large_domain_rejected(self):
    for x in [{'bits':3,'operators':[],'max_cost':1,'target':[0]*64,'seeds':[]},{'bits':1,'operators':[],'max_cost':1,'target':[0,1,1,0],'seeds':[]}]:
        with self.assertRaises(ValueError):t.teaching_atlas(x)
    for x in [None,{},[],True]:self.assertFalse(t.verify_teaching(x))

 def test_teaching_cli_roundtrip_and_atomic_rejection(self):
    x={'bits':2,'operators':OPS,'max_cost':5,'target':[a^b for a in range(4)for b in range(4)],'seeds':[0]}
    with tempfile.TemporaryDirectory()as d:
        p=Path(d)/'in.json';out=Path(d)/'out.json';p.write_text(json.dumps(x));cmd=[sys.executable,'-m','synthlab.teaching_cli'];r=subprocess.run(cmd+[str(p),'--output',str(out)],capture_output=True);self.assertEqual(r.returncode,0,r.stderr);self.assertLess(out.stat().st_size,8*1024*1024);self.assertEqual(json.loads(out.read_text()),t.teaching_atlas(x));r=subprocess.run(cmd+[str(out),'--verify'],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout,'valid\n');before=out.read_bytes();p.write_text('{');r=subprocess.run(cmd+[str(p),'--output',str(out)],capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(out.read_bytes(),before)

 def test_seeded_two_bit_targets_and_optimal_set_witnesses(self):
    rng=random.Random(1995)
    for _ in range(12):
        ops=sorted(rng.sample(OPS,rng.randrange(1,6)));x={'bits':2,'operators':ops,'max_cost':rng.randrange(1,6),'target':[0]*16,'seeds':sorted(rng.sample(range(16),rng.randrange(5)))};pool=synthesize(x)['pool'];x['target']=rng.choice(pool)['outputs'];a=t.teaching_atlas(x);self.assertTrue(t.verify_teaching(a));self.assertGreaterEqual(a['seed_constrained']['total_size'],a['minimum']['size']);self.assertGreaterEqual(a['seed_constrained']['added_size'],0)
        for mask in a['minimum']['masks']:
            self.assertTrue(a['subsets'][mask]['teaches'])
            for j in range(16):
                if mask>>j&1:self.assertFalse(a['subsets'][mask^(1<<j)]['teaches'])
        for mask in a['seed_constrained']['masks']:
            self.assertTrue(a['subsets'][mask]['teaches']);self.assertEqual(mask&a['seed_constrained']['seed_mask'],a['seed_constrained']['seed_mask'])
        # Teaching is monotone under adding correctly labeled rows.
        for _ in range(80):
            mask=rng.randrange(65536);j=rng.randrange(16)
            if a['subsets'][mask]['teaches']:self.assertTrue(a['subsets'][mask|1<<j]['teaches'])
