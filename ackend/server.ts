#!/usr/bin/env ts

import * as net from 'net'

const PORT = 3000
const IP = '127.0.0.1'
const BACKLOG = 100
let socketCounter = 0

net.createServer()
  .listen(PORT, IP, BACKLOG)
  .on('connection', socket => {
    const socketId = socketCounter++;
    console.log(`[${socketId}] new connection from ${socket.remoteAddress}:${socket.remotePort} - assigning id '${socketId}'`)
    let requestCounter = 0;
    socket.on('data', buffer => {
      const requestId = requestCounter++;
      const request = buffer.toString()
      console.log(`[${socketId}] new data from socket - assigning id '${requestId}'`)
      const requestLines = request.split('\n')
      for (let i = 0; i < requestLines.length; i++) {
        console.log(`[${socketId}] [${requestId}] [${i}] ${requestLines[i]}`)
      }
    })
  })
