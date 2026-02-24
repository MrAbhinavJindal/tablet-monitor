package com.tabletmonitor

import android.graphics.Bitmap
import android.media.MediaCodec
import android.media.MediaFormat
import android.os.Bundle
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
    }
    
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {}
    
    override fun surfaceDestroyed(holder: SurfaceHolder) {
        surface = null
    }
    
    private suspend fun connectAndStream() {
        try {
            // Connect to video stream
            videoSocket = Socket("localhost", 8888)
            touchSocket = Socket("localhost", 8889)
            
            val input = DataInputStream(videoSocket?.getInputStream())
            screenWidth = input.readInt()
            screenHeight = input.readInt()
            
            // Setup H.264 decoder with proper configuration
            decoder = MediaCodec.createDecoderByType("video/avc")
            val format = MediaFormat.createVideoFormat("video/avc", screenWidth, screenHeight).apply {
                setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, 1024 * 1024)
                setInteger(MediaFormat.KEY_LOW_LATENCY, 1)
            }
            decoder?.configure(format, surface, null, 0)
            decoder?.start()
            
            val nalBuffer = mutableListOf<Byte>()
            
            while (isActive && surface != null) {
                try {
                    val chunkSize = input.readInt()
                    val h264Data = ByteArray(chunkSize)
                    input.readFully(h264Data)
                    
                    // Add to NAL buffer
                    nalBuffer.addAll(h264Data.toList())
                    
                    // Process complete NAL units
                    processNalUnits(nalBuffer)
                    
                } catch (e: Exception) {
                    e.printStackTrace()
                    break
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    private fun processNalUnits(nalBuffer: MutableList<Byte>) {
        val nalArray = nalBuffer.toByteArray()
        
        decoder?.let { codec ->
            val inputBufferIndex = codec.dequeueInputBuffer(10000)
            if (inputBufferIndex >= 0) {
                val inputBuffer = codec.getInputBuffer(inputBufferIndex)
                inputBuffer?.clear()
                inputBuffer?.put(nalArray)
                codec.queueInputBuffer(inputBufferIndex, 0, nalArray.size, 0, 0)
                nalBuffer.clear()
            }
            
            val info = MediaCodec.BufferInfo()
            var outputBufferIndex = codec.dequeueOutputBuffer(info, 0)
            while (outputBufferIndex >= 0) {
                codec.releaseOutputBuffer(outputBufferIndex, true)
                outputBufferIndex = codec.dequeueOutputBuffer(info, 0)
            }
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
                e.printStackTrace()
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
