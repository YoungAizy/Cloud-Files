

class HTTPXStreamIterator():
    """
    Wraps an HTTPX response byte-stream chunk
    """
    def __init__(self, remote_stream, queue):
        self.response = remote_stream
        self.queue = queue
        
    async def downloader(self, CHUNK_SIZE: int):
        buffer = bytearray()

        async for data in self.response.aiter_bytes(CHUNK_SIZE):
            buffer.extend(data)

            while len(buffer) >= min(CHUNK_SIZE, 1):
                chunk = bytes(buffer[:CHUNK_SIZE])
                del buffer[:CHUNK_SIZE]
                

                await self.queue.put(chunk)

        # Tell uploader there are no more chunks
        await self.queue.put(None)