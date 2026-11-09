import{synthesize,parseRequest,evaluate,text}from'./engine.js';
const $=id=>document.getElementById(id),put=(id,v)=>$(id).textContent=v;let report=null;window.synthReport=null;window.synthRound=null;window.synthCandidate=null;window.synthProbe=null;
function rows(id,values){$(id).replaceChildren();for(const row of values){const tr=document.createElement('tr');for(const v of row){const td=document.createElement('td');td.textContent=v;tr.append(td);}$(id).append(tr);}}
function options(id,values){$(id).replaceChildren();for(const[v,label]of values){const o=document.createElement('option');o.value=v;o.textContent=label;$(id).append(o);}}
function clear(){report=null;window.synthReport=null;window.synthRound=null;window.synthCandidate=null;window.synthProbe=null;$('output').hidden=true;$('download').disabled=true;$('report').value='';put('error','');}
function inspect(){if(!report)return;const id=Number($('candidate').value),round=report.steps[Number($('round').value)],n=report.pool[id],probe=Number($('probe').value),point=report.inputs[probe];window.synthCandidate=id;window.synthProbe=probe;put('candidate-summary',`Function ID: ${id}
Expression: ${n.text}
AST node cost: ${n.cost}
Fits selected iteration's examples: ${round.eligible.includes(id)?'yes':'NO'}
Exact finite-domain correctness: ${n.outputs.every((v,j)=>v===report.request.target[j])?'yes':'NO'}
Probe row: ${probe} / x=${point.x}, y=${point.y}
Probe value / target: ${n.outputs[probe]} / ${report.request.target[probe]}`);const tree=[],cost=p=>typeof p==='string'?1:1+p.slice(1).reduce((a,c)=>a+cost(c),0);function visit(p,path){tree.push([path,typeof p==='string'?p:p[0],cost(p),evaluate(p,point.x,point.y,report.request.bits)]);if(Array.isArray(p))p.slice(1).forEach((q,j)=>visit(q,path+'.'+j));}visit(n.program,'root');rows('tree',tree);rows('truth',report.inputs.map((p,j)=>[j,p.x+' / '+p.y,round.examples.includes(j)?'yes':'no',report.request.target[j]+' / '+n.outputs[j],report.request.target[j]===n.outputs[j]?'yes':'NO']));}
function replay(){if(!report)return;const k=Number($('round').value),s=report.steps[k];window.synthRound=k;$('previous').disabled=k===0;$('next').disabled=k===report.steps.length-1;put('round-summary',`Iteration: ${k+1} / ${report.steps.length}
Known examples: ${s.examples.length}
Eligible semantic functions: ${s.eligible.length}
Selected candidate: ${s.candidate===null?'none':s.candidate+' / '+report.pool[s.candidate].text}
Verifier status: ${s.status}
Newly eliminated functions: ${s.eliminated.length}`);rows('examples',s.examples.map(j=>[j,report.inputs[j].x,report.inputs[j].y,report.request.target[j]]));put('counterexample',s.counterexample===null?(s.status==='solved'?'No wrong row exists in the complete supplied domain. This candidate is correct.':'No candidate in the complete bounded frontier fits even these examples. No solution in this grammar/cost bound.'):`Earliest wrong row: ${s.counterexample}
x=${report.inputs[s.counterexample].x}, y=${report.inputs[s.counterexample].y}
Candidate output: ${report.pool[s.candidate].outputs[s.counterexample]}
Target output: ${report.request.target[s.counterexample]}
This input is added before the next iteration.`);$('sets').value=JSON.stringify({eligible:s.eligible,eliminated:s.eliminated,next_examples:s.next_examples},null,2);$('candidate').value=s.candidate===null?0:s.candidate;$('probe').value=s.counterexample===null?0:s.counterexample;inspect();}
function run(){clear();try{report=synthesize(parseRequest($('input').value));window.synthReport=report;$('output').hidden=false;$('download').disabled=false;$('report').value=JSON.stringify(report,null,2);const s=report.summary;put('headline',s.status==='solved'?'A correct finite function. A minimum inside the grammar.':'The bounded grammar is exhausted.');put('summary',`Status: ${s.status}
Full-domain semantic classes: ${s.semantic_classes}
Representative compositions: ${s.compositions}
CEGIS iterations: ${s.iterations}
New counterexamples: ${s.counterexamples}
Final known examples: ${s.final_examples}
Minimum AST node cost: ${s.minimum_cost===null?'no solution in bound':s.minimum_cost}
Exact solution: ${report.solution===null?'none':report.pool[report.solution].text}`);put('claim',report.solution===null?'This is not a claim that the target is impossible to implement. The declared operators or cost limit may exclude it.':'Every input row agrees. All cheaper grammar expressions are covered by the complete semantic frontier. The minimum is relative to the stated pure-expression grammar and AST node cost, not runtime, code size in another language or general program synthesis.');rows('layers',report.layers.map(v=>[v.cost,v.compositions,v.new_classes.length]));options('round',report.steps.map((s,j)=>[j,(j+1)+': '+s.status+' / '+s.eligible.length+' eligible']));options('candidate',report.pool.map(n=>[n.id,n.id+': cost '+n.cost+' / '+n.text]));options('probe',report.inputs.map((p,j)=>[j,j+': x='+p.x+', y='+p.y]));$('round').value=0;replay();}catch(e){clear();put('error',e.message);}}
$('run').onclick=run;$('input').oninput=clear;$('round').onchange=replay;$('candidate').onchange=inspect;$('probe').onchange=inspect;$('previous').onclick=()=>{$('round').value=Number($('round').value)-1;replay();};$('next').onclick=()=>{$('round').value=Number($('round').value)+1;replay();};$('download').onclick=()=>{if(!report)return;const u=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='synthlab-certificate.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
try{const res=await fetch('controls.json');if(!res.ok)throw Error('Could not load controls');const cs=await res.json();options('control',cs.map((c,j)=>[j,c.name]));$('control').onchange=()=>{$('input').value=JSON.stringify(cs[Number($('control').value)].input,null,2);run();};$('control').value='0';$('control').onchange();}catch(e){put('error',e.message);}
