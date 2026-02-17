package com.tabletmonitor

import android.graphics.BitmapFactory
import android.os.Bundle
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.ImageView
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import java.io.DataInputStream
import java.net.Socket

class MainActivity : AppCompatActivity() {
    private lateinit var imageView: ImageView
    private var socket: Socket? = null
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var laptopWidth = 1920f
    private var laptopHeight = 1080f
    private var isConnected = false
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setContentView(R.layout.activity_main)
        imageView = findViewById(R.id.imageView)
        
        imageView.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> handleTouchEvent("DOWN", event.x, event.y)
                MotionEvent.ACTION_MOVE -> handleTouchEvent("MOVE", event.x, event.y)
                MotionEvent.ACTION_UP -> handleTouchEvent("UP", event.x, event.y)
            }
            true
        }
        
        startConnection()
    }
    
    private fun startConnection() {
        scope.launch {
            while (scope.isActive) {
                if (!isConnected) {
                    try {
                        connectAndStream()
                    } catch (e: Exception) {
                        e.printStackTrace()
                        delay(2000) // Wait 2 seconds before retry
                    }
                } else {
                    delay(1000)
                }
            }
        }
    }
    
    private suspend fun connectAndStream() {
        try {
            socket = Socket("localhost", 8888)
            isConnected = true
            
            while (scope.isActive && isConnected) {
                try {
                    socket?.getOutputStream()?.write("GET_SCREEN\n".toByteArray())
                    
                    val input = DataInputStream(socket?.getInputStream())
                    // Read actual screen dimensions
                    val screenWidth = input.readInt()
                    val screenHeight = input.readInt()
                    // Read image size and data
                    val size = input.readInt()
                    val imgData = ByteArray(size)
                    input.readFully(imgData)
                    
                    val bitmap = BitmapFactory.decodeByteArray(imgData, 0, size)
                    laptopWidth = screenWidth.toFloat()
                    laptopHeight = screenHeight.toFloat()
                    withContext(Dispatchers.Main) {
                        imageView.setImageBitmap(bitmap)
                    }
                    
                    delay(16)  // ~60 FPS
                } catch (e: Exception) {
                    isConnected = false
                    socket?.close()
                    throw e
                }
            }
        } catch (e: Exception) {
            isConnected = false
            socket?.close()
            throw e
        }
    }
    
    private fun handleTouchEvent(action: String, x: Float, y: Float) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Get ImageView dimensions
                val viewWidth = imageView.width.toFloat()
                val viewHeight = imageView.height.toFloat()
                
                // Direct mapping since fitXY stretches to fill
                val laptopX = (x / viewWidth) * laptopWidth
                val laptopY = (y / viewHeight) * laptopHeight
                
                val touchSocket = Socket("localhost", 8888)
                val msg = "$action $laptopX $laptopY\n"
                touchSocket.getOutputStream()?.write(msg.toByteArray())
                touchSocket.getInputStream()?.read()
                touchSocket.close()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        return super.onTouchEvent(event)
    }
    
    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
        socket?.close()
    }
}
