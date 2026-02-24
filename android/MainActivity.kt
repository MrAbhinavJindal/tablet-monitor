package com.tabletmonitor

import android.media.MediaCodec
import android.media.MediaFormat
import android.os.Bundle
import android.util.Log
import android.view.MotionEvent
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import java.io.DataInputStream
import java.net.Socket
import java.nio.ByteBuffer

class MainActivity : AppCompatActivity(), SurfaceHolder.Callback {
    private lateinit var surfaceView: SurfaceView
    private var videoSocket: Socket? = null
    private var touchSocket: Socket? = null
    private var decoder: MediaCodec? = null
    private var surface: Surface? = null
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var screenWidth = 0
    private var screenHeight = 0
    private var spsReceived = false
    private var ppsReceived = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        surfaceView = findViewById(R.id.surfaceView)
        surfaceView.holder.addCallback(this)
        
        scope.launch {
            connectAndStream()
        }
    }
    
    override fun surfaceCreated(holder: SurfaceHolder) {
        surface = holder.surface
        Log.d("MainActivity", "Surface created")
    }
    
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        Log.d("MainActivity", "Surface changed: ${width}x${height}")
    }
    
    override fun surfaceDestroyed(holder: SurfaceHolder) {
        surface = null
        Log.d("MainActivity", "Surface destroyed")
    }
    
    private suspend fun connectAndStream() {
        try {
            Log.d("MainActivity", "Connecting to server...")
            videoSocket = Socket("localhost", 8888)
            touchSocket = Socket("localhost", 8889)
            
            val input = DataInputStream(videoSocket?.getInputStream())
            screenWidth = input.readInt()
            screenHeight = input.readInt()
            Log.d("MainActivity", "Screen size: ${screenWidth}x${screenHeight}")
            
            // Wait for surface to be ready
            while (surface == null) {
                delay(100)
            }
            
            // Setup H.264 decoder with comprehensive configuration
            decoder = MediaCodec.createDecoderByType("video/avc")
            val format = MediaFormat.createVideoFormat("video/avc", screenWidth, screenHeight).apply {
                setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, 2 * 1024 * 1024) // 2MB buffer
                setInteger(MediaFormat.KEY_LOW_LATENCY, 1)
                setInteger(MediaFormat.KEY_PRIORITY, 0) // Realtime priority
            }
            
            decoder?.configure(format, surface, null, 0)
            decoder?.start()
            Log.d("MainActivity", "MediaCodec decoder started")
            
            while (isActive && surface != null) {
                try {
                    val chunkSize = input.readInt()
                    val h264Data = ByteArray(chunkSize)
                    input.readFully(h264Data)
                    
                    // Check NAL unit type
                    if (h264Data.size >= 5 && h264Data[0] == 0x00.toByte() && 
                        h264Data[1] == 0x00.toByte() && h264Data[2] == 0x00.toByte() && 
                        h264Data[3] == 0x01.toByte()) {
                        
                        val nalType = h264Data[4].toInt() and 0x1F
                        Log.d("MainActivity", "NAL unit type: $nalType, size: $chunkSize")
                        
                        when (nalType) {
                            7 -> { // SPS
                                spsReceived = true
                                Log.d("MainActivity", "SPS received")
                            }
                            8 -> { // PPS
                                ppsReceived = true
                                Log.d("MainActivity", "PPS received")
                            }
                            5 -> { // IDR frame
                                Log.d("MainActivity", "IDR frame received")
                            }
                            1 -> { // P frame
                                Log.d("MainActivity", "P frame received")
                            }
                        }
                        
                        // Feed to decoder
                        decoder?.let { codec ->
                            val inputBufferIndex = codec.dequeueInputBuffer(10000)
                            if (inputBufferIndex >= 0) {
                                val inputBuffer = codec.getInputBuffer(inputBufferIndex)
                                inputBuffer?.clear()
                                inputBuffer?.put(h264Data)
                                
                                val flags = if (nalType == 5) MediaCodec.BUFFER_FLAG_KEY_FRAME else 0
                                codec.queueInputBuffer(inputBufferIndex, 0, h264Data.size, 0, flags)
                                
                                // Process output
                                val info = MediaCodec.BufferInfo()
                                var outputBufferIndex = codec.dequeueOutputBuffer(info, 0)
                                while (outputBufferIndex >= 0) {
                                    codec.releaseOutputBuffer(outputBufferIndex, true)
                                    outputBufferIndex = codec.dequeueOutputBuffer(info, 0)
                                }
                            } else {
                                Log.w("MainActivity", "No input buffer available")
                            }
                        }
                    }
                } catch (e: Exception) {
                    Log.e("MainActivity", "Error processing H.264 data", e)
                    break
                }
            }
        } catch (e: Exception) {
            Log.e("MainActivity", "Connection error", e)
        }
    }
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        val action = when (event.action) {
            MotionEvent.ACTION_DOWN -> "DOWN"
            MotionEvent.ACTION_MOVE -> "MOVE"
            MotionEvent.ACTION_UP -> "UP"
            else -> return super.onTouchEvent(event)
        }
        
        scope.launch {
            try {
                val scaleX = screenWidth.toFloat() / surfaceView.width
                val scaleY = screenHeight.toFloat() / surfaceView.height
                val x = event.x * scaleX
                val y = event.y * scaleY
                
                val msg = "$action $x $y\n"
                touchSocket?.getOutputStream()?.write(msg.toByteArray())
                touchSocket?.getInputStream()?.read()
            } catch (e: Exception) {
                Log.e("MainActivity", "Touch error", e)
            }
        }
        return true
    }
    
    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
        decoder?.stop()
        decoder?.release()
        videoSocket?.close()
        touchSocket?.close()
    }
}
