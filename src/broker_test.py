import pytest
import asyncio
from websockets.legacy.protocol import WebSocketCommonProtocol
from unittest.mock import AsyncMock
from broker import register, connected_ecg_machines, doctor_subscriptions, stop_loops


@pytest.fixture
async def server_setup_and_teardown():
    # reset server state
    connected_ecg_machines.clear()
    doctor_subscriptions.clear()

    yield  #run test

    # stop loops in server
    stop_loops()
    #await asyncio.sleep(0.1)

@pytest.mark.asyncio
# test for checking ecg machine registration 
async def test_register_ecg_machine(server_setup_and_teardown):
    # simulate mock websocket connection object receiving a message
    mock_websocket = AsyncMock(spec=WebSocketCommonProtocol)
    mock_websocket.recv = AsyncMock(return_value='{"type": "ecg_machine", "id": "ECG1"}')

    await register(mock_websocket)

    # check whether the ECG machine is properly registered in the broker
    assert "ECG1" in connected_ecg_machines
    assert connected_ecg_machines["ECG1"] == mock_websocket

@pytest.mark.asyncio
# test for checking doctor registration
async def test_register_doctor(server_setup_and_teardown):
    # simulate mock websocket connection object receiving a message
    mock_websocket = AsyncMock(spec=WebSocketCommonProtocol)
    mock_websocket.recv = AsyncMock(return_value='{"type": "doctor", "subscribe_to": "ECG1"}')

    await register(mock_websocket)

    # check whether the doctor is properly registered in the broker
    assert mock_websocket in doctor_subscriptions
    assert doctor_subscriptions[mock_websocket] == "ECG1"