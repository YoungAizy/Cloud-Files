chrome.runtime.onMessage.addListener(
    (message) => {
        console.info("message received:", message.action)

        if (message.action === "SHOW_LOGIN_POPUP") {
            console.log("logiing in...")
            loginUI();
        }
        else if (message.action === "SHOW_SAVE_POPUP") {
            console.log("Saving...")
            showPopup(message.url);
        }
        else{
            console.log("Nothing....")
        }
    }
);

async function loadStyles() {
    const url = chrome.runtime.getURL(
        "notification.css"
    );

    const response = await fetch(url);

    return response.text();
}

function createShadowContainer(){
    const container = document.createElement("div");
    container.id = "drivedrop-host";

    container.style.position = "fixed";
    container.style.top = "20px";
    container.style.right = "20px";
    container.style.zIndex = "2147483647";

    return container;
}

async function loginUI(){
    console.log("Hellooooo");
    const container = document.createElement("div");
    container.id = "drivedrop-host";

    container.style.position = "fixed";
    container.style.top = "20px";
    container.style.right = "20px";
    container.style.zIndex = "2147483647";
    // my styles
    container.style.backgroundColor = "whitesmoke";
    container.style.borderRadius = 12;
    container.style.padding = 16;
    html = `
        <div class="popup">
            <div class="close-wrapper">
                <span class="close-btn">X</span>
            </div>
            <p>Authenticate with your Google account to save files to Drive.</p>
            <button id="login-btn">Connect to G-drive</button>
        </div>
    `;
    const css = await loadStyles();
    const shadow = container.attachShadow({
        mode: "open"
    });
    
    shadow.innerHTML = `
        <style>${css}</style>
        ${html}
    `;
    // const popup = container.firstElementChild;
    shadow.querySelector(".close-btn").onclick = () => container.remove();
    shadow.querySelector("#login-btn").onclick = () => {
        chrome.runtime.sendMessage(
            {action: "AUTHENTICATE"},
            response=>{
                chrome.storage.local.set({
                    auth: {
                      authenticated: true,
                      email: "saunmkhize30@gmail.com"
                    }
                  });
                  container.remove();
            }
        )
    };
    document.body.appendChild(container);
    

}

function getFilename(url) {

    try {

        return new URL(url)
            .pathname
            .split("/")
            .pop() || "download";

    } catch {

        return "download";
    }
}

async function showPopup(url) {
    console.log("popup template loading...")

    const filename = getFilename(url);

    const templateUrl = chrome.runtime.getURL(
        "popup-template.html"
    );

    const html = await fetch(templateUrl)
        .then(response => response.text());

    console.info("LOADED HTML", html);

    const css = await loadStyles();
    const popupContainer = createShadowContainer();
    const popup = popupContainer.attachShadow({
        mode: "open"
    });
    
    popup.innerHTML = `
        <style>${css}</style>
        ${html}
    `;

    // const popup =
    //     container.firstElementChild;

    popup.querySelector(
        "#filename"
    ).textContent = filename;

    popup.querySelector(".close-btn")
        .onclick = () => popup.remove();

    popup.querySelector(".save-btn")
        .onclick = () => {
            uploadToDrive(url, filename, popup);
        };
        
    document.body.appendChild(popupContainer);
}