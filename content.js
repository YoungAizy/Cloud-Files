chrome.runtime.onMessage.addListener(
    (message) => {

        if (message.action === "SHOW_LOGIN_POPUP") {
            loginUI(message.url);
        }
        else if (message.action === "SHOW_SAVE_POPUP") {
            showPopup(message.url, message.token);
        }
        else{
            console.log("Nothing....")
        }
    }
);

let cachedCSS = null;

async function loadStyles() {

    if(cachedCSS) return cachedCSS;

    const url = chrome.runtime.getURL(
        "notification.css"
    );

    const response = await fetch(url);
    cachedCSS = response.text();

    return cachedCSS;
}

async function createShadowContainer(html){
    const container = document.createElement("div");
    container.id = "drivedrop-host";

    container.style.zIndex = "2147483647";

    const css = await loadStyles();
    const shadow = container.attachShadow({mode: "open"});
    
    shadow.innerHTML = `
        <style>${css}</style>
        ${html}
    `;

    const removeContainer = () => container.remove();

    return {container, shadow, removeContainer};
}

async function loginUI(url){
    html = `
        <div class="popup">
            <div class="header">
            <span style="font-weight:600; text-transform: uppercase;">Drive-Drop</span>
                <button class="close-btn">X</button>
            </div>
            <p>Authenticate with your Google account to save files to Drive.</p>
            <button id="login-btn">Connect to G-drive</button>
        </div>
    `;

    const {container, shadow, removeContainer }= await createShadowContainer(html);
    
    shadow.querySelector(".close-btn").onclick = removeContainer;
    shadow.querySelector("#login-btn").onclick = () => {
        chrome.runtime.sendMessage(
            {action: "AUTHENTICATE"},
            response=>{
                chrome.storage.local.set({
                    auth: {
                      authenticated: true,
                    }
                  });
                  removeContainer();
                  showPopup(url,response.token);
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

async function showPopup(url, token) {
    const filename = getFilename(url);

    const templateUrl = chrome.runtime.getURL(
        "popup-template.html"
    );

    const html = await fetch(templateUrl)
        .then(response => response.text());

    const {container, shadow, removeContainer} = await createShadowContainer(html);

    shadow.querySelector("#filename").textContent = filename;

    shadow.querySelector(".close-btn").onclick = removeContainer;

    shadow.querySelector(".save-btn").onclick = async() => {
        removeContainer();
        await requestResponseUI(url, filename, token);
    };
        
    document.body.appendChild(container);
}

async function requestResponseUI(url, filename, token){
    html = `
        <div class="popup">
            <p id="popup-message">Requesting Download...</p>
            <div id="loader-wrapper" class="progress-container">
                <div class="progress-bar"></div>
            </div>
        </div>
    `;

    const {container, shadow, removeContainer} = await createShadowContainer(html);

    chrome.runtime.sendMessage(
        {action: "DOWNLOAD", url, filename, token},
            result=>{
                const message = shadow.querySelector("#popup-message");
                const loader = shadow.querySelector("#loader-wrapper");
                if(result.message){
                    message.textContent = result.message;
                    loader.classList.remove("progress-container");
                    loader.innerHTML = `
                        <button class="save-btn" id="close-button">Close</button>
                    `;
                
                    shadow.querySelector("#close-button").onclick = removeContainer;
                }
            }
    );

    document.body.appendChild(container);
}
