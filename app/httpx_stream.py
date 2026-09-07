

class HTTPXStreamIterator():
    """
    Wraps an HTTPX response byte-stream chunk
    """
    def __init__(self, remote_stream, queue):
        self.response = remote_stream
        self.queue = queue
        
    async def downloader(self, CHUNK_SIZE: int, LIMIT: int):
        buffer = bytearray()
        downloaded = 0

        async for data in self.response.aiter_bytes(CHUNK_SIZE):
            buffer.extend(data)
            downloaded += len(data)
            
            if downloaded > LIMIT:
                raise ValueError("File exceeded the size limit of 1GB while streaming.")
            
            while len(buffer) >= min(CHUNK_SIZE, 1):
                chunk = bytes(buffer[:CHUNK_SIZE])
                del buffer[:CHUNK_SIZE]
                

                await self.queue.put(chunk)

        # Tell uploader there are no more chunks
        await self.queue.put(None)