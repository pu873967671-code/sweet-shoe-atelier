'use strict';
// The shop as places instead of tabs. Three painted rooms stand side by side
// (workroom -> design corner -> boutique salon); the camera glides between
// them. The workroom holds the crafting page; the design corner's glass
// cabinet opens the Collection and its sketchbook Free design; the salon's
// counter opens the boutique renovations. Doorways at the screen edges walk
// to the next room. app.js decides what opens once the camera arrives.
(function(A){
  const ROOMS=['workroom','studio','salon'];
  // Hotspots in percent of the room picture (x, y, w, h), placed on the art.
  const SPOTS={
    workroom:[{nav:'studio',door:'right',label:{en:'Design corner',zh:'设计角'}}],
    studio:[
      {nav:'workroom',door:'left',label:{en:'Workroom',zh:'工作间'}},
      {nav:'collection',box:[65,14,21,75],label:{en:'Collection',zh:'作品陈列柜'}},
      {nav:'free',box:[26,42,38,26],label:{en:'Free design',zh:'自由设计'}},
      {nav:'salon',door:'right',label:{en:'Boutique',zh:'精品店'}}],
    salon:[
      {nav:'studio',door:'left',label:{en:'Design corner',zh:'设计角'}},
      {nav:'shop',box:[40,44,29,30],label:{en:'Renovate',zh:'装修小店'}}]
  };
  let stage=null,current='workroom',moving=null;
  const lang=()=>A.lang==='zh'?'zh':'en';
  // Objects you can tap live in the painting and travel with it.
  function spotMarkup(room){
    return SPOTS[room].filter(s=>s.box).map(s=>`<button class="scene-spot" data-nav="${s.nav}" style="left:${s.box[0]}%;top:${s.box[1]}%;width:${s.box[2]}%;height:${s.box[3]}%" aria-label="${s.label[lang()]}"><span>${s.label[lang()]}</span></button>`).join('');
  }
  // Doorways sit at the screen edges, above the page, for the room you are in.
  function doorMarkup(room){
    return SPOTS[room].filter(s=>s.door).map(s=>`<button class="scene-door ${s.door}" data-nav="${s.nav}" aria-label="${s.label[lang()]}"><i aria-hidden="true">${s.door==='left'?'‹':'›'}</i><span>${s.label[lang()]}</span></button>`).join('');
  }
  let doors=null;
  function mount(){
    if(stage)return stage;
    stage=document.createElement('div');stage.id='sceneStage';stage.setAttribute('aria-hidden','false');
    // Each room holds a layer with the painting's own proportions, so spots,
    // shoes and furniture are placed in painting coordinates at any window size.
    stage.innerHTML=`<div class="scene-strip">${ROOMS.map(r=>`<div class="scene-room" data-room="${r}"><div class="scene-art"><div class="scene-decor"></div><div class="scene-spots">${spotMarkup(r)}</div><div class="scene-cabinet"></div></div></div>`).join('')}</div>`;
    doors=document.createElement('div');doors.id='sceneDoors';doors.setAttribute('role','navigation');doors.setAttribute('aria-label',lang()==='zh'?'小店里的房间':'Rooms of the shop');
    document.body.prepend(stage);document.body.append(doors);shownLang=lang();place(false);return stage;
  }
  let shownLang='';
  function relabel(){if(!stage||shownLang===lang())return;shownLang=lang();stage.querySelectorAll('.scene-room').forEach(el=>{el.querySelector('.scene-spots').innerHTML=spotMarkup(el.dataset.room);});doors.innerHTML=doorMarkup(current);}
  function place(animate){
    const i=ROOMS.indexOf(current),strip=stage.querySelector('.scene-strip');
    strip.style.transition=animate?'':'none';strip.style.transform=`translateX(${-i*100}vw)`;
    document.body.dataset.room=current;if(doors)doors.innerHTML=doorMarkup(current);
  }
  // Glide to a room, then run `arrive`. Moving to the room you are in arrives at once.
  function go(room,arrive){
    mount();if(!ROOMS.includes(room))return;
    if(room===current&&!moving){arrive?.();return;}
    clearTimeout(moving);current=room;document.body.classList.add('scene-moving');place(true);
    const calm=matchMedia('(prefers-reduced-motion: reduce)').matches;
    moving=setTimeout(()=>{moving=null;document.body.classList.remove('scene-moving');arrive?.();},calm?0:900);
  }
  // Finished shoes stand on the design corner's glass shelves (newest first,
  // two per shelf). Each opens the Collection at that pair.
  const SHELVES=[[68.2,27.6],[75.4,27.6],[68.2,37.4],[75.4,37.4],[68.2,46.9],[75.4,46.9],[68.2,55.6],[75.4,55.6]];
  let shelfKey='';
  function cabinet(gallery,shoe,hydrate){
    mount();const host=stage.querySelector('.scene-room[data-room=studio] .scene-cabinet');
    const list=(gallery||[]).slice(0,SHELVES.length),key=JSON.stringify(list.map(a=>a.design))+lang();if(key===shelfKey)return;shelfKey=key;
    host.innerHTML=list.map((a,i)=>`<button class="cabinet-shoe" data-cabinet="${i}" style="left:${SHELVES[i][0]}%;top:${SHELVES[i][1]}%" aria-label="${lang()==='zh'?'作品':'Pair'} ${i+1}">${shoe(a.design)}</button>`).join('');
    hydrate(host);
  }
  // Renovations appear in the salon painting itself.
  const DECOR={rug:[12,74,28],counter:[41,42,26],shelf:[1.5,47,13],sofa:[4,68,24],mirror:[36,49.6,8],flowers:[60.5,42,6],chandelier:[17,-1,11],window:[85.5,40,12]};
  let decorKey='';
  function decor(levels){
    mount();const key=JSON.stringify(levels);if(key===decorKey)return;decorKey=key;
    const host=stage.querySelector('.scene-room[data-room=salon] .scene-decor');
    host.innerHTML=Object.entries(DECOR).filter(([slot])=>levels?.[slot]>0).map(([slot,[x,y,w]])=>`<img class="salon-decor decor-${slot}" src="assets/decor/d_${slot}${Math.min(2,levels[slot])}.webp" alt="" style="left:${x}%;top:${y}%;width:${w}%">`).join('');
  }
  A.Scenes={ROOMS,mount,go,relabel,cabinet,decor,room:()=>current};
})(globalThis.SweetShoe=globalThis.SweetShoe||{});
