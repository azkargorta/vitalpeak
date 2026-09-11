(() => {
  'use strict';

  function focusWeightInput(){
    const form=document.querySelector('.vp-weight-form');
    const input=form?.querySelector('input[name="kg"]');
    if(!form||!input) return;
    form.classList.add('open');
    input.removeAttribute('readonly');
    input.focus({preventScroll:true});
    try{input.setSelectionRange(input.value.length,input.value.length)}catch{}
  }

  document.addEventListener('click',e=>{
    const button=e.target.closest('[data-vp-toggle-weight]');
    if(!button) return;
    focusWeightInput();
  },true);

  document.addEventListener('touchend',e=>{
    const button=e.target.closest('[data-vp-toggle-weight]');
    if(!button) return;
    focusWeightInput();
  },{capture:true,passive:true});
})();