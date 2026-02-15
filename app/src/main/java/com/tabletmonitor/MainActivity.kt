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
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        imageView = findViewById(R.id.imageView)
        
        scope.launch {
            connectAndStream()
        }
    }
    
    private suspend fun connectAndStream() {
        try {
            socket = Socket("localhost", 8888) // Using USB with adb reverse
            
            while (scope.isActive) {
                socket?.getOutputStream()?.write("GET_SCREEN\n".toByteArray())
                
                val input = DataInputStream(socket?.getInputStream())
                val size = input.readInt()
                val imgData = ByteArray(size)
                input.readFully(imgData)
                
                val bitmap = BitmapFactory.decodeByteArray(imgData, 0, size)
                withContext(Dispatchers.Main) {
                    imageView.setImageBitmap(bitmap)
                }
                
                delay(100)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_DOWN) {
            scope.launch {
                try {
                    val msg = "TOUCH ${event.x} ${event.y}\n"
                    socket?.getOutputStream()?.write(msg.toByteArray())
                    socket?.getInputStream()?.read()
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
