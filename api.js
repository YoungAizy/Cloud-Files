import {CONFIG} from './config.js';

const BASE_URL = CONFIG.REMOTE_BACKEND;

export async function uploadToDrive(url,filename,access_token){
        try {
            const body = JSON.stringify({
                url, filename
            });
    
            const uploadResponse = await fetch(`${BASE_URL}/downloads`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${access_token}`,
                    "Content-Type": "application/json"
                },
                body,
            });
    
            if (!uploadResponse.ok) {
                const error = new Error(`Upload failed: ${uploadResponse.statusText}`);
                error.status = uploadResponse.status;
                throw error;
            }
    
            const result = await uploadResponse.json();
            return result;
        } catch (error) {            
            let message;
            
            switch (error.status) {
                case 400:
                    message = "It appears your request didn't pass server validation. Could be a bad URL or Filename.";
                    break;
                case 401: 
                    message = "Session token expired, please sign-in with Google again.";
                    break;
                case 404:
                    message = "The endpoint called doesn't appear to exist.";
                    break;
                case 500:
                    message = "The server appears to be unreachable.";
                    break;
                default:
                    message = "Apologies, couldn't make the request. Something's wrong on our side.";
            } 
            
            return {success: false, message}
        }
}