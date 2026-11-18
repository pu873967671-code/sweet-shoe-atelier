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
      {nav:'collection',box:[63,9,24,72],label:{en:'Collection',zh:'作品陈列柜'}},
      {nav:'free',box:[21,38,36,38],label:{en:'Free design',zh:'自由设计'}},
      {nav:'salon',door:'right',label:{en:'Boutique',zh:'精品店'}}],
    salon:[
      {nav:'studio',door:'left',label:{en:'Design corner',zh:'设计角'}},
      {nav:'shop',box:[46,40,24,32],label:{en:'Renovate',zh:'装修小店'}}]
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
    stage.innerHTML=`<div class="scene-strip">${ROOMS.map(r=>`<div class="scene-room" data-room="${r}"><div class="scene-spots">${spotMarkup(r)}</div></div>`).join('')}</div>`;
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
  A.Scenes={ROOMS,mount,go,relabel,room:()=>current};
})(globalThis.SweetShoe=globalThis.SweetShoe||{});
