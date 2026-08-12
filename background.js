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
        console.log(".....")

        if (info.menuItemId !== "cloud-save") {
            return;
        }
        let message;
        console.log("Checking for auth token...");

        chrome.identity.getAuthToken(
            { interactive: false },
            (token)=>{
                console.info("token returned!");
                if(chrome.runtime.lastError || !token){
                    console.log("show login message", tab.id);
                    message = "SHOW_SAVE_POPUP";
                }
                else{
                    console.log("show save message", tab.id);
                    message = "SHOW_SAVE_POPUP";
                }

                chrome.tabs.sendMessage(
                    tab.id,
                    {
                        action: message,
                        url: info.linkUrl
                    }
                );
            }
          );

    }
);

chrome.runtime.onMessage.addListener(
    (msg, sender, sendResponse)=>{
        if(msg.action === "AUTHENTICATE"){
            authenticate(sendResponse);
            console.info("Done");
            return true;
        }
    }
)

function authenticate(sendResponse){
    chrome.identity.getAuthToken(
        { interactive: true },
        (token) => {
          if(token){
            console.info("TOKEN returned.")
            sendResponse(token);
          }
        }
      );
}