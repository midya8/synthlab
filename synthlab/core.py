"""Bounded finite bit-vector CEGIS with full-domain semantic quotienting."""
import json
OPS=['add','and','neg','not','xor']
UNARY={'neg','not'}

def integer(v,lo,hi):return type(v)is int and lo<=v<=hi

def same(a,b):
    if type(a)is not type(b):return False
    if type(a)is list:return len(a)==len(b)and all(same(x,y)for x,y in zip(a,b))
    if type(a)is dict:return set(a)==set(b)and all(same(a[k],b[k])for k in a)
    return a==b

def validate(x):
    if type(x)is not dict or set(x)!={'bits','operators','max_cost','target','seeds'}:raise ValueError('request needs exactly bits, operators, max_cost, target, seeds')
    if not integer(x['bits'],1,3)or not integer(x['max_cost'],1,5):raise ValueError('bits must be 1..3 and max_cost 1..5 integers')
    o=x['operators'];side=1<<x['bits'];size=side*side
    if type(o)is not list or any(type(v)is not str or v not in OPS for v in o)or o!=sorted(set(o)):raise ValueError('operators must be sorted unique allowed names')
    t=x['target'];s=x['seeds']
    if type(t)is not list or len(t)!=size or any(not integer(v,0,side-1)for v in t):raise ValueError('target needs one bounded integer per x-major input row')
    if type(s)is not list or any(not integer(v,0,size-1)for v in s)or s!=sorted(set(s)):raise ValueError('seeds must be sorted unique input-row indices')
    return json.loads(json.dumps(x))

def text(p):return p if type(p)is str else '('+' '.join([p[0]]+[text(v)for v in p[1:]])+')'

def evaluate(p,x,y,bits):
    if type(p)is str:return {'0':0,'1':1,'x':x,'y':y}[p]
    op=p[0];a=evaluate(p[1],x,y,bits);mask=(1<<bits)-1
    if op=='not':return a^mask
    if op=='neg':return(-a)&mask
    b=evaluate(p[2],x,y,bits)
    return {'add':lambda:(a+b)&mask,'and':lambda:a&b,'xor':lambda:a^b}[op]()

def frontier(x):
    side=1<<x['bits'];inputs=[{'x':a,'y':b}for a in range(side)for b in range(side)];pool=[];seen={};layers=[]
    for cost in range(1,x['max_cost']+1):
        proposals=[]
        if cost==1:proposals=['0','1','x','y']
        for op in x['operators']:
            if op in UNARY:
                proposals.extend([op,n['program']]for n in pool if n['cost']==cost-1)
            else:
                for a in pool:
                    for b in pool:
                        if 1+a['cost']+b['cost']==cost:proposals.append([op,a['program'],b['program']])
        current={}
        for p in proposals:
            outputs=tuple(evaluate(p,d['x'],d['y'],x['bits'])for d in inputs)
            if outputs not in seen and(outputs not in current or text(p)<text(current[outputs])):current[outputs]=p
        added=[]
        for outputs,p in sorted(current.items(),key=lambda v:text(v[1])):
            i=len(pool);pool.append({'id':i,'cost':cost,'program':p,'text':text(p),'outputs':list(outputs)});seen[outputs]=i;added.append(i)
        layers.append({'cost':cost,'compositions':len(proposals),'new_classes':added})
    return inputs,pool,layers

def synthesize(request):
    x=validate(request);inputs,pool,layers=frontier(x);examples=x['seeds'][:];steps=[];target=x['target']
    while True:
        eligible=[n['id']for n in pool if all(n['outputs'][j]==target[j]for j in examples)];candidate=eligible[0]if eligible else None;ce=None
        if candidate is not None:ce=next((j for j,v in enumerate(pool[candidate]['outputs'])if v!=target[j]),None)
        status='exhausted-in-bound'if candidate is None else 'solved'if ce is None else 'counterexample';next_examples=sorted(examples+[ce])if ce is not None else examples[:];eliminated=[i for i in eligible if pool[i]['outputs'][ce]!=target[ce]]if ce is not None else []
        steps.append({'examples':examples[:],'eligible':eligible,'candidate':candidate,'counterexample':ce,'eliminated':eliminated,'next_examples':next_examples,'status':status});examples=next_examples
        if status!='counterexample':break
    solution=steps[-1]['candidate']if steps[-1]['status']=='solved'else None
    return {'schema':'synthlab-v1','request':x,'inputs':inputs,'pool':pool,'layers':layers,'steps':steps,'solution':solution,'summary':{'status':steps[-1]['status'],'semantic_classes':len(pool),'compositions':sum(v['compositions']for v in layers),'iterations':len(steps),'counterexamples':sum(v['counterexample']is not None for v in steps),'final_examples':len(examples),'minimum_cost':pool[solution]['cost']if solution is not None else None}}

def verify(report):
    try:_verify(report);return True
    except(ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError):return False

def _verify(c):
    def ok(v):
        if not v:raise ValueError('invalid synthesis certificate')
    ok(type(c)is dict and set(c)=={'schema','request','inputs','pool','layers','steps','solution','summary'}and c['schema']=='synthlab-v1');x=validate(c['request']);side=2**x['bits'];points=[(a,b)for a in range(side)for b in range(side)];ok(same(c['inputs'],[{'x':a,'y':b}for a,b in points]));raw={};semantics={};best={};mask=side-1
    # Audit independently by enumerating EVERY raw grammar tree. No semantic
    # pruning, no generator/evaluator/text/frontier calls. Small bound is vital.
    for size in range(1,x['max_cost']+1):
        trees=[('0',0),('1',1),('x',2),('y',3)]if size==1 else []
        rows=[]
        for name,code in trees:
            outs=[code if code<2 else pt[code-2]for pt in points];rows.append((name,name,outs))
        for op in x['operators']:
            if op in ['not','neg']:
                for t,p,vs in raw.get(size-1,[]):rows.append(('('+op+' '+t+')',[op,p],[(mask-v if op=='not'else -v)%side for v in vs]))
            else:
                for left in range(1,size-1):
                    for ta,pa,va in raw.get(left,[]):
                        for tb,pb,vb in raw.get(size-1-left,[]):
                            outs=[(a+b)%side if op=='add'else(a&b)if op=='and'else(a^b)for a,b in zip(va,vb)];rows.append(('('+op+' '+ta+' '+tb+')',[op,pa,pb],outs))
        raw[size]=rows
        for t,p,vs in rows:
            key=tuple(vs)
            if key not in best or(size,t)<(best[key][0],best[key][1]):best[key]=(size,t,p,vs)
    expected=[]
    for size,t,p,vs in sorted(best.values(),key=lambda v:(v[0],v[1])):expected.append({'id':len(expected),'cost':size,'program':p,'text':t,'outputs':vs})
    ok(same(c['pool'],expected));layers=[]
    for size in range(1,x['max_cost']+1):
        attempts=4 if size==1 else 0
        for op in x['operators']:
            if op in ['neg','not']:attempts+=sum(n['cost']==size-1 for n in expected)
            else:attempts+=sum(1 for a in expected for b in expected if a['cost']+b['cost']==size-1)
        layers.append({'cost':size,'compositions':attempts,'new_classes':[n['id']for n in expected if n['cost']==size]})
    ok(same(c['layers'],layers));ok(type(c['steps'])is list and 1<=len(c['steps'])<=len(points)+1);examples=x['seeds'][:];target=x['target'];steps=[]
    while True:
        ids=[n['id']for n in expected if all(n['outputs'][j]==target[j]for j in examples)];idx=ids[0]if ids else None;bad=[]if idx is None else[j for j in range(len(points))if expected[idx]['outputs'][j]!=target[j]];ce=bad[0]if bad else None;status='exhausted-in-bound'if idx is None else'counterexample'if bad else'solved';next_examples=sorted(set(examples)|{ce})if bad else examples[:];deleted=[]if not bad else[i for i in ids if expected[i]['outputs'][ce]!=target[ce]];steps.append({'examples':examples[:],'eligible':ids,'candidate':idx,'counterexample':ce,'eliminated':deleted,'next_examples':next_examples,'status':status});examples=next_examples
        if status!='counterexample':break
    ok(same(c['steps'],steps));solution=steps[-1]['candidate']if status=='solved'else None;ok(same(c['solution'],solution));summary={'status':status,'semantic_classes':len(expected),'compositions':sum(v['compositions']for v in layers),'iterations':len(steps),'counterexamples':sum(v['counterexample']is not None for v in steps),'final_examples':len(examples),'minimum_cost':expected[solution]['cost']if solution is not None else None};ok(same(c['summary'],summary))
