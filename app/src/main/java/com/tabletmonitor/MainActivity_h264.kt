package com.tabletmonitor

import android.graphics.Bitmap
import android.media.MediaCodec
import android.media.MediaFormat
import android.os.Bundle
import android.view.MotionEvent
import android.view.Surface
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import java.io.DataInputStream
import java.net.Socket
import java.nio.ByteBuffer

class MainActivity : AppCompatActivity(), SurfaceHolder.Callback {
    private lateinit var surfaceView: SurfaceView
    private var videoSocket: Socket? = null
    private var touchSocket: Socket? = null
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var laptopWidth = 1920f
    private var laptopHeight = 1080f
    private var isConnected = false
    private var decoder: MediaCodec? = null
    private var surface: Surface? = null
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContentView(R.layout.activity_main)
        surfaceView = findViewById(R.id.surfaceView)
        surfaceView.holder.addCallback(this)
        
        surfaceView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> handleTouchEvent("DOWN", event.x, event.y)
                MotionEvent.ACTION_MOVE -> handleTouchEvent("MOVE", event.x, event.y)
                MotionEvent.ACTION_UP -> handleTouchEvent("UP", event.x, event.y)
            }
            true
        }
    }
    
    override fun surfaceCreated(holder: SurfaceHolder) {
        surface = holder.surface
        startConnection()
    }
    
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {}
    
    override fun surfaceDestroyed(holder: SurfaceHolder) {
        surface = null
        decoder?.stop()
        decoder?.release()
        decoder = null
    }
    
    private fun startConnection() {
        scope.launch {
            while (scope.isActive) {
                if (!isConnected) {
                    try {
                        connectAndStream()
                    } catch (e: Exception) {
                        e.printStackTrace()
                        delay(2000)
                    }
                } else {
                    delay(1000)
                }
            }
        }
    }
    
    private suspend fun connectAndStream() {
        try {
            videoSocket = Socket("localhost", 8888)
            touchSocket = Socket("localhost", 8889)
            isConnected = true
            
            val input = DataInputStream(videoSocket?.getInputStream())
            val screenWidth = input.readInt()
            val screenHeight = input.readInt()
            laptopWidth = screenWidth.toFloat()
            laptopHeight = screenHeight.toFloat()
            
            val format = MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, screenWidth, screenHeight)
            decoder = MediaCodec.createDecoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
            decoder?.configure(format, surface, null, 0)
            decoder?.start()
            
            while (scope.isActive && isConnected) {
                try {
                    val chunkSize = input.readInt()
                    val h264Data = ByteArray(chunkSize)
                    input.readFully(h264Data)
                    
                    val inputBufferIndex = decoder?.dequeueInputBuffer(10000) ?: -1
                    if (inputBufferIndex >= 0) {
                        val inputBuffer = decoder?.getInputBuffer(inputBufferIndex)
                        inputBuffer?.clear()
                        inputBuffer?.put(h264Data)
                        decoder?.queueInputBuffer(inputBufferIndex, 0, h264Data.size, System.nanoTime() / 1000, 0)
                    }
                    
                    val bufferInfo = MediaCodec.BufferInfo()
                    val outputBufferIndex = decoder?.dequeueOutputBuffer(bufferInfo, 0) ?: -1
                    if (outputBufferIndex >= 0) {
                        decoder?.releaseOutputBuffer(outputBufferIndex, true)
                    }
                } catch (e: Exception) {
                    isConnected = false
                    videoSocket?.close()
                    touchSocket?.close()
                    decoder?.stop()
                    decoder?.release()
                    decoder = null
                    throw e
                }
            }
        } catch (e: Exception) {
            isConnected = false
            videoSocket?.close()
            touchSocket?.close()
            throw e
        }
    }
    
    private fun handleTouchEvent(action: String, x: Float, y: Float) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val viewWidth = surfaceView.width.toFloat()
                val viewHeight = surfaceView.height.toFloat()
                
                val laptopX = (x / viewWidth) * laptopWidth
                val laptopY = (y / viewHeight) * laptopHeight
                
                val msg = "$action $laptopX $laptopY\n"
                touchSocket?.getOutputStream()?.write(msg.toByteArray())
                touchSocket?.getInputStream()?.read()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
        videoSocket?.close()
        touchSocket?.close()
        decoder?.stop()
        decoder?.release()
    }
}
