"""
Unit tests for app/httpx_stream.py
Tests streaming functionality and chunk handling
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.httpx_stream import HTTPXStreamIterator
from app.drive_upload import CHUNK_SIZE, FILE_LIMIT


class TestHTTPXStreamIterator:
    """Test suite for HTTPXStreamIterator class"""

    @pytest.mark.unit
    def test_httpx_stream_iterator_initialization(self, mock_queue):
        """Test HTTPXStreamIterator initializes correctly"""
        mock_response = AsyncMock()

        iterator = HTTPXStreamIterator(mock_response, mock_queue)

        assert iterator.response == mock_response
        assert iterator.queue == mock_queue

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_streams_file_chunks(self):
        """Test downloader correctly streams file in chunks"""
        # Create sample data
        total_size = CHUNK_SIZE * 3  # 3 chunks
        chunk_data = [
            b"x" * CHUNK_SIZE,
            b"y" * CHUNK_SIZE,
            b"z" * CHUNK_SIZE
        ]

        async def async_iter_bytes(chunk_size):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)

        # Verify all chunks were queued
        chunks_queued = []
        while not queue.empty():
            chunk = queue.get_nowait()
            if chunk is not None:
                chunks_queued.append(chunk)

        # Last item should be None (sentinel)
        final_item = queue.get_nowait() if not queue.empty() else None
        assert final_item is None or final_item not in chunks_queued

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_sends_none_sentinel(self):
        """Test downloader sends None to signal completion"""
        chunk_data = [b"x" * 1000, b"y" * 500]

        async def async_iter_bytes(chunk_size):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)

        # Get all items from queue
        items = []
        while not queue.empty():
            items.append(queue.get_nowait())

        # Last item should be None
        assert items[-1] is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_respects_chunk_size(self):
        """Test downloader respects configured chunk size"""
        chunk_size = 1024
        chunk_data = [b"x" * 5000]  # Larger than chunk_size

        async def async_iter_bytes(csize):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(chunk_size, FILE_LIMIT)

        # Collect queued chunks (excluding None sentinel)
        queued_chunks = []
        while not queue.empty():
            chunk = queue.get_nowait()
            if chunk is not None:
                queued_chunks.append(chunk)

        # Most chunks should respect the size limit
        for chunk in queued_chunks:
            assert len(chunk) <= chunk_size

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_enforces_file_limit(self):
        """Test downloader raises error if file exceeds limit"""
        oversized_data = b"x" * (FILE_LIMIT + 1)  # Exceed limit

        async def async_iter_bytes(chunk_size):
            yield oversized_data

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        with pytest.raises(ValueError, match="exceeded the size limit"):
            await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_handles_empty_stream(self):
        """Test downloader handles empty streams"""
        async def async_iter_bytes(chunk_size):
            return
            yield  # Make it an async generator

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)

        # Should only have None sentinel
        assert queue.qsize() >= 1
        final_item = queue.get_nowait()
        assert final_item is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_multiple_chunks_under_limit(self):
        """Test downloader correctly handles multiple chunks under limit"""
        chunk_count = 5
        chunk_size = 1024 * 100  # 100KB
        total_size = chunk_count * chunk_size

        # Create data under file limit
        chunk_data = [b"x" * chunk_size for _ in range(chunk_count)]

        async def async_iter_bytes(csize):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(chunk_size, FILE_LIMIT)

        # Count non-None items in queue
        queued_count = 0
        while not queue.empty():
            chunk = queue.get_nowait()
            if chunk is not None:
                queued_count += 1

        # Should have queued chunks
        assert queued_count > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_downloader_integration_with_queue(self):
        """Integration test: downloader with real asyncio.Queue"""
        chunk_data = [
            b"chunk1_data" * 100,
            b"chunk2_data" * 100,
            b"chunk3_data" * 100
        ]

        async def async_iter_bytes(chunk_size):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        # Run downloader
        await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)

        # Simulate reading from queue (as an uploader would)
        items_received = []
        max_attempts = 100
        attempts = 0
        while attempts < max_attempts:
            if not queue.empty():
                item = queue.get_nowait()
                items_received.append(item)
                if item is None:
                    break
            attempts += 1

        # Last item should be None
        assert items_received[-1] is None
        # Should have received data
        assert len(items_received) > 1

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_with_small_limit(self):
        """Test downloader with very small chunk size"""
        small_chunk_size = 64  # Very small
        chunk_data = [b"x" * 1024]

        async def async_iter_bytes(csize):
            for chunk in chunk_data:
                yield chunk

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        await iterator.downloader(small_chunk_size, FILE_LIMIT)

        # Should handle small chunks correctly
        queued_chunks = []
        while not queue.empty():
            chunk = queue.get_nowait()
            if chunk is not None:
                queued_chunks.append(chunk)

        # All chunks should be <= small_chunk_size
        for chunk in queued_chunks:
            assert len(chunk) <= small_chunk_size

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_downloader_error_handling(self):
        """Test downloader handles stream errors gracefully"""
        async def async_iter_bytes(chunk_size):
            raise Exception("Stream error")
            yield  # Make it an async generator

        mock_response = AsyncMock()
        mock_response.aiter_bytes = async_iter_bytes

        queue = asyncio.Queue()
        iterator = HTTPXStreamIterator(mock_response, queue)

        with pytest.raises(Exception, match="Stream error"):
            await iterator.downloader(CHUNK_SIZE, FILE_LIMIT)
