/* ALDUIN X — resilient Live2D runtime loader
   The app itself never depends on a single CDN. Runtime sources are tried in order.
*/
(function(){
  const sources = {
    pixi: [
      'https://fastly.jsdelivr.net/npm/pixi.js@6.5.2/dist/browser/pixi.min.js',
      'https://unpkg.com/pixi.js@6.5.2/dist/browser/pixi.min.js',
      'https://cdn.jsdelivr.net/npm/pixi.js@6.5.2/dist/browser/pixi.min.js'
    ],
    core: [
      'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js',
      'https://fastly.jsdelivr.net/npm/live2dcubismcore@1.0.2/live2dcubismcore.min.js',
      'https://unpkg.com/live2dcubismcore@1.0.2/live2dcubismcore.min.js',
      'https://cdn.jsdelivr.net/npm/live2dcubismcore@1.0.2/live2dcubismcore.min.js'
    ],
    plugin: [
      'https://fastly.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js',
      'https://unpkg.com/pixi-live2d-display@0.4.0/dist/cubism4.min.js',
      'https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js'
    ],
    jszip: [
      'https://fastly.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js',
      'https://unpkg.com/jszip@3.10.1/dist/jszip.min.js',
      'https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js'
    ]
  };

  const state={pixi:false,core:false,plugin:false,jszip:false,errors:[]};
  window.__alduinLive2DState=state;
  window.__alduinLive2DReady=(async function(){
    async function load(list,label,check){
      if(check()) return true;
      for(const url of list){
        try{
          await new Promise((resolve,reject)=>{
            const s=document.createElement('script');
            s.src=url; s.async=false;
            s.onload=()=>resolve();
            s.onerror=()=>reject(new Error(url));
            document.head.appendChild(s);
          });
          if(check()) return true;
        }catch(e){ state.errors.push(label+': '+url); }
      }
      return false;
    }
    state.pixi=await load(sources.pixi,'PIXI',()=>!!window.PIXI);
    if(!state.pixi) return false;

    // The plugin needs window.PIXI to exist before it initializes.
    state.core=await load(sources.core,'Cubism Core',()=>!!window.Live2DCubismCore);
    if(!state.core) return false;

    state.plugin=await load(sources.plugin,'pixi-live2d-display',()=>!!window.PIXI?.live2d?.Live2DModel);
    state.jszip=await load(sources.jszip,'JSZip',()=>!!window.JSZip);

    window.__alduinLive2DReadyState=state;
    return !!(state.pixi && state.core && state.plugin);
  })();
})();
