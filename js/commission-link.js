'use strict';
// One page, one customer at a time. The current customer's shoe wishes
// (state.order.requirements) are fulfilled by crafting: each wish needs one
// material from the board (colour and fabric -> thread chain, heel and straps
// -> leather, jewels -> sparkle, bows -> ribbon). Adding it puts that detail
// on the shoe in Mimi's thought bubble; when every wish is in, the shoe is
// finished. nextStep() is the one line telling the player what to do now.
(function(A){
  const CHAIN_OF={color:'fab',material:'fab',pattern:'fab',heel:'lea',heelHeight:'lea',strap:'lea',decoration:'rib',noBows:'rib',charm:'spk'};
  const SPARKLY=/pearl|crystal|gem|stud|drop|butterfly|glitter|pave/;
  const has=(board,chain)=>!!board?.cells?.some(c=>c?.kind==='generator'&&c.chain===chain);
  const zh=()=>A.lang==='zh';

  function chainFor(r,board){
    let chain=CHAIN_OF[r.key]||'fab';
    if((r.key==='decoration'||r.key==='strap')&&SPARKLY.test(String(r.value)))chain='spk';
    if(!has(board,chain))chain=['fab','lea'].find(c=>has(board,c))||'fab';
    return chain;
  }
  // A piece is makeable now if one of that kind and size (or bigger) is on the
  // board, or the basket can still draw enough with the energy there is.
  function makeable(board,need,now){
    if(board.cells.some(c=>c?.kind==='item'&&c.chain===need.chain&&c.tier>=need.tier))return true;
    const energy=Number.isFinite(board.energy)?Math.max(0,Math.floor(board.energy)):Infinity;
    return !!A.MergeOrders.supplied?.(board,[need],now,energy);
  }
  // One material per wish. Prefer the wish's own kind; if its basket is
  // resting with nothing on the board, use a kind that can be made now, so a
  // cooldown never stalls her shoe. Big days ask a step higher for the first.
  function materialsFor(s,order,now=Date.now()){
    const board=s.atelier,higher=(order.beat&&order.beat.step>=1)||(s.day||1)>=3;
    return (order.requirements||[]).map((r,i)=>{
      const own=chainFor(r,board),tiers=higher&&i===0?[3,2]:[2];
      for(const tier of tiers){const need={chain:own,tier,count:1};if(makeable(board,need,now))return need;}
      for(const chain of ['fab','lea','spk','rib'].filter(c=>c!==own&&has(board,c))){const need={chain,tier:2,count:1};if(makeable(board,need,now))return need;}
      return {chain:own,tier:2,count:1};
    });
  }
  // The customer's wishes with their materials, created once per customer.
  function wishes(s){
    const o=s?.order;if(!o||!s.atelier)return [];
    if(!Array.isArray(o.wishes)||o.wishes.length!==o.requirements.length){
      const needs=materialsFor(s,o);
      // "None" and "no bows" wishes ask for nothing: they are simply kept.
      const plain=r=>r.value==='none'||r.key==='noBows';
      o.wishes=o.requirements.map((r,i)=>plain(r)?{need:null,done:true,plain:true}:{need:needs[i],done:false});
      if(o.wishes.every(w=>w.plain))o.wishes[0]={need:{chain:'fab',tier:2,count:1},done:false};
      // She is served on her own card; regular orders go to other neighbours.
      const pool=A.Boutique.customerPool(s.atelier).filter(p=>p!==o.person);
      const orders=A.MergeOrders.ensure(s.atelier);
      orders.forEach((x,k)=>{if(x.person!==o.person)return;const other=orders[1-k]?.person,pick=pool.find(p=>p!==other);if(pick!==undefined)x.person=pick;});
    }
    return o.wishes;
  }
  // The smallest piece on the board that fills this wish (exact or bigger).
  function source(board,need){
    let best=-1;
    board.cells.forEach((c,i)=>{if(c?.kind==='item'&&c.chain===need.chain&&c.tier>=need.tier&&(best<0||c.tier<board.cells[best].tier))best=i;});
    return best;
  }
  // A piece fits a wish if it is the same kind and at least that size.
  const fits=(cell,need)=>!!(cell&&need&&cell.kind==='item'&&cell.chain===need.chain&&cell.tier>=need.tier);
  // The open wish a given board piece can fill (the first, preferring an exact size).
  function wishFor(s,cellIndex,prefer){
    const cell=s.atelier.cells[cellIndex],w=wishes(s),open=w.map((x,i)=>({x,i})).filter(({x})=>!x.done&&fits(cell,x.need));
    if(prefer!=null&&open.some(o=>o.i===prefer))return prefer;
    return (open.find(({x})=>x.need.tier===cell.tier)||open[0])?.i??-1;
  }
  function addWish(s,i,cellIndex){
    const w=wishes(s)[i];if(!w||w.done||!w.need)return {ok:false};
    const at=cellIndex!=null?(fits(s.atelier.cells[cellIndex],w.need)?cellIndex:-1):source(s.atelier,w.need);if(at<0)return {ok:false,reason:'missing'};
    s.atelier.cells[at]=null;w.done=true;
    return {ok:true,cell:at,complete:complete(s)};
  }
  const complete=s=>{const w=wishes(s);return w.some(x=>!x.plain)&&w.every(x=>x.done);};
  // The shoe as made so far: her finished wishes on the house defaults.
  function design(s){
    const o=s.order;if(!o)return null;const w=wishes(s);
    return A.commissionDesign({requirements:o.requirements.filter((r,i)=>w[i]?.done)});
  }
  const wishDesign=s=>s.order?A.commissionDesign(s.order):null;
  function label(r){
    if(r.key==='noBows')return A.t('noBows');
    if(r.key==='heelHeight')return r.value+'cm';
    if(r.key==='heel'&&r.value==='kitten')return A.t('thinPump');
    return A.t(r.value);
  }
  const itemName=n=>(A.MergeNames?.[zh()?'zh':'en']?.[n.chain]?.[n.tier-1])||n.chain;
  // Kept for older call sites: nothing is ever gated now.
  const pending=()=>false;
  // The one next thing to do. {text, nav}: nav opens a screen (or null).
  function nextStep(s,mode){
    if(!s||A.Introduction?.active?.(s)||!s.tutorial)return null;
    const o=s.order,name=o?A.t('name'+o.person):'',z=zh(),day=A.customersForDay?A.customersForDay(s.day):5,t=A.Boutique.task(s);
    const home=mode==='merge'?null:'atelier';
    if(t&&(s.stars||0)>=t.cost)return {text:z?`星星够了：去精品店装修（${s.stars}/${t.cost}★）`:`You have the stars: renovate your boutique (${s.stars}/${t.cost}★)`,nav:'shop'};
    if(o&&(s.served||0)<day){
      const w=wishes(s),open=w.map((x,i)=>({x,i})).filter(({x})=>!x.done);
      const ready=open.find(({x})=>x.need&&source(s.atelier,x.need)>=0);
      if(ready)return {text:z?`把${itemName(ready.x.need)}加到${name}的鞋上（${label(o.requirements[ready.i])}）`:`Add the ${itemName(ready.x.need)} to ${name}'s shoe (${label(o.requirements[ready.i])})`,nav:home};
      const first=open[0];
      if(first)return {text:z?`为${name}的「${label(o.requirements[first.i])}」合成${itemName(first.x.need)}`:`Craft a ${itemName(first.x.need)} for ${name}'s ${label(o.requirements[first.i])}`,nav:home};
    }
    if(!o&&(s.served||0)>=day)return {text:z?'今天的客人都招待完了：开始新的一天':'All of today\'s customers are served: start a new day',nav:'day'};
    if(t)return {text:z?`完成订单赚星星：${s.stars||0}/${t.cost}★ 可装修下一处`:`Fill orders for stars: ${s.stars||0}/${t.cost}★ to the next renovation`,nav:home};
    return null;
  }
  A.Commission={materialsFor,wishes,source,fits,wishFor,addWish,complete,design,wishDesign,label,itemName,pending,nextStep};
})(globalThis.SweetShoe=globalThis.SweetShoe||{});
