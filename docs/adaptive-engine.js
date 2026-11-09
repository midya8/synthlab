import {synthesize} from './engine.js';
const pop=v=>{let n=0;for(;v;v&=v-1)n++;return n;};
export function adaptiveAtlas(input){
 const b=synthesize(input);if(b.request.bits>2)throw Error('adaptive atlas supports 1..2-bit domains only');if(b.solution===null)throw Error('adaptive target must be representable');
 const {seeds,target}=b.request,pool=b.pool,ids=pool.filter(p=>seeds.every(r=>p.outputs[r]===target[r])).map(p=>p.id);if(ids.length>10)throw Error('seeded version space exceeds 10 functions; add initial observations');
 const n=ids.length,rows=b.inputs.length,outputs=ids.map(i=>pool[i].outputs),states=[];
 for(let mask=1;mask<2**n;mask++){
  const members=ids.map((_,i)=>i).filter(i=>mask>>i&1),queries=[];let depth=0,optimal=[],balanced=[],best=0,worst=0;
  if(members.length>1){
   for(let row=0;row<rows;row++){
    const groups=new Map();for(const i of members)groups.set(outputs[i][row],(groups.get(outputs[i][row])||0)|(1<<i));const parts=[...groups.entries()].sort((a,b)=>a[0]-b[0]).map(([label,mask])=>({label,mask}));
    queries.push({row,branches:parts,worst_depth:parts.length>1?1+Math.max(...parts.map(p=>states[p.mask-1].depth)):null,largest_group:Math.max(...parts.map(p=>pop(p.mask)))});
   }
   const legal=queries.filter(q=>q.worst_depth!==null);depth=Math.min(...legal.map(q=>q.worst_depth));optimal=legal.filter(q=>q.worst_depth===depth).map(q=>q.row);const balance=Math.min(...legal.map(q=>q.largest_group));balanced=legal.filter(q=>q.largest_group===balance);best=Math.min(...balanced.map(q=>1+Math.max(...q.branches.map(p=>states[p.mask-1].balanced_best))));worst=Math.max(...balanced.map(q=>1+Math.max(...q.branches.map(p=>states[p.mask-1].balanced_worst))));
  }
  states.push({mask,members:members.map(i=>ids[i]),depth,queries,optimal_rows:optimal,balanced_rows:balanced.map(q=>q.row),balanced_best:best,balanced_worst:worst});
 }
 const differences=[];for(let i=0;i<n;i++)for(let j=0;j<i;j++)differences.push(outputs[i].reduce((m,v,r)=>m|(v!==outputs[j][r]?1<<r:0),0));let minimum=rows+1,masks=[];
 for(let mask=0;mask<2**rows;mask++){const size=pop(mask);if(size<=minimum&&differences.every(v=>mask&v)){if(size<minimum){minimum=size;masks=[];}masks.push(mask);}}
 const tree=mask=>{const s=states[mask-1];if(s.members.length===1)return {mask,hypothesis:s.members[0]};const row=s.optimal_rows[0];return {mask,row,branches:s.queries[row].branches.map(p=>({label:p.label,tree:tree(p.mask)}))};};
 const root=2**n-1,policy=tree(root),traces=ids.map(hypothesis=>{let node=policy;const steps=[];while('row'in node){const row=node.row,label=pool[hypothesis].outputs[row],child=node.branches.find(p=>p.label===label).tree;steps.push({mask:node.mask,row,label,next_mask:child.mask});node=child;}return {hypothesis,steps,leaf:node.hypothesis};});
 return {schema:'synthlab-adaptive-v1',synthesis:b,initial_ids:ids,states,passive:{size:minimum,masks,chosen_mask:masks[0]},policy,traces,summary:{initial_observations:seeds.length,initial_functions:n,version_spaces:states.length,root_mask:root,remaining_minimax_queries:states.at(-1).depth,passive_remaining_queries:minimum,balanced_best:states.at(-1).balanced_best,balanced_worst:states.at(-1).balanced_worst}};
}
