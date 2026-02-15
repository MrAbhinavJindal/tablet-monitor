package com.tabletmonitor

import android.graphics.BitmapFactory
import android.os.Bundle
import android.view.MotionEvent
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
        setContentView(R.layout.activity_main)
        imageView = findViewById(R.id.imageView)
        
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
                    val size = input.readInt()
                    val imgData = ByteArray(size)
                    input.readFully(imgData)
                    
                    val bitmap = BitmapFactory.decodeByteArray(imgData, 0, size)
                    laptopWidth = bitmap.width.toFloat()
                    laptopHeight = bitmap.height.toFloat()
                    withContext(Dispatchers.Main) {
                        imageView.setImageBitmap(bitmap)
                    }
                    
                    delay(100)
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
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_DOWN) {
            CoroutineScope(Dispatchers.IO).launch {
                try {
                    // Get ImageView dimensions and position
                    val imageWidth = imageView.width.toFloat()
                    val imageHeight = imageView.height.toFloat()
                    
                    // Calculate scale
                    val scaleX = laptopWidth / imageWidth
                    val scaleY = laptopHeight / imageHeight
                    
                    // Convert touch coordinates to laptop coordinates
                    val laptopX = event.x * scaleX
                    val laptopY = event.y * scaleY
                    
                    val touchSocket = Socket("localhost", 8888)
                    val msg = "TOUCH $laptopX $laptopY\n"
                    touchSocket.getOutputStream()?.write(msg.toByteArray())
                    touchSocket.getInputStream()?.read()
                    touchSocket.close()
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        }
        return true
    }
    
    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
        socket?.close()
    }
}
