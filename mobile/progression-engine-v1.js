(() => {
  'use strict';

  const num=v=>Number(v||0);
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const roundHalf=v=>Math.round(v*2)/2;

  function parseRepsTarget(value){
    const text=String(value??'').trim();
    const nums=(text.match(/\d+(?:[.,]\d+)?/g)||[]).map(x=>Number(x.replace(',','.'))).filter(Number.isFinite);
    if(!nums.length)return {min:null,max:null};
    if(nums.length===1)return {min:nums[0],max:nums[0]};
    return {min:Math.min(nums[0],nums[1]),max:Math.max(nums[0],nums[1])};
  }

  function exerciseExposures(state,name){
    const out=[];
    for(const session of state.sessions||[]){
      const sets=(session.sets||[]).filter(s=>String(s.exercise)===String(name));
      if(!sets.length)continue;
      out.push({
        date:session.date,
        routineName:session.routineName||'Entrenamiento',
        sets,
        topWeight:Math.max(...sets.map(s=>num(s.weight))),
        bestReps:Math.max(...sets.map(s=>num(s.reps))),
        avgReps:sets.reduce((a,s)=>a+num(s.reps),0)/sets.length,
        rirValues:sets.map(s=>Number(s.rir)).filter(Number.isFinite)
      });
    }
    return out.sort((a,b)=>String(a.date).localeCompare(String(b.date)));
  }

  function avg(arr){return arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:null}
  function latestWorkingWeight(exposure){
    if(!exposure?.sets?.length)return 0;
    const weighted=exposure.sets.filter(s=>num(s.weight)>0);
    if(!weighted.length)return 0;
    const counts=new Map();
    weighted.forEach(s=>counts.set(num(s.weight),(counts.get(num(s.weight))||0)+1));
    return [...counts.entries()].sort((a,b)=>b[1]-a[1]||b[0]-a[0])[0][0];
  }

  function recommendation(state,name,target={}){
    const exposures=exerciseExposures(state,name), repsTarget=parseRepsTarget(target.reps), targetSets=Math.max(1,Number(target.sets||1));
    if(exposures.length<2){
      return {status:'insufficient',label:'Sin datos suficientes',action:'Mantén una referencia cómoda',reason:'Necesitamos al menos 2 sesiones del ejercicio antes de recomendar una progresión.',exposures:exposures.length,target:repsTarget};
    }

    const recent=exposures.slice(-3), last=recent.at(-1), previous=recent.at(-2), working=latestWorkingWeight(last), minRep=repsTarget.min, maxRep=repsTarget.max;
    const lastWorkingSets=last.sets.filter(s=>Math.abs(num(s.weight)-working)<0.001), lastRir=avg(lastWorkingSets.map(s=>Number(s.rir)).filter(Number.isFinite));
    const prevWorking=latestWorkingWeight(previous), sameLoad=Math.abs(prevWorking-working)<0.001;
    const latestMeetsTop=maxRep!=null && lastWorkingSets.length>=Math.min(targetSets,last.sets.length) && lastWorkingSets.every(s=>num(s.reps)>=maxRep);
    const previousSets=previous.sets.filter(s=>Math.abs(num(s.weight)-prevWorking)<0.001);
    const previousMeetsTop=maxRep!=null && previousSets.length>=Math.min(targetSets,previous.sets.length) && previousSets.every(s=>num(s.reps)>=maxRep);
    const latestBelowMin=minRep!=null && lastWorkingSets.length && lastWorkingSets.filter(s=>num(s.reps)<minRep).length>=Math.ceil(lastWorkingSets.length/2);
    const previousBelowMin=minRep!=null && previousSets.length && previousSets.filter(s=>num(s.reps)<minRep).length>=Math.ceil(previousSets.length/2);
    const hardSet=lastRir!=null && lastRir<=0.75;

    if(working>0 && latestMeetsTop && previousMeetsTop && (lastRir==null || lastRir>=1)){
      const pct=0.035;
      const suggested=Math.max(working+0.5,roundHalf(working*(1+pct)));
      return {status:'increase',label:'Sube carga',action:`Prueba ~${suggested.toLocaleString('es-ES')} kg`,suggestedWeight:suggested,currentWeight:working,reason:lastRir==null?'Has alcanzado el techo de repeticiones en dos sesiones consecutivas.':'Has alcanzado el techo de repeticiones en dos sesiones y todavía conservas margen según tu RIR.',exposures:exposures.length,rir:lastRir,target:repsTarget};
    }

    if(hardSet && latestMeetsTop){
      return {status:'hold',label:'Mantén carga',action:`Repite ${working.toLocaleString('es-ES')} kg`,currentWeight:working,reason:'Has cumplido las repeticiones, pero el RIR indica que la serie ya fue muy exigente. Consolida antes de subir.',exposures:exposures.length,rir:lastRir,target:repsTarget};
    }

    if(latestBelowMin && previousBelowMin && sameLoad && working>0){
      const suggested=roundHalf(working*0.95);
      return {status:'review',label:'Revisa la carga',action:`Valora ${suggested.toLocaleString('es-ES')}–${working.toLocaleString('es-ES')} kg`,currentWeight:working,suggestedWeight:suggested,reason:'En dos sesiones seguidas la mayoría de series quedaron por debajo del mínimo de repeticiones previsto.',exposures:exposures.length,rir:lastRir,target:repsTarget};
    }

    if(working>0){
      let reason='Aún no has consolidado el techo del rango de repeticiones en sesiones consecutivas.';
      if(maxRep==null)reason='No hay un rango de repeticiones claro para aplicar una progresión automática.';
      else if(lastRir!=null && lastRir<1.5)reason='El rendimiento es estable, pero el RIR todavía es bajo para recomendar una subida con seguridad.';
      return {status:'hold',label:'Mantén carga',action:`Sigue con ${working.toLocaleString('es-ES')} kg`,currentWeight:working,reason,exposures:exposures.length,rir:lastRir,target:repsTarget};
    }

    return {status:'insufficient',label:'Sin referencia de carga',action:'Registra algunas sesiones',reason:'Todavía no hay suficiente información de peso para recomendar una progresión.',exposures:exposures.length,target:repsTarget};
  }

  window.VITALPEAK_PROGRESSION_ENGINE={
    version:1,
    parseRepsTarget,
    exerciseExposures,
    recommendation
  };
})();
