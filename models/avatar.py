import streamlit as st
import os
import base64

# Path to the GLB model
glb_file_path = r"C:\Users\Probook\Desktop\zubaida\Automated_Interviews\static\human\human.glb"

# Load the GLB model data as base64
with open(glb_file_path, "rb") as f:
    glb_data = f.read()
    glb_base64 = base64.b64encode(glb_data).decode("utf-8")

# HTML and JavaScript to render the model in a WebGL canvas
html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ margin: 0; }}
        canvas {{ width: 100%; height: 100% }}
    </style>
</head>
<body>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        var scene = new THREE.Scene();
        var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        var renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        // Add ambient lighting to the scene for uniform illumination
        var ambientLight = new THREE.AmbientLight(0x404040, 1); // Soft white light
        scene.add(ambientLight);

        // Add a point light to highlight the model from a specific direction
        var pointLight = new THREE.PointLight(0xffffff, 1, 100);
        pointLight.position.set(10, 10, 10);
        scene.add(pointLight);

        // Load the GLB model using base64 encoded data
        var loader = new THREE.GLTFLoader();
        var glbDataUri = "data:application/octet-stream;base64,{glb_base64}";  // The f-string here

        var glbData = atob(glbDataUri.split(',')[1]);  // Decoding the base64 part
        
        // Create an ArrayBuffer to hold the binary data
        var arrayBuffer = new ArrayBuffer(glbData.length);
        var uint8Array = new Uint8Array(arrayBuffer);

        for (var i = 0; i < glbData.length; i++) {{
            uint8Array[i] = glbData.charCodeAt(i);
        }}

        // Parse the GLB data from the ArrayBuffer
        loader.parse(arrayBuffer, '', function (gltf) {{
            var model = gltf.scene;
            scene.add(model);

            // Scale the model down (e.g., 0.3 means 30% of the original size)
            model.scale.set(0.3, 0.3, 0.3); 
        }}, function (error) {{
            console.error(error);
        }});

        camera.position.z = 5;

        // Add orbit controls to move the camera around
        var controls = new THREE.OrbitControls(camera, renderer.domElement);

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();  // Only required if controls.enableDamping or controls.auto-rotation are set
            renderer.render(scene, camera);
        }}
        animate();
    </script>
</body>
</html>
"""

# Display in Streamlit
st.components.v1.html(html_code, height=600)
