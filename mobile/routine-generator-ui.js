(() => {
  const C = window.VITALPEAK_CATALOG || {};
  if (!Array.isArray(C.exercises) || !C.exercises.length) return;

  const GOALS = [
    ["hipertrofia","Ganar músculo"],["fuerza","Ganar fuerza"],["perdida_grasa","Perder grasa"],
    ["recomposicion","Recomposición corporal"],["resistencia","Mejorar resistencia"],
    ["potencia","Rendimiento / potencia"],["fitness_general","Estar en forma"]
  ];
  const MUSCLES = ["Pecho","Espalda","Cuádriceps","Isquios","Glúteos","Deltoide lateral","Deltoide posterior","Bíceps","Tríceps","Gemelos","Core"];
  const UPPER=["Pecho","Espalda","Deltoide lateral","Deltoide posterior","Bíceps","Tríceps"];
  const LOWER=["Cuádriceps","Isquios","Glúteos","Gemelos","Core"];
  const PUSH=["Pecho","Deltoide lateral","Tríceps"], PULL=["Espalda","Deltoide posterior","Bíceps"], LEGS=["Cuádriceps","Isquios","Glúteos","Gemelos","Core"];
  let preview = null;

  const norm = s => String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().trim();
  const esc = v => String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const goalLabel = g => (GOALS.find(x=>x[0]===g)||[g,g])[1];

  function chooseSplit(goal, level, days){
    if(days===2) return "Full Body";
    if(days===3) return (goal==="fuerza" || goal==="fitness_general" || level==="principiante") ? "Full Body" : "PPL";
    if(days===4) return "Upper / Lower";
    if(days===5) return "Upper / Lower + PPL";
    return "PPL x2";
  }
  function splitDays(split, days){
    let list;
    if(split==="Full Body") list=["A","B","C"].map(x=>({name:`Full Body ${x}`,muscles:[...UPPER,...LOWER]}));
    else if(split==="Upper / Lower") list=[{name:"Upper A",muscles:UPPER},{name:"Lower A",muscles:LOWER},{name:"Upper B",muscles:UPPER},{name:"Lower B",muscles:LOWER}];
    else if(split==="PPL") list=[{name:"Push",muscles:PUSH},{name:"Pull",muscles:PULL},{name:"Legs",muscles:LEGS}];
    else if(split==="Upper / Lower + PPL") list=[{name:"Upper",muscles:UPPER},{name:"Lower",muscles:LOWER},{name:"Push",muscles:PUSH},{name:"Pull",muscles:PULL},{name:"Legs",muscles:LEGS}];
    else list=[{name:"Push A",muscles:PUSH},{name:"Pull A",muscles:PULL},{name:"Legs A",muscles:LEGS},{name:"Push B",muscles:PUSH},{name:"Pull B",muscles:PULL},{name:"Legs B",muscles:LEGS}];
    return list.slice(0,days);
  }
  function sessionCap(minutes){ return minutes<=40?5:minutes<=60?7:minutes<=80?8:9; }
  function weeklyVolume(goal, level, days, priorities){
    const base=(C.volumeEngine?.goals||{})[goal] || (C.volumeEngine?.goals||{}).fitness_general || {};
    const lf=level==="principiante"?.70:level==="avanzado"?1.15:1;
    const df=({2:.90,3:.95,4:1,5:1,6:1})[days]||1;
    const limits=C.volumeEngine?.limits||{};
    const p=new Set(priorities.map(norm));
    const out={};
    for(const [m,b] of Object.entries(base)){
      let v=Number(b)*lf*df*(p.has(norm(m))?1.20:1);
      const lim=limits[m]||[2,20]; out[m]=Math.max(lim[0],Math.min(lim[1],Math.round(v)));
    }
    return out;
  }
  function muscleMatch(metaMuscle,target){
    const aliases=C.exerciseSelector?.muscle_aliases?.[target]||[target]; const m=norm(metaMuscle);
    return aliases.some(a=>m.includes(norm(a))||norm(a).includes(m));
  }
  function equipmentAllowed(meta, eq){
    if(eq==="gimnasio_completo") return true;
    const e=norm(meta.equipment);
    if(e.includes("peso corporal")) return true;
    if(eq==="casa") return e.includes("mancuer")||e.includes("peso corporal")||e.includes("kettlebell")||e.includes("rueda");
    if(eq==="basico") return !e.includes("trineo")&&!e.includes("battle")&&!e.includes("martillo");
    return true;
  }
  function scoreExercise(x,target,goal,level,patterns,used,eq){
    const m=x.metadata||{}; if(!equipmentAllowed(m,eq)) return -999;
    let s=0;
    if(muscleMatch(m.primary_muscle,target)) s+=12;
    else if((m.secondary_muscles||[]).some(v=>muscleMatch(v,target))) s+=4; else return -999;
    const goals=(m.goals||[]).map(norm); if(goals.includes(norm(goal))) s+=4;
    else if(["recomposicion","perdida_grasa"].includes(goal)&&goals.includes("hipertrofia")) s+=2.5;
    const rank={beginner:0,principiante:0,intermediate:1,intermedio:1,advanced:2,avanzado:2};
    const ul=rank[level]??1, el=rank[norm(m.difficulty)]??1; if(el>ul) s-=8*(el-ul); else if(el===ul)s+=1.5;
    const type=norm(m.exercise_type), equipment=norm(m.equipment), fatigue=norm(m.fatigue);
    if(goal==="fuerza"){ if(type==="compuesto")s+=4; if(equipment.includes("barra"))s+=2; if(fatigue==="high")s+=1; }
    if(["hipertrofia","recomposicion","perdida_grasa"].includes(goal)){ if(/maquina|polea|mancuer|smith/.test(equipment))s+=2; if(fatigue==="low")s+=1.5; if(fatigue==="high")s-=.5; }
    if(goal==="potencia"&&/potencia|explosivo|acondicionamiento/.test(type))s+=6;
    if(goal==="resistencia"&&/acondicionamiento|potencia/.test(type))s+=3;
    const pat=String(m.movement_pattern||""); if(patterns[pat]) s-=4*patterns[pat];
    if(used.has(x.name))s-=100;
    return s;
  }
  function prescription(goal,meta){
    const compound=norm(meta.exercise_type)==="compuesto", high=norm(meta.fatigue)==="high";
    if(goal==="fuerza") return {reps:compound?"3-6":"6-10",rir:2,rest_sec:compound?180:120};
    if(goal==="potencia") return {reps:compound?"3-5":"5-8",rir:3,rest_sec:150};
    if(goal==="resistencia") return {reps:"12-20",rir:2,rest_sec:60};
    if(["hipertrofia","recomposicion","perdida_grasa"].includes(goal)) return {reps:compound?"6-10":"10-15",rir:2,rest_sec:high?150:(compound?120:75)};
    return {reps:"8-12",rir:2,rest_sec:90};
  }
  function generate({goal,level,days,minutes,equipment,priorities}){
    const split=chooseSplit(goal,level,days), defs=splitDays(split,days), volume=weeklyVolume(goal,level,days,priorities), cap=sessionCap(minutes);
    const sessions=defs.map(d=>({name:d.name,muscles:d.muscles,targetSets:{},items:[]}));
    for(const [m,total] of Object.entries(volume)){
      const eligible=sessions.map((d,i)=>d.muscles.includes(m)?i:-1).filter(i=>i>=0); if(!eligible.length)continue;
      const q=Math.floor(total/eligible.length),r=total%eligible.length; eligible.forEach((idx,j)=>sessions[idx].targetSets[m]=q+(j<r?1:0));
    }
    for(const s of sessions){
      const slots={}; Object.entries(s.targetSets).forEach(([m,n])=>{if(n>0)slots[m]=n>=5?2:1;});
      while(Object.values(slots).reduce((a,b)=>a+b,0)>cap){ const two=Object.keys(slots).find(m=>slots[m]>1); if(two)slots[two]--; else {const sm=Object.keys(slots).sort((a,b)=>s.targetSets[a]-s.targetSets[b])[0]; delete slots[sm];} }
      const used=new Set(),patterns={};
      for(const [muscle,count] of Object.entries(slots)){
        for(let n=0;n<count;n++){
          const ranked=C.exercises.filter(x=>x.metadata).map(x=>({x,score:scoreExercise(x,muscle,goal,level,patterns,used,equipment)})).filter(o=>o.score>-900).sort((a,b)=>b.score-a.score);
          if(!ranked.length)continue; const ex=ranked[0].x, meta=ex.metadata||{}; used.add(ex.name); const pat=String(meta.movement_pattern||""); if(pat)patterns[pat]=(patterns[pat]||0)+1;
          s.items.push({exercise:ex.name,target_muscle:muscle,metadata:meta});
        }
      }
      const grouped={}; s.items.forEach(it=>(grouped[it.target_muscle]??=[]).push(it));
      for(const [m,list] of Object.entries(grouped)){ const total=Math.max(list.length*2,s.targetSets[m]||0),q=Math.floor(total/list.length),r=total%list.length; list.forEach((it,i)=>{const p=prescription(goal,it.metadata);it.sets=Math.max(2,Math.min(5,q+(i<r?1:0)));it.reps=p.reps;it.rir=p.rir;it.rest_sec=p.rest_sec;}); }
      const typeOrder={potencia:0,explosivo:0,compuesto:1,aislamiento:2,core:3,acondicionamiento:4}; s.items.sort((a,b)=>(typeOrder[norm(a.metadata.exercise_type)]??2)-(typeOrder[norm(b.metadata.exercise_type)]??2));
    }
    return {goal,level,days,minutes,equipment,priorities,split,sessions,volume};
  }

  function previewHTML(p){
    return `<div class="vp-smart-summary"><span class="template-meta">PLAN RECOMENDADO</span><h3>${esc(p.split)} · ${p.days} días</h3><p class="muted">${esc(goalLabel(p.goal))} · ${esc(p.level)} · ${p.minutes} min/sesión</p></div>`+
      p.sessions.map((d,i)=>`<details class="vp-smart-day" ${i===0?"open":""}><summary><b>${esc(d.name)}</b><span>${d.items.length} ejercicios</span></summary><div>${d.items.map(x=>`<div class="vp-smart-ex"><div><b>${esc(x.exercise)}</b><small>${esc(x.target_muscle)}</small></div><span>${x.sets} × ${esc(x.reps)} · RIR ${x.rir}</span></div>`).join("")}</div></details>`)+
      `<button class="primary wide" type="button" data-vp-smart-save>Guardar este plan</button>`;
  }

  async function readState(){
    return new Promise((resolve,reject)=>{const r=indexedDB.open("vitalpeak-mobile",2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains("state"))r.result.createObjectStore("state")};r.onerror=()=>reject(r.error);r.onsuccess=()=>{const db=r.result,tx=db.transaction("state","readonly"),q=tx.objectStore("state").get("user");q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error);};});
  }
  async function writeState(data){
    return new Promise((resolve,reject)=>{const r=indexedDB.open("vitalpeak-mobile",2);r.onerror=()=>reject(r.error);r.onsuccess=()=>{const db=r.result,tx=db.transaction("state","readwrite");tx.objectStore("state").put(data,"user");tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);};});
  }
  async function savePlan(){
    if(!preview)return; const name=`VitalPeak · ${preview.split} · ${goalLabel(preview.goal)}`, id=`smart-${Date.now()}`;
    const routine={id,name,description:`Plan inteligente: ${goalLabel(preview.goal)} · ${preview.level} · ${preview.days} días`,goal:preview.goal,level:preview.level,days_per_week:preview.days,activeDay:0,generated:true,days:preview.sessions.map(d=>({name:d.name,focus:d.muscles.join(", "),items:d.items.map(x=>({exercise:x.exercise,sets:x.sets,reps:x.reps,weight:0,rest_sec:x.rest_sec,notes:`RIR ${x.rir}`}))}))};
    const state=await readState(); state.routines=Array.isArray(state.routines)?state.routines:[]; state.routines.push(routine); state.activeRoutineId=id; await writeState(state);
    const msg=document.querySelector("#toast"); if(msg){msg.textContent="Plan inteligente guardado";msg.classList.add("show");}
    setTimeout(()=>location.reload(),450);
  }

  function sectionHTML(){
    return `<section id="vp-smart-generator"><section class="section-head"><h2>Crear plan inteligente</h2><span class="pill">NUEVO</span></section><div class="card"><p class="muted">VitalPeak elegirá el split, volumen y ejercicios según tus respuestas.</p><form id="vp-smart-form" class="stack">
      <label class="field">Objetivo<select name="goal">${GOALS.map(([v,l])=>`<option value="${v}">${l}</option>`).join("")}</select></label>
      <div class="form-grid"><label class="field">Nivel<select name="level"><option value="principiante">Principiante</option><option value="intermedio" selected>Intermedio</option><option value="avanzado">Avanzado</option></select></label><label class="field">Días/semana<select name="days">${[2,3,4,5,6].map(n=>`<option value="${n}" ${n===4?"selected":""}>${n}</option>`).join("")}</select></label></div>
      <div class="form-grid"><label class="field">Duración<select name="minutes">${[40,50,60,75,90].map(n=>`<option value="${n}" ${n===60?"selected":""}>${n} min</option>`).join("")}</select></label><label class="field">Equipamiento<select name="equipment"><option value="gimnasio_completo">Gimnasio completo</option><option value="basico">Gimnasio básico</option><option value="casa">Casa / mancuernas</option></select></label></div>
      <fieldset class="vp-priority"><legend>Músculos prioritarios <small>(opcional)</small></legend><div class="vp-chips">${MUSCLES.map(m=>`<label><input type="checkbox" name="priority" value="${esc(m)}"><span>${esc(m)}</span></label>`).join("")}</div></fieldset>
      <button class="primary wide" type="submit">Generar mi plan</button></form><div id="vp-smart-preview"></div></div></section>`;
  }
  function addStyles(){ if(document.querySelector("#vp-smart-style"))return; const s=document.createElement("style");s.id="vp-smart-style";s.textContent=`#vp-smart-generator{margin-top:18px}.vp-priority{border:0;padding:0;margin:4px 0}.vp-priority legend{font-weight:800;margin-bottom:8px}.vp-priority legend small{font-weight:600;color:#6b7d82}.vp-chips{display:flex;flex-wrap:wrap;gap:7px}.vp-chips input{display:none}.vp-chips span{display:block;padding:8px 10px;border:1px solid #cfe0dc;border-radius:999px;background:#fff;font-size:12px;font-weight:700;cursor:pointer}.vp-chips input:checked+span{background:#dff5ef;border-color:#16a98e;color:#0c6d5b}.vp-smart-summary{margin:18px 0 10px;padding-top:14px;border-top:1px solid #e1ece9}.vp-smart-day{border:1px solid #d8e7e3;border-radius:14px;margin:8px 0;background:#fbfefd;overflow:hidden}.vp-smart-day summary{display:flex;justify-content:space-between;gap:10px;padding:12px;cursor:pointer}.vp-smart-day summary span{font-size:12px;color:#60757a}.vp-smart-ex{display:flex;justify-content:space-between;gap:12px;padding:10px 12px;border-top:1px solid #e6efed;align-items:center}.vp-smart-ex div{min-width:0}.vp-smart-ex b{display:block;font-size:13px}.vp-smart-ex small{display:block;color:#60757a;margin-top:2px}.vp-smart-ex>span{font-size:12px;font-weight:800;white-space:nowrap}`;document.head.appendChild(s); }
  function mount(){
    addStyles(); if(document.querySelector("#vp-smart-generator"))return;
    const h1=[...document.querySelectorAll("h1")].find(x=>x.textContent.includes("Planes y ejercicios")); if(!h1)return;
    const hero=h1.closest(".hero"); if(!hero)return; hero.insertAdjacentHTML("afterend",sectionHTML());
  }
  document.addEventListener("submit",e=>{if(e.target?.id!=="vp-smart-form")return;e.preventDefault();const f=new FormData(e.target);preview=generate({goal:f.get("goal"),level:f.get("level"),days:Number(f.get("days")),minutes:Number(f.get("minutes")),equipment:f.get("equipment"),priorities:f.getAll("priority")});document.querySelector("#vp-smart-preview").innerHTML=previewHTML(preview);document.querySelector("#vp-smart-preview").scrollIntoView({behavior:"smooth",block:"start"});});
  document.addEventListener("click",e=>{if(e.target.closest("[data-vp-smart-save]"))savePlan().catch(()=>alert("No se pudo guardar el plan. Inténtalo de nuevo."));});
  new MutationObserver(mount).observe(document.body,{childList:true,subtree:true}); mount();
})();