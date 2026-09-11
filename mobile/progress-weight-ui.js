(() => {
  'use strict';

  let lastTouch = 0;

  function getForm(){
    return document.querySelector('.vp-progress-page .vp-weight-form');
  }

  function openWeightForm(){
    const form = getForm();
    if(!form) return false;
    form.classList.add('open');
    const input = form.querySelector('input[name="kg"]');
    if(input){
      input.removeAttribute('readonly');
      requestAnimationFrame(() => {
        try { input.focus({preventScroll:true}); }
        catch { input.focus(); }
      });
    }
    return true;
  }

  document.addEventListener('touchend', e => {
    const button = e.target.closest('.vp-progress-page [data-vp-toggle-weight]');
    if(!button) return;
    lastTouch = Date.now();
    e.preventDefault();
    e.stopPropagation();
    openWeightForm();
  }, {capture:true, passive:false});

  document.addEventListener('click', e => {
    const button = e.target.closest('.vp-progress-page [data-vp-toggle-weight]');
    if(!button) return;
    e.preventDefault();
    e.stopPropagation();
    if(Date.now() - lastTouch < 600){
      openWeightForm();
      return;
    }
    const form = getForm();
    if(!form) return;
    if(form.classList.contains('open')){
      form.classList.remove('open');
      return;
    }
    openWeightForm();
  }, true);
})();
