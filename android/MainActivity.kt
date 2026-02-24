package com.tabletmonitor

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
            videoSocket = Socket("localhost", 8888)
            touchSocket = Socket("localhost", 8889)
            
            val input = DataInputStream(videoSocket?.getInputStream())
            screenWidth = input.readInt()
            screenHeight = input.readInt()
            
            // Wait for surface to be ready
            while (surface == null) {
                delay(100)
            }
            
            // Setup H.264 decoder
            decoder = MediaCodec.createDecoderByType("video/avc")
            val format = MediaFormat.createVideoFormat("video/avc", screenWidth, screenHeight)
            decoder?.configure(format, surface, null, 0)
            decoder?.start()
            
            while (isActive && surface != null) {
                try {
                    val chunkSize = input.readInt()
                    val h264Data = ByteArray(chunkSize)
                    input.readFully(h264Data)
                    
                    decoder?.let { codec ->
                        val inputBufferIndex = codec.dequeueInputBuffer(0)
                        if (inputBufferIndex >= 0) {
                            val inputBuffer = codec.getInputBuffer(inputBufferIndex)
                            inputBuffer?.clear()
                            inputBuffer?.put(h264Data)
                            codec.queueInputBuffer(inputBufferIndex, 0, h264Data.size, 0, 0)
                        }
                        
                        val info = MediaCodec.BufferInfo()
                        val outputBufferIndex = codec.dequeueOutputBuffer(info, 0)
                        if (outputBufferIndex >= 0) {
                            codec.releaseOutputBuffer(outputBufferIndex, true)
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                    break
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
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
