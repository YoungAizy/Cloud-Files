import { uploadToDrive } from "./api.js";

//Create context menu for right clicks
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "cloud-save",
        title: "Cloud Save",
        contexts: ["link"]
    });
});

chrome.contextMenus.onClicked.addListener(
    (info, tab) => {

        if (info.menuItemId !== "cloud-save") return;
        
        let message;

        chrome.identity.getAuthToken(
            { interactive: false },
            (token)=>{
                if(chrome.runtime.lastError || !token){
                    message = "SHOW_LOGIN_POPUP";
                }else{
                    message = "SHOW_SAVE_POPUP";
                }

                chrome.tabs.sendMessage(
                    tab.id,
                    {
                        action: message,
                        url: info.linkUrl,
                        token
                    }
                );
            }
          );

    }
);

chrome.runtime.onMessage.addListener(
    async (msg, sender, sendResponse) =>{
        if(msg.action === "AUTHENTICATE"){
            authenticate(sendResponse);
            return true;
        }else if (msg.action === "DOWNLOAD"){
            const result = await uploadToDrive(msg.url, msg.filename, msg.token)
            sendResponse(result);
            return true;
        }
    }
)

function authenticate(sendResponse){
    chrome.identity.getAuthToken(
        { interactive: true },
        (token) => {
          if(token){
            sendResponse({token});
          }
        }
      );
}