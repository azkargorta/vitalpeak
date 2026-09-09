(() => {
  'use strict';

  if (!window.__VITALPEAK_ROUTINE_FILTER_STATE__) {
    window.__VITALPEAK_ROUTINE_FILTER_STATE__ = true;
    const filterState = document.createElement('script');
    filterState.src = './routine-filter-persistence.js?v=2';
    document.head.appendChild(filterState);
  }

  const catalog = window.VITALPEAK_CATALOG;
  if (!catalog) return;
  catalog.exercises = Array.isArray(catalog.exercises) ? catalog.exercises : [];
  catalog.templates = Array.isArray(catalog.templates) ? catalog.templates : [];

  const cardioExercises = [
    { name:'Cinta de correr', group:'Cardio', cardio:true, cardioType:'treadmill', cues:['Empieza con unos minutos suaves antes de subir el ritmo.','Mantén una zancada natural y evita agarrarte a la consola salvo necesidad.'], animation:{kind:'image',path:'cardio-images/cinta-de-correr.webp'} },
    { name:'Caminata en cinta con inclinación', group:'Cardio', cardio:true, cardioType:'treadmill', cues:['Mantén el tronco erguido y una inclinación que puedas sostener con buena técnica.','Ajusta velocidad e inclinación para controlar la intensidad sin tener que correr.'], animation:{kind:'image',path:'cardio-images/caminata-cinta-inclinacion.webp'} },
    { name:'Bicicleta estática', group:'Cardio', cardio:true, cardioType:'bike', cues:['Ajusta el sillín para que la rodilla quede ligeramente flexionada abajo.','Pedalea de forma fluida y controla la resistencia sin perder cadencia.'], animation:{kind:'image',path:'cardio-images/bicicleta-estatica.webp'} },
    { name:'Bicicleta de aire', group:'Cardio', cardio:true, cardioType:'air-bike', cues:['Empuja y tira con brazos mientras mantienes un pedaleo constante.','En intervalos intensos prioriza una postura estable antes que la velocidad máxima.'], animation:{kind:'image',path:'cardio-images/bicicleta-aire.webp'} },
    { name:'Bicicleta elíptica', group:'Cardio', cardio:true, cardioType:'elliptical', cues:['Mantén el apoyo completo del pie y el tronco estable.','Aumenta resistencia antes de acelerar si buscas más intensidad con menos impacto.'], animation:{kind:'image',path:'cardio-images/bicicleta-eliptica.webp'} },
    { name:'Remo ergómetro', group:'Cardio', cardio:true, cardioType:'rower', cues:['Empuja primero con las piernas, después acompaña con tronco y brazos.','En la vuelta recupera brazos, tronco y finalmente piernas.'], animation:{kind:'image',path:'cardio-images/remo-ergometro.webp'} },
    { name:'Escaladora', group:'Cardio', cardio:true, cardioType:'stair-climber', cues:['Evita descargar el peso sobre las manos.','Usa pasos controlados y regula el ritmo para mantener la intensidad objetivo.'], animation:{kind:'image',path:'cardio-images/escaladora.webp'} },
    { name:'Saltar a la comba', group:'Cardio', cardio:true, cardioType:'jump-rope', cues:['Haz saltos bajos y suaves, principalmente desde los tobillos.','Mantén los codos cerca del cuerpo y mueve la cuerda con las muñecas.'], animation:{kind:'image',path:'cardio-images/saltar-comba.webp'} },
    { name:'Carrera exterior', group:'Cardio', cardio:true, cardioType:'running', cues:['Empieza suave y aumenta progresivamente el ritmo.','Adapta el esfuerzo al terreno y a las condiciones del día.'], animation:{kind:'image',path:'cardio-images/carrera-exterior.webp'} },
    { name:'Caminata rápida', group:'Cardio', cardio:true, cardioType:'walking', cues:['Busca un paso vivo que puedas mantener sin perder postura.','Usa el movimiento natural de brazos para acompañar el ritmo.'], animation:{kind:'image',path:'cardio-images/caminata-rapida.webp'} }
  ];

  for (const ex of cardioExercises) {
    const existing = catalog.exercises.find(x => String(x.name).toLocaleLowerCase('es') === ex.name.toLocaleLowerCase('es'));
    if (existing) Object.assign(existing, ex);
    else catalog.exercises.push(ex);
  }

  const item = (exercise, duration_min, intensity='Moderada', extra={}) => ({
    exercise,
    sets:1,
    reps:duration_min,
    rest_sec:0,
    weight:0,
    cardio:true,
    cardioUnit:'min',
    duration_min,
    intensity,
    ...extra
  });

  const cardioTemplates = [
    {
      id:'cardio-iniciacion-3d', name:'Cardio iniciación · 3 días', days_per_week:3, level:'principiante', goal:'Cardio', cardio:true,
      description:'Plan progresivo de bajo impacto para crear una base cardiovascular y mejorar la tolerancia al esfuerzo.',
      days:[
        {name:'Día 1 · Caminata inclinada',focus:'Cardio suave',items:[item('Caminata en cinta con inclinación',25,'Suave')]},
        {name:'Día 2 · Bicicleta',focus:'Cardio continuo',items:[item('Bicicleta estática',30,'Suave-moderada')]},
        {name:'Día 3 · Elíptica',focus:'Cardio continuo',items:[item('Bicicleta elíptica',30,'Moderada')]}
      ], activeDay:0, source:'template'
    },
    {
      id:'cardio-quema-grasa-4d', name:'Cardio base · 4 días', days_per_week:4, level:'intermedio', goal:'Cardio', cardio:true,
      description:'Cuatro sesiones semanales combinando trabajo continuo, inclinación y máquinas de bajo impacto.',
      days:[
        {name:'Día 1 · Cinta',focus:'Zona aeróbica',items:[item('Cinta de correr',35,'Moderada')]},
        {name:'Día 2 · Remo',focus:'Cardio total',items:[item('Remo ergómetro',25,'Moderada')]},
        {name:'Día 3 · Caminata inclinada',focus:'Cardio sostenido',items:[item('Caminata en cinta con inclinación',40,'Moderada')]},
        {name:'Día 4 · Bicicleta',focus:'Cardio largo',items:[item('Bicicleta estática',45,'Suave-moderada')]}
      ], activeDay:0, source:'template'
    },
    {
      id:'cardio-intervalos-3d', name:'Cardio intervalos · 3 días', days_per_week:3, level:'avanzado', goal:'Cardio', cardio:true,
      description:'Sesiones de intervalos para mejorar capacidad cardiovascular y tolerancia a esfuerzos intensos.',
      days:[
        {name:'Día 1 · Air bike',focus:'Intervalos',items:[item('Bicicleta de aire',20,'Alta',{intervals:'10 × 30 s intenso / 60 s suave'})]},
        {name:'Día 2 · Remo',focus:'Intervalos',items:[item('Remo ergómetro',24,'Alta',{intervals:'8 × 1 min intenso / 2 min suave'})]},
        {name:'Día 3 · Cinta',focus:'Cambios de ritmo',items:[item('Cinta de correr',30,'Alta',{intervals:'6 × 2 min rápido / 3 min suave'})]}
      ], activeDay:0, source:'template'
    },
    {
      id:'cardio-mixto-4d', name:'Cardio mixto · 4 días', days_per_week:4, level:'intermedio', goal:'Cardio', cardio:true,
      description:'Varía máquinas y estímulos durante la semana para desarrollar una condición cardiovascular completa.',
      days:[
        {name:'Día 1 · Carrera',focus:'Resistencia',items:[item('Cinta de correr',30,'Moderada')]},
        {name:'Día 2 · Escaladora',focus:'Resistencia',items:[item('Escaladora',25,'Moderada-alta')]},
        {name:'Día 3 · Remo + bici',focus:'Cardio mixto',items:[item('Remo ergómetro',15,'Moderada'),item('Bicicleta estática',20,'Moderada')]},
        {name:'Día 4 · Recuperación activa',focus:'Cardio suave',items:[item('Caminata rápida',40,'Suave')]}
      ], activeDay:0, source:'template'
    }
  ];

  for (const t of cardioTemplates) {
    if (!catalog.templates.some(x => String(x.id) === t.id)) catalog.templates.push(t);
  }
})();
