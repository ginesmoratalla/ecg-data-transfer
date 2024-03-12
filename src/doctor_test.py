import pytest
import asyncio
from websockets.legacy.protocol import WebSocketCommonProtocol
from unittest.mock import AsyncMock
from doctor import get_ws_message

@pytest.mark.asyncio
async def test_register_ecg_machine():
    mock_websocket = AsyncMock(spec=WebSocketCommonProtocol)
    mock_websocket.recv = AsyncMock(return_value='{"type": "ecg_machine", "id": "ECG1"}')
    response = await get_ws_message(mock_websocket)
    assert '{"type": "ecg_machine", "id": "ECG1"}' in response
    yield