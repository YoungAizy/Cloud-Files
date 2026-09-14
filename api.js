import {CONFIG} from './config.js';

const BASE_URL = CONFIG.BACKEND_URL;

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
                throw new Error(`Upload failed: ${uploadResponse.statusText}`);
            }
    
            const result = await uploadResponse.json();
            return result;
        } catch (error) {
            return {success: false, message: error}
        }
}