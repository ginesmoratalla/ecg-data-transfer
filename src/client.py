'''
libraries to import for the file to run

may need to install some libraries that aren't present
in native Python
'''
import asyncio
import websockets
import json
import random
import sys
from collections import deque

'''
ecg_data_failed_queue

    - Define queue for failed packages and size
    - If packets cannot be sent for any reason, they
    will be queued

    - queued packets have priority over new generated packets, since the
    order of the packets sent is CRUCIAL
'''
# Max failed queue size
failed_queue_size = 100  
ecg_data_failed_queue = deque(maxlen=failed_queue_size)


'''
Defining variables for the specific ECG machine. This class is the simulation
of a real ECG Machine, therefore, it will create a random set of values as the ones seen
in a physical machine. These values will be randomized (heart rate) within a range,
so the look of this device will be simulated.

Variables:
    - id
    - seconds test flag for unit testing

ECG Simulated variables:
    - seconds (seconds passed after initalization) s
    - voltage (Heart rate voltage) mV

Patient information:
    - Health center / email
    - age
    - gender
    - weight
    - height
'''
ecg_machine_id = "ECG1"
try:
    if len(sys.argv[1]) > 1:
        ecg_machine_id = sys.argv[1]
except: 
    ecg_machine_id = "ECG1"  
ecg_id = ecg_machine_id
seconds = 0
seconds_test = 0
voltage = 0

# Patient information
health_center = "Klaipeda Hospital  -  klaipeda@gmail.com"
age = "21"
gender = "Masculine"
weight = "150 kg"
height = "1.47 m"


# reset global variables to plot
def reset():
    global seconds, voltage
    seconds = 0
    voltage = random.randint(-1, 4)

'''
update()

function will generate random values every time the machine pings
which is set up to be every 1 second.

The seconds variable will be increasing by 1 every time while the
voltage is always random value within a range
'''
def update():
    global seconds, voltage
    seconds += 1
    voltage = random.randint(-1, 4)

'''
Class to create a message to send through the WebSocket protocol

This message class will be serialized and deserialized through the process
in order to retreive its data to plot it in the graph from the end-node side
'''
class Message:
    def __init__(self, ecg_id, seconds, voltage, health_center, age, gender, weight, height):
        self.ecg_id = ecg_id
        self.seconds = seconds
        self.voltage = voltage

        self.health_center = health_center
        self.age = age
        self.gender = gender
        self.weight = weight
        self.height = height

    def to_json(self):
        return {
        "voltage": self.voltage,
        "seconds": self.seconds,
        "id": self.ecg_id,
        "health_center": self.health_center,
        "gender": self.gender,
        "age": self.age,
        "weight": self.weight,
        "height": self.height,
        }

'''
resend_failed_data()

    - Asynchronous function to queue data into a 'failed queue'
    - The function will try to send the previously queued data through the websocket connection
    and if it fails, it will queue the incoming package

send_data()

    - Asynchronous function that will send the serialized message with current ECG data
    and patient info through the WebSocket connection

    - If it fails, the packet should be queued into the failed queue
'''
async def resend_failed_data(websocket):

    # Try to send failed data through WebSocket first
    # Queue data again if it fails
    while ecg_data_failed_queue:
        data = ecg_data_failed_queue.popleft()

        # Try to send data popped
        try:
            await websocket.send(data)
            print("Cached data sent successfully.")

        # Re-queuing if exception
        except Exception as e:
            print(f"Failed to resend cached data, re-caching. Error: {e}")
            ecg_data_failed_queue.appendleft(data)
            break


async def send_data(websocket, data):

    try:
        await websocket.send(data)
        return True
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed error during send, caching data. Error: {e}")
        print("QUEUE SIZE:", len(ecg_data_failed_queue))
        return False
        
    except Exception as e:
        print(f"Unexpected error during send, caching data. Error: {e}")
        return False

'''
ecg_data()

Asynchronous function will do run whole ecg simulation
    - Connect to websocket
    - Serialize new packet containg new ECG data and patient information
    - Try to send packet though websocket connection
    - Queue data if failed sent
    - Sleep the asynchronous event simulating a data generation every time it sleeps 1 second
'''
async def ecg_data(stop_event=asyncio.Event()):

     # Global variables used across the file
    global ecg_data_failed_queue, seconds, seconds_test, voltage
    # Define WebSocket connection (ws://ip:port)
    uri = "ws://localhost:6789"
    
    # Run workflow indefinitely
    while True:
        try:

            # Attempt to connect to the server with the specified connection from above
            async with websockets.connect(uri) as websocket:

                if stop_event.is_set():
                    print("Stop event triggered")
                    break

                # send ECG Machine ID once
                await websocket.send(json.dumps({"type": "ecg_machine", "id": ecg_id}))

                # Flush queued data upon reconnection
                await resend_failed_data(websocket)
                
                # After flushing, continue with normal operation
                while not stop_event.is_set():

                    # generate data regardless of connection state
                    update()
                    message = Message(ecg_id, seconds, voltage, health_center, age, gender, weight, height)
                    serializedMessage = json.dumps(message.to_json())
                    
                    # Attempt to send data or queue if failed
                    send_success = await send_data(websocket, serializedMessage)

                    # Failed statement - queue data
                    if not send_success:
                        ecg_data_failed_queue.append(serializedMessage)
                        break

                    # Add counter to check for succesful sent connection (unit test checker)
                    else:
                        seconds_test += 1

                    # Simulate generating tasks every 1 second  
                    await asyncio.sleep(1)

                # Check stop_event immediately after inner loop breaks
                if stop_event.is_set():
                    print("Stop event triggered")
                    break


        except websockets.exceptions.ConnectionClosedError as e:

            print(f"Connection closed, caching data. Will attempt to reconnect. Error: {e}")
            update()
            # Queue the current data if connection is lost
            message = Message(ecg_id, seconds, voltage, health_center, age, gender, weight, height)
            serializedMessage = json.dumps(message.to_json())
            ecg_data_failed_queue.append(serializedMessage)
            print("QUEUE SIZE:", len(ecg_data_failed_queue))

            #  Check the stop_event after handling errors
            if stop_event.is_set():
                break

            # Simulate generating tasks every 1 second 
            await asyncio.sleep(1)
            
        except Exception as e:

            print(f"Failed to connect or send data, caching data. Will attempt to reconnect. Error: {e}")
            update()
            # Queue the current data on unexpected exception error
            message =  Message(ecg_id, seconds, voltage, health_center, age, gender, weight, height)
            serializedMessage = json.dumps(message.to_json())
            ecg_data_failed_queue.append(serializedMessage)
            print("QUEUE SIZE:", len(ecg_data_failed_queue))

            #  Check the stop_event after handling errors
            if stop_event.is_set():
                break

            # Simulate generating tasks every 1 second 
            await asyncio.sleep(1)


# Main execution - block to avoid direct undesired execution of file from other files
if __name__ == "__main__":
    # code here will only run when the file is executed
    asyncio.get_event_loop().run_until_complete(ecg_data())