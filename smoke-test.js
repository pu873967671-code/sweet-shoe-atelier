'use strict';
const assert=require('node:assert/strict');
// Keep the fitted-commission handoff in the mandatory smoke gate.
require('node:child_process').execFileSync(process.execPath,[require.resolve('./qa/commission-flow-test.js')],{stdio:'inherit'});
const {generateOrder,scoreOrder,sanitizeSave,freshSave,cleanDesign,matches,customersForDay,designKey,shoeLayout,shoeCanvas,SHOE_ANCHORS,ASSET_NAMES,opts,I18N}=require('./game.js');
// An older cloud write can finish after a later local save in the same
// millisecond. Do not discard the local design, wallet or fitting on reload.
{
 const {selectSaveCandidate}=require('./game.js');
 const local=JSON.stringify({savedAt:100,coins:50,design:{color:'blue'},fitting:{sock:'fishnet'}});
 const staleCloud=JSON.stringify({savedAt:100,coins:30,design:{color:'pink'},fitting:{sock:'none'}});
 assert.deepEqual(selectSaveCandidate(local,staleCloud),JSON.parse(local));
 assert.deepEqual(selectSaveCandidate(local,JSON.stringify({savedAt:101,coins:60})),{savedAt:101,coins:60});
 assert.deepEqual(selectSaveCandidate(local,JSON.stringify({savedAt:'101',coins:60})),{savedAt:'101',coins:60});
 assert.deepEqual(selectSaveCandidate('invalid',staleCloud),JSON.parse(staleCloud));
 assert.deepEqual(selectSaveCandidate(local,'[]'),JSON.parse(local));
}
let seed=94;const random=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
for(let day=1;day<=30;day++)for(let served=0;served<customersForDay(day);served++){
 const s={...freshSave(),day,served};const o=generateOrder(s,random);
 assert(o.requirements.length>=2&&o.requirements.length<=4);
 assert.equal(o.vip,day>=3&&served===customersForDay(day)-1);
 const d=cleanDesign({});
 for(const r of o.requirements){if(r.key==='noBows'){if(['small','big'].includes(d.decoration))d.decoration='none';if(d.charm==='mini')d.charm='none';if(['ribbon','cross'].includes(d.strap))d.strap='none';}else{d[r.key]=r.value;assert(!opts[r.key].find(x=>x[0]===r.value)[2]);}}
 assert(o.requirements.every(r=>matches(d,r)));
 assert.equal(scoreOrder(d,o,o.duration).stars,3);
 assert(scoreOrder(d,o,o.duration).earned>scoreOrder(d,o,0).earned);
 assert.equal(sanitizeSave({...s,order:o}).order.person,o.person);
}
const o={person:1,duration:80,vip:false,requirements:[{key:'color',value:'cream'},{key:'strap',value:'pearl'}]};
const d={...cleanDesign({}),color:'cream',strap:'pearl'};
assert.equal(scoreOrder(d,o,0,2).multiplier,1.25);
assert.equal(scoreOrder(d,{...o,vip:true},0).earned,scoreOrder(d,o,0).earned*2);
assert.equal(scoreOrder({...d,color:'pink',strap:'none'},o,0).stars,1);
assert(!matches({...d,decoration:'big'},{key:'noBows'}));
assert(!matches({...d,strap:'ribbon'},{key:'noBows'}));
assert(!matches({...d,strap:'cross'},{key:'noBows'}),'Cross laces have a tied side bow in product and fitting cameras');
// Expanded trims must survive real saves and never create contradictory
// commissions once all crafted details are available.
{
 const A=require('./game.js'),s=freshSave();
 for(const category of ['strap','decoration','charm']){
  assert(opts[category].length-1>=6&&opts[category].length-1<=10);
  for(const [value] of opts[category]){
   s.design=cleanDesign({...d,[category]:value});
   s.gallery=[{design:{...s.design},day:1,stars:3}];
   const saved=sanitizeSave(JSON.parse(JSON.stringify(s)));
   assert.equal(saved.design[category],value);
   assert.equal(saved.gallery[0].design[category],value);
  }
 }
 for(const decoration of ['puffy','doublebow','heelbow'])assert(!matches({...d,decoration},{key:'noBows'}));
 assert(matches({...d,decoration:'rosette'},{key:'noBows'}),'A flower rosette contains no bow');
 for(const [category,values] of Object.entries({strap:['crystalband','satinbraid'],decoration:['camellia','heelbow'],charm:['butterfly','pearlcluster']}))for(const value of values){
  assert(A.AccessoryRenderer.handles(category,value),'Missing shared ornament renderer: '+value);
  const earned=freshSave();assert(!A.unlocked(earned,category,value),'New couture details must be earned');
  const gate=A.CRAFT_UNLOCKS[category+':'+value];assert(gate);earned.atelier.discovered.push(gate);assert(A.unlocked(earned,category,value));
  for(const lang of ['en','zh'])assert(I18N[lang][value]&&I18N[lang][value]!==value);
 }
 assert(matches({...d,decoration:'camellia',charm:'butterfly',strap:'satinbraid'},{key:'noBows'}),'Flower, butterfly and braid do not contain bows');
 s.day=8;
 s.unlocks=Object.entries(opts).flatMap(([key,values])=>values.map(([value])=>key+':'+value));
 for(let i=0;i<2500;i++){
  const order=generateOrder(s,random),sample=A.commissionDesign(order);
  assert(order.requirements.every(r=>matches(sample,r)),'Expanded trim commission cannot be fulfilled');
 }
}
assert.equal(customersForDay(99),8);
assert.deepEqual(sanitizeSave(null,1000),freshSave(1000));
const corrupted=sanitizeSave({coins:NaN,day:-10,unlocks:[null,'color:purple','bad'],gallery:[null,{design:{color:'bad'}}],order:{},design:{color:'invalid'}});
assert.equal(corrupted.coins,30);assert.equal(corrupted.day,1);assert.equal(corrupted.order,null);assert.deepEqual(corrupted.unlocks,['color:purple']);assert.equal(corrupted.gallery[0].design.color,'pink');
// Invalid saved commission keys must discard only that commission. Inherited
// object properties are not option lists and must never abort save recovery.
for(const key of ['constructor','toString','__proto__','unknown']){
 const recoveryTime=1700000000000,damaged={...freshSave(recoveryTime),coins:321,unlocks:['color:purple'],gallery:[{design:d,day:3,stars:3}],order:{person:0,duration:80,requirements:[{key,value:'invalid'},{key:'color',value:'pink'}]}};
 const restored=sanitizeSave(JSON.parse(JSON.stringify(damaged)),recoveryTime);
 assert.equal(restored.order,null,'Invalid commission key: '+key);
 assert.equal(restored.coins,321);assert.deepEqual(restored.unlocks,['color:purple']);assert.equal(restored.gallery.length,1);
 assert.deepEqual(restored.atelier,damaged.atelier,'Board progress survives invalid commission key: '+key);
}
assert.deepEqual(sanitizeSave(JSON.parse(JSON.stringify({...freshSave(),coins:123,unlocks:['color:purple']}))).coins,123);
for(const key of Object.keys(I18N.en))assert.equal(typeof I18N.zh[key],'string','Missing Chinese '+key);
for(const key of Object.keys(I18N.zh))assert.equal(typeof I18N.en[key],'string','Missing English '+key);
for(const [k,list] of Object.entries(opts))for(const item of list){
 const variant={...d,[k]:item[0]},markup=shoeCanvas(variant),layout=shoeLayout(variant);
 assert(markup.startsWith('<canvas'));assert(!markup.includes('undefined'));assert(!markup.includes('NaN'));
 assert(SHOE_ANCHORS[layout.asset]);assert(ASSET_NAMES.includes(layout.asset));
 for(const point of [layout.toe,layout.back])assert(point.every(x=>Number.isFinite(x)&&x>=0&&x<=1000));
 assert.equal(designKey(variant),designKey({...variant,extra:true}));
}
assert.equal(Object.keys(SHOE_ANCHORS).length,20);
assert.equal(new Set(ASSET_NAMES).size,ASSET_NAMES.length);
for(const heel of opts.heel)for(const strap of opts.strap){const layout=shoeLayout({...d,heel:heel[0],strap:strap[0]});assert(layout.y>=0);assert(layout.y+layout.height<=550.001);}
console.log('PASS: 30 days of achievable orders; VIP, scoring, combos, negatives, save recovery, localization, all canvas variants and 20 artwork anchors.');

// v2 migration preserves every existing studio field and creates a deterministic v3 board.
const now=1700000000000, M=require('./game.js').Merge;
const legacy={...freshSave(now),version:2,coins:487,lang:'zh',tutorial:true,gallery:[{design:d,day:3,stars:3}],unlocks:['color:purple'],atelier:undefined};
const migrated=sanitizeSave(legacy,now);
assert.equal(migrated.version,3);assert.equal(migrated.coins,487);assert.equal(migrated.lang,'zh');assert.equal(migrated.gallery.length,1);assert.deepEqual(migrated.unlocks,['color:purple']);
assert.equal(migrated.atelier.cells.length,63);assert.equal(migrated.atelier.cells.filter(c=>c?.kind==='crate').length,28);
assert.deepEqual(sanitizeSave(JSON.parse(JSON.stringify(migrated)),now),migrated);
const b=M.create(now), before=JSON.stringify(b);
assert(!M.move(b,-1,4).ok);assert(!M.move(b,23,25).ok);assert.equal(JSON.stringify(b),before);
let merge=M.move(b,23,24);assert(merge.ok);assert.equal(b.cells[24].tier,2);assert.equal(b.cells[23],null);
assert(M.move(b,24,31).ok);assert.equal(b.cells[31].tier,3);
// Merge opens only orthogonal crates, including at an edge; rows never wrap.
b.cells[8]={kind:'item',chain:'fab',tier:1};b.cells[9]={kind:'item',chain:'fab',tier:1};
merge=M.move(b,9,8);assert.deepEqual(merge.opened.sort((a,b)=>a-b),[1,7]);assert.equal(b.cells[1],null);
assert(!M.adjacent(6).includes(7));assert.deepEqual(M.adjacent(0),[1,7]);
// Generator refuses blocked spawns without spending resources.
const g=M.create(now);for(const i of M.adjacent(16))g.cells[i]={kind:'item',chain:'lea',tier:7};
assert.equal(M.generate(g,16,now).reason,'space');assert.equal(g.energy,100);assert.equal(g.cells[16].charges,12);
for(let i=0;i<12;i++){for(const index of M.adjacent(16))g.cells[index]=null;assert(M.generate(g,16,now).ok);}
assert.equal(g.energy,88);assert.equal(g.cells[16].charges,0);assert.equal(M.generate(g,16,now).reason,'cooldown');
M.tick(g,now+M.COOLDOWN_MS-1);assert.equal(g.cells[16].charges,0);M.tick(g,now+M.COOLDOWN_MS);assert.equal(g.cells[16].charges,12);
const energy=M.create(now);energy.energy=0;M.tick(energy,now+89999);assert.equal(energy.energy,0);M.tick(energy,now+90000);assert.equal(energy.energy,1);assert.equal(energy.energyAt,now+90000);
assert.equal(M.sanitize({...energy,energy:0,energyAt:now},now+M.REGEN_MS*150).energy,100);
energy.energy=100;M.tick(energy,now+M.REGEN_MS*500);M.generate(energy,16,now+M.REGEN_MS*500);M.tick(energy,now+M.REGEN_MS*500+1);assert.equal(energy.energy,99,'No banked regen at full energy');
energy.energy=0;assert.equal(M.generate(energy,16,now+M.REGEN_MS*500+2).reason,'energy');
const corrupt=M.sanitize({cells:Array(63).fill({kind:'item',chain:'fab',tier:7}),energy:NaN,energyAt:Infinity},now);
assert.equal(corrupt.cells.filter(c=>c?.kind==='generator').length,2);assert.equal(corrupt.energy,100);
const top=M.create(now);top.cells[23].tier=7;top.cells[24].tier=7;assert(!M.move(top,23,24).ok);
// Play a long deterministic sequence; every successful operation conserves board invariants.
const sim=M.create(now);for(let turn=0;turn<3000;turn++){
 const time=now+turn*10000;M.tick(sim,time);
 const pairs=[];for(let i=0;i<63;i++)for(let j=i+1;j<63;j++)if(M.canMerge(sim.cells[i],sim.cells[j]))pairs.push([i,j]);
 if(pairs.length)M.move(sim,...pairs[Math.floor(random()*pairs.length)]);
 else {const gens=sim.cells.map((c,i)=>c?.kind==='generator'?i:-1).filter(i=>i>=0);M.generate(sim,gens[turn%2],time);}
 assert(sim.energy>=0&&sim.energy<=100);assert.equal(sim.cells.length,63);assert.equal(sim.cells.filter(c=>c?.kind==='generator').length,2);
 assert(sim.cells.every(c=>!c||c.kind!=='item'||c.tier>=1&&c.tier<=7));
}
console.log('PASS: v3 migration/roundtrip/corrupt recovery, merge adjacency, max tiers, generator atomicity/cooldown, offline energy, 3000-turn board simulation.');

// Atelier orders consume exact items once, pay atomically, survive saves and stay craftable.
const O=require('./game.js').MergeOrders;
const deliveryState=freshSave(now), first=deliveryState.atelier.orders[0];
const payout=O.reward(first), originalCoins=deliveryState.coins;
assert(O.indices(deliveryState.atelier,first));
assert(O.deliver(deliveryState,first.id).ok);
assert.equal(deliveryState.coins,originalCoins+payout.coins);
assert.equal(deliveryState.stars,1);assert.equal(deliveryState.xp,payout.xp);
const paid=JSON.stringify(deliveryState);assert(!O.deliver(deliveryState,first.id).ok);assert.equal(JSON.stringify(deliveryState),paid);
assert.deepEqual(sanitizeSave(JSON.parse(paid),now),deliveryState);
const missing=freshSave(now);missing.atelier.cells=missing.atelier.cells.map(c=>c?.kind==='item'?null:c);
const noMaterials=JSON.stringify(missing);assert(!O.deliver(missing,missing.atelier.orders[0].id).ok);assert.equal(JSON.stringify(missing),noMaterials);
const recovered=sanitizeSave({...freshSave(now),atelier:{...M.create(now),orders:[null],orderSequence:-3}},now);
assert.equal(recovered.atelier.orders.length,2);assert.equal(recovered.atelier.orderSequence,0);
// Availability allocates individual pieces once, even with repeated requirements.
const partial=freshSave(now).atelier;
const repeated={needs:[{chain:'fab',tier:2,count:1},{chain:'fab',tier:2,count:1},{chain:'fab',tier:2,count:1}]};
assert.deepEqual(O.availability(partial,repeated).map(n=>n.ready),[true,true,false]);
assert.equal(O.indices(partial,repeated),null);
const partialState=freshSave(now);
partialState.atelier.orders[1]={id:1,person:1,needs:[{chain:'fab',tier:2,count:1},{chain:'lea',tier:5,count:1}]};
const partialBefore=JSON.stringify(partialState);assert(!O.deliver(partialState,1).ok);assert.equal(JSON.stringify(partialState),partialBefore,'Partially ready orders consume and pay nothing');
const economy=freshSave(now);let generatedWork=0,totalStars=0;const lengths=new Set();
for(let completed=0;completed<100;completed++){
 const slot=completed%2,order=economy.atelier.orders[slot];lengths.add(order.needs.length);
 assert(order.needs.length>=1&&order.needs.length<=3);
 assert(order.needs.every(n=>['fab','lea'].includes(n.chain)&&n.tier>=2&&n.tier<=5));
 assert.equal(economy.atelier.orders[0].needs.length,1,'Easy slot stays a single material');
 assert(economy.atelier.orders[0].needs[0].tier<=3,'Always retain an easy order');
 economy.atelier.cells=economy.atelier.cells.map(c=>c?.kind==='generator'?c:null);
 economy.atelier.energy=100;
 // Work downward so finished high-tier requests are never reused as crafting inputs.
 for(const need of [...order.needs].sort((a,b)=>b.tier-a.tier)){
  const mass=2**(need.tier-1);generatedWork+=mass;
  const gen=economy.atelier.cells.findIndex(c=>c?.kind==='generator'&&c.chain===need.chain);
  for(let unit=0;unit<mass;unit++){
   const generatorCell=economy.atelier.cells[gen];generatorCell.charges=M.CHARGES;generatorCell.readyAt=0;
   const result=M.generate(economy.atelier,gen,now);assert(result.ok,'Requested chain must be generated');
   let index=result.to;
   while(economy.atelier.cells[index].tier<need.tier){const match=economy.atelier.cells.findIndex((c,i)=>i!==index&&M.canMerge(economy.atelier.cells[index],c));if(match<0)break;assert(M.move(economy.atelier,index,match).ok);index=match;}
   if(M.adjacent(gen).includes(index)){const free=economy.atelier.cells.findIndex((c,i)=>!c&&!M.adjacent(gen).includes(i));assert(free>=0);assert(M.move(economy.atelier,index,free).ok);}
  }
 }
 assert(O.indices(economy.atelier,order));const expected=O.reward(order);totalStars+=expected.stars;
 assert(O.deliver(economy,order.id).ok);
 assert.equal(sanitizeSave(JSON.parse(JSON.stringify(economy)),now).atelier.orderSequence,completed+1);
 assert.notDeepEqual(economy.atelier.orders[0].needs,economy.atelier.orders[1].needs,'Keep the two requests distinct');
 assert.notEqual(economy.atelier.orders[0].person,economy.atelier.orders[1].person);
}
assert.equal(economy.stars,totalStars);assert(generatedWork>100);assert.deepEqual([...lengths].sort(),[1,2,3]);
// Board inventory influences deterministic weights; locked chains never appear.
const weighted=M.create(now);weighted.discovered.push('fab4','lea4');
assert.deepEqual(O.make(27,1,weighted),O.make(27,1,weighted));
const richFab={...weighted,cells:weighted.cells.map(c=>c?.kind==='item'?{kind:'item',chain:'fab',tier:3}:c)};
let normalFab=0,richFabCount=0;
for(let seq=1;seq<=400;seq++){
 normalFab+=O.make(seq,0,weighted).needs.filter(n=>n.chain==='fab').length;
 richFabCount+=O.make(seq,0,richFab).needs.filter(n=>n.chain==='fab').length;
 assert(O.make(seq,1,weighted).needs.every(n=>['fab','lea'].includes(n.chain)));
}
assert(richFabCount>normalFab,'Existing inventory should make matching requests more likely');
const oldSave=freshSave(now);oldSave.atelier.orders[1]={id:1,person:1,needs:[{chain:'lea',tier:5,count:1}]};
assert.deepEqual(sanitizeSave(oldSave,now).atelier.orders[1],oldSave.atelier.orders[1],'Existing single-item wishes survive migration');
// A player can explicitly trade a cooldown-blocked wish for available work.
// Rendering the offer and rejected/stale clicks never alter inventory or saves.
const reliefState=freshSave(now),reliefBoard=reliefState.atelier;
reliefBoard.cells=reliefBoard.cells.map(c=>c?.kind==='generator'?c:null);
const reliefFab=reliefBoard.cells.find(c=>c?.kind==='generator'&&c.chain==='fab');
reliefFab.charges=0;reliefFab.readyAt=now+M.COOLDOWN_MS;
reliefBoard.cells[23]={kind:'item',chain:'lea',tier:2};
reliefBoard.orders[1]={id:1,person:1,needs:[{chain:'fab',tier:5,count:1}]};
const beforeRelief=JSON.stringify(reliefState),reliefChoice=O.relief(reliefBoard,reliefBoard.orders[1],now);
assert.deepEqual(reliefChoice,{available:true,reason:'cooldown',next:{chain:'lea',tier:2,count:1}});
assert.equal(JSON.stringify(reliefState),beforeRelief,'Showing a replacement offer is pure');
const reliefOriginal=JSON.parse(beforeRelief),reliefOther=JSON.stringify(reliefBoard.orders[0]);
assert(O.replace(reliefState,1,now).ok);
assert.equal(reliefBoard.orders[1].id,1);assert.equal(reliefBoard.orders[1].person,1);
assert.equal(reliefBoard.orderSequence,reliefOriginal.atelier.orderSequence);
assert.deepEqual(reliefBoard.cells,reliefOriginal.atelier.cells);
for(const wallet of ['coins','stars','gems','xp'])assert.equal(reliefState[wallet],reliefOriginal[wallet]);
assert.equal(JSON.stringify(reliefBoard.orders[0]),reliefOther);
assert.deepEqual(sanitizeSave(JSON.parse(JSON.stringify(reliefState)),now).atelier.orders,reliefBoard.orders);
const afterRelief=JSON.stringify(reliefState);
assert(!O.replace(reliefState,1,now).ok);assert(!O.replace(reliefState,999,now).ok);
assert.equal(JSON.stringify(reliefState),afterRelief,'Repeat/stale replacement clicks do nothing');
const replacementPayout=O.reward(reliefBoard.orders[1],reliefState);
assert(O.deliver(reliefState,1,now).ok);
assert.equal(reliefState.coins,reliefOriginal.coins+replacementPayout.coins);
assert.equal(reliefBoard.orderSequence,reliefOriginal.atelier.orderSequence+1);
// Inventory is allocated across requirements: an existing high piece cannot be
// broken up or counted again for the lower piece in the same wish.
const reliefEdge=freshSave(now).atelier;
reliefEdge.cells=reliefEdge.cells.map(c=>c?.kind==='generator'?c:null);
for(const c of reliefEdge.cells)if(c?.kind==='generator'){c.charges=0;c.readyAt=now+10000;}
reliefEdge.cells[23]={kind:'item',chain:'fab',tier:3};
const edgeWish={id:4,person:0,needs:[{chain:'fab',tier:3,count:1},{chain:'fab',tier:2,count:1}]};
assert(O.relief(reliefEdge,edgeWish,now).available,'Reserve the finished high-tier requirement');
assert.equal(O.relief(reliefEdge,{id:4,person:0,needs:[{chain:'fab',tier:3,count:1}]},now).reason,'ready');
reliefEdge.cells[23]=null;
assert.equal(O.relief(reliefEdge,edgeWish,now).reason,'no-alternative');
const edgeLea=reliefEdge.cells.find(c=>c?.kind==='generator'&&c.chain==='lea');
edgeLea.charges=1;edgeLea.level=2;edgeLea.draws=3;
assert.deepEqual(O.relief(reliefEdge,edgeWish,now).next,{chain:'lea',tier:2,count:1},'Respect the next saved expert drop');
reliefEdge.energy=0;
assert.equal(O.relief(reliefEdge,edgeWish,now).reason,'no-alternative','A replacement cannot require unavailable energy');
reliefEdge.cells[23]={kind:'item',chain:'lea',tier:1};
reliefEdge.cells[24]={kind:'item',chain:'lea',tier:1};
assert.deepEqual(O.relief(reliefEdge,edgeWish,now).next,{chain:'lea',tier:2,count:1},'Inventory-backed relief remains available at zero energy');
reliefEdge.cells[23]=null;reliefEdge.cells[24]=null;
reliefEdge.energy=1;
assert(O.relief(reliefEdge,edgeWish,now).available,'One saved expert draw needs only one energy');
delete reliefEdge.energy;
assert(O.relief(reliefEdge,edgeWish,now).available,'Pure board fixtures without energy retain their supply semantics');
reliefEdge.energy=100;
edgeLea.draws=0;
assert.equal(O.relief(reliefEdge,edgeWish,now).reason,'no-alternative');
const edgeFab=reliefEdge.cells.find(c=>c?.kind==='generator'&&c.chain==='fab');
edgeFab.readyAt=now;
assert.equal(O.relief(reliefEdge,edgeWish,now).reason,'supplied','Expired cooldowns are usable without mutating the board');
// Charged baskets still require energy. An energy-blocked wish may be traded
// for a finished piece or an inventory-only merge without waiting for recharge.
const energyRelief=freshSave(now),energyBoard=energyRelief.atelier;
energyBoard.cells=energyBoard.cells.map(c=>c?.kind==='generator'?c:null);
energyBoard.energy=0;
energyBoard.cells[23]={kind:'item',chain:'lea',tier:2};
energyBoard.orders[1]={id:1,person:1,needs:[{chain:'fab',tier:3,count:1}]};
const energySnapshot=JSON.stringify(energyRelief);
assert.deepEqual(O.relief(energyBoard,energyBoard.orders[1],now).next,{chain:'lea',tier:2,count:1},'Charged baskets cannot hide energy-free relief');
assert.equal(JSON.stringify(energyRelief),energySnapshot,'Energy-aware preview stays read-only');
assert(O.replace(energyRelief,1,now).ok);
assert(O.indices(energyBoard,energyBoard.orders[1]),'Zero-energy replacement is immediately deliverable');
energyBoard.cells[23]=null;
energyBoard.energy=2;
const twoChainWish={id:4,person:0,needs:[{chain:'fab',tier:2,count:1},{chain:'lea',tier:2,count:1}]};
assert(O.relief(energyBoard,twoChainWish,now).available,'Two baskets cannot each spend the same two energy');
energyBoard.energy=4;
assert.equal(O.relief(energyBoard,twoChainWish,now).reason,'supplied','Exactly sufficient shared energy preserves the original wish');
const energyFab=energyBoard.cells.find(c=>c?.kind==='generator'&&c.chain==='fab');
energyFab.level=2;energyFab.draws=3;
energyBoard.energy=2;
assert(O.relief(energyBoard,twoChainWish,now).available,'Expert draws still share energy with the other chain');
energyBoard.energy=3;
assert.equal(O.relief(energyBoard,twoChainWish,now).reason,'supplied','Expert sequence spends only the one draw it needs');
energyBoard.energy=0;
energyBoard.cells[23]={kind:'item',chain:'fab',tier:1};energyBoard.cells[24]={kind:'item',chain:'fab',tier:1};
assert.equal(O.relief(energyBoard,{id:4,person:0,needs:[{chain:'fab',tier:2,count:1}]},now).reason,'supplied','Inventory-only crafting never requires energy');
console.log('PASS: atomic multi-item delivery, distinct per-piece availability, 100 crafted weighted orders, 1–3 requirements, proportional rewards, board-aware weights, legacy requests and persistent easy slot.');
console.log('PASS: explicit free relief, read-only previews, exact shared inventory/energy, expert-drop/expiry handling, save persistence, stale-click atomicity and unchanged delivery cadence.');

// Thank-you gifts persist, pay exactly once and never consume blocked rewards.
const R=require('./game.js').MergeRewards;
const gifts=freshSave(now).atelier;
gifts.orderSequence=5;
assert.equal(R.pending(gifts),1);
const chestClaim=R.claim(gifts);assert(chestClaim.ok);
assert.equal(R.pending(gifts),0);assert(!R.claim(gifts).ok);
const chestIndex=chestClaim.to, chestEnergy=gifts.energy;
const expected=[['fab',1],['fab',2],['lea',1],['lea',2]];
for(let i=0;i<4;i++){
 const drop=R.open(gifts,chestIndex);assert(drop.ok);
 assert.deepEqual([drop.item.chain,drop.item.tier],expected[i]);
 assert.equal(gifts.cells[chestIndex].kind,i===3?'item':'chest');
 assert.equal(gifts.energy,chestEnergy,'Gift opening never costs energy');
 const saved=sanitizeSave({...freshSave(now),atelier:gifts},now).atelier;
 assert.deepEqual(saved.cells,gifts.cells);assert.equal(saved.chestsClaimed,1);
}
assert(!R.open(gifts,chestIndex).ok,'Spent chest cannot pay twice');
const full=freshSave(now).atelier;full.orderSequence=10;
full.cells=full.cells.map(c=>c||{kind:'item',chain:'fab',tier:7});
const fullBefore=JSON.stringify(full);assert.equal(R.claim(full).reason,'chestSpace');assert.equal(JSON.stringify(full),fullBefore);
full.cells[10]={kind:'chest',seed:1,drops:2};
const blockedBefore=JSON.stringify(full);assert.equal(R.open(full,10).reason,'chestSpace');assert.equal(JSON.stringify(full),blockedBefore);
full.cells[10].drops=1;assert(R.open(full,10).ok,'Final drop uses the chest cell on a full board');
assert.equal(full.cells[10].kind,'item');
assert.equal(R.pending({...gifts,chestsClaimed:-50}),1);
assert.equal(R.pending({...gifts,chestsClaimed:500}),0);
const hintBoard=M.create(now);const pair=R.hint(hintBoard);assert.equal(pair.length,2);assert(M.canMerge(...pair.map(i=>hintBoard.cells[i])));
hintBoard.cells=hintBoard.cells.map(c=>c?.kind==='item'?{...c,tier:7}:c);assert.deepEqual(R.hint(hintBoard),[]);
assert.deepEqual(R.hint({...hintBoard,cells:Array(63).fill(null)}),[]);
console.log('PASS: milestone chest queue, atomic full-board refusal, deterministic four-drop contents, no energy cost, save/partial-chest recovery, final-slot replacement, valid idle hints.');

// Sustained play uses real energy, generator cooldowns and the original board without resets.
const sustained=freshSave(now);let simNow=now,taps=0,waitMs=0,openedGifts=0,sustainedStars=0;
function advance(ms){simNow+=ms;M.tick(sustained.atelier,simNow);}
for(let completed=0;completed<60;completed++){
 const board=sustained.atelier, order=board.orders[completed%2];
 let guard=0;
 while(!O.indices(board,order)){
  assert(++guard<1000,'Every order must eventually complete');
  const availability=O.availability(board,order),need=order.needs[availability.findIndex(n=>!n.ready)];
  const reserved=new Set(availability.filter(n=>n.ready).flatMap(n=>n.indices));
  const candidates=board.cells.map((c,i)=>!reserved.has(i)&&c?.kind==='item'&&c.chain===need.chain&&c.tier<need.tier?i:-1).filter(i=>i>=0);
  let merged=false;
  for(let a=0;a<candidates.length&&!merged;a++)for(let b=a+1;b<candidates.length;b++)if(M.canMerge(board.cells[candidates[a]],board.cells[candidates[b]])){
   assert(M.move(board,candidates[a],candidates[b]).ok);advance(2000);merged=true;break;
  }
  if(merged)continue;
  const gen=board.cells.findIndex(c=>c?.kind==='generator'&&c.chain===need.chain);
  if(!M.adjacent(gen).some(i=>board.cells[i]===null)){
   const occupied=M.adjacent(gen).find(i=>board.cells[i]?.kind==='item');
   const destination=board.cells.findIndex((c,i)=>c===null&&!M.adjacent(gen).includes(i));
   assert(occupied!==undefined&&destination>=0,'Board must retain room to gather');
   assert(M.move(board,occupied,destination).ok);advance(1000);
  }
  const drop=M.generate(board,gen,simNow);
  if(drop.ok){taps++;advance(1500);}
  else{
   assert(['energy','cooldown'].includes(drop.reason),drop.reason);
   const wake=drop.reason==='energy'?board.energyAt+M.REGEN_MS:board.cells[gen].readyAt;
   const wait=Math.max(1,wake-simNow);waitMs+=wait;advance(wait);
  }
 }
 sustainedStars+=O.reward(order).stars;assert(O.deliver(sustained,order.id).ok);advance(3000);
 if(R.pending(board)){
  const claimed=R.claim(board);assert(claimed.ok);
  for(let i=0;i<4;i++){assert(R.open(board,claimed.to).ok);advance(1000);}
  openedGifts++;
 }
 assert.equal(board.cells.filter(c=>c?.kind==='generator').length,2);
 assert(board.energy>=0&&board.energy<=100);
 assert.equal(sanitizeSave(JSON.parse(JSON.stringify(sustained)),simNow).atelier.orderSequence,completed+1);
}
assert.equal(openedGifts,12);assert.equal(sustained.stars,sustainedStars);assert(waitMs>0);
console.log(`PASS: 60 sustained orders, ${taps} actual energy taps, ${openedGifts} free chests; ${( (simNow-now)/60000).toFixed(1)} simulated minutes (${(waitMs/60000).toFixed(1)} waiting), no resource/board resets or paid boosts. The renovation-aware simulation is in qa/pacing-test.js.`);

// Bubbles never occupy a grid cell, charge on success only, and expire across reloads.
const B=require('./game.js').MergeBubbles,G=require('./game.js').MergeGuide;
const bubbles=freshSave(now);bubbles.mergeGuide=6;bubbles.gems=10;bubbles.atelier.merges=9;
const bubble=B.offer(bubbles.atelier,{ok:true,type:'merge',item:{chain:'fab',tier:3}},now);
assert(bubble);assert.equal(bubble.expiresAt,now+60000);assert.equal(B.offer(bubbles.atelier,{ok:true,type:'merge',item:{chain:'fab',tier:3}},now),null);
const bubbleReload=sanitizeSave(JSON.parse(JSON.stringify(bubbles)),now+20000);
assert.equal(bubbleReload.atelier.bubbles[0].expiresAt,now+60000);
const cellsBefore=bubbles.atelier.cells;bubbles.atelier.cells=Array(63).fill({kind:'item',chain:'fab',tier:7});
assert.equal(B.claim(bubbles,bubble.id,now+10).reason,'chestSpace');assert.equal(bubbles.gems,10);assert.equal(bubbles.atelier.bubbles.length,1);
bubbles.atelier.cells=cellsBefore;bubbles.gems=0;assert.equal(B.claim(bubbles,bubble.id,now+20).reason,'bubbleGems');assert.equal(bubbles.atelier.bubbles.length,1);
bubbles.gems=10;const claimedBubble=B.claim(bubbles,bubble.id,now+30);assert(claimedBubble.ok);assert.equal(bubbles.gems,6);assert.equal(bubbles.atelier.cells[claimedBubble.to].tier,3);assert(!B.claim(bubbles,bubble.id,now+40).ok);
assert.equal(sanitizeSave(bubbleReload,now+60000).atelier.bubbles.length,0);
const dismiss=freshSave(now);dismiss.atelier.merges=9;const extra=B.offer(dismiss.atelier,{ok:true,type:'merge',item:{chain:'lea',tier:2}},now);assert(B.dismiss(dismiss.atelier,extra.id));assert.equal(dismiss.gems,0);assert(!B.dismiss(dismiss.atelier,extra.id));
// Exact guided actions fit the real starter board and survive each reload.
let guide=freshSave(now);assert(G.advance(guide,M.generate(guide.atelier,16,now)));assert.equal(guide.mergeGuide,1);
for(const [from,to] of [[23,24],[30,15],[24,15]]){assert(G.advance(guide,M.move(guide.atelier,from,to)));guide=sanitizeSave(JSON.parse(JSON.stringify(guide)),now);}
assert.equal(guide.atelier.cells[14],null);assert.equal(guide.mergeGuide,4);assert(O.deliver(guide,0).ok);assert(G.advance(guide,{ok:true,type:'delivery'}));assert.equal(guide.gems,5);assert(!G.advance(guide,{ok:true,type:'delivery'}));assert.equal(guide.gems,5);
assert(require('./game.js').unlocked(guide,'decoration','big'),'Tier-3 discovery unlocks a design detail');assert(!require('./game.js').unlocked(guide,'heel','kitten'));guide.atelier.discovered.push('lea5');assert(require('./game.js').unlocked(guide,'heel','kitten'));assert(!generateOrder(guide,random).requirements.some(r=>r.key==='material'&&r.value==='glitter'));
assert.equal(sanitizeSave({version:3,visited:true,tutorial:true},now).mergeGuide,6,'Legacy players skip onboarding');
assert.equal(sanitizeSave({...freshSave(now),mergeGuide:3},now).mergeGuide,3);
for(const heel of ['flat','block','kitten','wedge'])for(const kind of ['leg','mask'])assert(require('node:fs').existsSync(`assets/legs/${kind}_${heel}.webp`));
console.log('PASS: bubble expiry/reload/full-board/insufficient-gems/atomic purchase/dismissal; real guided starter sequence and one-time reward; crafted detail unlocks, achievable commissions, legacy guide migration, four local worn masks.');

{
// Renovation is a persisted sequence: stale UI callbacks cannot buy the next task.
const B=require('./game.js').Boutique, O=require('./game.js').MergeOrders;
const shop=freshSave(now);shop.stars=1000;let spent=0;
assert.equal(B.renovate({...shop,stars:1},0).reason,'stars');
assert.equal(B.renovate(shop,1).reason,'stale');
for(let i=0;i<16;i++){
 const expected=B.task(shop);assert.equal(expected.id,i);const stars=shop.stars;
 const result=B.renovate(shop,i);assert(result.ok);spent+=expected.cost;
 assert.equal(shop.stars,stars-expected.cost);assert(!B.renovate(shop,i).ok);
 assert.equal(result.chapterComplete,[3,9,15].includes(i));
 const restored=sanitizeSave(JSON.parse(JSON.stringify(shop)),now);assert.equal(B.count(restored),i+1);
 assert.deepEqual(B.levels(restored),B.levels(shop));
 for(const chain of ['spk','rib'])assert.equal(restored.atelier.cells.filter(c=>c?.kind==='generator'&&c.chain===chain).length,(i>=(chain==='spk'?3:9))?1:0);
}
assert.equal(shop.stars,1000-spent);assert.equal(B.chapter(shop),3);assert(B.SLOTS.every(k=>B.levels(shop)[k]===2));assert.equal(B.task(shop),null);assert(!B.renovate(shop,16).ok);
assert.equal(B.count(sanitizeSave({boutique:{completed:Infinity}},now)),0);
const packed=freshSave(now);packed.boutique.completed=3;packed.stars=10;packed.atelier.cells=Array.from({length:63},()=>({kind:'item',chain:'fab',tier:1}));
const pending=B.renovate(packed,3);assert(pending.ok);assert.deepEqual(pending.pending,['spk']);assert.equal(packed.atelier.cells.filter(c=>c?.kind==='generator').length,0);
packed.atelier.cells[10]=null;B.sync(packed);B.sync(packed);assert.equal(packed.atelier.cells.filter(c=>c?.chain==='spk').length,1);
const chainSave=sanitizeSave(shop,now);let jewelOrders=0,ribbonOrders=0;
for(let i=1;i<=100;i++)for(let slot=0;slot<2;slot++){
 const request=O.make(i,slot,chainSave.atelier);assert(request.needs.length>=1&&request.needs.length<=3);
 for(const need of request.needs){assert(chainSave.atelier.cells.some(c=>c?.kind==='generator'&&c.chain===need.chain));if(need.chain==='spk')jewelOrders++;if(need.chain==='rib')ribbonOrders++;}
}
assert(jewelOrders>0&&ribbonOrders>0);
const bonusState=freshSave(now);bonusState.boutique.completed=16;const basePay=O.reward(bonusState.atelier.orders[0]);const paid=O.deliver(bonusState,0);assert.equal(paid.reward.coins,Math.round(basePay.coins*1.32));
assert.equal(O.reward(bonusState.atelier.orders[1],bonusState).coins,Math.round(O.reward(bonusState.atelier.orders[1]).coins*1.32));
console.log('PASS: all 16 renovation tasks / eight two-level slots, exact stars, stale-callback protection, chapter boundaries, full-board deferred generator, save recovery, reachable jewel/ribbon orders and charm payouts.');

}

{
const {Boutique:B,Merge:M,MergeOrders:O,commissionStars}=require('./game.js');
const start=Date.UTC(2026,9,22,12),day=86400000;
let expert=freshSave(start);expert.boutique.completed=4;B.sync(expert,start);
assert.deepEqual(B.customers(expert),[0,1,2,3,4,6,7,8]);
let generator=expert.atelier.cells.findIndex(c=>c?.kind==='generator'&&c.chain==='fab');
assert.equal(expert.atelier.cells[generator].level,2);
const tiers=[];
for(let i=0;i<8;i++){
 const r=M.generate(expert.atelier,generator,start);assert(r.ok);tiers.push(expert.atelier.cells[r.to].tier);expert.atelier.cells[r.to]=null;
 expert=sanitizeSave(JSON.parse(JSON.stringify(expert)),start);
}
assert.deepEqual(tiers,[1,1,1,2,1,1,1,2],'Reload never rerolls expert drops');
const before=JSON.stringify(expert.atelier);expert.atelier.energy=0;const draws=expert.atelier.cells[generator].draws;
assert.equal(M.generate(expert.atelier,generator,start).reason,'energy');assert.equal(expert.atelier.cells[generator].draws,draws);
assert(before.length>0);
expert.boutique.completed=14;B.sync(expert,start);assert(expert.atelier.cells.filter(c=>c?.kind==='generator').every(c=>c.level===2));
assert.deepEqual(B.customers(expert),[0,1,2,3,4,5,6,7,8]);
const newFaces=new Set(Array.from({length:100},(_,i)=>[O.make(i+1,0,expert.atelier).person,O.make(i+1,1,expert.atelier).person]).flat());assert(newFaces.has(3)&&newFaces.has(4)&&newFaces.has(5));
const story=freshSave(start);story.boutique.completed=16;story.atelier.energy=20;B.sync(story,start);
assert(!B.claimDaily(story,B.daily(story,start).key,start));
for(let i=0;i<5;i++)B.recordDelivery(story,start);
const key=B.daily(story,start).key,coins=story.coins,gems=story.gems;
assert(B.claimDaily(story,key,start));assert.equal(story.coins,coins+50);assert.equal(story.gems,gems+1);assert.equal(story.atelier.energy,40);
assert(!B.claimDaily(story,key,start));
const restored=sanitizeSave(JSON.parse(JSON.stringify(story)),start);assert(restored.boutique.daily.claimed);
assert(!B.claimDaily(restored,key,start-day),'Clock rollback cannot claim a second gift');
assert.equal(B.daily(restored,start+day).delivered,0);assert(!B.claimDaily(restored,key,start+day),'Stale claim across midnight fails');
restored.boutique.daily={key:'broken',delivered:100,claimed:false};assert.equal(B.daily(restored,start).delivered,0);
const wallet=freshSave(start);wallet.stars=100;wallet.atelier.energy=10;wallet.atelier.energyAt=start;
assert(B.renovate(wallet,0,start).ok);assert.equal(wallet.atelier.energy,26);assert(!B.renovate(wallet,0,start).ok);assert.equal(wallet.atelier.energy,26);
assert.deepEqual([1,2,3].map(stars=>commissionStars({stars})),[0,1,2]);
assert.equal(sanitizeSave({sound:false},start).music,false,'Legacy mute stays muted');
assert.equal(sanitizeSave({sound:false,music:true},start).music,true);
for(const lang of ['en','zh']){require('./game.js').lang=lang;assert.equal((B.storyMarkup(story).match(/<article>/g)||[]).length,16);assert(!B.markup(story).includes('undefined'));}
require('./game.js').lang='en';
console.log('PASS: expert generators deterministic across eight reloads, failed-tap atomicity, customer chapter gates, 16 bilingual story entries, daily claim/reload/midnight/clock rollback, renovation energy and commission stars, legacy audio mute.');
}

// The extended introduction follows real rewards and spending, across saved checkpoints.
const J=require('./game.js').Introduction;
let intro=freshSave(now);intro.introductionFlow=1;intro.mergeGuide=6;intro.stars=1;J.begin(intro);
assert.equal(intro.introduction,1);assert(!J.advance(intro,'finish'));
intro.stars=2;J.sync(intro);assert.equal(intro.introduction,2);
assert(require('./game.js').Boutique.renovate(intro,0,now).ok);J.sync(intro);
assert.equal(intro.introduction,3);assert.equal(intro.stars,0);
for(const event of ['studio','bow','commission','fitting','pose','finish']){
 assert(!J.advance(intro,'unexpected'));assert(J.advance(intro,event));
 intro=sanitizeSave(JSON.parse(JSON.stringify(intro)),now);
}
assert.equal(intro.introduction,9);assert(!J.active(intro));assert(!J.advance(intro,'finish'));
const oldIntro={...freshSave(now),mergeGuide:6};delete oldIntro.introduction;
assert.equal(sanitizeSave(oldIntro,now).introduction,9,'Existing players are not forced into the new lessons');
assert.equal(sanitizeSave({...oldIntro,mergeGuide:3},now).introduction,0);
for(let step=1;step<=8;step++)for(const lang of ['en','zh']){
 globalThis.SweetShoe.lang=lang;const s={...freshSave(now),mergeGuide:6,introduction:step};
 const lesson=J.lesson(s,{mode:'merge',modal:'',design:s.design,tab:'color'});
 assert(lesson.title&&lesson.body);assert(!JSON.stringify(lesson).includes('undefined'));
}
J.skip(intro);assert.equal(intro.introduction,9);
console.log('PASS: extended introduction, real renovation spending, saved checkpoints, wrong-event/idempotent guards, legacy opt-out and bilingual lessons.');

// Showcase migration, atomic earned-currency purchases, invalid selections and per-artwork scenes.
const Showcase=require('./game.js').Showcase,lookbook=freshSave(now);
assert.deepEqual(lookbook.showcase,{version:1,owned:['salon'],selected:'salon'});
assert.deepEqual(Showcase.sanitize({owned:['car','car','fake'],selected:'fake'}),{version:1,owned:['salon','car'],selected:'salon'});
const lookBefore=JSON.stringify(lookbook);assert.equal(Showcase.choose(lookbook,'car').reason,'coins');assert.equal(JSON.stringify(lookbook),lookBefore);
lookbook.coins=2000;lookbook.gallery=[{design:d,day:1,stars:3}];
for(const scene of Showcase.scenes){const old=lookbook.coins,result=Showcase.choose(lookbook,scene.id,lookbook.gallery[0]);assert(result.ok);assert.equal(lookbook.coins,old-scene.price);assert.equal(lookbook.gallery[0].scene,scene.id);const balance=lookbook.coins;assert(Showcase.choose(lookbook,scene.id).ok);assert.equal(lookbook.coins,balance);}
assert.equal(lookbook.coins,780);assert.deepEqual(sanitizeSave(JSON.parse(JSON.stringify(lookbook)),now).showcase,lookbook.showcase);
assert.equal(sanitizeSave({gallery:[{design:d,scene:'car'}]},now).gallery[0].scene,'salon');
assert.equal(Showcase.choose(lookbook,'invalid').reason,'scene');
console.log('PASS: showcase legacy migration, corrupt recovery, atomic coin purchases, no double-spending, gallery scenes and save roundtrip.');

const newJourney=freshSave(now);newJourney.mergeGuide=6;J.begin(newJourney);assert.equal(newJourney.introduction,3);for(const event of ['studio','bow','commission','fitting','pose'])assert(J.advance(newJourney,event));assert.equal(newJourney.introduction,2);newJourney.stars=3;assert(globalThis.SweetShoe.Boutique.renovate(newJourney,0).ok);J.sync(newJourney);assert.equal(newJourney.introduction,8);assert(J.advance(newJourney,'finish'));assert.equal(newJourney.introduction,9);console.log('PASS: new-player commission → fitting → first renovation route, using real earned stars.');
// Persisted locale aliases must preserve Chinese throughout reload and fitting.
{
 const A=require('./game.js');
 for(const locale of ['zh','zh-CN','zh_TW','ZH-hans']){
  const seed=A.freshSave();seed.lang=locale;seed.coins=123;seed.gallery=[{design:{...A.defaults},day:2,stars:3}];
  const loaded=A.sanitizeSave(seed);assert.equal(loaded.lang,'zh');assert.equal(loaded.coins,123);assert.equal(loaded.gallery.length,1);
  assert.equal(A.sanitizeSave(JSON.parse(JSON.stringify(loaded))).lang,'zh');
 }
 assert.equal(A.sanitizeSave({...A.freshSave(),lang:'en-US'}).lang,'en');
 assert.equal(A.sanitizeSave({...A.freshSave(),lang:'unknown'}).lang,null);
 assert.deepEqual(Object.keys(A.I18N.en).filter(key=>!A.I18N.zh[key]),[]);
 console.log('PASS: Chinese locale alias migration/reload, preserved wallet/gallery, complete bilingual dictionary.');
}

// Painted product views must keep one source design and avoid loading WebGL.
{
 const fs=require('node:fs'),path=require('node:path'),A=require('./game.js');
 const entry=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
 assert(/src="js\/shoe2d\.js(?:\?v=[a-z\d]+)?"/.test(entry));
 assert(!/src="[^"]*(?:shoe3d|fitting3d|vendor\/)/i.test(entry),'Archived 3D code loaded by browser entry');
 for(const heel of A.opts.heel){
  const design=A.cleanDesign({heel:heel[0]}),pair=A.productCanvas(design);
  assert(pair.includes('data-pair="true"'));
  assert(pair.includes('data-design="'+A.designKey(design)+'"'));
  for(const part of ['base','upper','shadow','highlight'])assert(fs.existsSync(path.join(__dirname,'assets/shoe2d',heel[0]+'_'+part+'.webp')));
 }
 console.log('PASS: all registered painted shoe kits, shared pair markup and browser entry without archived 3D.');
}

// A built-in instep band must stay one band through saves and customer briefs.
{
 const A=require('./game.js'),s=A.freshSave();
 assert.equal(A.cleanDesign({...A.defaults,heel:'maryjane',strap:'cross'}).strap,'none');
 assert(!A.unlocked(s,'heel','maryjane'));
 s.atelier.discovered.push('lea3');assert(A.unlocked(s,'heel','maryjane'));
 s.day=5;s.served=1;let seed=257,count=0;
 const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<2000;i++){
  const order=A.generateOrder(s,rng);
  if(order.requirements.some(r=>r.key==='heel'&&r.value==='maryjane')){
   count++;const strap=order.requirements.find(r=>r.key==='strap');assert(!strap||strap.value==='none');
   const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));
   assert(order.requirements.every(r=>A.matches(design,r)),'Mary Jane commission cannot be fulfilled');
  }
 }
 assert(count>0);s.design={...A.defaults,heel:'maryjane'};s.gallery=[{design:s.design,day:1,stars:3}];
 const loaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));assert.equal(loaded.design.heel,'maryjane');assert.equal(loaded.gallery[0].design.heel,'maryjane');
 console.log('PASS: Mary Jane discovery, compatible customer requests, one built-in strap and save/gallery migration.');
}

{
 const A=require('./game.js'),s=A.freshSave();assert(!A.unlocked(s,'heel','ballet'));s.atelier.discovered.push('rib3');assert(A.unlocked(s,'heel','ballet'));
 assert.equal(A.cleanDesign({...A.defaults,heel:'ballet',strap:'cross'}).strap,'none');assert(!A.matches({...A.defaults,heel:'ballet'},{key:'noBows',value:true}));
 s.day=6;s.served=1;let seed=817;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 let requested=0;
 for(let i=0;i<2500;i++){const order=A.generateOrder(s,rng);if(order.requirements.some(r=>r.key==='heel'&&r.value==='ballet')){requested++;assert(!order.requirements.some(r=>r.key==='noBows'));const strap=order.requirements.find(r=>r.key==='strap');assert(!strap||strap.value==='none');const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));assert(order.requirements.every(r=>A.matches(design,r)),'Ribbon ballet commission cannot be fulfilled');}}
 assert(requested>0,'Unlocked ribbon ballet must appear in customer requests');
 s.design={...A.defaults,heel:'ballet',strap:'ribbon'};s.gallery=[{design:s.design,day:1,stars:3}];
 const loaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));assert.equal(loaded.design.heel,'ballet');assert.equal(loaded.design.strap,'none');assert.equal(loaded.gallery[0].design.heel,'ballet');assert.equal(loaded.gallery[0].design.strap,'none');
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('builtInRibbons'),'builtInRibbons');}A.lang='en';
 console.log('PASS: ribbon ballet discovery, fulfillable requests, built-in ribbon/bow and save/gallery compatibility.');
}

// An open heel has a sewn slingback band, never a floating rear ornament.
{
 const A=require('./game.js'),s=A.freshSave();
 assert(!A.unlocked(s,'heel','slingback'));
 let seed=2305,requested=0;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 s.day=6;s.served=1;
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='slingback'));
 s.atelier.discovered.push('lea4');assert(A.unlocked(s,'heel','slingback'));
 for(let i=0;i<3000;i++){
  const order=A.generateOrder(s,rng);
  if(!order.requirements.some(r=>r.key==='heel'&&r.value==='slingback'))continue;
  requested++;
  const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));
  assert.equal(design.strap,'none');assert.equal(design.decoration,'none');
  assert(order.requirements.every(r=>A.matches(design,r)),'Slingback commission cannot be fulfilled');
 }
 assert(requested>0,'Discovered slingbacks must enter commission pool');
 s.design={...A.defaults,heel:'slingback',strap:'cross',decoration:'big',charm:'crystal'};
 s.gallery=[{design:s.design,day:3,stars:3}];
 s.order={person:0,requirements:[{key:'heel',value:'slingback'},{key:'charm',value:'crystal'}],duration:85,vip:false,adUsed:false};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 for(const d of [saved.design,saved.gallery[0].design]){assert.equal(d.heel,'slingback');assert.equal(d.strap,'none');assert.equal(d.decoration,'none');assert.equal(d.charm,'crystal');}
 assert.equal(saved.order.requirements[0].value,'slingback');
 assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['slingback','builtInSlingback','openHeelDecor'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned slingback, compatible open-heel commissions, source-safe ornaments and save/gallery recovery.');
}

// Penny loafers are earned leather craft, with an integral saddle and saved identity.
{
 const A=require('./game.js'),s=A.freshSave();s.day=5;s.served=1;
 let seed=1007;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 assert(!A.unlocked(s,'heel','loafer'));
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='loafer'));
 s.atelier.discovered.push('lea4');assert(A.unlocked(s,'heel','loafer'));
 let requests=0;
 for(let i=0;i<3000;i++){
  const order=A.generateOrder(s,rng);if(!order.requirements.some(r=>r.key==='heel'&&r.value==='loafer'))continue;
  requests++;const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));
  assert(order.requirements.every(r=>A.matches(design,r)),'Loafer commission is contradictory');
  assert.equal(design.strap,'none');
 }
 assert(requests>0);
 s.design={...A.defaults,heel:'loafer',strap:'cross',decoration:'drop',charm:'pearl'};s.gallery=[{design:s.design,day:5,stars:3}];
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 for(const d of [saved.design,saved.gallery[0].design]){assert.equal(d.heel,'loafer');assert.equal(d.strap,'none');assert.equal(d.charm,'pearl');assert.equal(d.decoration,'drop');}
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['loafer','builtInSaddle'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned penny loafer, sewn saddle, fulfillable orders and saved finish/Collection identity.');
}

// Platforms unlock late in the leather chain and retain optional ornaments.
{
 const A=require('./game.js'),s=A.freshSave();s.day=5;s.served=1;
 let seed=1241;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 assert(!A.unlocked(s,'heel','platform'));
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='platform'));
 s.atelier.discovered.push('lea6');assert(A.unlocked(s,'heel','platform'));
 let requests=0;
 for(let i=0;i<3000;i++){
  const order=A.generateOrder(s,rng);if(!order.requirements.some(r=>r.key==='heel'&&r.value==='platform'))continue;
  requests++;const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));
  assert(order.requirements.every(r=>A.matches(design,r)),'Platform commission is contradictory');
 }
 assert(requests>0);s.design={...A.defaults,heel:'platform',strap:'thin',decoration:'drop',charm:'crystal'};s.gallery=[{design:s.design,day:5,stars:3}];
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));assert.deepEqual(saved.design,s.design);assert.deepEqual(saved.gallery[0].design,s.design);
 assert.equal(A.shoeLayout(s.design).asset,'shoe_block_thin','platform fallback uses accepted block painting');
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('platform'),'platform');}A.lang='en';
 console.log('PASS: earned platform pump, fulfillable orders, optional finishes, local fallback and saved Collection.');
}

// Short boots earn their own identity and never request pump-only ankle/rear trims.
{
 const A=require('./game.js'),s=A.freshSave();s.day=6;s.served=1;
 let seed=1127;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 assert(!A.unlocked(s,'heel','bootie'));
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='bootie'));
 s.atelier.discovered.push('lea5');assert(A.unlocked(s,'heel','bootie'));
 let requested=0;
 for(let i=0;i<3000;i++){
  const order=A.generateOrder(s,rng);if(!order.requirements.some(r=>r.key==='heel'&&r.value==='bootie'))continue;
  requested++;
  const design=A.cleanDesign(Object.assign({},A.defaults,...order.requirements.filter(r=>r.key!=='noBows').map(r=>({[r.key]:r.value}))));
  assert.equal(design.strap,'none');assert.equal(design.decoration,'none');
  assert(order.requirements.every(r=>A.matches(design,r)),'Ankle bootie commission is contradictory');
 }
 assert(requested>0,'Earned ankle booties must enter the commission pool');
 s.design={...A.defaults,heel:'bootie',strap:'cross',decoration:'big',charm:'crystal'};
 s.gallery=[{design:s.design,day:6,stars:3}];
 s.order={person:0,requirements:[{key:'heel',value:'bootie'},{key:'charm',value:'crystal'}],duration:85,vip:false,adUsed:false};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 for(const design of [saved.design,saved.gallery[0].design]){assert.equal(design.heel,'bootie');assert.equal(design.strap,'none');assert.equal(design.decoration,'none');assert.equal(design.charm,'crystal');}
 assert.equal(saved.order.requirements[0].value,'bootie');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 assert.equal(A.shoeLayout(saved.design).asset,'shoe_block_none','bootie missing-art fallback stays local');
 const coinUnlocked=A.freshSave();coinUnlocked.unlocks.push('heel:bootie');assert(A.unlocked(coinUnlocked,'heel','bootie'));assert(A.sanitizeSave(coinUnlocked).unlocks.includes('heel:bootie'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['bootie','bootieShaft','bootieDecor'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned ankle bootie, compatible shaft/toe details, fulfillable requests, local fallback and saved Collection.');
}

// Height-free slim-pump wishes remain forgiving; explicit heights survive saves.
{
 const A=require('./game.js'),s=A.freshSave();
 for(const heel of Object.keys(A.THIN_HEELS))assert(!A.unlocked(s,'heel',heel));
 s.unlocks.push('heel:kitten');
 for(const [heel,cm] of Object.entries(A.THIN_HEELS)){
  assert(A.unlocked(s,'heel',heel));
  const d=A.cleanDesign({...A.defaults,heel});assert.equal(d.heel,heel);
  assert(A.matches(d,{key:'heel',value:'kitten'}));
  assert(A.matches(d,{key:'heelHeight',value:cm}));
  assert(!A.matches(d,{key:'heelHeight',value:cm===3?9:3}));
  s.design=d;s.gallery=[{design:d,day:1,stars:3}];
  s.order={person:1,duration:80,requirements:[{key:'heel',value:'kitten'},{key:'heelHeight',value:cm}]};
  const reloaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
  assert.equal(reloaded.design.heel,heel);assert.equal(reloaded.gallery[0].design.heel,heel);
  assert.equal(A.commissionDesign(reloaded.order).heel,heel);
  assert(reloaded.order.requirements.every(r=>A.matches(A.commissionDesign(reloaded.order),r)));
 }
 const crafted=A.freshSave();crafted.atelier.discovered.push('lea5');
 for(const heel of Object.keys(A.THIN_HEELS))assert(A.unlocked(crafted,'heel',heel));
 for(const requirements of [[{key:'heel',value:'block'},{key:'heelHeight',value:9}],[{key:'heel',value:'stiletto6'},{key:'heelHeight',value:9}],[{key:'heelHeight',value:3},{key:'heelHeight',value:9}]])assert.equal(A.sanitizeSave({...s,order:{person:1,duration:80,requirements}}).order,null,'Contradictory height wish survived save recovery');
 console.log('PASS: all thin heights share unlock/discovery; forgiving family wishes, explicit-height sample/match and save/gallery roundtrip.');
}


// Pearl couture is earned, source-painted and never asks for overlapping trims.
{
 const A=require('./game.js'),s=A.freshSave();s.day=6;s.served=1;
 assert(!A.unlocked(s,'heel','pearlpump'));
 let seed=621;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='pearlpump'));
 s.atelier.discovered.push('spk5');assert(A.unlocked(s,'heel','pearlpump'));
 let requested=0;
 for(let i=0;i<5000;i++){
  const order=A.generateOrder(s,rng);if(!order.requirements.some(r=>r.key==='heel'&&r.value==='pearlpump'))continue;
  requested++;
  const design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)),'Pearl couture commission is contradictory');
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none');
 }
 assert(requested>0);
 s.design={...A.defaults,heel:'pearlpump',color:'black',material:'velvet',strap:'cross',decoration:'big',charm:'crystal'};
 s.gallery=[{design:s.design,day:6,stars:3,fitting:{sock:'lace',color:'white'}}];
 s.order={person:0,requirements:[{key:'heel',value:'pearlpump'},{key:'color',value:'black'}],duration:85};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 for(const d of [saved.design,saved.gallery[0].design]){assert.equal(d.heel,'pearlpump');assert.equal(d.color,'black');assert.equal(d.material,'velvet');for(const key of ['strap','decoration','charm'])assert.equal(d[key],'none');}
 assert.equal(saved.gallery[0].fitting.sock,'lace');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 const coin=A.freshSave();coin.unlocks.push('heel:pearlpump');assert(A.unlocked(coin,'heel','pearlpump'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['pearlpump','builtInPearls'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned pearl satin pump, source-safe fixed pearls, compatible requests and saved artwork/socks.');
}

// Integral bow slingbacks stay compatible with wishes and saved styling.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert(!A.unlocked(s,'heel','bowsling'));assert.equal(A.option('heel','bowsling')[2],100);
 let seed=802;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='bowsling'));
 s.atelier.discovered.push('rib5');assert(A.unlocked(s,'heel','bowsling'));
 let requested=0,noBows=0;
 for(let i=0;i<7000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  const hasStyle=order.requirements.some(r=>r.key==='heel'&&r.value==='bowsling');
  if(order.requirements.some(r=>r.key==='noBows')){noBows++;assert(!hasStyle,'Integral bow requested alongside No bows');}
  assert(order.requirements.every(r=>A.matches(design,r)),'New-style commission cannot be fulfilled');
  if(!hasStyle)continue;requested++;
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none','Integral construction overlaps optional hardware');
 }
 assert(requested>0);assert(noBows>0);
 const bow=A.cleanDesign({...A.defaults,heel:'bowsling',color:'black',material:'velvet',pattern:'stars',strap:'cross',decoration:'big',charm:'crystal'});
 assert(!A.matches(bow,{key:'noBows',value:true}));
 s.design=bow;s.gallery=[{design:bow,stars:3,day:8,fitting:{sock:'frill',color:'pink'}}];
 s.order={person:0,requirements:[{key:'heel',value:'bowsling'},{key:'color',value:'black'}],duration:85};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,bow);assert.deepEqual(saved.gallery[0].design,bow);
 assert.equal(saved.gallery[0].fitting.sock,'frill');assert.equal(saved.gallery[0].fitting.color,'pink');
 assert.equal(saved.order.requirements[0].value,'bowsling');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 const paid=A.freshSave();paid.unlocks.push('heel:bowsling');assert(A.unlocked(paid,'heel','bowsling'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['bowsling','builtInSlingBow'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned bow slingback, no overlapping hardware or No-bows wishes, exact saved design/socks and bilingual copy.');
}

// Backless bow mules stay compatible with wishes and saved styling.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.CRAFT_UNLOCKS['heel:bowmule'],'rib6');assert(!A.unlocked(s,'heel','bowmule'));assert.equal(A.option('heel','bowmule')[2],110);
 let seed=802;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='bowmule'));
 s.atelier.discovered.push('rib6');assert(A.unlocked(s,'heel','bowmule'));
 let requested=0,noBows=0;
 for(let i=0;i<7000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  const hasStyle=order.requirements.some(r=>r.key==='heel'&&r.value==='bowmule');
  if(order.requirements.some(r=>r.key==='noBows')){noBows++;assert(!hasStyle,'Integral bow requested alongside No bows');}
  assert(order.requirements.every(r=>A.matches(design,r)),'New-style commission cannot be fulfilled');
  if(!hasStyle)continue;requested++;
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none','Integral construction overlaps optional hardware');
 }
 assert(requested>0);assert(noBows>0);
 const bow=A.cleanDesign({...A.defaults,heel:'bowmule',color:'black',material:'velvet',pattern:'stars',strap:'cross',decoration:'big',charm:'crystal'});
 assert(!A.matches(bow,{key:'noBows',value:true}));
 s.design=bow;s.gallery=[{design:bow,stars:3,day:8,fitting:{sock:'frill',color:'pink'}}];
 s.order={person:0,requirements:[{key:'heel',value:'bowmule'},{key:'color',value:'black'}],duration:85};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,bow);assert.deepEqual(saved.gallery[0].design,bow);
 assert.equal(saved.gallery[0].fitting.sock,'frill');assert.equal(saved.gallery[0].fitting.color,'pink');
 assert.equal(saved.order.requirements[0].value,'bowmule');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 const paid=A.freshSave();paid.unlocks.push('heel:bowmule');assert(A.unlocked(paid,'heel','bowmule'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['bowmule','builtInMuleBow'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned bow mule, no overlapping hardware or No-bows wishes, exact saved design/socks and bilingual copy.');
}

// Earned crystal couture keeps integral jewellery separate from optional trims.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.option('heel','crystalpump')[2],120);
 assert.equal(A.CRAFT_UNLOCKS['heel:crystalpump'],'spk6');
 assert(!A.unlocked(s,'heel','crystalpump'));
 let seed=316;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='crystalpump'),'Locked crystal couture requested');
 s.atelier.discovered.push('spk6');assert(A.unlocked(s,'heel','crystalpump'));
 let requested=0;
 for(let i=0;i<6000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)),'Crystal couture introduced a contradictory commission');
  if(!order.requirements.some(r=>r.key==='heel'&&r.value==='crystalpump'))continue;
  requested++;
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none','Integral crystal spray overlaps optional hardware');
 }
 assert(requested>0,'Earned crystal couture never appears in wishes');
 const couture=A.cleanDesign({...A.defaults,heel:'crystalpump',color:'black',material:'velvet',pattern:'stars',strap:'cross',decoration:'big',charm:'crystal'});
 assert(A.matches(couture,{key:'noBows',value:true}),'Crystal jewellery was treated as a bow');
 s.design=couture;s.gallery=[{design:couture,stars:3,day:8,fitting:{sock:'lace',color:'white'}}];
 s.order={person:0,requirements:[{key:'heel',value:'crystalpump'},{key:'color',value:'black'},{key:'noBows',value:true}],duration:85};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,couture);assert.deepEqual(saved.gallery[0].design,couture);
 assert.equal(saved.gallery[0].fitting.sock,'lace');assert.equal(saved.gallery[0].fitting.color,'white');
 assert.equal(saved.order.requirements[0].value,'crystalpump');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 const paid=A.freshSave();paid.unlocks.push('heel:crystalpump');assert(A.unlocked(paid,'heel','crystalpump'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['crystalpump','builtInCrystals'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned crystal spray pump, compatible fixed-trim/no-bow wishes and exact saved artwork/socks.');
}


// Studded couture uses its integral topline hardware in every saved design.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.option('heel','studpump')[2],120);
 assert.equal(A.CRAFT_UNLOCKS['heel:studpump'],'lea7');
 assert(!A.unlocked(s,'heel','studpump'));
 let seed=714;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='studpump'),'Locked studded pump requested');
 s.atelier.discovered.push('lea7');assert(A.unlocked(s,'heel','studpump'));
 let requested=0;
 for(let i=0;i<6000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)),'Studded pump introduced a contradictory commission');
  if(!order.requirements.some(r=>r.key==='heel'&&r.value==='studpump'))continue;
  requested++;
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none','Integral studs overlap optional hardware');
 }
 assert(requested>0,'Earned studded pump never appears in wishes');
 const couture=A.cleanDesign({...A.defaults,heel:'studpump',color:'black',material:'velvet',pattern:'stars',strap:'cross',decoration:'big',charm:'crystal'});
 assert(A.matches(couture,{key:'noBows',value:true}),'Metal studs were treated as a bow');
 s.design=couture;s.gallery=[{design:couture,stars:3,day:8,fitting:{sock:'lace',color:'white'}}];
 s.order={person:0,requirements:[{key:'heel',value:'studpump'},{key:'color',value:'black'},{key:'noBows',value:true}],duration:85};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,couture);assert.deepEqual(saved.gallery[0].design,couture);
 assert.equal(saved.gallery[0].fitting.sock,'lace');assert.equal(saved.gallery[0].fitting.color,'white');
 assert.equal(saved.order.requirements[0].value,'studpump');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
 const paid=A.freshSave();paid.unlocks.push('heel:studpump');assert(A.unlocked(paid,'heel','studpump'));
 for(const lang of ['en','zh']){A.lang=lang;for(const key of ['studpump','builtInStuds'])assert.notEqual(A.t(key),key);}A.lang='en';
 console.log('PASS: earned studded pump, integral-trim/no-bow commissions and exact saved artwork/socks.');
}


// Patent is a complete saved finish, earned without a missing texture download.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.option('material','patent')[2],55);
 assert.equal(A.CRAFT_UNLOCKS['material:patent'],'lea6');
 assert(!A.unlocked(s,'material','patent'));
 let seed=619;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<500;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='material'&&r.value==='patent'));
 s.atelier.discovered.push('lea6');assert(A.unlocked(s,'material','patent'));
 let requests=0;
 for(let i=0;i<3000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)));
  if(order.requirements.some(r=>r.key==='material'&&r.value==='patent'))requests++;
 }
 assert(requests>0);
 s.design=A.cleanDesign({...A.defaults,heel:'studpump',material:'patent'});
 s.gallery=[{design:s.design,stars:3,day:8}];
 s.order={person:0,requirements:[{key:'heel',value:'studpump'},{key:'material',value:'patent'}],duration:85};
 const loaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.equal(loaded.design.material,'patent');assert.equal(loaded.gallery[0].design.material,'patent');
 assert.equal(A.commissionDesign(loaded.order).material,'patent');assert.equal(A.scoreOrder(loaded.design,loaded.order,80).stars,3);
 const paid=A.freshSave();paid.unlocks.push('material:patent');assert(A.unlocked(paid,'material','patent'));
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('patent'),'patent');}A.lang='en';
 console.log('PASS: patent progression, compatible earned wishes, design/gallery persistence and bilingual copy.');
}

// The sculptural pearl heel remains a normal earned, saved shoe with all
// compatible decorations; no-bows requests must still exclude real silk bows.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.option('heel','pearlheel')[2],125);
 assert.equal(A.CRAFT_UNLOCKS['heel:pearlheel'],'spk6');
 assert(!A.unlocked(s,'heel','pearlheel'));
 let seed=625;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<500;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='pearlheel'));
 s.atelier.discovered.push('spk6');assert(A.unlocked(s,'heel','pearlheel'));
 let requested=0;
 for(let i=0;i<2500;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)));
  requested+=order.requirements.some(r=>r.key==='heel'&&r.value==='pearlheel');
 }
 assert(requested>0);
 const design=A.cleanDesign({...A.defaults,heel:'pearlheel',material:'velvet',color:'black',strap:'pearl',decoration:'heelcrystal',charm:'oval'});
 assert(A.matches(design,{key:'noBows',value:true}));
 assert(!A.matches({...design,decoration:'puffy'},{key:'noBows',value:true}));
 s.design=design;s.gallery=[{design,stars:3,day:8,fitting:{sock:'lace',color:'mint'}}];
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,design);assert.deepEqual(saved.gallery[0].design,design);
 assert.equal(saved.gallery[0].fitting.sock,'lace');assert.equal(saved.gallery[0].fitting.color,'mint');
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('pearlheel'),'pearlheel');}A.lang='en';
 console.log('PASS: earned pearl-orb heel, achievable commissions, compatible no-bows ornaments and saved fitted artwork.');
}

// The transparent lucite heel remains a normal earned, saved shoe with all
// compatible decorations; no-bows requests must still exclude real silk bows.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;
 assert.equal(A.option('heel','luciteheel')[2],125);
 assert.equal(A.CRAFT_UNLOCKS['heel:luciteheel'],'spk6');
 assert(!A.unlocked(s,'heel','luciteheel'));
 let seed=625;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<500;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='luciteheel'));
 s.atelier.discovered.push('spk6');assert(A.unlocked(s,'heel','luciteheel'));
 let requested=0;
 for(let i=0;i<2500;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)));
  requested+=order.requirements.some(r=>r.key==='heel'&&r.value==='luciteheel');
 }
 assert(requested>0);
 const design=A.cleanDesign({...A.defaults,heel:'luciteheel',material:'velvet',color:'black',strap:'pearl',decoration:'heelcrystal',charm:'oval'});
 assert(A.matches(design,{key:'noBows',value:true}));
 assert(!A.matches({...design,decoration:'puffy'},{key:'noBows',value:true}));
 s.design=design;s.gallery=[{design,stars:3,day:8,fitting:{sock:'lace',color:'mint'}}];
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.design,design);assert.deepEqual(saved.gallery[0].design,design);
 assert.equal(saved.gallery[0].fitting.sock,'lace');assert.equal(saved.gallery[0].fitting.color,'mint');
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('luciteheel'),'luciteheel');}A.lang='en';
 console.log('PASS: earned transparent lucite heel, achievable commissions, compatible no-bows ornaments and saved fitted artwork.');
}

{
 const A=require('./game.js'),s=A.freshSave();
 const long=['thigh','blacksheer','pantyhose','opaque','fishnet'];
 s.fitting={sock:'fishnet',color:'black'};
 s.gallery=long.map((sock,i)=>({design:{...A.defaults,material:i%2?'metallic':'pearlescent',pattern:i%2?'rosebuds':'diamonds'},day:1,stars:3,fitting:{sock,color:i%2?'black':'mint'}}));
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(saved.fitting,s.fitting);assert.deepEqual(saved.gallery.map(a=>a.fitting),s.gallery.map(a=>a.fitting));
 saved.gallery[0].fitting.color='pink';assert.equal(saved.gallery[1].fitting.color,'black');
 assert.deepEqual(A.sanitizeSave({version:3}).fitting,{sock:'none',color:'cream'});
 assert.deepEqual(A.cleanFittingOptions({sock:'unknown',color:'unknown'}),{sock:'none',color:'cream'});
 for(const material of ['metallic','pearlescent']){
  assert(!A.unlocked(s,'material',material));s.atelier.discovered.push(A.CRAFT_UNLOCKS['material:'+material]);assert(A.unlocked(s,'material',material));
 }
 assert.deepEqual(saved.gallery.map(a=>a.design),s.gallery.map(a=>A.cleanDesign(a.design)));
 console.log('PASS: long hosiery/midnight colour and couture finishes survive save migration/roundtrip with independent artwork styling and earned material gates.');
}

{
 const A=require('./game.js'),s=A.freshSave();
 assert.equal(A.CRAFT_UNLOCKS['pattern:gingham'],'fab3');
 assert.equal(A.option('pattern','gingham')[2],25);
 assert(!A.unlocked(s,'pattern','gingham'));s.day=6;s.served=2;
 let seed=503;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<400;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='pattern'&&r.value==='gingham'));
 s.atelier.discovered.push('fab3');assert(A.unlocked(s,'pattern','gingham'));s.day=6;s.served=2;
 let requested=0;
 for(let i=0;i<1800;i++){const order=A.generateOrder(s,rng),d=A.commissionDesign(order);assert(order.requirements.every(r=>A.matches(d,r)));requested+=order.requirements.some(r=>r.key==='pattern'&&r.value==='gingham');}
 assert(requested>0);
 const design=A.cleanDesign({...A.defaults,pattern:'gingham',color:'green'});
 s.design=design;s.gallery=[{design,day:3,stars:3,fitting:{sock:'knee',color:'white'}}];
 s.order={person:0,duration:85,requirements:[{key:'pattern',value:'gingham'},{key:'color',value:'green'}],vip:false};
 const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.equal(saved.design.pattern,'gingham');assert.equal(saved.gallery[0].design.pattern,'gingham');
 assert.equal(saved.gallery[0].fitting.sock,'knee');assert.equal(saved.order.requirements[0].value,'gingham');
 assert(A.matches(A.commissionDesign(saved.order),saved.order.requirements[0]));
 const bought=A.freshSave();bought.unlocks.push('pattern:gingham');assert(A.unlocked(bought,'pattern','gingham'));
 for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t('gingham'),'gingham');}A.lang='en';
 console.log('PASS: earned gingham checks, optional coin unlock, achievable requests and bilingual saved design/gallery/commission roundtrip.');
}

{
 const A=require('./game.js');
 for(const [material,item,price] of [['suede','lea3',30],['brocade','fab6',60],['pave','spk5',65]]){
  const s=A.freshSave();s.day=6;s.served=2;
  assert.equal(A.CRAFT_UNLOCKS['material:'+material],item);
  assert.equal(A.option('material',material)[2],price);
  assert(!A.unlocked(s,'material',material));
  let seed=732;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
  for(let i=0;i<400;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='material'&&r.value===material));
  s.atelier.discovered.push(item);assert(A.unlocked(s,'material',material));
  let requested=0;
  for(let i=0;i<1800;i++){
   const order=A.generateOrder(s,rng),d=A.commissionDesign(order);
   assert(order.requirements.every(r=>A.matches(d,r)));
   requested+=order.requirements.some(r=>r.key==='material'&&r.value===material);
  }
  assert(requested>0);
  s.design={...A.defaults,material,heel:'stiletto9',color:'black'};
  s.gallery=[{design:{...s.design},day:6,stars:3,fitting:{sock:'knee',color:'mint'}}];
  s.order={person:0,duration:85,requirements:[{key:'material',value:material},{key:'color',value:'pink'}],vip:false};
  const loaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
  assert.equal(loaded.design.material,material);assert.equal(loaded.gallery[0].design.material,material);
  assert.equal(loaded.order.requirements[0].value,material);assert.equal(loaded.gallery[0].fitting.sock,'knee');
  for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t(material),material);}A.lang='en';
 }
 console.log('PASS: suede/brocade/pavé craft gates, achievable earned requests and bilingual design/Collection/hosiery save roundtrip.');
}

{
 const A=require('./game.js');
 for(const [pattern,item] of [['scallops','rib3'],['pinstripes','fab3']]){
  const s=A.freshSave();s.day=6;s.served=2;
  assert.equal(A.CRAFT_UNLOCKS['pattern:'+pattern],item);
  assert(!A.unlocked(s,'pattern',pattern));
  let seed=867;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
  for(let i=0;i<300;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='pattern'&&r.value===pattern));
  s.atelier.discovered.push(item);assert(A.unlocked(s,'pattern',pattern));
  let requested=0;
  for(let i=0;i<1800;i++){
   const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
   assert(order.requirements.every(r=>A.matches(design,r)));
   requested+=order.requirements.some(r=>r.key==='pattern'&&r.value===pattern);
  }
  assert(requested>0);
  s.design={...A.defaults,pattern,color:'blue'};
  s.gallery=[{design:{...s.design},day:6,stars:3,fitting:{sock:'knee',color:'white'}}];
  s.order={person:0,duration:85,requirements:[{key:'pattern',value:pattern},{key:'color',value:'blue'}],vip:false};
  const loaded=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
  assert.equal(loaded.design.pattern,pattern);assert.equal(loaded.gallery[0].design.pattern,pattern);
  assert.equal(loaded.order.requirements[0].value,pattern);assert.equal(loaded.gallery[0].fitting.sock,'knee');
  assert(A.matches(A.commissionDesign(loaded.order),loaded.order.requirements[0]));
  const bought=A.freshSave();bought.unlocks.push('pattern:'+pattern);assert(A.unlocked(bought,'pattern',pattern));
  for(const lang of ['en','zh']){A.lang=lang;assert.notEqual(A.t(pattern),pattern);}A.lang='en';
 }
 console.log('PASS: scalloped embroidery/pinstripes stay earned, requestable and achievable, with bilingual saved designs and independent Collection hosiery.');
}

// Accepted open-toe crystal chains are earned once, keep integral jewellery,
// and preserve saved artwork and its independently chosen hosiery.
{
 const A=require('./game.js'),s=A.freshSave();s.day=8;s.served=1;s.coins=140;
 assert.equal(A.option('heel','crystalsandal')[2],140);
 assert.equal(A.CRAFT_UNLOCKS['heel:crystalsandal'],'spk6');
 assert(!A.unlocked(s,'heel','crystalsandal'));
 const wallet=s.coins,unlocks=[...s.unlocks];
 let seed=22625;const rng=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/4294967296);
 for(let i=0;i<1000;i++)assert(!A.generateOrder(s,rng).requirements.some(r=>r.key==='heel'&&r.value==='crystalsandal'),'Locked sandal requested');
 assert.equal(s.coins,wallet);assert.deepEqual(s.unlocks,unlocks);
 s.atelier.discovered.push('spk6');assert(A.unlocked(s,'heel','crystalsandal'));
 assert.equal(s.coins,wallet,'Craft discovery must not debit catalog coins');
 const style=A.SHOE_STYLES.crystalsandal;
 assert(style.openToe&&style.fixedTrims&&style.builtInStrap);assert(!style.builtInBow);
 let requested=0,noBows=0;
 for(let i=0;i<6000;i++){
  const order=A.generateOrder(s,rng),design=A.commissionDesign(order);
  assert(order.requirements.every(r=>A.matches(design,r)),'Sandal introduced an impossible commission');
  if(!order.requirements.some(r=>r.key==='heel'&&r.value==='crystalsandal'))continue;
  requested++;noBows+=order.requirements.some(r=>r.key==='noBows');
  for(const key of ['strap','decoration','charm'])assert.equal(design[key],'none','Sandal jewellery overlaps optional hardware');
 }
 assert(requested>0,'Earned crystal sandal never requested');assert(noBows>0,'Bow-free crystal sandal never requested alongside No bows');
 const design=A.cleanDesign({...A.defaults,heel:'crystalsandal',color:'black',material:'pave',pattern:'scallops',strap:'cross',decoration:'big',charm:'spray'});
 for(const key of ['strap','decoration','charm']){assert.equal(design[key],'none');assert(!A.supportsStyleOption('crystalsandal',key,key==='strap'?'pearl':key==='decoration'?'small':'crystal'));assert(A.supportsStyleOption('crystalsandal',key,'none'));}
 assert(A.matches(design,{key:'noBows',value:true}),'Integral crystal chain was treated as a bow');
 s.design=design;s.order={person:0,requirements:[{key:'heel',value:'crystalsandal'},{key:'color',value:'black'},{key:'noBows',value:true}],duration:85};
 for(const lang of ['en','zh']){
  A.lang=lang;assert.notEqual(A.t('crystalsandal'),'crystalsandal');assert.notEqual(A.t('builtInCrystalChain'),'builtInCrystalChain');
  s.lang=lang;s.fitting={sock:'knee',color:'white'};
  s.gallery=[{design,stars:3,day:8,fitting:{sock:'lace',color:'mint'}},{design:{...design,color:'pink'},stars:3,day:8,fitting:{sock:'none',color:'cream'}}];
  const saved=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
  assert.equal(saved.lang,lang);assert.deepEqual(saved.design,design);assert.deepEqual(saved.gallery[0].design,design);
  assert.deepEqual(saved.fitting,s.fitting);assert.deepEqual(saved.gallery.map(a=>a.fitting),s.gallery.map(a=>a.fitting));
  assert.equal(saved.order.requirements[0].value,'crystalsandal');assert.equal(A.scoreOrder(saved.design,saved.order,80).stars,3);
  assert.equal(saved.coins,wallet);saved.gallery[0].fitting.color='pink';assert.equal(saved.gallery[1].fitting.color,'cream');
 }
 A.lang='en';
 const legacy=A.freshSave();legacy.coins=7;legacy.unlocks.push('heel:crystalsandal');
 const restored=A.sanitizeSave(JSON.parse(JSON.stringify(legacy)));
 assert(A.unlocked(restored,'heel','crystalsandal'));assert.equal(restored.coins,7,'Restoring an owned sandal must not charge again');
 console.log('PASS: earned crystal chain sandal, wallet-safe unlocks, achievable fixed-trim/no-bow commissions and bilingual saved artwork/hosiery.');
}

require('./qa/merge-storage-test.js');

// Picker history is bounded, migration-safe and cannot affect ownership or designs.
{
 const A=require('./game.js'),s=A.freshSave();
 s.recentChoices={material:['lace','mesh','lace','velvet','satin'],heel:['crystalsandal'],pattern:['unknown',null,'flowers'],bad:['value']};
 const restored=A.sanitizeSave(JSON.parse(JSON.stringify(s)));
 assert.deepEqual(restored.recentChoices.material,['lace','mesh','velvet']);
 assert.deepEqual(restored.recentChoices.pattern,['flowers']);
 assert.deepEqual(restored.recentChoices.heel,['crystalsandal']);
 assert(!A.unlocked(restored,'heel','crystalsandal'),'History must never unlock a design');
 assert.deepEqual(restored.design,s.design);assert.equal(restored.coins,s.coins);
 assert.deepEqual(A.sanitizeSave({recentChoices:{material:'lace',color:[{},'blue']}}).recentChoices.color,['blue']);
 assert.deepEqual(A.sanitizeSave({}).recentChoices.material,[]);
 console.log('PASS: bounded picker history migrates corrupt/legacy saves without granting unlocks or changing resources.');
}

// Approved Mimi frames use the original 8fps clock and a calibrated static camera.
{
 require('./js/mentor-animation.js');
 const animation=globalThis.SweetShoe.MentorAnimation;
 assert.equal(animation.frameCount,40);assert.equal(animation.frameDuration,125);
 const fs=require('node:fs'),crypto=require('node:crypto');
 const paths=Array.from({length:40},(_,i)=>animation.framePath(i));
 assert.equal(new Set(paths).size,40);
 for(const path of paths)assert(fs.statSync(path).size>1000,'Missing approved Mimi frame '+path);
 const {scale,x,y}=animation.calibration;
 assert(Math.abs(28*scale+y-20)<1e-8);assert(Math.abs(1049*scale+y-980)<1e-8);
 assert(Math.abs(436*scale+x-419.5)<1e-8);
 console.log('PASS: forty approved Mimi frames, 8fps timing and static head/sole registration.');
}
