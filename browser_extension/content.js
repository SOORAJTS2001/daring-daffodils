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
}

fetch(chrome.runtime.getURL('static/easter_eggs.json'))
  .then(res => res.json())
  .then(videoList => {
    // Shuffle the list (Fisher–Yates)
    for (let i = videoList.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [videoList[i], videoList[j]] = [videoList[j], videoList[i]];
    }

    const spacing = Math.min(window.innerWidth, window.innerHeight) / videoList.length;
    const diagonalPositions = [];

    videoList.forEach((video, i) => {
      const a = document.createElement('a');
      a.href = video.url;
      a.target = "_blank";
      a.id = "pyscript-hidden-easter-eggs";
      a.style.position = "absolute";
      a.style.opacity = "0";
      a.style.pointerEvents = "auto";
      a.style.zIndex = "9999";

      const x = Math.floor(i * spacing);
      const y = Math.floor(i * spacing);

      a.style.left = `${x}px`;
      a.style.top  = `${y}px`;

      document.body.appendChild(a);

      // Save for PyScript wandering logic
      diagonalPositions.push([x, y]);
    });

    // Expose to PyScript
    window.diagonalPositions = diagonalPositions;
  });
}


injectWhenReady()
