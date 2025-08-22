function injectWhenReady() {
    // Ensure the DOM is ready before injecting anything
    if (!document.head || !document.body) {
        requestAnimationFrame(injectWhenReady);
        return;
    }

    // --- Load PyScript runtime CSS ---
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = chrome.runtime.getURL('runtime/pyscript.css');
    document.head.appendChild(css);

    // --- Load PyScript runtime JS ---
    const pyscriptJs = document.createElement('script');
    pyscriptJs.src = chrome.runtime.getURL('runtime/pyscript.js');
    pyscriptJs.defer = true;
    document.head.appendChild(pyscriptJs);

    // Wait until PyScript runtime is loaded before injecting Python code
    pyscriptJs.onload = async () => {
        // --- Load main.py ---
        const mainCode = await fetch(chrome.runtime.getURL('main.py')).then(r => r.text());

        // --- Load all utils/*.py files (helper modules) ---
        const utilsFiles = [
            "__init__.py",
            "easter_eggs.py",
            "fake_cursor.py",
            "make_highlights.py",
            "move_and_click.py",
            "toast.py"
            // Add more utils/*.py files here if needed
        ];

        // Create Python code to build utils/ directory at runtime
        let utilsLoader = `
import os
os.makedirs("utils", exist_ok=True)
`;

        // For each Python util file, write its contents into the in-browser FS
        for (const f of utilsFiles) {
            const code = await fetch(chrome.runtime.getURL(`utils/${f}`)).then(r => r.text());
            utilsLoader += `with open("utils/${f}", "w") as fp:\n    fp.write("""${code.replace(/"""/g, '\\"""')}""")\n\n`;
        }

        // --- Inject everything into <py-script> ---
        // (PyScript tag runs Python code directly in the browser)
        const pyTag = document.createElement('py-script');
        pyTag.textContent = utilsLoader + "\n\n" + mainCode;
        document.body.appendChild(pyTag);
    };

    // --- Easter eggs loader ---
    // Fetch JSON file with video links and create invisible <a> elements on screen
    fetch(chrome.runtime.getURL('static/easter_eggs.json'))
        .then(res => res.json())
        .then(videoList => {
            // Randomize video order using Fisher–Yates shuffle
            for (let i = videoList.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [videoList[i], videoList[j]] = [videoList[j], videoList[i]];
            }

            // Distribute easter eggs along diagonal of the screen
            const spacing = Math.min(window.innerWidth, window.innerHeight) / videoList.length;
            const diagonalPositions = [];

            videoList.forEach((video, i) => {
                const a = document.createElement('a');
                a.href = video.url;
                a.target = "_blank"; // open in new tab
                a.id = "pyscript-hidden-easter-eggs";

                // Make link invisible but still clickable by fake cursor
                a.style.position = "absolute";
                a.style.opacity = "0";
                a.style.pointerEvents = "auto";
                a.style.zIndex = "9999";

                // Position each link on the diagonal
                const x = Math.floor(i * spacing);
                const y = Math.floor(i * spacing);

                a.style.left = `${x}px`;
                a.style.top = `${y}px`;

                // Add to DOM and keep track of coordinates
                document.body.appendChild(a);
                diagonalPositions.push([x, y]);
            });

            // Expose diagonal positions globally for PyScript wandering mode
            window.diagonalPositions = diagonalPositions;
        });
}

// Kick off the injection once the page is ready
injectWhenReady();
