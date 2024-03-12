#!/bin/bash

# Parse command-line arguments
num_clients=0
num_doctors=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clients)
      shift
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        num_clients=$1
      else
        echo "Error: Invalid number of clients provided."
        exit 1
      fi
      shift
      ;;
    --doctors)
      shift
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        num_doctors=$1
      else
        echo "Error: Invalid number of doctors provided."
        exit 1
      fi
      shift
      ;;
    -*)
      echo "Error: Unknown option '$1'."
      exit 1
      ;;
    *)
      echo "Error: Unexpected argument '$1'."
      exit 1
      ;;
  esac
done

# Launch database writer and broker
python3 database_writer.py &
writer_pid=$!

python3 broker.py &
broker_pid=$!

# Launch client processes
for (( i=1; i<=$num_clients; i++ )); do
  python3 client.py "ECG$i" &
  eval "client${i}_pid=\$!"  # Capture PID in a dynamic variable
done

# Launch doctor processes
for (( i=1; i<=$num_doctors; i++ )); do
  python3 doctor.py "ECG$i" &
  eval "clientDoc${i}_pid=\$!"  # Capture PID in a dynamic variable
done

# Print PIDs
echo "Database Writer PID: $writer_pid"
echo "Broker PID: $broker_pid"

for (( i=1; i<=$num_clients; i++ )); do
  eval "echo Client \${i} PID: \$${client${i}_pid}"
done

for (( i=1; i<=$num_doctors; i++ )); do
  eval "echo Client Doctor \${i} PID: \$${clientDoc${i}_pid}"
done

# Trap for clean exit
trap "kill -INT $broker_pid; for ((i=1; i<=$num_clients; i++)); do kill -INT \$${client${i}_pid}; done; for ((i=1; i<=$num_doctors; i++)); do kill -INT \$${clientDoc${i}_pid}; done; kill -INT $writer_pid; exit" EXIT

# Infinite Loop (Optional)
while true; do
  sleep 1 
done