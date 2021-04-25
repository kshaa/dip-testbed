# IoT Frisbee

Attach sensor microcontrollers to a frisbee, track throw performance, off-load data to centralized server, review in an app.  

## Concept
- We attach a tiny, re-chargable, sensing, short-distance networked [mote](https://en.wikipedia.org/wiki/Sensor_node) (sensor node) to a `frisbee` or more likely a disk golf disk  
- We attach a bulkier, wire powered (or re-chargable), internet-connected mote (sensor node) to a disk golf `basket`  
- We throw the disk golf forward multiple times and it records sensor metrics  
- The disk golf at some point gets thrown into a disk golf `basket` at which point the `frisbee` or disk mote off-loads all metrics to the `basket`  
- The `basket` then sends all the received `frisbee` metrics to a cloud-hosted `broker`
- A `backend` server reactively gets notified by `broker` of the new `basket`/`frisbee` metrics and stores the information in `database`  
- If some `app` was currently connected to the `backend` (most likely w/ WebSockets), it gets notified of the changes  
- The `app` can of course check historical data through `backend`, which will be fetched from `database`  

## Hardware
- `frisbee` is an [Adafruit Feather nRF52 Bluefruit LE](https://www.adafruit.com/product/3406) board with an [Adafruit LSM6DSOX + LIS3MDL FeatherWing](https://www.adafruit.com/product/4565) sensor node  
- `basket` is a [Raspberry Pi 4 Model B](https://raspberrypi.dk/en/product/raspberry-pi-4-model-b-8-gb/?src=raspberrypi&wcmlc=EUR)  

## Structure
- `database` - PostgreSQL database. Contains storage for `backend`  
- `broker` - RabbitMQ message broker. Receives `basket` messages  
- `backend` - Scala Play server. Listens to `broker` for `basket` messages. Stores info in `database`. Notifies info to `app`  
- `app` - Flutter application. Provides system interactivity to user. Listens `backend` for info
- `basket` - Rust microcontroller firmware. Receives `frisbee` messages. Sends to `broker`  
- `frisbee` - C++ microcontroller firmware. Interacts w/ external `sensors` lib. Intermittently sends to `basket`  
