(() => {
  'use strict';

  const round=(v,d=1)=>Number(Number(v||0).toFixed(d));
  const pct=(a,b)=>b>0?((a-b)/b)*100:null;
  const mean=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:0;
  const today=()=>new Date().toISOString().slice(0,10);

  function e1rm(weight,reps){
    const w=Number(weight||0), r=Number(reps||0);
    if(w<=0||r<=0) return 0;
    if(r===1) return w;
    if(r>12) return 0;
    return w*(1+r/30);
  }

  function groupExerciseExposures(state,name){
    const out=[];
    for(const session of state.sessions||[]){
      const sets=(session.sets||[]).filter(s=>String(s.exercise)===String(name));
      if(!sets.length) continue;
      const valid=sets.filter(s=>Number(s.weight||0)>0&&Number(s.reps||0)>0);
      const scored=valid.map(s=>({
        ...s,
        e1rm:e1rm(s.weight,s.reps),
        volume:Number(s.weight||0)*Number(s.reps||0)
      }));
      const bestE1rm=Math.max(0,...scored.map(s=>s.e1rm));
      const bestWeight=Math.max(0,...valid.map(s=>Number(s.weight||0)));
      const bestAtWeight=valid
        .filter(s=>Number(s.weight||0)===bestWeight)
        .sort((a,b)=>Number(b.reps||0)-Number(a.reps||0))[0]||null;
      out.push({
        date:session.date,
        routineName:session.routineName||'Entrenamiento',
        session,
        sets:valid,
        setCount:valid.length,
        volume:valid.reduce((n,s)=>n+Number(s.weight||0)*Number(s.reps||0),0),
        bestE1rm,
        bestWeight,
        bestRepsAtBestWeight:Number(bestAtWeight?.reps||0)
      });
    }
    return out.sort((a,b)=>String(a.date).localeCompare(String(b.date)));
  }

  function classifyExercise(state,name){
    const exposures=groupExerciseExposures(state,name);
    const n=exposures.length;
    if(n<4){
      return {name,status:'insufficient',label:'Sin datos suficientes',exposures:n,reason:`Necesitamos al menos 4 sesiones de ${name} para detectar una tendencia fiable.`,deltaPct:null};
    }

    const w=Math.min(3,Math.floor(n/2));
    const recent=exposures.slice(-w), previous=exposures.slice(-2*w,-w);
    const recentMetric=mean(recent.map(x=>x.bestE1rm).filter(x=>x>0));
    const prevMetric=mean(previous.map(x=>x.bestE1rm).filter(x=>x>0));
    const delta=pct(recentMetric,prevMetric);
    const prior=exposures.slice(0,-w);
    const priorBest=Math.max(0,...prior.map(x=>x.bestE1rm));
    const recentBest=Math.max(0,...recent.map(x=>x.bestE1rm));
    const recentWeight=Math.max(0,...recent.map(x=>x.bestWeight));
    const priorWeight=Math.max(0,...prior.map(x=>x.bestWeight));
    const hasClearPR=(priorBest>0&&recentBest>=priorBest*1.015)||(priorWeight>0&&recentWeight>priorWeight);

    const last5=exposures.slice(-5);
    const firstLast5=last5[0]?.bestE1rm||0, lastLast5=last5.at(-1)?.bestE1rm||0;
    const fiveTrend=pct(lastLast5,firstLast5);
    const noRecentPR=priorBest>0&&recentBest<=priorBest*1.01;

    let status='stable', label='Estable', reason='Tu rendimiento reciente se mantiene en un rango parecido al periodo anterior.';
    if(hasClearPR || (delta!=null&&delta>=2.5)){
      status='progressing';label='Progresando';
      reason=`Tu rendimiento estimado ha mejorado ${delta!=null?`${round(delta,1)} %`:'respecto a tus sesiones anteriores'}.`;
    }else if(n>=6 && noRecentPR && fiveTrend!=null && fiveTrend>-1.5 && fiveTrend<1.5){
      status='plateau';label='Posible estancamiento';
      reason='Llevas varias exposiciones sin una mejora clara de carga, repeticiones o rendimiento estimado.';
    }else if(delta!=null&&delta<=-3){
      status='stable';label='Estable';
      reason=`Tu rendimiento reciente está ${Math.abs(round(delta,1))} % por debajo del bloque anterior. Aún no lo tratamos como estancamiento.`;
    }

    return {
      name,status,label,reason,exposures:n,
      deltaPct:delta==null?null:round(delta,1),
      recentE1rm:recentMetric?round(recentMetric,1):null,
      previousE1rm:prevMetric?round(prevMetric,1):null,
      bestE1rm:Math.max(0,...exposures.map(x=>x.bestE1rm))||null,
      bestWeight:Math.max(0,...exposures.map(x=>x.bestWeight))||null,
      recentBestE1rm:recentBest||null,
      fiveTrendPct:fiveTrend==null?null:round(fiveTrend,1)
    };
  }

  function exerciseNames(state){
    const s=new Set();
    for(const session of state.sessions||[]) for(const set of session.sets||[]) if(set.exercise)s.add(set.exercise);
    return [...s];
  }

  function adherence28(state){
    const end=today();
    const start=new Date(`${end}T12:00:00`); start.setDate(start.getDate()-27);
    const startIso=start.toISOString().slice(0,10);
    let planned=0, done=0;
    for(const [date,raw] of Object.entries(state.plan||{})){
      if(date<startIso||date>end) continue;
      const entries=Array.isArray(raw)?raw:(raw?[raw]:[]);
      planned+=entries.length;
      for(const key of entries){
        if((state.sessions||[]).some(s=>String(s.date)===String(date)&&String(s.routineKey||'')===String(key)))done++;
      }
    }
    return {planned,done,pct:planned?round(done/planned*100,0):null};
  }

  function analyze(state){
    const exercises=exerciseNames(state).map(name=>classifyExercise(state,name));
    const usable=exercises.filter(x=>x.status!=='insufficient');
    const progressing=usable.filter(x=>x.status==='progressing');
    const plateaus=usable.filter(x=>x.status==='plateau');
    let status='insufficient',label='Sin datos suficientes',summary='Sigue registrando entrenamientos para que VitalPeak pueda detectar tendencias.';
    if(usable.length>=2){
      if(progressing.length>=Math.max(1,Math.ceil(usable.length*.4))){status='progressing';label='Progresando';summary=`${progressing.length} ejercicio${progressing.length===1?'':'s'} muestran una mejora clara.`}
      else if(plateaus.length>=2&&progressing.length===0){status='plateau';label='Posible estancamiento';summary=`Hay ${plateaus.length} ejercicios con varias sesiones sin mejora clara.`}
      else {status='stable';label='Estable';summary='Tu rendimiento general se mantiene estable, con cambios pequeños entre ejercicios.'}
    }
    const adherence=adherence28(state);
    const insights=[
      ...progressing.sort((a,b)=>(b.deltaPct||0)-(a.deltaPct||0)).slice(0,2),
      ...plateaus.slice(0,2),
      ...usable.filter(x=>x.status==='stable').sort((a,b)=>(a.deltaPct||0)-(b.deltaPct||0)).slice(0,1)
    ].slice(0,3);
    return {status,label,summary,exercises,usableCount:usable.length,adherence,insights};
  }

  window.VITALPEAK_PROGRESS_ENGINE={version:'1.0.0',e1rm,groupExerciseExposures,classifyExercise,analyze};
})();