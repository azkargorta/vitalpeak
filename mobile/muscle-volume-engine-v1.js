(() => {
  'use strict';

  const DAY=86400000;
  const toDate=v=>new Date(`${String(v||'')}T12:00:00`);
  const iso=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const monday=(value=new Date())=>{const d=value instanceof Date?new Date(value):toDate(value);d.setHours(12,0,0,0);d.setDate(d.getDate()-((d.getDay()+6)%7));return d};
  const addDays=(d,n)=>new Date(d.getTime()+n*DAY);
  const catalog=()=>window.VITALPEAK_CATALOG?.exercises||[];
  const normalize=s=>String(s||'').trim().toLocaleLowerCase('es');

  function metaFor(name){
    const key=normalize(name);
    const item=catalog().find(x=>normalize(x.name)===key);
    return item?.metadata||null;
  }

  function weekKey(date){return iso(monday(date))}
  function emptyWeek(start){return {start:iso(start),end:iso(addDays(start,6)),muscles:{},sessions:0,sets:0}}
  function ensureMuscle(week,muscle){return week.muscles[muscle]||(week.muscles[muscle]={direct:0,involved:0,exercises:{}})}

  function buildWeeks(state,count=6){
    const current=monday(new Date());
    const weeks=Array.from({length:count},(_,i)=>emptyWeek(addDays(current,-7*(count-1-i))));
    const byStart=new Map(weeks.map(w=>[w.start,w]));
    for(const session of state.sessions||[]){
      const wk=byStart.get(weekKey(session.date));if(!wk)continue;wk.sessions+=1;
      for(const set of session.sets||[]){
        const meta=metaFor(set.exercise);if(!meta)continue;wk.sets+=1;
        const primary=String(meta.primary_muscle||'').trim();
        if(primary){const row=ensureMuscle(wk,primary);row.direct+=1;row.involved+=1;row.exercises[set.exercise]=(row.exercises[set.exercise]||0)+1}
        for(const secondary of meta.secondary_muscles||[]){const m=String(secondary||'').trim();if(!m||m===primary)continue;const row=ensureMuscle(wk,m);row.involved+=0.5}
      }
    }
    return weeks;
  }

  function avg(values){const xs=values.filter(Number.isFinite);return xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0}
  function pct(cur,base){return base>0?(cur-base)/base*100:null}

  function analyzeMuscle(name,weeks){
    const current=weeks.at(-1)?.muscles?.[name]||{direct:0,involved:0,exercises:{}};
    const prev=weeks.slice(-4,-1).map(w=>w.muscles?.[name]?.direct||0);
    const baseline=avg(prev),change=pct(current.direct,baseline);
    const activeWeeks=weeks.slice(-4).filter(w=>(w.muscles?.[name]?.direct||0)>0).length;
    let status='stable',label='Estable',reason='Volumen similar a tu media reciente.';
    if(activeWeeks<2 && baseline===0){status='insufficient';label='Sin datos suficientes';reason='Necesitamos más semanas para valorar la tendencia.'}
    else if(baseline>=4 && current.direct===0){status='low';label='Muy por debajo';reason=`Esta semana no hay series directas; tu media reciente era ${baseline.toFixed(1)}.`}
    else if(baseline>=4 && current.direct<baseline*.5){status='low';label='Por debajo';reason=`Has bajado claramente frente a tu media de ${baseline.toFixed(1)} series directas.`}
    else if(baseline>=4 && current.direct>baseline*1.5 && current.direct>=8){status='high';label='Muy por encima';reason=`Esta semana estás bastante por encima de tu media de ${baseline.toFixed(1)} series directas.`}
    else if(change!=null && change>=25){status='rising';label='Subiendo';reason=`El volumen directo sube ${Math.round(change)}% frente a tu media reciente.`}
    else if(change!=null && change<=-25){status='falling';label='Bajando';reason=`El volumen directo baja ${Math.abs(Math.round(change))}% frente a tu media reciente.`}
    const topExercises=Object.entries(current.exercises||{}).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([exercise,sets])=>({exercise,sets}));
    return {name,direct:current.direct,involved:Math.round(current.involved*10)/10,baseline:Math.round(baseline*10)/10,changePct:change==null?null:Math.round(change*10)/10,status,label,reason,activeWeeks,topExercises};
  }

  function analyze(state,{weeks:count=6}={}){
    const weeks=buildWeeks(state,count);
    const names=new Set();for(const w of weeks)for(const name of Object.keys(w.muscles||{}))names.add(name);
    const muscles=[...names].map(name=>analyzeMuscle(name,weeks)).sort((a,b)=>b.direct-a.direct||a.name.localeCompare(b.name,'es'));
    const alerts=muscles.filter(x=>['low','high','rising','falling'].includes(x.status)).sort((a,b)=>({low:0,high:1,falling:2,rising:3}[a.status]-({low:0,high:1,falling:2,rising:3}[b.status]))).slice(0,4);
    return {version:1,weeks,muscles,alerts,currentWeek:weeks.at(-1)||null};
  }

  window.VitalPeakMuscleVolume={analyze,metaFor,buildWeeks};
})();