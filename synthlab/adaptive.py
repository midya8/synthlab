"""Exact remaining-query minimax policies for tiny seeded version spaces."""
from .core import synthesize,verify,same

SCHEMA='synthlab-adaptive-v1'

def adaptive_atlas(request):
    b=synthesize(request)
    if b['request']['bits']>2:raise ValueError('adaptive atlas supports 1..2-bit domains only')
    if b['solution']is None:raise ValueError('adaptive target must be representable')
    seeds=b['request']['seeds'];target=b['request']['target'];pool=b['pool'];ids=[p['id']for p in pool if all(p['outputs'][r]==target[r]for r in seeds)]
    if len(ids)>10:raise ValueError('seeded version space exceeds 10 functions; add initial observations')
    n=len(ids);rows=len(b['inputs']);outputs=[pool[i]['outputs']for i in ids];states=[]
    # Every branch is a proper submask, so numeric mask order is topological.
    for mask in range(1,1<<n):
        members=[i for i in range(n)if mask>>i&1];queries=[]
        if len(members)>1:
            for row in range(rows):
                groups={}
                for i in members:groups[outputs[i][row]]=groups.get(outputs[i][row],0)|(1<<i)
                parts=[{'label':label,'mask':v}for label,v in sorted(groups.items())];splits=len(parts)>1
                queries.append({'row':row,'branches':parts,'worst_depth':1+max(states[p['mask']-1]['depth']for p in parts)if splits else None,'largest_group':max(p['mask'].bit_count()for p in parts)})
            legal=[q for q in queries if q['worst_depth']is not None];depth=min(q['worst_depth']for q in legal);optimal=[q['row']for q in legal if q['worst_depth']==depth];balance=min(q['largest_group']for q in legal);balanced=[q for q in legal if q['largest_group']==balance]
            best=min(1+max(states[p['mask']-1]['balanced_best']for p in q['branches'])for q in balanced);worst=max(1+max(states[p['mask']-1]['balanced_worst']for p in q['branches'])for q in balanced)
        else:depth=0;optimal=[];balanced=[];best=worst=0
        states.append({'mask':mask,'members':[ids[i]for i in members],'depth':depth,'queries':queries,'optimal_rows':optimal,'balanced_rows':[q['row']for q in balanced],'balanced_best':best,'balanced_worst':worst})
    # Passive class separation is not target-specific teaching. Every pair must differ.
    differences=[sum(1<<r for r in range(rows)if outputs[i][r]!=outputs[j][r])for i in range(n)for j in range(i)];minimum=rows+1;masks=[]
    for mask in range(1<<rows):
        size=mask.bit_count()
        if size<=minimum and all(mask&v for v in differences):
            if size<minimum:minimum=size;masks=[]
            masks.append(mask)
    def tree(mask):
        s=states[mask-1]
        if len(s['members'])==1:return {'mask':mask,'hypothesis':s['members'][0]}
        row=s['optimal_rows'][0];q=s['queries'][row]
        return {'mask':mask,'row':row,'branches':[{'label':p['label'],'tree':tree(p['mask'])}for p in q['branches']]}
    root=(1<<n)-1;policy=tree(root);traces=[]
    for i in ids:
        node=policy;steps=[]
        while 'row'in node:
            row=node['row'];label=pool[i]['outputs'][row];child=next(p['tree']for p in node['branches']if p['label']==label);steps.append({'mask':node['mask'],'row':row,'label':label,'next_mask':child['mask']});node=child
        traces.append({'hypothesis':i,'steps':steps,'leaf':node['hypothesis']})
    return {'schema':SCHEMA,'synthesis':b,'initial_ids':ids,'states':states,'passive':{'size':minimum,'masks':masks,'chosen_mask':masks[0]},'policy':policy,'traces':traces,'summary':{'initial_observations':len(seeds),'initial_functions':n,'version_spaces':len(states),'root_mask':root,'remaining_minimax_queries':states[-1]['depth'],'passive_remaining_queries':minimum,'balanced_best':states[-1]['balanced_best'],'balanced_worst':states[-1]['balanced_worst']}}

def verify_adaptive(c):
    try:_audit(c);return True
    except(ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError,StopIteration):return False

def _audit(c):
    def ok(v):
        if not v:raise ValueError('invalid adaptive certificate')
    ok(type(c)is dict and set(c)=={'schema','synthesis','initial_ids','states','passive','policy','traces','summary'}and c['schema']=='synthlab-adaptive-v1');b=c['synthesis'];ok(verify(b));ok(b['request']['bits']<=2 and b['solution']is not None)
    # Rebuild the declared class only from initial observations, not final CEGIS examples.
    pool=b['pool'];seeds=b['request']['seeds'];target=b['request']['target'];ids=[p['id']for p in pool if all(p['outputs'][r]==target[r]for r in seeds)];n=len(ids);rows=len(b['inputs']);ok(1<=n<=10 and same(c['initial_ids'],ids));states=c['states'];ok(type(states)is list and len(states)==2**n-1)
    # Independently reconstruct explicit member sets and all label partitions.
    audited={};balanced_best={};balanced_worst={}
    for mask in range(1,2**n):
        members=[ids[i]for i in range(n)if(mask//2**i)%2];queries=[];choices=[];balanced=[]
        if len(members)>1:
            for row in range(rows):
                labels=sorted({pool[i]['outputs'][row]for i in members});parts=[]
                for label in labels:
                    child=[i for i in members if pool[i]['outputs'][row]==label];cm=sum(2**ids.index(i)for i in child);parts.append({'label':label,'mask':cm})
                score=1+max(audited[p['mask']]for p in parts)if len(parts)>1 else None
                queries.append({'row':row,'branches':parts,'worst_depth':score,'largest_group':max(sum((p['mask']//2**i)%2 for i in range(n))for p in parts)})
                if score is not None:choices.append(queries[-1])
            depth=min(q['worst_depth']for q in choices);optimal=[q['row']for q in choices if q['worst_depth']==depth];balance=min(q['largest_group']for q in choices);balanced=[q for q in choices if q['largest_group']==balance];best=min(1+max(balanced_best[p['mask']]for p in q['branches'])for q in balanced);worst=max(1+max(balanced_worst[p['mask']]for p in q['branches'])for q in balanced)
        else:depth=0;optimal=[];best=worst=0
        expected={'mask':mask,'members':members,'depth':depth,'queries':queries,'optimal_rows':optimal,'balanced_rows':[q['row']for q in balanced],'balanced_best':best,'balanced_worst':worst};ok(same(states[mask-1],expected));audited[mask]=depth;balanced_best[mask]=best;balanced_worst[mask]=worst
    # A separate exhaustive passive audit compares projected full output tuples.
    best=rows+1;ties=[]
    for mask in range(2**rows):
        selected=[r for r in range(rows)if(mask//2**r)%2]
        if len(selected)>best:continue
        signatures={tuple(pool[i]['outputs'][r]for r in selected)for i in ids}
        if len(signatures)==n:
            if len(selected)<best:best=len(selected);ties=[]
            ties.append(mask)
    ok(same(c['passive'],{'size':best,'masks':ties,'chosen_mask':ties[0]}));root=2**n-1
    def check_tree(node,mask):
        s=states[mask-1];ok(type(node)is dict and type(node.get('mask'))is int and node['mask']==mask)
        if len(s['members'])==1:ok(same(node,{'mask':mask,'hypothesis':s['members'][0]}));return
        ok(set(node)=={'mask','row','branches'}and type(node['row'])is int and node['row']==s['optimal_rows'][0]);q=s['queries'][node['row']];ok(type(node['branches'])is list and len(node['branches'])==len(q['branches']))
        for a,p in zip(node['branches'],q['branches']):ok(type(a)is dict and set(a)=={'label','tree'}and type(a['label'])is int and a['label']==p['label']);check_tree(a['tree'],p['mask'])
    check_tree(c['policy'],root);traces=[]
    for hypothesis in ids:
        node=c['policy'];steps=[]
        while 'row'in node:
            row=node['row'];label=pool[hypothesis]['outputs'][row];child=next(p['tree']for p in node['branches']if p['label']==label);steps.append({'mask':node['mask'],'row':row,'label':label,'next_mask':child['mask']});node=child
        ok(node['hypothesis']==hypothesis);traces.append({'hypothesis':hypothesis,'steps':steps,'leaf':hypothesis})
    ok(same(c['traces'],traces));ok(max(len(t['steps'])for t in traces)==audited[root]);ok(same(c['summary'],{'initial_observations':len(seeds),'initial_functions':n,'version_spaces':2**n-1,'root_mask':root,'remaining_minimax_queries':audited[root],'passive_remaining_queries':best,'balanced_best':balanced_best[root],'balanced_worst':balanced_worst[root]}))
