import asyncio
import websockets
import json
import xmlrpc.client

connected_clients = set()
connected_ecg_machines = {}  #ECG machine IDs
doctor_subscriptions = {}  # maps doctors to ECG machines IDs they're subscribed to
centralized_queue = asyncio.Queue()
ecg_machine_dlqs = {}  # separate dql for any ECG machine that connects
shutdown = asyncio.Event()

client = xmlrpc.client.ServerProxy("http://localhost:8899")

async def register(websocket):
    connected_clients.add(websocket)
    init_message = await websocket.recv()
    deserialized_init_message = json.loads(init_message)
    
    if deserialized_init_message.get("type") == "ecg_machine":

        ecg_id = deserialized_init_message["id"]
        connected_ecg_machines[ecg_id] = websocket
        ecg_machine_dlqs[ecg_id] = asyncio.Queue()  # create dql
        print(f"ECG Machine {ecg_id} registered.")
    
    elif deserialized_init_message.get("type") == "doctor":
        doctor_subscriptions[websocket] = deserialized_init_message["subscribe_to"]
        print(f"Doctor subscribed to ECG Machine {deserialized_init_message['subscribe_to']}.")
        #await flush_dlq_to_doctor(deserialized_init_message["subscribe_to"], websocket)

# handle incoming messages
async def consumer_handler(websocket):
    async for message in websocket:
        await centralized_queue.put(json.loads(message))
        client.process_request("WRITE_MSG", message)

# distribute incoming messages (from ecg machines) to doctors/dlqs
async def centralized_message_processor(): 
    while not shutdown.is_set():
        message = await centralized_queue.get()
        await process_message(message)

# process incoming messages (from ecg machines) to doctors/dlqs
async def process_message(message):
    ecg_id = message.get("id")
    if ecg_id in doctor_subscriptions.values():
        for doctor_ws, subscribed_ecg_id in doctor_subscriptions.items():
            if subscribed_ecg_id == ecg_id:
                try:
                    await doctor_ws.send(json.dumps(message))
                except websockets.ConnectionClosed:
                    await ecg_machine_dlqs[ecg_id].put(message)
    else:
        await ecg_machine_dlqs[ecg_id].put(message)
    for ecg_id, dlq in ecg_machine_dlqs.items():
        print(f"DLQ Size for ECG Machine {ecg_id}: {dlq.qsize()}")

# process messages from dqls
async def start_dlq_processor(ecg_id):
    while not shutdown.is_set():
        message = await ecg_machine_dlqs[ecg_id].get()
        print(f"DLQ message for ECG Machine {ecg_id}: {message}")

async def handler(websocket, path):
    await register(websocket)
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    try:
        await consumer_task
    except websockets.ConnectionClosed:
        print("A connection was closed.")
        connected_clients.remove(websocket)
        if websocket in doctor_subscriptions:
            del doctor_subscriptions[websocket]
            print("Removed a doctor subscription.")

# send all messages from a specific dlq to respective doctor
async def flush_dlq_to_doctor(ecg_id, doctor_websocket):
    if ecg_id in ecg_machine_dlqs:
        dlq = ecg_machine_dlqs[ecg_id]
        while not dlq.empty():
            message = await dlq.get()
            try:
                await doctor_websocket.send(json.dumps(message))
                print(f"Flushed DLQ message to doctor: {message}")
            except websockets.ConnectionClosed as e:
                print(f"Doctor client terminated while sending DLQ message. Error: {e}")
                break 

def stop_loops():
    shutdown.set()

async def main():
    async with websockets.serve(handler, "localhost", 6789):
        await asyncio.gather(
            centralized_message_processor(),
            *(start_dlq_processor(ecg_id) for ecg_id in ecg_machine_dlqs)
        )

if __name__ == "__main__":
    asyncio.run(main())