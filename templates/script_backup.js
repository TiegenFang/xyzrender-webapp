
  $('theme-btn').textContent=isDark?'☀️ 亮色':'🌙 暗色';
  localStorage.setItem('theme',html.dataset.theme);
}
$('fs-slider').addEventListener('input',function(){
  const v=this.value+'px';
  document.documentElement.style.setProperty('--fs',v);
  $('fs-val').textContent=v;
  localStorage.setItem('fs',v);
});
(()=>{
  const t=localStorage.getItem('theme');
  if(t){document.documentElement.dataset.theme=t;$('theme-btn').textContent=t==='light'?'🌙 暗色':'☀️ 亮色';}
  const f=localStorage.getItem('fs');
  if(f){document.documentElement.style.setProperty('--fs',f);$('fs-slider').value=parseInt(f);$('fs-val').textContent=f;}
})();

// ═══════════════════════════════════════════════
//  Arcball / Quaternion Math (identical to v4)
// ═══════════════════════════════════════════════
function v3norm(v){const d=Math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);return d<1e-12?[0,0,1]:[v[0]/d,v[1]/d,v[2]/d];}
function v3dot(a,b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
function v3cross(a,b){return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];}
function sphProj(px,py,cx,cy,r){const x=(px-cx)/r,y=-(py-cy)/r,d2=x*x+y*y;return d2<=1?[x,y,Math.sqrt(1-d2)]:(d=Math.sqrt(d2),[x/d,y/d,0]);}
function qident(){return[1,0,0,0];}
function qmul(a,b){return[a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]];}
function qnorm(q){const d=Math.sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);return[q[0]/d,q[1]/d,q[2]/d,q[3]/d];}
function axQ(axis,angle){const s=Math.sin(angle/2);return qnorm([Math.cos(angle/2),axis[0]*s,axis[1]*s,axis[2]*s]);}
function qMat(q){const[w,x,y,z]=q;return[[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],[2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],[2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]];}
function pcaQ(pts){
  const n=pts.length;
  const cx=pts.reduce((s,p)=>s+p[0],0)/n,cy=pts.reduce((s,p)=>s+p[1],0)/n,cz=pts.reduce((s,p)=>s+p[2],0)/n;
  let Cxx=0,Cyy=0,Czz=0,Cxy=0,Cxz=0,Cyz=0;
  for(const p of pts){const dx=p[0]-cx,dy=p[1]-cy,dz=p[2]-cz;Cxx+=dx*dx;Cyy+=dy*dy;Czz+=dz*dz;Cxy+=dx*dy;Cxz+=dx*dz;Cyz+=dy*dz;}
  let v=[1,0.1,0.05];
  for(let i=0;i<50;i++){const nx=Cxx*v[0]+Cxy*v[1]+Cxz*v[2],ny=Cxy*v[0]+Cyy*v[1]+Cyz*v[2],nz=Cxz*v[0]+Cyz*v[1]+Czz*v[2];v=v3norm([nx,ny,nz]);}
  const axis=v3cross(v,[1,0,0]),al=Math.sqrt(axis[0]*axis[0]+axis[1]*axis[1]+axis[2]*axis[2]);
  if(al<1e-9) return qident();
  return axQ(v3norm(axis),Math.acos(Math.max(-1,Math.min(1,v3dot(v,[1,0,0])))));
}

const CPK={H:'#EEEEEE',C:'#888888',N:'#3050F8',O:'#FF0D0D',F:'#90E050',P:'#FF8000',S:'#FFFF30',Cl:'#1FF01F',Br:'#A62929',I:'#940094',He:'#D9FFFF',Li:'#CC80FF',Na:'#AB5CF2',Mg:'#8AFF00',Al:'#BFA6A6',Si:'#F0C8A0',Ca:'#3DFF00',Fe:'#E06633',Co:'#F090A0',Ni:'#50D050',Cu:'#C88033',Zn:'#7D80B0',Au:'#FFD123',Pt:'#D0D0E0'};
const VDW_R={H:.31,C:.77,N:.75,O:.73,F:.72,P:1.06,S:1.02,Cl:.99,Br:1.14,I:1.33};
function cpk(sym){return CPK[sym]||'#FF69B4';}
function vr(sym){return(VDW_R[sym]||0.9)*0.38;}
function lerp(hex,white,t){const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);const w=white?255:0;return`rgb(${Math.round(r+(w-r)*t)},${Math.round(g+(w-g)*t)},${Math.round(b+(w-b)*t)})`;}

const V={q:qident(),zoom:1,atoms:null,dragging:false,lastSph:null,molName:''};
const mc=$('mol-canvas');const mctx=mc.getContext('2d');
const ac=$('axis-indicator');const actx=ac.getContext('2d');

function drawMol(){
  const W=mc.width,H=mc.height;
  mctx.clearRect(0,0,W,H);
  // canvas-bg from CSS var
  mctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--canvas-bg').trim()||'#050709';
  mctx.fillRect(0,0,W,H);
  if(!V.atoms||V.atoms.n===0){mctx.fillStyle='#3a4a70';mctx.font='12px DM Mono,monospace';mctx.textAlign='center';mctx.fillText('请先选择分子文件',W/2,H/2);return;}
  const{symbols,coords,n}=V.atoms;const M=qMat(V.q);
  const scale=Math.min(W,H)*0.4*V.zoom;const cx=W/2,cy=H/2;
  const proj=coords.map(p=>[M[0][0]*p[0]+M[0][1]*p[1]+M[0][2]*p[2],M[1][0]*p[0]+M[1][1]*p[1]+M[1][2]*p[2],M[2][0]*p[0]+M[2][1]*p[1]+M[2][2]*p[2]]);
  const order=[...Array(n).keys()].sort((a,b)=>proj[a][2]-proj[b][2]);
  // bonds
  mctx.lineWidth=1.2;
  for(let ii=0;ii<order.length;ii++){const i=order[ii];for(let jj=ii+1;jj<order.length;jj++){const j=order[jj];const dx=coords[i][0]-coords[j][0],dy=coords[i][1]-coords[j][1],dz=coords[i][2]-coords[j][2];const dist=Math.sqrt(dx*dx+dy*dy+dz*dz);if(dist<(vr(symbols[i])+vr(symbols[j]))/0.38*1.55){mctx.globalAlpha=0.5+0.35*((proj[i][2]+proj[j][2])/2+5)/10;mctx.strokeStyle='#5a6a90';mctx.beginPath();mctx.moveTo(cx+proj[i][0]*scale,cy-proj[i][1]*scale);mctx.lineTo(cx+proj[j][0]*scale,cy-proj[j][1]*scale);mctx.stroke();}}}
  mctx.globalAlpha=1;
  // atoms back-to-front
  for(const i of order){const x=cx+proj[i][0]*scale,y=cy-proj[i][1]*scale,r=vr(symbols[i])*scale*0.85;const fog=Math.max(0,Math.min(1,(proj[i][2]+5)/10));const col=cpk(symbols[i]);const g=mctx.createRadialGradient(x-r*.3,y-r*.35,r*.1,x,y,r);g.addColorStop(0,lerp(col,true,0.55));g.addColorStop(0.5,col);g.addColorStop(1,lerp(col,false,0.45*(1-fog*.4)));mctx.globalAlpha=0.6+0.4*fog;mctx.beginPath();mctx.arc(x,y,Math.max(2,r),0,Math.PI*2);mctx.fillStyle=g;mctx.fill();mctx.strokeStyle='rgba(0,0,0,.3)';mctx.lineWidth=0.6;mctx.stroke();}
  mctx.globalAlpha=1;
  mctx.fillStyle='#3a4a70';mctx.font='9px DM Mono,monospace';mctx.textAlign='left';mctx.fillText(n+' atoms',6,H-6);
  drawAxis();updateHUD();
}
function drawAxis(){
  const W=ac.width,H=ac.height;actx.clearRect(0,0,W,H);const M=qMat(V.q);const cx=W/2,cy=H/2,L=18;
  const axes=[{v:[1,0,0],c:'#ff5f6d',l:'X'},{v:[0,1,0],c:'#4aff8a',l:'Y'},{v:[0,0,1],c:'#4a9eff',l:'Z'}];
  axes.map(a=>({...a,px:M[0][0]*a.v[0]+M[0][1]*a.v[1]+M[0][2]*a.v[2],py:M[1][0]*a.v[0]+M[1][1]*a.v[1]+M[1][2]*a.v[2],rz:M[2][0]*a.v[0]+M[2][1]*a.v[1]+M[2][2]*a.v[2]})).sort((a,b)=>a.rz-b.rz).forEach(a=>{const ex=cx+a.px*L,ey=cy-a.py*L;actx.strokeStyle=a.c;actx.lineWidth=1.5;actx.beginPath();actx.moveTo(cx,cy);actx.lineTo(ex,ey);actx.stroke();actx.fillStyle=a.c;actx.font='8px Syne,sans-serif';actx.textAlign='center';actx.fillText(a.l,ex+(ex-cx)*.3,ey+(ey-cy)*.3+3);});
}
function updateHUD(){const M=qMat(V.q);$('hud-matrix').textContent=M.map(r=>r.map(v=>(v>=0?' ':'')+v.toFixed(3)).join(' ')).join('\n');}

mc.addEventListener('mousedown',e=>{V.dragging=true;const r=mc.getBoundingClientRect();V.lastSph=sphProj(e.clientX-r.left,e.clientY-r.top,mc.width/2,mc.height/2,Math.min(mc.width,mc.height)*.48);});
window.addEventListener('mousemove',e=>{if(!V.dragging||!V.lastSph)return;const r=mc.getBoundingClientRect();const cur=sphProj(e.clientX-r.left,e.clientY-r.top,mc.width/2,mc.height/2,Math.min(mc.width,mc.height)*.48);const axis=v3cross(V.lastSph,cur);const al=Math.sqrt(axis[0]*axis[0]+axis[1]*axis[1]+axis[2]*axis[2]);if(al>1e-9){const dot=Math.max(-1,Math.min(1,v3dot(V.lastSph,cur)));V.q=qnorm(qmul(axQ(v3norm(axis),Math.acos(dot)*2),V.q));}V.lastSph=cur;drawMol();});
window.addEventListener('mouseup',()=>{V.dragging=false;});
mc.addEventListener('wheel',e=>{e.preventDefault();V.zoom*=e.deltaY>0?.92:1.09;V.zoom=Math.max(.2,Math.min(8,V.zoom));drawMol();},{passive:false});

const modal=$('viewer-modal');
function viewerKey(e){
  if(!modal.classList.contains('open'))return;
  const deg=(parseFloat($('rot-speed').value)||8)*(e.shiftKey?.2:1)*Math.PI/180;
  let dq=null;
  if(e.key==='ArrowLeft') dq=axQ([0,1,0],deg);
  else if(e.key==='ArrowRight') dq=axQ([0,1,0],-deg);
  else if(e.key==='ArrowUp') dq=axQ([1,0,0],deg);
  else if(e.key==='ArrowDown') dq=axQ([1,0,0],-deg);
  else if(e.key==='PageUp') dq=axQ([0,0,1],deg);
  else if(e.key==='PageDown') dq=axQ([0,0,1],-deg);
  else if(e.key==='r'||e.key==='R'){V.q=qident();V.zoom=1;drawMol();}
  else if(e.key==='Escape'){closeViewer();}
  if(dq){V.q=qnorm(qmul(dq,V.q));drawMol();e.preventDefault();}
}
window.addEventListener('keydown',viewerKey);
function closeViewer(){modal.classList.remove('open');}
$('rot-speed').addEventListener('input',function(){$('spd-val').textContent=this.value+'°';});
$('v-reset').addEventListener('click',()=>{V.q=qident();V.zoom=1;drawMol();});
$('v-pca').addEventListener('click',()=>{if(V.atoms){V.q=pcaQ(V.atoms.coords);drawMol();toast('PCA 对齐完成');}});
$('v-close').addEventListener('click',closeViewer);
$('v-apply').addEventListener('click',applyViewerRotation);

async function openViewer(){
  if(!S.mol||S.smiMode){toast('请先选择分子文件','error');return;}
  modal.classList.add('open');
  $('hud-mol').textContent=S.mol;
  try{
    const res=await fetch('/api/get_xyz',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file:S.mol})});
    const d=await res.json();
    if(!res.ok||d.error){toast('加载坐标失败','error');return;}
    const n=d.n,coords=d.coords;
    const cx=coords.reduce((s,p)=>s+p[0],0)/n,cy=coords.reduce((s,p)=>s+p[1],0)/n,cz=coords.reduce((s,p)=>s+p[2],0)/n;
    const centred=coords.map(p=>[p[0]-cx,p[1]-cy,p[2]-cz]);
    V.atoms={symbols:d.symbols,coords:centred,n};V.molName=S.mol;
    V.q=pcaQ(centred);V.zoom=1;drawMol();
  }catch(ex){toast('加载失败：'+ex.message,'error');}
}

async function applyViewerRotation(){
  if(!V.atoms||!S.mol)return;
  setStatus('busy','应用旋转');
  try{
    const res=await fetch('/api/rotate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({file:S.mol,matrix:qMat(V.q)})});
    const d=await res.json();
    if(!res.ok||d.error){toast('旋转失败：'+(d.error||''),'error');setStatus('error','失败');return;}
    toast('旋转完成 → '+d.rotated_file);
    closeViewer();await loadMols();selMol(d.rotated_file);
    $('o-nori').checked=true;setStatus('ok','旋转完成');
    $('rb').click();
  }catch(ex){toast('错误：'+ex.message,'error');setStatus('error','错误');}
}

// ═══════════════════════════════════════════════
//  App State + Utilities
// ═══════════════════════════════════════════════
const S={mol:null,fmt:'svg',style:'default',hy:'auto',fog:'on',grad:'on',
         bbe:'auto',bgr:'auto',ghosts:'auto',axes:'auto',hedge:'on',
         smiMode:false,lastTemp:null,lastCmd:null};

function toast(msg,t='success'){const e=document.createElement('div');e.className=`toast ${t}`;e.innerHTML=`<div class="tdot"></div><span class="tmsg">${msg}</span><button class="tcl" onclick="this.parentElement.remove()">✕</button>`;$('tc').appendChild(e);setTimeout(()=>e.remove(),4000);}
function setStatus(s,l){$('dot').className=`sdot ${s}`;$('slbl').textContent=l;}
function setP(p){$('pb2').style.width=p+'%';if(p>=100)setTimeout(()=>setP(0),600);}
function fmtB(b){if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB';}

function switchTab(id){
  $a('.ctab').forEach(t=>t.classList.remove('active'));
  $a('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelector(`.ctab[onclick="switchTab('${id}')"]`).classList.add('active');
  $(`tab-${id}`).classList.add('active');
}
$a('.fmt-tab').forEach(t=>t.addEventListener('click',()=>{$a('.fmt-tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');S.fmt=t.dataset.fmt;}));
$a('.sb').forEach(b=>b.addEventListener('click',()=>{$a('.sb').forEach(x=>x.classList.remove('active'));b.classList.add('active');S.style=b.dataset.style;}));
$a('.ch').forEach(h=>{const bid=h.id.replace('ch-','cb-');const b=$(bid);if(b)h.addEventListener('click',()=>{h.classList.toggle('open');b.classList.toggle('closed');});});

function onVdwChange(){$('vdw-extra').style.display=$('o-vdw').checked?'':'none';}
function mkTri(id,key){$a(`#${id} .tbtn`).forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===S[key])b.classList.add(S[key]==='off'||S[key]==='none'?'aoff':'aon');});}
function setHy(v){S.hy=v;$a('#hy-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='none'?'aoff':'aon');});$('hy-idx-row').style.display=v==='all'?'':'none';}
function setFog(v){S.fog=v;$a('#fog-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setGrad(v){S.grad=v;$a('#grad-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setBBE(v){S.bbe=v;$a('#bbe-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setBGR(v){S.bgr=v;$a('#bgr-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setGhosts(v){S.ghosts=v;$a('#ghosts-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setAxes(v){S.axes=v;$a('#axes-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function setHEdge(v){S.hedge=v;$a('#hedge-tri .tbtn').forEach(b=>{b.classList.remove('aon','aoff');if(b.dataset.v===v)b.classList.add(v==='off'?'aoff':'aon');});}
function checkGifMx(){$('gif-mx').classList.toggle('show',$('o-gts').checked&&$('o-gtrj').checked);}
function checkSurfMx(){
  const mo=$('o-mo').checked,dens=$('o-dens').checked,esp=!!$('o-esp').value,nci=!!$('o-ncisurf').value;
  $('surf-mx').classList.toggle('show',[mo,dens,esp,nci].filter(Boolean).length>1);
  $('box-mo').classList.toggle('as',mo&&!dens&&!esp&&!nci);
  $('box-dens').classList.toggle('as',dens&&!mo&&!esp&&!nci);
  $('box-esp').classList.toggle('as',esp&&!mo&&!dens&&!nci);
  $('box-ncisurf').classList.toggle('as',nci&&!mo&&!dens&&!esp);
}
function useSMILES(){const v=$('smi-input').value.trim();if(!v){toast('请输入 SMILES','error');return;}S.mol='__smi__';S.smiMode=true;$('sn').textContent='SMILES: '+v;$('sn').className='';$('rb').disabled=false;$('open-viewer-btn').disabled=true;toast('已设置 SMILES 输入');}
function addHighlight(){const li=$('hl-list');const r=document.createElement('div');r.className='hl-item';r.innerHTML=`<input type="text" placeholder='原子范围 "1-5,8"'><input type="text" placeholder="颜色（可空）" style="width:80px;flex:none;"><button class="dx" onclick="this.parentElement.remove()">✕</button>`;li.appendChild(r);}
function getHighlights(){return $a('#hl-list .hl-item').map(r=>{const i=r.querySelectorAll('input');return{atoms:i[0].value.trim(),color:i[1].value.trim()};}).filter(h=>h.atoms);}
const PRESETS=['default','flat','paton','pmol','skeletal','bubble','tube','wire','graph'];
function addRegion(){const li=$('reg-list');const r=document.createElement('div');r.className='reg-item';const opts=PRESETS.map(p=>`<option value="${p}">${p}</option>`).join('');r.innerHTML=`<div style="display:flex;gap:3px;"><input type="text" placeholder='原子范围 "1-20"'><select style="width:80px;flex:none;appearance:none;background:var(--bg3);border:1px solid var(--bd);color:var(--tx);padding:2px 4px;font-size:10px;">${opts}</select></div><button class="dx" onclick="this.parentElement.remove()" style="padding:0 4px;">✕</button>`;li.appendChild(r);}
function getRegions(){return $a('#reg-list .reg-item').map(r=>{const i=r.querySelector('input'),s=r.querySelector('select');return{atoms:i?.value.trim(),preset:s?.value};}).filter(r=>r.atoms&&r.preset);}

// ═══════════════════════════════════════════════
//  File management
// ═══════════════════════════════════════════════
async function loadMols(){
  try{
    const files=await(await fetch('/api/molecules')).json();
    const list=$('mol-list');
    $('o-esp').innerHTML='<option value="">— 不使用 —</option>';
    $('o-ncisurf').innerHTML='<option value="">— 不使用 —</option>';
    $('o-ovl').innerHTML='<option value="">— 不使用 —</option>';
    if(!files.length){list.innerHTML='<div class="empty-state"><p>暂无文件</p></div>';return;}
    list.innerHTML='';
    files.forEach(f=>{
      const ext=f.suffix.replace('.','');
      const item=document.createElement('div');item.className='fi'+(S.mol===f.name?' active':'');item.dataset.name=f.name;
      item.innerHTML=`<span class="eb ${ext}">${ext}</span><span class="fn" title="${f.name}">${f.name}</span><span class="fz">${fmtB(f.size)}</span><button class="fdel">✕</button>`;
      item.addEventListener('click',e=>{if(!e.target.classList.contains('fdel'))selMol(f.name);});
      item.querySelector('.fdel').addEventListener('click',e=>{e.stopPropagation();delMol(f.name);});
      list.appendChild(item);
      if(ext==='cube'){const mk=(s,n)=>{const o=document.createElement('option');o.value=n;o.textContent=n;$(s).appendChild(o);};mk('o-esp',f.name);mk('o-ncisurf',f.name);}
      const oo=document.createElement('option');oo.value=f.name;oo.textContent=f.name;$('o-ovl').appendChild(oo);
    });
    checkSurfMx();
  }catch(e){console.error(e);}
}
function selMol(name){S.mol=name;S.smiMode=false;$('sn').textContent=name;$('sn').className='';$a('.fi').forEach(x=>x.classList.toggle('active',x.dataset.name===name));$('rb').disabled=false;$('open-viewer-btn').disabled=false;}
async function delMol(name){
  if(!confirm(`删除 ${name}？`))return;
  const r=await(await fetch('/api/delete_molecule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})})).json();
  if(r.ok){if(S.mol===name){S.mol=null;S.smiMode=false;$('sn').textContent='尚未选择';$('sn').className='none';$('rb').disabled=true;$('open-viewer-btn').disabled=true;}loadMols();toast(`已删除 ${name}`);}
}

// ═══════════════════════════════════════════════
//  TEMP gallery (previews)
// ═══════════════════════════════════════════════
async function loadTemp(){
  try{
    const figs=await(await fetch('/api/temp_figures')).json();
    const g=$('temp-gallery');
    if(!figs.length){g.innerHTML='<div class="empty-state" style="padding:3px 0;"><p>TEMP 为空</p></div>';return;}
    g.innerHTML='';
    figs.forEach(f=>{
      const ext=f.suffix.replace('.','');
      const item=document.createElement('div');item.className='gi'+(S.lastTemp===f.name?' active':'');item.dataset.name=f.name;
      item.innerHTML=`<span class="gb">${ext}</span><span class="gin" title="${f.name}">${f.name}</span><button class="gsv" title="保存到 FIGURE">⬆</button><button class="gid" title="删除">✕</button>`;
      item.addEventListener('click',e=>{if(!e.target.classList.contains('gsv')&&!e.target.classList.contains('gid'))prevTemp(f.name);});
      item.querySelector('.gsv').addEventListener('click',e=>{e.stopPropagation();saveToFigure(f.name);});
      item.querySelector('.gid').addEventListener('click',e=>{e.stopPropagation();delTemp(f.name);});
      g.appendChild(item);
    });
  }catch(e){console.error(e);}
}
async function delTemp(name){
  const r=await(await fetch('/api/delete_temp',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})})).json();
  if(r.ok){if(S.lastTemp===name){S.lastTemp=null;clearPrev();}loadTemp();}
}
async function clearTemp(){
  if(!confirm('清空所有 TEMP 预览文件？'))return;
  await fetch('/api/clear_temp',{method:'POST'});clearPrev();loadTemp();toast('TEMP 已清空');
}

// ═══════════════════════════════════════════════
//  FIGURE gallery (saved)
// ═══════════════════════════════════════════════
async function loadFigs(){
  try{
    const figs=await(await fetch('/api/figures')).json();const g=$('fig-gallery');
    if(!figs.length){g.innerHTML='<div class="empty-state" style="padding:3px 0;"><p>FIGURE 为空</p></div>';return;}
    g.innerHTML='';
    figs.forEach(f=>{
      const ext=f.suffix.replace('.','');const item=document.createElement('div');item.className='gi';item.dataset.name=f.name;
      item.innerHTML=`<span class="gb saved">${ext}</span><span class="gin" title="${f.name}">${f.name}</span><a href="/figures/${encodeURIComponent(f.name)}" download class="gsv" title="下载" style="text-decoration:none;">⬇</a><button class="gid" title="删除">✕</button>`;
      item.addEventListener('click',e=>{if(!e.target.classList.contains('gid')&&e.target.tagName!=='A')prevFig(f.name);});
      item.querySelector('.gid').addEventListener('click',e=>{e.stopPropagation();delFig(f.name);});
      g.appendChild(item);
    });
  }catch(e){console.error(e);}
}
async function delFig(name){
  const r=await(await fetch('/api/delete_figure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})})).json();
  if(r.ok){loadFigs();toast(`已从 FIGURE 删除 ${name}`);}
}

// ═══════════════════════════════════════════════
//  Save TEMP → FIGURE
// ═══════════════════════════════════════════════
async function saveToFigure(name){
  const r=await(await fetch('/api/save_figure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})})).json();
  if(r.ok){loadFigs();toast(`已保存 ${r.saved} 到 FIGURE`,'success');}
  else toast('保存失败：'+(r.error||''),'error');
}
async function saveCurrentToFigure(){
  if(!S.lastTemp){toast('请先在 TEMP 中选择一个预览文件','error');return;}
  await saveToFigure(S.lastTemp);
}
async function saveAllToFigure(){
  const figs=await(await fetch('/api/temp_figures')).json();
  if(!figs.length){toast('TEMP 为空','error');return;}
  let ok=0;
  for(const f of figs){const r=await(await fetch('/api/save_figure',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:f.name})})).json();if(r.ok)ok++;}
  loadFigs();toast(`已保存 ${ok} 个文件到 FIGURE`);
}

// ═══════════════════════════════════════════════
//  Preview
// ═══════════════════════════════════════════════
async function prevTemp(name){
  S.lastTemp=name;const url=`/temp/${encodeURIComponent(name)}`;const ext=name.split('.').pop().toLowerCase();
  $a('.gi').forEach(x=>x.classList.toggle('active',x.dataset.name===name));
  $('pfn').textContent=name;
  $('dl').href=url;$('dl').download=name;$('dl').style.display='';
  $('save-btn').style.display='';$('fsbtn').style.display='';
  $('pph').style.display='none';$('pimg').style.display='none';$('psvg').style.display='none';
  if(ext==='svg'){try{const txt=await(await fetch(url)).text();const c=$('psvg');c.innerHTML=txt;const s=c.querySelector('svg');if(s){s.style.maxWidth='100%';s.style.maxHeight='90%';}c.style.display='block';}catch{showImg(url);}}
  else if(['png','gif'].includes(ext)){showImg(url);}
  else{$('pph').innerHTML=`<p style="color:var(--tx);">${name}</p><p class="hint">PDF — 请下载</p>`;$('pph').style.display='';}
}
async function prevFig(name){
  const url=`/figures/${encodeURIComponent(name)}`;const ext=name.split('.').pop().toLowerCase();
  $('pfn').textContent=name+'  [已保存]';
  $('dl').href=url;$('dl').download=name;$('dl').style.display='';
  $('save-btn').style.display='none';$('fsbtn').style.display='';
  $('pph').style.display='none';$('pimg').style.display='none';$('psvg').style.display='none';
  if(ext==='svg'){try{const txt=await(await fetch(url)).text();const c=$('psvg');c.innerHTML=txt;const s=c.querySelector('svg');if(s){s.style.maxWidth='100%';s.style.maxHeight='90%';}c.style.display='block';}catch{showImg(url);}}
  else if(['png','gif'].includes(ext)){showImg(url);}
  else{$('pph').innerHTML=`<p>${name}</p>`;$('pph').style.display='';}
}
function showImg(url){const i=$('pimg');i.src=url+'?t='+Date.now();i.style.display='block';}
function clearPrev(){$('pimg').style.display='none';$('psvg').style.display='none';$('pph').innerHTML=`<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="display:block;margin:0 auto;opacity:.15"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg><p>选择文件 → 点击 ▶ 渲染预览</p><p class="hint">渲染结果保存到 TEMP/，点击 ⬆ 保存到 FIGURE/</p>`;$('pph').style.display='';$('pfn').textContent='尚无结果';$('dl').style.display='none';$('save-btn').style.display='none';$('fsbtn').style.display='none';$('cpcmd').style.display='none';}

// ═══════════════════════════════════════════════
//  Render
// ═══════════════════════════════════════════════
$('rb').addEventListener('click',async()=>{
  if(!S.mol&&!S.smiMode)return;
  const btn=$('rb'),log=$('log');
  const cj=$('o-json').value.trim();
  if(cj){try{JSON.parse(cj);}catch{toast('JSON 格式错误','error');return;}}
  if($('o-gts').checked&&$('o-gtrj').checked){toast('--gif-ts 与 --gif-trj 互斥','error');return;}
  const boChk=$('o-bo').checked;
  const p={
    file:S.smiMode?'':S.mol,format:S.fmt,style:S.style,
    smi:S.smiMode?$('smi-input').value.trim():'',
    mol_frame:$('o-molfr').value,rebuild:$('o-rebuild').checked,threshold:$('o-thresh').value,
    charge:$('o-chg').value,multiplicity:$('o-mult').value,
    canvas_size:$('o-cs').value,atom_scale:$('o-as').value,bond_width:$('o-bw').value,
    atom_stroke_width:$('o-asw').value,bond_color:$('o-bc').value,
    bg_color:$('o-bg').value,transparent:$('o-transp').checked,
    fog:S.fog==='on'?true:S.fog==='off'?false:null,fog_strength:$('o-fog-s').value,
    gradient:S.grad==='on'?true:S.grad==='off'?false:null,gradient_strength:$('o-grad-s').value,
    vdw_opacity:$('o-vdw-op').value,vdw_scale:$('o-vdw-sc').value,vdw_gradient:$('o-vdw-gr').value,
    dpi:$('o-dpi').value,
    bond_by_element:S.bbe==='on'?true:S.bbe==='off'?false:null,
    bond_gradient:S.bgr==='on'?true:S.bgr==='off'?false:null,
    bond_cutoff:$('o-bcut').value,no_bonds:$('o-nobonds').checked,
    ts_color:$('o-tscol').value,nci_color:$('o-ncicol').value,
    hydrogens:S.hy==='all',no_hy:S.hy==='none',hy_indices:S.hy==='all'?$('o-hy-idx').value:'',
    bond_orders:boChk?null:false,kekule:$('o-kek').checked,
    vdw:$('o-vdw').checked?($('o-vdw-r').value||''):null,
    dof:$('o-dof').checked,dof_strength:$('o-dof-s').value,
    mol_color:$('o-molcol').value,highlights:getHighlights(),
    idx:$('o-idx').value,stereo:$('o-stereo').checked,stereo_style:$('o-stereo-style').value,
    annotations:$('o-annot').value,label_size:$('o-lsize').value,
    cmap_data:$('o-cmap').value.trim(),cmap_range:$('o-cmrng').value,
    cmap_symm:$('o-cmsymm').checked,cmap_palette:$('o-cmpal').value,cbar:$('o-cbar').checked,
    no_orient:$('o-nori').checked,
    ts:$('o-ts').checked,ts_frame:$('o-tsf').value,ts_bond:$('o-tsb').value,
    nci:$('o-nci').checked,nci_bond:$('o-ncib').value,
    surface_style:$('o-surf-style').value,iso:$('o-iso').value,opacity:$('o-opac').value,
    mo:$('o-mo').checked,mo_pos_color:$('o-mop').value,mo_neg_color:$('o-mon').value,
    flat_mo:$('o-flatmo').checked,mo_blur:$('o-moblur').value,mo_upsample:$('o-moup').value,
    dens:$('o-dens').checked,dens_color:$('o-dcol').value,
    esp_file:$('o-esp').value,nci_surf_file:$('o-ncisurf').value,
    nci_mode:$('o-ncimode').value,nci_cutoff:$('o-ncicut').value,
    hull:$('o-hull').value,hull_color:$('o-hcol').value,hull_opacity:$('o-hop').value,
    hull_edge:S.hedge==='on'?null:false,hull_edge_ratio:$('o-heratio').value,
    overlay_file:$('o-ovl').value,overlay_color:$('o-ovlcol').value,
    ensemble:$('o-ens').checked,ensemble_color:$('o-enscol').value,
    align_atoms:$('o-align').value,conf_opacity:$('o-ensop').value,regions:getRegions(),
    gif_rot:$('o-grot').value,gif_ts:$('o-gts').checked,gif_trj:$('o-gtrj').checked,
    gif_diffuse:$('o-gdiff').checked,gif_fps:$('o-gfps').value,rot_frames:$('o-rfrm').value,
    crystal:$('o-cryst').value==='auto'?'crystal':$('o-cryst').value,
    cell:$('o-cell').checked,no_cell:$('o-nocell').checked,
    cell_color:$('o-cellcol').value,cell_width:$('o-cellw').value,
    ghosts:S.ghosts==='on'?true:S.ghosts==='off'?false:null,ghost_opacity:$('o-ghostop').value,
    axes:S.axes==='on'?true:S.axes==='off'?false:null,axis:$('o-axis').value,supercell:$('o-super').value,
    custom_json:cj,
  };
  btn.disabled=true;btn.classList.add('loading');btn.querySelector('.bt').textContent='渲染中…';
  setStatus('busy','渲染中');setP(20);log.className='log v';log.textContent='→ 调用 xyzrender…';
  try{
    const res=await fetch('/api/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});
    setP(70);const d=await res.json();
    if(!res.ok||d.error){
      log.textContent='✗ 错误:\n'+(d.error||'未知');log.className='log v err';
      setStatus('error','失败');toast('渲染失败：'+(d.error||'').split('\n')[0],'error');
    }else{
      S.lastCmd=d.cmd;S.lastTemp=d.output;
      log.textContent='✓ 成功！\n$ '+d.cmd;log.className='log v ok';
      setStatus('ok','完成');setP(100);
      toast(`预览已保存到 TEMP/${d.output}`);
      $('cpcmd').style.display='';
      await loadTemp();await prevTemp(d.output);
    }
  }catch(e){
    log.textContent='✗ 错误：'+e.message;log.className='log v err';
    setStatus('error','错误');setP(0);toast('请求失败','error');
  }finally{
    btn.disabled=false;btn.classList.remove('loading');btn.querySelector('.bt').textContent='▶ 渲染预览';
  }
});

// ── Toolbar ───────────────────────────────────────────────────────────────
$('cpcmd').addEventListener('click',()=>{if(S.lastCmd)navigator.clipboard.writeText(S.lastCmd).then(()=>toast('命令已复制'));});
$('fsbtn').addEventListener('click',()=>{const v=$('vp');if(v.requestFullscreen)v.requestFullscreen();});
$('rfg').addEventListener('click',loadFigs);

// ── Upload ────────────────────────────────────────────────────────────────
async function uploadFiles(files){let ok=0;for(const f of files){const fd=new FormData();fd.append('file',f);try{const r=await(await fetch('/api/upload',{method:'POST',body:fd})).json();if(r.ok){ok++;toast(`已上传 ${f.name}`);}else toast(`失败：${r.error}`,'error');}catch{toast(`错误：${f.name}`,'error');}}if(ok)await loadMols();}
$('fi').addEventListener('change',e=>uploadFiles([...e.target.files]));
const dz=$('dz');
dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('dragover');});
dz.addEventListener('dragleave',()=>dz.classList.remove('dragover'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('dragover');uploadFiles([...e.dataTransfer.files]);});

// ── Init ──────────────────────────────────────────────────────────────────
(async()=>{await loadMols();await loadTemp();await loadFigs();setStatus('ok','就绪');})();
