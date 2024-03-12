# ECG Data WebSocket protocol

Coursework Project for **Computer Networks** university module.

Electrocardiogram-simulated data is sent through the network using WebSockets:
- **Client** sends a serialized message containing patient details (ecg data, height, weight...)
- **Broker** receives it and maps it to a doctor
- **Doctor** receives the message, deserializes it, and plots it into its simulator

## Developers
[Andrejs Bagdonas](github.com/Dreis27), [Gines Moratalla](github.com/ginesmoratalla) and [Juozas skarbalius](github.com/terahidro2003)

![screenshot](https://github.com/ginesmoratalla/ecg-websocket-protocol/assets/126341997/bef79b03-34fc-4d8f-bee7-a708f5045dcc)
