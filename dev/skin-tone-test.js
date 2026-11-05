'use strict';
// Uses the existing app harness read-only; all task evidence stays in dev/.
const assert=require('node:assert/strict'),A=require('../game.js');
const {host}=require('../qa/commission-flow-test.js');
async function main(){
 for(const theme of A.themes)assert.equal(theme.skin,theme.asset==='c_bride'?'#8a5a3c':undefined);
 for(const person of [3,8,0]){
  const s=A.freshSave();s.order={person,requirements:[{key:'color',value:'pink'},{key:'material',value:'satin'}],duration:85,vip:false};
  s.fitting={sock:'fishnet',color:'black',skin:'#123456'};
  const h=await host({seedState:s});
  try{
   await h.fitting();assert.equal(h.saved().gallery[0].fitting.skin,A.themes[person].skin);
   assert.equal(A.sanitizeSave(h.saved()).gallery[0].fitting.skin,A.themes[person].skin);
   h.click({fittingSock:'sheer'});await h.settle();
   assert.equal(h.saved().gallery[0].fitting.skin,A.themes[person].skin);
   assert.equal(h.saved().fitting.skin,undefined,'Customer skin cannot become the global preference');
  }finally{h.dispose();}
 }
 const s=A.freshSave();s.fitting={sock:'none',color:'cream',skin:'#8a5a3c'};
 const h=await host({free:true,seedState:s});
 try{await h.fitting();assert.equal(h.saved().gallery[0].fitting.skin,undefined);}finally{h.dispose();}
 for(const bad of ['red','#abc','url(x)',42,null])assert.equal(A.cleanFittingOptions({skin:bad}).skin,undefined);
 assert.equal(A.cleanFittingOptions({skin:'#8A5A3C'}).skin,'#8a5a3c');
 console.log('PASS: bride-only tone, real customer packing/fitting/sock changes, save roundtrip, free/fair isolation and colour validation.');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
