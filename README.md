# Misclick <img src="browser_extension/static/misclick_with_mouse_transparent.png" alt="Misclick Logo" width="80" align="right"/>

<p align="center">
  <img src="mobile_page/static/mouse_pointer.png" alt="Mouse Pointer"/>
</p>
<p align="center">"<b>Wrong mouse, for a reason</b>"</p>
<p align="center">
  <!-- Stars -->
  <img src="https://img.shields.io/github/stars/SOORAJTS2001/daring-daffodils?style=for-the-badge" alt="GitHub Stars"/>

  <!-- Forks -->
  <img src="https://img.shields.io/github/forks/SOORAJTS2001/daring-daffodils?style=for-the-badge" alt="GitHub Forks"/>

  <!-- Issues -->
  <img src="https://img.shields.io/github/issues/SOORAJTS2001/daring-daffodils?style=for-the-badge" alt="GitHub Issues"/>

  <!-- License -->
  <img src="https://img.shields.io/github/license/SOORAJTS2001/daring-daffodils?style=for-the-badge" alt="GitHub License"/>
</p>
Sure, you have a perfectly good keyboard and mouse… but why not run Python in your browser with a mobile?
What about doing a scroll, drag and maybe a click or that's all ?

That is Misclick - A way to control your mouse, **but in opposite way**

---

## 📑 Table of Contents

- [What can it do](#-what-can-it-do)
- [Installation](#-installation)
- [Working](#-working)
- [Limitations](#-limitations)
- [Contributors--Contribution](#-contributors--contribution)

---

## What can it do ?

- Oh, just casually pair your phone with your browser over WebSocket — because Bluetooth and USB are *too mainstream*.
- Control your browser’s mouse with your phone, but in reverse. Yes, swipe left to go right. Because logic is overrated.
    - What’s on the menu?
        - Swipe left, swipe right — like Tinder, but for your cursor.
        - Swipe up or swipe down.
        - Click links and sections — basically what your mouse already does, but now slower and more annoying.
        - Scroll up, scroll down — congratulations, you’ve invented scrolling.
- Feeling idle? Don’t worry, the mouse entertains itself with *modes*:
    - **Wander Mode** – your cursor takes itself on a joyride. You’re just a spectator.
    - **Rage Mode** – because why not double the speed and lose control even faster?
    - **Shadow Mode** – cursor goes invisible. Perfect for when you *really* want to rage-quit.
    - Sometimes you get all of them combined, so best of luck.
    - Bonus: it randomly clicks on stuff, so enjoy your surprise shopping carts and unexpected **easter eggs**.
    - If you get redirected to another page, don’t worry — the chaos restarts automatically.
- **Drag text from your browser and send it to your phone. Groundbreaking. Nobel-worthy.**
- Install it as a browser extension, and enjoy the privilege of also opening a webpage on your phone. Wow.
- Cross-platform. Yes, it works everywhere, so nobody is safe.
- Runs locally, no hosting, no leaks — except your sanity.
- No accounts, no personal info — because who would *willingly* sign up for this anyway?

---

## ⚙️ Installation

### Prerequisites

- Python 3.12+
- A modern web browser (Chrome recommended)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/SOORAJTS2001/daring-daffodils
   cd daring-daffodils
2. Installing Extension
    1. Open [chrome://extensions/](chrome://extensions/) and enable **Developer mode** as shown below:

   ![Enable Developer Mode](./documentation/browser_developer_mode.png)
    2. Click Load unpacked button and select
       the [browser_extension](https://github.com/SOORAJTS2001/daring-daffodils/tree/main/browser_extension) folder
       inside
       the **cloned repo**
       ![Enable Developer Mode](./documentation/load_unpacked_button.png)
3. Starting up server — **Make sure your PC/Laptop and phone are connected via the same WiFi**

    1. Using [Makefile](https://en.wikipedia.org/wiki/Make_(software))
        1. Just run the command:
           ```bash
           make
           ```  
           inside the root directory, where the `Makefile` is located.
    2. Manual setup
        1. Create your environment:
           ```bash
           python3 -m venv .env
           ```  
        2. Activate it:
           ```bash
           source .env/bin/activate
           ```  
        3. Install Poetry:
           ```bash
           pip install poetry
           ```  
        4. Install dependencies:
           ```bash
           poetry install
           ```  
        5. Start the server
           ```bash
           python3 app.py
           ```
    3. After the server starts, it will show you a QR code. [Open that with your phone](https://www.android.com/articles/how-do-you-scan-qr-codes-on-android/)
         <p align="center">
          <img src="documentation/server_qr_code.png" alt="Mouse Pointer"/>
         </p>
