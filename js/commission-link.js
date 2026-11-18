'use strict';
// One customer, one journey. A Serve customer's shoe needs materials crafted
// in the Atelier: her wishes decide which chains (colour and fabric -> thread,
// heel and straps -> leather, jewels -> sparkle, bows -> ribbon). Her material
// order takes the first Atelier order slot, labelled for her shoes; the studio
// opens once it is delivered. nextStep() is the one line telling the player
// what to do now, wherever they are.
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
  // One material per distinct chain, at most two; big days ask a step higher.
  function materialsFor(s,order){
    const board=s.atelier,chains=[];
    for(const r of order.requirements||[]){const c=chainFor(r,board);if(!chains.includes(c))chains.push(c);if(chains.length>=2)break;}
    if(!chains.length)chains.push('fab');
    const higher=(order.beat&&order.beat.step>=1)||(s.day||1)>=3;
    return chains.map((chain,i)=>({chain,tier:higher&&i===0?3:2,count:1}));
  }
  const pending=s=>!!(s?.order&&Array.isArray(s.order.materials)&&s.order.materials.length&&!s.order.materialsReady);
  // Called whenever the studio shows a customer: give a new order its
  // materials and make sure her request is on the Atelier board.
  function attach(s){
    const o=s?.order;if(!o||!s.atelier||!A.MergeOrders)return;
    if(A.Introduction?.active?.(s)||!s.tutorial){if(!o.materials){o.materials=[];o.materialsReady=true;}return;}
    if(!Array.isArray(o.materials)){o.materials=materialsFor(s,o);o.materialsReady=false;}
    if(!pending(s))return;
    const orders=A.MergeOrders.ensure(s.atelier);
    if(orders.some(x=>x.commission))return;
    const slot=orders[0];
    orders[0]={id:slot.id,person:o.person,needs:o.materials.map(n=>({...n})),commission:true};
    if(orders[1].person===o.person&&!orders[1].commission){const pool=A.Boutique.customerPool(s.atelier),i=pool.indexOf(o.person);orders[1]={...orders[1],person:pool[(i+1)%pool.length]===o.person?pool[(i+2)%pool.length]:pool[(i+1)%pool.length]};}
  }
  // The Atelier delivered an order: if it was her materials, the studio opens.
  function delivered(s,order){
    if(!order?.commission||!s?.order)return false;
    s.order.materialsReady=true;return true;
  }
  const itemName=n=>(A.MergeNames?.[zh()?'zh':'en']?.[n.chain]?.[n.tier-1])||n.chain;
  const list=needs=>needs.map(itemName).join(zh()?'、':' + ');
  function card(s){
    const o=s.order,name=A.t('name'+o.person);
    return {title:zh()?`${name}的鞋需要材料`:`${name}'s shoes need materials`,
      body:zh()?`先在工坊合成：${list(o.materials)}。交付后就能开始做鞋，在那之前她会耐心等你。`:`Craft ${list(o.materials)} in the Atelier first. Deliver it and her shoes can be made; she'll wait patiently until then.`,
      button:zh()?'前往工坊 →':'Go to the Atelier →'};
  }
  // The one next thing to do. {text, nav} where nav is a tab to open (or null).
  function nextStep(s,mode){
    if(!s||A.Introduction?.active?.(s)||!s.tutorial)return null;
    const o=s.order,name=o?A.t('name'+o.person):'',z=zh(),day=A.customersForDay?A.customersForDay(s.day):5,t=A.Boutique.task(s);
    // Renovating first is free while she waits for materials (her patience is paused).
    if(t&&(s.stars||0)>=t.cost&&(!o||pending(s)))return {text:z?`星星够了：去精品店装修（${s.stars}/${t.cost}★）`:`You have the stars: renovate your boutique (${s.stars}/${t.cost}★)`,nav:'shop'};
    if(pending(s)){
      const ready=A.MergeOrders.ensure(s.atelier).find(x=>x.commission);const can=ready&&A.MergeOrders.indices(s.atelier,ready);
      if(mode!=='merge')return {text:z?`为${name}合成 ${list(o.materials)}`:`Craft ${list(o.materials)} for ${name}`,nav:'atelier'};
      return {text:can?(z?`把材料交给${name}！`:`Deliver the materials to ${name}!`):(z?`为${name}合成 ${list(o.materials)}：点工具篮，合并相同的材料`:`Craft ${list(o.materials)} for ${name}: tap a basket, merge matching pieces`),nav:null};
    }
    if(o&&(s.served||0)<day){
      if(mode!=='order')return {text:z?`材料齐了，去为${name}做鞋`:`Materials ready: make ${name}'s shoes`,nav:'serve'};
      return {text:z?`满足${name}的心愿，然后装进礼盒`:`Match ${name}'s wishes, then Pack it!`,nav:null};
    }
    if(t&&(s.stars||0)>=t.cost)return {text:z?`星星够了：去精品店装修（${s.stars}/${t.cost}★）`:`You have the stars: renovate your boutique (${s.stars}/${t.cost}★)`,nav:'shop'};
    if(o==null&&(s.served||0)>=day)return {text:z?'今天的客人都招待完了——开始新的一天':'All of today\'s customers are served: start a new day',nav:'serve'};
    if(t)return {text:z?`完成工坊订单赚星星：${s.stars||0}/${t.cost}★ 可装修下一处`:`Fill Atelier orders for stars: ${s.stars||0}/${t.cost}★ to the next renovation`,nav:mode==='merge'?null:'atelier'};
    return null;
  }
  A.Commission={materialsFor,attach,pending,delivered,card,nextStep,itemName};
})(globalThis.SweetShoe=globalThis.SweetShoe||{});
