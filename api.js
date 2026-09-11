async function uploadToDrive(url,filename,access_token){
    
        try {
            const body = {
                url, filename
            }
    
            const uploadResponse = await fetch('http://localhost:8000/downloads', {
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
            console.info('File uploaded successfully:', result);
            return result;
        } catch (error) {
            console.error('Error downloading file to Google Drive:', error);
            return {success: false, message: error}
        }
}