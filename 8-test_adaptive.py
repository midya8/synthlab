import copy,json,itertools,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from functools import lru_cache
from unittest.mock import patch
from synthlab import adaptive as a
from synthlab.core import synthesize,OPS

CONTROLS=json.loads((Path(__file__).resolve().parents[1]/'docs/adaptive-controls.json').read_text())

class AdaptiveTests(unittest.TestCase):
 def test_controls_and_exhaustive_policy_feasibility(self):
    for control in CONTROLS:
        c=a.adaptive_atlas(control['input']);self.assertTrue(a.verify_adaptive(c));pool=c['synthesis']['pool'];rows=len(c['synthesis']['inputs'])
        # Enumerate depth-bounded decision policies, not the Bellman generator.
        @lru_cache(None)
        def feasible(ids,budget):
            if len(ids)==1:return True
            if budget==0:return False
            for r in range(rows):
                groups=[tuple(i for i in ids if pool[i]['outputs'][r]==label)for label in sorted({pool[i]['outputs'][r]for i in ids})]
                if len(groups)>1 and all(feasible(g,budget-1)for g in groups):return True
            return False
        for s in c['states']:
            members=tuple(s['members']);self.assertTrue(feasible(members,s['depth']))
            if s['depth']:self.assertFalse(feasible(members,s['depth']-1))
        self.assertEqual(max(len(t['steps'])for t in c['traces']),c['summary']['remaining_minimax_queries'])
        self.assertLess(len(json.dumps(c,indent=2)),32*1024*1024)
    gap=a.adaptive_atlas(CONTROLS[2]['input']);self.assertEqual(gap['summary']['remaining_minimax_queries'],2);self.assertEqual(gap['passive']['size'],3);self.assertEqual([gap['summary'][k]for k in ['balanced_best','balanced_worst']],[2,3]);self.assertEqual(len(gap['initial_ids']),10)
 def test_boolean_grammars_and_all_initial_observations(self):
    count=0
    for mask in range(32):
        ops=[x for i,x in enumerate(OPS)if mask>>i&1];base={'bits':1,'operators':ops,'max_cost':3,'target':[0]*4,'seeds':[]};pool=synthesize(base)['pool']
        for seedmask in range(16):
            x=dict(base,seeds=[r for r in range(4)if seedmask>>r&1]);c=a.adaptive_atlas(x);self.assertTrue(a.verify_adaptive(c));count+=1
            for s in c['states']:
                self.assertLessEqual(s['depth'],len(c['synthesis']['inputs']));self.assertLessEqual(s['depth'],s['balanced_best']);self.assertLessEqual(s['balanced_best'],s['balanced_worst'])
                self.assertTrue(set(s['optimal_rows']).isdisjoint(x['seeds']))
    self.assertEqual(count,512)
 def test_target_independence_and_observation_accounting(self):
    c=a.adaptive_atlas(CONTROLS[2]['input']);pool=c['synthesis']['pool']
    for i in c['initial_ids']:
        x=dict(CONTROLS[2]['input'],target=pool[i]['outputs']);other=a.adaptive_atlas(x)
        for key in c:
            if key!='synthesis':self.assertEqual(other[key],c[key])
    self.assertEqual(c['summary']['initial_observations'],2);self.assertEqual(c['summary']['remaining_minimax_queries'],2)
    for tr in c['traces']:
        seen=set(CONTROLS[2]['input']['seeds'])
        for step in tr['steps']:self.assertNotIn(step['row'],seen);seen.add(step['row'])
 def test_verifier_independence_forgery_and_strict_types(self):
    c=a.adaptive_atlas(CONTROLS[0]['input'])
    with patch.object(a,'adaptive_atlas',side_effect=AssertionError),patch.object(a,'synthesize',side_effect=AssertionError):self.assertTrue(a.verify_adaptive(c))
    changes=[lambda x:x['states'].pop(),lambda x:x['initial_ids'].reverse(),lambda x:x['states'][-1].update(depth=True),lambda x:x['states'][-1]['optimal_rows'].pop(),lambda x:x['states'][-1]['balanced_rows'].pop(),lambda x:x['states'][-1].update(balanced_best=99),lambda x:x['states'][-1]['queries'][0]['branches'][0].update(mask=999),lambda x:x['passive'].update(size=0),lambda x:x['passive']['masks'].pop(),lambda x:x['policy'].update(row=True),lambda x:x['policy']['branches'][0].update(label=True),lambda x:x['traces'][0]['steps'][0].update(next_mask=0),lambda x:x['summary'].update(initial_observations=99),lambda x:x['synthesis']['pool'][0]['outputs'].__setitem__(0,1)]
    for change in changes:
        bad=copy.deepcopy(c);change(bad);self.assertFalse(a.verify_adaptive(bad))
    for bad in [None,{},[],True]:self.assertFalse(a.verify_adaptive(bad))
 def test_caps_unrealizable_and_no_silent_subclasses(self):
    for x in [dict(CONTROLS[2]['input'],seeds=[]),{'bits':3,'operators':[],'max_cost':1,'target':[0]*64,'seeds':[]},{'bits':1,'operators':[],'max_cost':1,'target':[1,0,0,1],'seeds':[]}]:
        with self.assertRaises(ValueError):a.adaptive_atlas(x)
    singleton=a.adaptive_atlas(CONTROLS[3]['input']);self.assertEqual(singleton['policy'],{'mask':1,'hypothesis':singleton['initial_ids'][0]});self.assertEqual(singleton['passive']['masks'],[0]);self.assertEqual(singleton['states'][0]['queries'],[])
 def test_varied_seeded_word_targets_and_monotonicity(self):
    rng=random.Random(413);cases=[]
    for attempt in range(2000):
        ops=sorted(rng.sample(OPS,rng.randrange(6)));cost=rng.randrange(1,6);base={'bits':2,'operators':ops,'max_cost':cost,'target':[0]*16,'seeds':[]};pool=synthesize(base)['pool'];target=rng.choice(pool)['outputs'];seeds=sorted(rng.sample(range(16),rng.randrange(1,7)));initial=[p for p in pool if all(p['outputs'][r]==target[r]for r in seeds)]
        if not 2<=len(initial)<=10:continue
        x=dict(base,target=target,seeds=seeds);c=a.adaptive_atlas(x);self.assertTrue(a.verify_adaptive(c));self.assertEqual(c['initial_ids'],[p['id']for p in initial]);extra=next(r for r in range(16)if r not in seeds);more=a.adaptive_atlas(dict(x,seeds=sorted(seeds+[extra])));self.assertTrue(a.verify_adaptive(more));self.assertLessEqual(more['summary']['remaining_minimax_queries'],c['summary']['remaining_minimax_queries']);self.assertLessEqual(c['summary']['remaining_minimax_queries'],c['passive']['size'])
        for mask in c['passive']['masks']:self.assertTrue(all(not(mask>>r&1)for r in seeds))
        cases.append(x)
        if len(cases)==24:break
    self.assertEqual(len(cases),24)
 def test_cli_largest_roundtrip_and_atomic_rejection(self):
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory()as d:
        p=Path(d)/'input.json';out=Path(d)/'out.json';p.write_text(json.dumps(CONTROLS[2]['input']));cmd=[sys.executable,'-m','synthlab.adaptive_cli'];r=subprocess.run(cmd+[str(p),'--output',str(out)],cwd=root,capture_output=True);self.assertEqual(r.returncode,0,r.stderr);self.assertGreater(out.stat().st_size,5_000_000);r=subprocess.run(cmd+[str(out),'--verify'],cwd=root,capture_output=True);self.assertEqual(r.stdout,b'valid\n');out.write_text('preserve')
        for bad in ['{"bits":1,"bits":2}','NaN','['*66+']'*66,'x'*65537]:
            p.write_text(bad);r=subprocess.run(cmd+[str(p),'--output',str(out)],cwd=root,capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(out.read_text(),'preserve')
        self.assertEqual(sorted(v.name for v in Path(d).iterdir()),['input.json','out.json'])

if __name__=='__main__':unittest.main()
