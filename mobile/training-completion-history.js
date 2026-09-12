(() => {
  'use strict';
  if(document.querySelector('script[data-vp-history-lite]'))return;
  const s=document.createElement('script');
  s.src='./training-completion-history-lite.js?v=1';
  s.async=false;
  s.dataset.vpHistoryLite='1';
  document.head.appendChild(s);
})();