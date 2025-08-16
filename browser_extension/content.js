function injectWhenReady() {
  if (!document.head || !document.body) {
    // Retry until DOM is ready
    requestAnimationFrame(injectWhenReady);
    return;
  }
const css = document.createElement('link');
css.rel = 'stylesheet';
css.href = chrome.runtime.getURL('runtime/pyscript.css');
document.head.appendChild(css);

const pyscriptJs = document.createElement('script');
pyscriptJs.src = chrome.runtime.getURL('runtime/pyscript.js');
pyscriptJs.defer = true;
document.head.appendChild(pyscriptJs);

pyscriptJs.onload = () => {
  fetch(chrome.runtime.getURL('main.py'))
    .then(res => res.text())
    .then(code => {
      const pyTag = document.createElement('py-script');
      pyTag.textContent = code;
      document.body.appendChild(pyTag);
    });
}}
injectWhenReady()
