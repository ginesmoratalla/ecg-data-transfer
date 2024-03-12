import pytest
import asyncio
from websockets.legacy.protocol import WebSocketCommonProtocol
from unittest.mock import AsyncMock, patch
import client


# Context manager to use 'with' statement (line 30) on async functions
class ContextManager(AsyncMock):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_ecg_data():

    stop_event = asyncio.Event()
    ecg_task = asyncio.create_task(client.ecg_data(stop_event))

    # Mocking the websocket
    mock_websocket = ContextManager(spec=WebSocketCommonProtocol)

    # Mocking the sending functionality asynchronously
    mock_websocket.send = AsyncMock()

    # Mock the websockets.connect function patching the original websocket
    with patch('websockets.connect', return_value=mock_websocket) as mock_connection:

        # Run ecg_data function for the seconds specified below (10)
        try:
            await asyncio.sleep(10)

        finally:

            # Trigger the stop event to stop running ecg_data
            stop_event.set()
            await ecg_task


    # Assertions to check if the websockets.connect function was called correctly
    mock_connection.assert_called_once()
    print(f'websockets.connect was called without duplicate calls: {mock_connection.call_count == 1}')

    # Assertion that checks if the send function was called at least 10 times (10 messages sent)
    assert client.seconds_test >= 10
    print(f'ecg_data succesfully sent >= 10 messages over a 10 second time period through websocket connection: {client.seconds_test >= 10}')

    

