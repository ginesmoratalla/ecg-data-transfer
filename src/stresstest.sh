#!/bin/bash

python3 database_writer.py &
writer_pid=$!

# Launch the broker process
python3 broker.py &
broker_pid=$!

# Launch client processes 
python3 client.py "ECG1" &
client1_pid=$! 
python3 client.py "ECG2" &
client2_pid=$!
python3 client.py "ECG3" &
client3_pid=$!
python3 client.py "ECG4" &
client4_pid=$!
python3 client.py "ECG5" &
client5_pid=$!
python3 client.py "ECG6" &
client6_pid=$!
python3 client.py "ECG7" &
client7_pid=$!
python3 client.py "ECG8" &
client8_pid=$!
python3 client.py "ECG9" &
client9_pid=$!
python3 client.py "ECG10" &
client10_pid=$!
python3 client.py "ECG11" &
client11_pid=$!
python3 client.py "ECG12" &
client12_pid=$!

# Launch client doctor processes
python3 doctor.py "ECG1" &
clientDoc_pid=$!
python3 doctor.py "ECG2" &
clientDoc2_pid=$!
python3 doctor.py "ECG3" &
clientDoc3_pid=$!
python3 doctor.py "ECG4" &
clientDoc4_pid=$!
python3 doctor.py "ECG5" &
clientDoc5_pid=$!
python3 doctor.py "ECG6" &
clientDoc6_pid=$!
python3 doctor.py "ECG7" &
clientDoc7_pid=$!

echo "Database Writer PID: $writer_pid"
echo "Broker PID: $broker_pid"
echo "Client 1 PID: $client1_pid"
echo "Client 2 PID: $client2_pid"
echo "Client 3 PID: $client3_pid"
echo "Client 4 PID: $client4_pid"
echo "Client 5 PID: $client5_pid"
echo "Client 6 PID: $client6_pid"
echo "Client 7 PID: $client7_pid"
echo "Client 8 PID: $client8_pid"
echo "Client 9 PID: $client9_pid"
echo "Client 10 PID: $client10_pid"
echo "Client 11 PID: $client11_pid"
echo "Client 12 PID: $client12_pid"
echo "Client Doctor 1 PID: $clientDoc_pid"
echo "Client Doctor 2 PID: $clientDoc2_pid"
echo "Client Doctor 3 PID: $clientDoc3_pid"
echo "Client Doctor 4 PID: $clientDoc4_pid"
echo "Client Doctor 5 PID: $clientDoc5_pid"
echo "Client Doctor 6 PID: $clientDoc6_pid"
echo "Client Doctor 7 PID: $clientDoc7_pid"

trap "kill -INT $broker_pid $client1_pid $client2_pid $clientDoc_pid $clientDoc2_pid $writer_pid; exit" EXIT

while true; do
  sleep 1 
done