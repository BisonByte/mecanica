// Manejo de datos y peticiones
let cargasPuntuales = [];
let cargasDistribuidas = [];
let beamChart, shearChart, momentChart;
let RA = 0, RB = 0, RC = 0;
let L = 0, torsor = 0, tipoC = 'Ninguno', c = 0;

const postData = async (url, data) => {
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(data)
  });
  if(!res.ok) throw new Error('Network');
  return res.json();
};

function agregarCarga(){
  const pos = parseFloat(document.getElementById('posCarga').value);
  const mag = parseFloat(document.getElementById('magCarga').value);
  if(isNaN(pos) || isNaN(mag)) return;
  cargasPuntuales.push({pos, mag});
}

function agregarDist(){
  const inicio = parseFloat(document.getElementById('inicioDist').value);
  const fin = parseFloat(document.getElementById('finDist').value);
  const mag = parseFloat(document.getElementById('magDist').value);
  if(isNaN(inicio)||isNaN(fin)||isNaN(mag)||fin<=inicio) return;
  cargasDistribuidas.push({inicio, fin, mag});
}

document.getElementById('addCarga').onclick = agregarCarga;
document.getElementById('addDist').onclick = agregarDist;

document.getElementById('limpiar').onclick = () => {
  cargasPuntuales = [];
  cargasDistribuidas = [];
  RA = RB = RC = 0;
  actualizarGraficos([], [], []);
  document.getElementById('resultado').textContent = '';
};

async function calcularReacciones(){
  L = parseFloat(document.getElementById('longitud').value);
  torsor = parseFloat(document.getElementById('torsor').value);
  tipoC = document.getElementById('apoyoC').value;
  c = parseFloat(document.getElementById('posC').value);
  const payload = {L, torsor, tipoC, c, cargasPuntuales, cargasDistribuidas};
  try{
    const res = await postData('/api/reacciones', payload);
    RA = res.RA; RB = res.RB; RC = res.RC;
    actualizarGraficos(res.x, res.V, res.M);
    document.getElementById('resultado').textContent = res.texto;
  }catch(e){
    calcularLocal();
  }
}

document.getElementById('calcular').onclick = calcularReacciones;

function calcularLocal(){
  let sumaF=0, sumaM=0;
  cargasPuntuales.forEach(cg=>{sumaF+=cg.mag; sumaM+=cg.mag*cg.pos;});
  cargasDistribuidas.forEach(cd=>{let F=cd.mag*(cd.fin-cd.inicio); let cent=cd.inicio+(cd.fin-cd.inicio)/2; sumaF+=F; sumaM+=F*cent;});
  RA = RB = RC = 0;
  if(tipoC==='Ninguno'){ RB = (sumaM + torsor)/L; RA = sumaF - RB; }
  else{ RB=((sumaM+torsor)-c*sumaF/2)/(L-c); RA=(sumaF-RB)/2; RC=RA; }
  const resultado = `RA = ${RA.toFixed(2)} N\nRB = ${RB.toFixed(2)} N${tipoC!=='Ninguno'?`\nRC = ${RC.toFixed(2)} N`:''}`;
  document.getElementById('resultado').textContent = resultado;
  const puntos=200,x=[],V=[],M=[];
  for(let i=0;i<=puntos;i++){
    const xi=L*i/puntos; let v=RA; let m=RA*xi+torsor;
    if(tipoC!=='Ninguno' && xi>=c){v+=RC; m+=RC*(xi-c);} if(xi>=L){v+=RB; m+=RB*(xi-L);}
    cargasPuntuales.forEach(cp=>{ if(xi>cp.pos){v-=cp.mag; m-=cp.mag*(xi-cp.pos);} });
    cargasDistribuidas.forEach(cd=>{if(xi>cd.inicio){ if(xi<=cd.fin){let l=xi-cd.inicio; v-=cd.mag*l; m-=cd.mag*l*l/2;} else {let lt=cd.fin-cd.inicio; v-=cd.mag*lt; m-=cd.mag*lt*(xi-(cd.inicio+lt/2));}}});
    x.push(xi); V.push(v); M.push(m);
  }
  actualizarGraficos(x,V,M);
}

function actualizarGraficos(x,V,M){
  if(beamChart){beamChart.destroy(); shearChart.destroy(); momentChart.destroy();}
  const beamCtx=document.getElementById('beamChart');
  const shearCtx=document.getElementById('shearChart');
  const momentCtx=document.getElementById('momentChart');
  beamChart=new Chart(beamCtx,{type:'line',data:{labels:x,datasets:[{label:'Viga',data:Array(x.length).fill(0),borderColor:'black',borderWidth:4,fill:false}]},options:{scales:{y:{beginAtZero:true}}}});
  shearChart=new Chart(shearCtx,{type:'line',data:{labels:x,datasets:[{label:'Cortante',data:V,borderColor:'blue',backgroundColor:'rgba(0,0,255,0.3)'}]},options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:false}}}});
  momentChart=new Chart(momentCtx,{type:'line',data:{labels:x,datasets:[{label:'Momento',data:M,borderColor:'red',backgroundColor:'rgba(255,0,0,0.3)'}]},options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:false}}}});
}

async function calcularParEnPunto(){
  const x=parseFloat(document.getElementById('puntoPar').value);
  if(isNaN(x)) return;
  try{
    const res=await postData('/api/torsion',{x, L, RA, RB, RC, torsor, tipoC, c, cargasPuntuales, cargasDistribuidas});
    const texto=document.getElementById('resultado').textContent+`\n${res.texto}`;
    document.getElementById('resultado').textContent=texto;
  }catch(e){
    let momento=torsor; if(x>=0) momento+=RA*x; if(tipoC!=='Ninguno'&&x>=c) momento+=RC*(x-c); if(x>=L) momento+=RB*(x-L);
    cargasPuntuales.forEach(cp=>{ if(x>cp.pos){ momento-=cp.mag*(x-cp.pos); } });
    cargasDistribuidas.forEach(cd=>{ if(x>cd.inicio){ if(x<=cd.fin){ let l=x-cd.inicio; momento-=cd.mag*l*l/2; } else { let lt=cd.fin-cd.inicio; momento-=cd.mag*lt*(x-(cd.inicio+lt/2)); } } });
    const texto=document.getElementById('resultado').textContent+`\nPar en x=${x.toFixed(2)} m: ${momento.toFixed(2)} N·m`;
    document.getElementById('resultado').textContent=texto;
  }
}

document.getElementById('calcPar').onclick = calcularParEnPunto;

// Geometría simple (ejemplo)
async function calcularGeometria(){
  const b=parseFloat(document.getElementById('base').value);
  const h=parseFloat(document.getElementById('altura').value);
  if(isNaN(b)||isNaN(h)) return;
  try{
    const res=await postData('/api/centroide',{b,h});
    document.getElementById('geoResultado').textContent=res.texto;
  }catch(e){
    const area=b*h; const cx=b/2; const cy=h/2; const Ix=b*h*h*h/12; const Iy=h*b*b*b/12;
    const texto=`Área=${area.toFixed(2)} m²\nCx=${cx.toFixed(2)} m, Cy=${cy.toFixed(2)} m\nIx=${Ix.toFixed(2)} m⁴, Iy=${Iy.toFixed(2)} m⁴`;
    document.getElementById('geoResultado').textContent=texto;
  }
}

document.getElementById('btnGeo').onclick = calcularGeometria;

// Footer year
document.getElementById('year').textContent = new Date().getFullYear();

window.addEventListener('load',()=>{
  const overlay=document.getElementById('welcomeOverlay');
  const startBtn=document.getElementById('startBtn');
  if(overlay&&startBtn){
    startBtn.addEventListener('click',()=>{
      overlay.classList.add('hide');
      setTimeout(()=>overlay.remove(),600);
    });
  }
});
