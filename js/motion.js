'use strict';
// The game's own motion setting. Effects play in full by default, whatever
// the system's "reduce motion" preference says (with Windows "Animation
// effects" off, browsers report reduced motion and every effect used to switch
// itself off). Players choose Gentle in the pause menu for a calm game.
// Loaded first: it answers matchMedia('(prefers-reduced-motion ...)') for the
// effects library, Mimi's animation and the game scripts, and switches the
// stylesheets' reduced-motion rules to match.
(function(root){
  const A=root.SweetShoe=root.SweetShoe||{};
  const KEY='sweet-shoe-effects',QUERY=/prefers-reduced-motion/;
  let gentle=false;try{gentle=localStorage.getItem(KEY)==='gentle';}catch{}
  const listeners=new Set(),native=root.matchMedia?.bind(root);
  // An answer that follows the setting, with the MediaQueryList shape callers use.
  function answer(query){
    const reduce=/:\s*reduce/.test(query),mql={media:query,get matches(){return reduce?gentle:!gentle;},onchange:null,
      addEventListener(type,fn){if(type==='change')listeners.add({mql,fn});},removeEventListener(type,fn){for(const l of listeners)if(l.fn===fn)listeners.delete(l);},
      addListener(fn){listeners.add({mql,fn});},removeListener(fn){for(const l of listeners)if(l.fn===fn)listeners.delete(l);},dispatchEvent(){return true;}};
    return mql;
  }
  if(native)root.matchMedia=query=>QUERY.test(String(query))?answer(String(query)):native(query);
  // Stylesheet rules written for reduced / no-preference motion follow the setting too.
  const touched=[];
  function rules(list,out=[]){for(const r of list||[]){if(r.media&&QUERY.test(r.media.mediaText))out.push(r);if(r.cssRules)rules(r.cssRules,out);}return out;}
  function applySheets(){
    for(const sheet of document.styleSheets){let list;try{list=sheet.cssRules;}catch{continue;}
      for(const r of rules(list)){if(!r.__motion){r.__motion=r.media.mediaText;touched.push(r);}}}
    for(const r of touched){const reduce=/:\s*reduce/.test(r.__motion),on=reduce?gentle:!gentle;r.media.mediaText=on?'all':'not all';}
  }
  function apply(){
    document.documentElement.dataset.effects=gentle?'gentle':'full';
    if(document.readyState!=='loading')applySheets();
    for(const l of listeners){try{l.fn.call(l.mql,{matches:l.mql.matches,media:l.mql.media});}catch{}}
  }
  document.documentElement.dataset.effects=gentle?'gentle':'full';
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applySheets,{once:true});else applySheets();
  root.addEventListener('load',applySheets,{once:true});
  A.Motion={gentle:()=>gentle,set(value){gentle=!!value;try{localStorage.setItem(KEY,gentle?'gentle':'full');}catch{}apply();},toggle(){this.set(!gentle);return gentle;}};
})(globalThis);
