"""Exact finite target-distinguishing sets, not class-wide teaching dimension."""
from .core import synthesize,verify,same

def teaching_atlas(request):
    base=synthesize(request)
    if base['request']['bits']>2:raise ValueError('teaching atlas supports only1..2-bit domains, at most16 rows')
    if base['solution']is None:raise ValueError('teaching requires a target representable in this grammar and bound')
    target=base['solution'];pool=base['pool'];n=len(base['inputs']);rivals=[v for v in pool if v['id']!=target];all_rivals=(1<<len(rivals))-1;rows=[]
    for row in range(n):
        mask=sum(1<<j for j,v in enumerate(rivals)if v['outputs'][row]==base['request']['target'][row]);rows.append(mask)
    survivors=[all_rivals]*(1<<n);subsets=[];best=n+1;best_masks=[];seed=sum(1<<i for i in base['request']['seeds']);ext_best=n+1;ext_masks=[]
    for mask in range(1<<n):
        if mask:
            low=mask&-mask;survivors[mask]=survivors[mask^low]&rows[low.bit_length()-1]
        size=mask.bit_count();left=survivors[mask].bit_count();subsets.append({'mask':mask,'size':size,'rivals_remaining':left,'teaches':left==0})
        if left==0:
            if size<best:best=size;best_masks=[]
            if size==best:best_masks.append(mask)
            if mask&seed==seed:
                if size<ext_best:ext_best=size;ext_masks=[]
                if size==ext_best:ext_masks.append(mask)
    chosen=best_masks[0];chosen_rows=[j for j in range(n)if chosen>>j&1];witnesses=[]
    for row in chosen_rows:
        reduced=chosen^(1<<row);first=next(v['id']for j,v in enumerate(rivals)if survivors[reduced]>>j&1);witnesses.append({'removed_row':row,'surviving_rival':first})
    cegis_mask=sum(1<<j for j in base['steps'][-1]['next_examples']);cegis_ids=[v['id']for j,v in enumerate(rivals)if survivors[cegis_mask]>>j&1]
    return {'schema':'synthlab-teaching-v1','synthesis':base,'rivals':[v['id']for v in rivals],'row_eliminations':[[v['id']for v in rivals if v['outputs'][j]!=base['request']['target'][j]]for j in range(n)],'subsets':subsets,'minimum':{'size':best,'masks':best_masks,'chosen_mask':chosen,'rows':chosen_rows,'deletion_witnesses':witnesses},'seed_constrained':{'seed_mask':seed,'total_size':ext_best,'added_size':ext_best-seed.bit_count(),'masks':ext_masks,'chosen_mask':ext_masks[0]},'cegis':{'mask':cegis_mask,'size':cegis_mask.bit_count(),'rivals_remaining':cegis_ids,'teaches':not cegis_ids},'summary':{'domain_rows':n,'rival_functions':len(rivals),'subset_count':1<<n,'teaching_subsets':sum(v['teaches']for v in subsets),'minimum_size':best,'minimum_count':len(best_masks),'seed_extension_minimum':ext_best-seed.bit_count()}}

def verify_teaching(c):
    try:_check(c);return True
    except(ValueError,TypeError,KeyError,IndexError,AttributeError,RecursionError):return False

def _check(c):
    def ok(x):
        if not x:raise ValueError('invalid teaching certificate')
    ok(type(c)is dict and set(c)=={'schema','synthesis','rivals','row_eliminations','subsets','minimum','seed_constrained','cegis','summary'}and c['schema']=='synthlab-teaching-v1');b=c['synthesis'];ok(verify(b));ok(b['request']['bits']<=2 and b['solution']is not None);n=len(b['inputs']);target=b['request']['target'];others=[v for v in b['pool']if v['outputs']!=target];ids=[v['id']for v in others];ok(same(c['rivals'],ids))
    # Independent direct disagreement sets and every subset/rival incidence.
    # No generator masks, dynamic programming, helpers or teaching_atlas calls.
    differences={v['id']:{j for j in range(n)if v['outputs'][j]!=target[j]}for v in others};rows=[[i for i in ids if j in differences[i]]for j in range(n)];ok(same(c['row_eliminations'],rows));table=[];good=[];seedset=set(b['request']['seeds']);extended=[]
    for mask in range(2**n):
        chosen={j for j in range(n)if(mask//(2**j))%2};left=[i for i in ids if chosen.isdisjoint(differences[i])];teaches=not left;table.append({'mask':mask,'size':len(chosen),'rivals_remaining':len(left),'teaches':teaches})
        if teaches:
            good.append((len(chosen),mask))
            if seedset<=chosen:extended.append((len(chosen),mask))
    ok(same(c['subsets'],table));best=min(a for a,_ in good);masks=[m for a,m in good if a==best];chosen=masks[0];selected=[j for j in range(n)if(chosen//2**j)%2];w=[]
    for j in selected:
        keep=set(selected)-{j};w.append({'removed_row':j,'surviving_rival':next(i for i in ids if keep.isdisjoint(differences[i]))})
    ok(same(c['minimum'],{'size':best,'masks':masks,'chosen_mask':chosen,'rows':selected,'deletion_witnesses':w}));ebest=min(a for a,_ in extended);emasks=[m for a,m in extended if a==ebest];sm=sum(2**j for j in seedset);ok(same(c['seed_constrained'],{'seed_mask':sm,'total_size':ebest,'added_size':ebest-len(seedset),'masks':emasks,'chosen_mask':emasks[0]}));examples=set(b['steps'][-1]['next_examples']);left=[i for i in ids if examples.isdisjoint(differences[i])];ok(same(c['cegis'],{'mask':sum(2**j for j in examples),'size':len(examples),'rivals_remaining':left,'teaches':not left}));ok(same(c['summary'],{'domain_rows':n,'rival_functions':len(ids),'subset_count':2**n,'teaching_subsets':len(good),'minimum_size':best,'minimum_count':len(masks),'seed_extension_minimum':ebest-len(seedset)}))
