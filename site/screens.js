/* ============================================================
   Shelby — the LCD, as a reusable module.
   Draws the firmware into a 160x128 canvas context. scene.js
   uses that canvas as a live texture on the 3D device; it also
   powers the flat 2D fallbacks.
   ============================================================ */

export const W = 160, H = 128;

export const C = {
  bg:"#0b100c", panel:"#10180f", ink:"#e7efdd", dim:"#6f8466", faint:"#46563f",
  gold:"#e3a92f", amber:"#f0c264", green:"#8fd14f", red:"#e3654a", line:"#22301f",
  gh:["#16241a","#244b2c","#3f8f44","#79d16a"], ghEmpty:"#182219",
};

function rng(seed){ let s=seed>>>0; return ()=>{ s=(s*1664525+1013904223)>>>0; return s/4294967296; }; }
function pad(n){ return n<10?"0"+n:""+n; }

function clear(g,col){ g.fillStyle=col||C.bg; g.fillRect(0,0,W,H); }
function rect(g,x,y,w,h,col){ g.fillStyle=col; g.fillRect(x|0,y|0,w|0,h|0); }
function text(g,str,x,y,col,size,align){
  g.fillStyle=col; g.font=(size||10)+'px "Space Mono", monospace';
  g.textBaseline="top"; g.textAlign=align||"left"; g.fillText(str,x,y);
}
function hintBar(g,label){
  rect(g,0,H-13,W,13,C.panel); rect(g,0,H-14,W,1,C.line);
  text(g,label,6,H-12,C.dim,9);
}

function drawClock(g){
  clear(g); rect(g,0,0,W,14,C.panel);
  text(g,"SHELBY",6,3,C.gold,9);
  const now=new Date();
  text(g,now.toLocaleDateString(undefined,{weekday:"short"}).toUpperCase(),W-6,3,C.dim,9,"right");
  const colon=now.getSeconds()%2===0?":":" ";
  text(g,pad(now.getHours())+colon+pad(now.getMinutes()),W/2,40,C.ink,40,"center");
  text(g,now.toLocaleDateString(undefined,{month:"long",day:"numeric"}),W/2,88,C.green,12,"center");
  hintBar(g,"L menu   github +3   2 tasks");
}
function drawGithub(g){
  clear(g); rect(g,0,0,W,14,C.panel);
  text(g,"github",6,3,C.gold,9); text(g,"@swamstick",W-6,3,C.dim,9,"right");
  const cols=18,rows=7,cell=6,gap=1,x0=9,y0=22,rand=rng(20260622); let total=0;
  for(let c=0;c<cols;c++){ const bias=c/cols;
    for(let r=0;r<rows;r++){ const v=rand(); let lvl;
      if(v<0.32-bias*0.18)lvl=-1; else if(v<0.6)lvl=0; else if(v<0.8)lvl=1; else if(v<0.93)lvl=2; else lvl=3;
      const col=lvl<0?C.ghEmpty:C.gh[lvl]; if(lvl>=0)total+=lvl+1;
      rect(g,x0+c*(cell+gap),y0+r*(cell+gap),cell,cell,col);
    }
  }
  text(g,total*6+" contributions",6,70,C.ink,10);
  text(g,"last 18 weeks",6,84,C.dim,9);
  text(g,"current streak  12d",6,98,C.green,10);
  hintBar(g,"J back");
}
function drawHackatime(g){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"hackatime",6,3,C.gold,9);
  text(g,"TODAY",6,20,C.dim,9); text(g,"3h 12m",W-6,18,C.ink,14,"right");
  text(g,"THIS WEEK",6,40,C.dim,9); text(g,"18h 40m",W-6,38,C.green,14,"right");
  rect(g,6,58,W-12,1,C.line);
  const projs=[["shelby",0.62],["website",0.24],["dotfiles",0.14]]; let y=66;
  for(const [name,frac] of projs){ text(g,name,6,y,C.ink,9);
    rect(g,64,y+1,W-76,6,C.line); rect(g,64,y+1,(W-76)*frac,6,C.gold); y+=16; }
  hintBar(g,"J back");
}
function drawTasks(g,state){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"tasks",6,3,C.gold,9);
  const sel=state?state.taskSel:0;
  const tasks=[["flash the firmware",true],["write the docs",false],["ship the website",false],["touch grass",false]];
  let y=22; tasks.forEach((t,i)=>{
    if(i===sel) rect(g,2,y-2,W-4,16,C.line);
    text(g,t[1]?"[x]":"[ ]",6,y,t[1]?C.green:C.dim,11);
    text(g,t[0],34,y,t[1]?C.dim:C.ink,11); y+=18;
  });
  hintBar(g,"W/S move   I tick   J back");
}
function drawSystem(g){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"system",6,3,C.gold,9);
  const used=0.41; text(g,"RAM",6,22,C.dim,9);
  rect(g,6,34,W-12,9,C.line); rect(g,6,34,(W-12)*used,9,C.green);
  text(g,Math.round(used*264)+"K / 264K",W-6,22,C.ink,9,"right");
  const rows=[["wifi","connected",C.green],["rssi","-58 dBm",C.ink],["clock","250 MHz",C.amber],["uptime","4h 09m",C.ink]];
  let y=54; rows.forEach(([k,v,col])=>{ text(g,k,6,y,C.dim,10); text(g,v,W-6,y,col,10,"right"); y+=15; });
  hintBar(g,"J back");
}
function drawMusic(g,state){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"music",6,3,C.gold,9);
  text(g,"now playing",6,22,C.dim,9); text(g,"buzzer sonata",6,36,C.ink,13);
  text(g,"ch.1 - square wave",6,54,C.dim,9);
  const t=state?state.t:0,bars=16,bw=7;
  for(let i=0;i<bars;i++){ const h=4+Math.abs(Math.sin(t*0.12+i*0.7))*30;
    rect(g,8+i*(bw+1),100-h,bw,h,i%2?C.gold:C.green); }
  text(g,"vol",6,104,C.dim,9); rect(g,30,106,80,5,C.line); rect(g,30,106,52,5,C.amber);
  hintBar(g,"J back");
}
export const MENU=[["GitHub","github"],["Hackatime","hackatime"],["Tasks","tasks"],["System","system"],["Music","music"],["Settings","settings"]];
function drawMenu(g,state){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"MENU",6,3,C.gold,9);
  text(g,pad(new Date().getHours())+":"+pad(new Date().getMinutes()),W-6,3,C.dim,9,"right");
  const sel=state?state.menuSel:0; let y=20;
  MENU.forEach((m,i)=>{ if(i===sel){ rect(g,2,y-2,W-4,16,C.line); text(g,">",6,y,C.green,11); }
    text(g,m[0],20,y,i===sel?C.ink:C.dim,11); y+=17; });
  hintBar(g,"W/S move   I open   J clock");
}
function drawSettings(g){
  clear(g); rect(g,0,0,W,14,C.panel); text(g,"settings",6,3,C.gold,9);
  const rows=[["clock","24-hour"],["volume","65%"],["overclock","250 MHz"],["wifi","home-net"]]; let y=24;
  rows.forEach(([k,v])=>{ text(g,k,6,y,C.ink,11); text(g,v,W-6,y,C.amber,11,"right"); y+=18; });
  hintBar(g,"J back");
}

// the boot / login splash the device plays before it reaches the clock
function drawBoot(g,state){
  clear(g);
  const f=state.t;
  text(g,"SHELBY",W/2,14,C.green,22,"center");
  text(g,"a desk companion",W/2,40,C.dim,9,"center");
  // label, finished value, in-progress word
  const steps=[
    ["cpu","250 MHz","testing"],
    ["display","ready","init"],
    ["wifi","connected","connecting"],
    ["time","synced","ntp sync"],
    ["apps","loaded","loading"],
  ];
  const startAt=8,per=8,settle=4; let y=56;
  for(let i=0;i<steps.length;i++){
    const a=startAt+i*per; if(f<a) break;
    const done=f>=a+settle;
    text(g,steps[i][0],10,y,C.dim,9);
    text(g,done?steps[i][1]:steps[i][2],W-10,y,done?C.green:C.amber,9,"right");
    y+=11;
  }
  const total=startAt+steps.length*per+10;
  text(g,f<total?"booting":"ready",W/2,H-26,C.dim,8,"center");
  rect(g,10,H-12,W-20,3,C.line);
  rect(g,10,H-12,(W-20)*Math.min(1,f/total),3,C.green);
  if(f>=total) state.view="clock";
}

export const RENDER={ boot:drawBoot, clock:drawClock, github:drawGithub, hackatime:drawHackatime,
  tasks:drawTasks, system:drawSystem, music:drawMusic, menu:drawMenu, settings:drawSettings };

// starts on the boot splash; the page resets state.t when the model appears
export function createState(){ return { view:"boot", menuSel:0, taskSel:0, t:0, manual:false }; }

export function drawScreen(g, state){
  const fn = RENDER[state.view] || drawClock;
  fn(g, state);
}

/* navigation — returns true if the press did something */
export function press(state, key){
  const k=key.toUpperCase(); state.manual=true;
  if(state.view==="boot"){ state.view="clock"; return true; }
  if(state.view==="clock"){ if(k==="L") state.view="menu"; }
  else if(state.view==="menu"){
    if(k==="W") state.menuSel=(state.menuSel+MENU.length-1)%MENU.length;
    else if(k==="S") state.menuSel=(state.menuSel+1)%MENU.length;
    else if(k==="I"||k==="K") state.view=MENU[state.menuSel][1];
    else if(k==="J") state.view="clock";
  } else {
    if(k==="J") state.view="menu";
    if(state.view==="tasks"){
      if(k==="W") state.taskSel=(state.taskSel+3)%4;
      else if(k==="S") state.taskSel=(state.taskSel+1)%4;
    }
  }
  return true;
}

/* jump straight to a screen (used by the "show on device" links) */
export function setView(state, name){ state.view=name; state.manual=true;
  const i=MENU.findIndex(m=>m[1]===name); if(i>=0) state.menuSel=i;
}
