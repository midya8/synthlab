import {synthesize}from './engine.js';
const count=n=>{let k=0;for(;n;n&=n-1n)k++;return k;};
export function teachingAtlas(input){
 const b=synthesize(input);if(b.request.bits>2)throw Error('teaching atlas supports only1..2-bit domains, at most16 rows');if(b.solution===null)throw Error('teaching requires a target representable in this grammar and bound');const n=b.inputs.length,rivals=b.pool.filter(v=>v.id!==b.solution),all=(1n<<BigInt(rivals.length))-1n,agreement=Array.from({length:n},(_,j)=>rivals.reduce((m,v,k)=>v.outputs[j]===b.request.target[j]?m|(1n<<BigInt(k)):m,0n)),remaining=Array(2**n).fill(all),subsets=[];let best=n+1,masks=[],ebest=n+1,emasks=[];const seed=b.request.seeds.reduce((m,j)=>m|1<<j,0);
 for(let mask=0;mask<2**n;mask++){
  if(mask){const low=mask&-mask;remaining[mask]=remaining[mask^low]&agreement[Math.log2(low)];}
  const size=count(BigInt(mask)),left=count(remaining[mask]);subsets.push({mask,size,rivals_remaining:left,teaches:left===0});if(!left){if(size<best){best=size;masks=[];}if(size===best)masks.push(mask);if((mask&seed)===seed){if(size<ebest){ebest=size;emasks=[];}if(size===ebest)emasks.push(mask);}}
 }
 const chosen=masks[0],rows=Array.from({length:n},(_,j)=>j).filter(j=>chosen>>j&1),witnesses=rows.map(row=>({removed_row:row,surviving_rival:rivals.find((v,j)=>remaining[chosen^(1<<row)]>>BigInt(j)&1n).id})),cm=b.steps.at(-1).next_examples.reduce((m,j)=>m|1<<j,0),left=rivals.filter((v,j)=>remaining[cm]>>BigInt(j)&1n).map(v=>v.id);
 return{schema:'synthlab-teaching-v1',synthesis:b,rivals:rivals.map(v=>v.id),row_eliminations:Array.from({length:n},(_,j)=>rivals.filter(v=>v.outputs[j]!==b.request.target[j]).map(v=>v.id)),subsets,minimum:{size:best,masks,chosen_mask:chosen,rows,deletion_witnesses:witnesses},seed_constrained:{seed_mask:seed,total_size:ebest,added_size:ebest-count(BigInt(seed)),masks:emasks,chosen_mask:emasks[0]},cegis:{mask:cm,size:count(BigInt(cm)),rivals_remaining:left,teaches:left.length===0},summary:{domain_rows:n,rival_functions:rivals.length,subset_count:2**n,teaching_subsets:subsets.filter(v=>v.teaches).length,minimum_size:best,minimum_count:masks.length,seed_extension_minimum:ebest-count(BigInt(seed))}};
}
