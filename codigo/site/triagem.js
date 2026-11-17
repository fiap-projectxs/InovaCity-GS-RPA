/* Triagem no navegador: porta em JavaScript da logica do robo (validacao, classificacao,
   duplicidade, prioridade). O modelo (vocabulario, idf, coeficientes) e exportado do Python
   por build_site.py. Nada sai do computador de quem abre a pagina. */
(function(root){
const LIMIAR=0.45, RAIO=150, SIM=0.6;
const RISCO=["risco","acidente","queda","caiu","crianca","urgente","perigo","perigosa","medo","invade","cadeira","idosos","muleta"];
const BASE={buraco_via:2,iluminacao:2,alagamento_drenagem:3,lixo_entulho:1,calcada_acessibilidade:2};
function norm(t){return String(t).toLowerCase().normalize("NFKD").replace(/[^\x00-\x7f]/g,"").replace(/[^a-z0-9 ]+/g," ");}
function parseCSV(txt){
  txt=txt.replace(/^﻿/,""); const rows=[]; let r=[],c="",q=false;
  for(let i=0;i<txt.length;i++){const ch=txt[i];
    if(q){ if(ch==='"'){ if(txt[i+1]==='"'){c+='"';i++;} else q=false; } else c+=ch; }
    else if(ch==='"') q=true;
    else if(ch===","){r.push(c);c="";}
    else if(ch==="\n"||ch==="\r"){ if(ch==="\r"&&txt[i+1]==="\n")i++; r.push(c);c=""; if(r.length>1||r[0]!=="")rows.push(r); r=[]; }
    else c+=ch; }
  if(c!==""||r.length){r.push(c);rows.push(r);}
  if(!rows.length) return [];
  const h=rows[0].map(x=>x.trim().toLowerCase());
  return rows.slice(1).map(v=>{const o={};h.forEach((k,i)=>o[k]=v[i]);return o;});
}
function validar(l){
  const texto=(l.texto||"").trim();
  if(texto.length<3) throw new Error("texto vazio ou curto");
  const num=x=>{if(x==null||String(x).trim()==="")return NaN;return Number(x);};
  const lat=num(l.lat),lon=num(l.lon);
  if(isNaN(lat)||isNaN(lon)) throw new Error("coordenada nao numerica");
  if(!(lat>=-90&&lat<=90&&lon>=-180&&lon<=180)) throw new Error("coordenada fora do intervalo");
  const m=/^\s*(\d+)-(\d+)-(\d+)\s*$/.exec(l.data||""); let ok=false;
  if(m){const a=+m[1],mo=+m[2],d=+m[3],dt=new Date(Date.UTC(a,mo-1,d)); ok=a>=1&&dt.getUTCFullYear()===a&&dt.getUTCMonth()===mo-1&&dt.getUTCDate()===d;}
  if(!ok) throw new Error("data invalida (esperado AAAA-MM-DD)");
  return {id:String(l.id),texto,lat,lon,data:l.data.trim()};
}
function prever(M,texto){
  const tk=norm(texto).split(" ").filter(w=>w.length>=2), feats=[];
  for(let n=1;n<=2;n++) for(let i=0;i+n<=tk.length;i++) feats.push(tk.slice(i,i+n).join(" "));
  const tf={}; for(const f of feats) if(M.idx[f]!==undefined) tf[M.idx[f]]=(tf[M.idx[f]]||0)+1;
  const x=[]; let nn=0;
  for(const k in tf){const v=(1+Math.log(tf[k]))*M.idf[k]; x.push([+k,v]); nn+=v*v;}
  nn=Math.sqrt(nn)||1;
  const z=M.classes.map((_,c)=>{let s=M.b[c]; for(const [k,v] of x) s+=M.w[c][k]*v/nn; return s;});
  const mx=Math.max(...z), e=z.map(v=>Math.exp(v-mx)), S=e.reduce((a,b)=>a+b,0), p=e.map(v=>v/S);
  let bi=0; p.forEach((v,i)=>{if(v>p[bi])bi=i;});
  return [M.classes[bi],p[bi]];
}
function haversine(a,b,c,d){const R=6371000,r=Math.PI/180,s=Math.sin((c-a)*r/2)**2+Math.cos(a*r)*Math.cos(c*r)*Math.sin((d-b)*r/2)**2;return 2*R*Math.asin(Math.sqrt(s));}
function jaccard(a,b){const A=new Set(norm(a).split(/\s+/).filter(Boolean)),B=new Set(norm(b).split(/\s+/).filter(Boolean));
  if(!A.size&&!B.size)return 0; let i=0;for(const x of A)if(B.has(x))i++; return i/(A.size+B.size-i);}
function prioridade(cat,texto){const t=norm(texto);let pts=BASE[cat]||1;const hits=RISCO.filter(w=>t.includes(w));pts+=Math.min(2,hits.length);
  return [pts>=4?"alta":pts>=3?"media":"baixa",hits];}
function triar(M,linhas){
  const out=[],vistos=[];
  linhas.forEach((b,n)=>{
    const id=(b.id&&String(b.id).trim())||("linha "+(n+2)); b.id=id; const r={id,texto:b.texto||""};
    let v; try{v=validar(b);}catch(e){r.res="quarentena";r.motivo=e.message;out.push(r);return;}
    const [cat,conf]=prever(M,v.texto); Object.assign(r,{categoria:cat,confianca:conf});
    if(conf<LIMIAR){r.res="revisao";r.motivo="baixa confianca";out.push(r);return;}
    const d=vistos.find(o=>o.categoria===cat&&haversine(v.lat,v.lon,o.lat,o.lon)<=RAIO&&jaccard(v.texto,o.texto)>=SIM);
    if(d){r.res="duplicada";r.duplicada_de=d.id;out.push(r);return;}
    const [pr,hits]=prioridade(cat,v.texto); Object.assign(r,{res:"processada",prio:pr,sinais:hits.join(";")});
    vistos.push({id,categoria:cat,lat:v.lat,lon:v.lon,texto:v.texto}); out.push(r);
  });
  return out;
}
const CAT={buraco_via:"buraco na via",iluminacao:"iluminação",lixo_entulho:"lixo e entulho",alagamento_drenagem:"alagamento e drenagem",calcada_acessibilidade:"calçada e acessibilidade"};
function interpretar(res){
  const n=res.length, g=k=>res.filter(r=>r.res===k), ok=g("processada"), rv=g("revisao"), qu=g("quarentena"), du=g("duplicada");
  const P=[]; const pl=(k,a,b)=>k===1?a:b;
  P.push(`O arquivo tem ${n} ${pl(n,"linha","linhas")}. O robô processou ${ok.length}, mandou ${rv.length} para revisão humana, colocou ${qu.length} em quarentena e identificou ${du.length} ${pl(du.length,"duplicata","duplicatas")}.`);
  if(ok.length){
    const c={}; ok.forEach(r=>c[r.categoria]=(c[r.categoria]||0)+1);
    const top=Object.entries(c).sort((a,b)=>b[1]-a[1]); const alta=ok.filter(r=>r.prio==="alta");
    let t=`Entre as processadas, a categoria mais frequente é ${CAT[top[0][0]]} (${top[0][1]})`;
    if(top.length>1&&top[1][1]===top[0][1]) t+=`, empatada com ${CAT[top[1][0]]}`;
    t+=". "+(alta.length?`${alta.length} ${pl(alta.length,"relato recebeu","relatos receberam")} prioridade alta (${alta.map(r=>r.id).join(", ")}), por combinar a categoria com sinais de risco no texto.`:"Nenhum relato recebeu prioridade alta.");
    P.push(t);
  }
  if(rv.length) P.push(`${rv.length} ${pl(rv.length,"relato ficou","relatos ficaram")} com confiança abaixo de 0,45 e ${pl(rv.length,"vai","vão")} para uma pessoa decidir (${rv.map(r=>r.id).join(", ")}). Em geral são textos vagos ou com palavras que o modelo não viu no treino.`);
  if(qu.length){const m={}; qu.forEach(r=>(m[r.motivo]=m[r.motivo]||[]).push(r.id));
    P.push("Quarentena: "+Object.entries(m).map(([k,v])=>`${k} (${v.join(", ")})`).join("; ")+". Essas linhas não são perdidas: ficam separadas, com o motivo, e o robô segue com as demais.");}
  if(du.length) P.push("Duplicatas: "+du.map(r=>`${r.id} repete ${r.duplicada_de}`).join("; ")+". Não geram novo chamado.");
  P.push("Lembrete: o classificador foi treinado com 200 relatos sintéticos. Em relatos reais a acurácia pode ser menor, e por isso a revisão humana existe.");
  return P;
}
const API={norm,parseCSV,validar,prever,triar,interpretar,LIMIAR};
if(typeof module!=="undefined")module.exports=API; else root.Triagem=API;
})(this);
