'''
libraries to import for the file to run

may need to install some libraries that aren't present
in native Python
'''
import asyncio
import websockets
import json
import numpy as np
import xmlrpc.client
import sys
from threading import Thread

import pyqtgraph as pg
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QObject

import email_gui

# Flag to add Patient information to the graph only once
label_flag = False

client = xmlrpc.client.ServerProxy("http://localhost:8899")

'''
reset()

Function to initialize the arrays
that will act as x and y axis for the ECG Diagram plot
'''
def reset():

    global x, y
    x = np.array([0])
    y = np.array([0])

async def retrieve_cache_from_db(ecg_id):
    json_data_req = json.loads('{"ecg": "{ecg_id}"}')
    json_data_req["ecg"] = ecg_id
    json_string = json.dumps(json_data_req)
    cache_result = client.process_request("RETRIEVE_DOCTOR_CACHE", json_string)

    json_strings = [item[0] for item in cache_result]

    # Remove the extra escape characters (optional)
    clean_json_strings = [s.replace("\\", "") for s in json_strings]  # Optional step

    # Convert each JSON string to a dictionary
    data_dicts = [json.loads(s) for s in clean_json_strings]    

    return data_dicts

async def draw_point_on_graph(obj, point):
    obj.signal_holder.data_received.emit(point)

async def get_ws_message(ws):
    message = await ws.recv()
    return message

async def await_for_ws_message(uri, ecg_id, obj):
    try:
        async with websockets.connect(uri) as websocket:
            # Code block for the first connection with server
            # Only executed at the beginning, to recognize ECG machine
            await websocket.send(json.dumps({"type": "doctor", "subscribe_to": ecg_id}))
            print(f"Subscribed to ECG data from {ecg_id}")

            # Run indefinitely
            it = 0
            while True:
                message = await get_ws_message(websocket)
                messageReceived = json.loads(message)
                if messageReceived["seconds"] < 1 and it == 0:
                    reset()

                print(f"Received ECG data: {messageReceived}")
                await draw_point_on_graph(obj, messageReceived)
                it = it + 1

    except Exception as e:
        # Wait for 5 seconds before trying to reconnect
        print(f"Connection lost, attempting to reconnect in 5 seconds. Error: {e}")
        await asyncio.sleep(5)  

'''
Main classes


1. Message class:
    Class that encapsulates the data from the serialized
    JSON object comming from the broker

    from_json(): converts the sent JSON object into a 'Message'

2. SignalHolder class:
    Subclass of QObject used to hold a signal and emitting
    it when data is received (implementation on ADD LINE ADD LINE) 

3. WebSocketListener class:
    Subclass of QThread, implemented to manage threads and asynchronous
    functions. The main receiving code will be handled in listen_for_ecg_data()
    function within the class
'''

class Message:

    def __init__(self, seconds, voltage, health_center, age, gender, weight, height):
        # Message parameters
        self.seconds = seconds
        self.voltage = voltage

        self.health_center = health_center
        self.age = age
        self.gender = gender
        self.weight = weight
        self.height = height

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return cls(**data)   


class SignalHolder(QObject):
    data_received = pyqtSignal(dict)


class WebSocketListener(QThread):

    def __init__(self, signal_holder, ecg_id):
        super().__init__()
        self.signal_holder = signal_holder
        self.ecg_id = ecg_id
        self.is_running = True

    '''
        function listen_for_ecg_data():
            - Asynchronous function that listens to data from ECG broker.
            - Creates WebSocket connection with websockets library (works alongside async functions)
            - Waits indefinitely for broker message, retries if connection not succesful
            - If successful, deserializes message and sends it to plot in the graph
    '''

    async def listen_for_ecg_data(self):

        # Calls to initialize the ECG graph
        global label_flag
        reset()

        # fill the graph with cached data from db
        cache_data = await retrieve_cache_from_db(self.ecg_id)
        for x in cache_data:
            self.signal_holder.data_received.emit(x)

        # WebSocket code (ws://ip:port) 
        uri = "ws://localhost:6789"
        # try to reconnect as long as is_running is True
        while self.is_running:
            await await_for_ws_message(uri, self.ecg_id, self)

    '''
    run(self)
    
        - function to create an asynchronous event loop.
        - The event loop will execute listen_to_ecg_data function
        - Event loop helps to run different parts of the code asynchronously (listen_ecg and plotting the ecg graph)
    '''
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.listen_for_ecg_data())
        loop.close()

    # Function to stop the infinite loop to receive messages
    def stop(self):
        self.is_running = False


'''
Code related to the GUI for the ECG Diagram window:

This will set a pyqt window with the necessary data, including
the graph and a section to write patient information below

ECG Data graph:
    x axis = time (seconds passed)
    y axis = voltage (mV) to measure heart rate
'''
app = pg.mkQApp()
main_window = QMainWindow()
main_window.setWindowTitle('Electrocardiogram Data')
central_widget = QWidget()
main_window.setCentralWidget(central_widget)

layout = QVBoxLayout()
central_widget.setLayout(layout)

plotwidget = pg.PlotWidget()
plotwidget.setTitle('ECG Graph')
plotwidget.setMouseEnabled(x=False, y=False)

# Define range of data for ECG Diagram
# Voltage typically ranges from -1 to 4 mV
plotwidget.setYRange(-2, 5)
curve = plotwidget.plot(pen='red')

# GUI axis details
plotwidget.setLabel('left', 'Voltage (mV)')
plotwidget.setLabel('bottom', 'Time (Seconds)')
layout.addWidget(plotwidget)

# Create widget for patient information (weight, height...)
patient_info_widget = QWidget()
patient_info_layout = QVBoxLayout()
patient_info_widget.setLayout(patient_info_layout)
layout.addWidget(patient_info_widget)


'''
update(message)

Function that will append the ECG data every
time it is sent from broker

If label_flag global bool is set to true,
it will also add the patients information to the lower part
of the graph window
'''
def update(message):
    global x, y, label_flag

    # Add patient info
    if not label_flag:

        labels = [
        'Health Center: ' + message["health_center"],
        'Age: ' + message["age"],
        'Gender: ' + message["gender"],
        'Weight: ' + message["weight"],
        'Height: ' + message["height"]
        ]

        for label_text in labels:
            label = QLabel(label_text)
            patient_info_layout.addWidget(label)

        label_flag = True
        
    # Append new ECG data to the graph from the deserialized JSON object
    x = np.append(x, message["seconds"]) 
    y = np.append(y, message["voltage"])
    curve.setData(x, y)



'''
Instantiate the classes declared above to run the WebSocket connection and plot the graph at the same time

    - signal_holder: emits a signal when called
    - listener: create WebSocket class to listen to broker and emit signal_holder when executed
    - call update function (to plot the graph with new data) when the signal is emitted
'''
signal_holder = SignalHolder()
ecg_machine_id = "ECG1"
try:
    if len(sys.argv[1]) > 1:
        ecg_machine_id = sys.argv[1]
except: 
    ecg_machine_id = "ECG1"       
listener = WebSocketListener(signal_holder, ecg_machine_id)
signal_holder.data_received.connect(update)
listener.start()


'''
This part of the code is where the graph defined
above is set to a certain size and executed
'''
main_window.setGeometry(100, 100, 1000, 600)
main_window.show()
app.exec_()