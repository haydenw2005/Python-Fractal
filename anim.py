import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import glm
import ctypes
import time
import math
import random
from functools import lru_cache

# Maximum recursion depth and delay between fractalizations
MAX_RECURSION_DEPTH = 5
RECURSION_DELAY = .25  # Seconds between each fractalization step
SCALE_FACTOR = .2

# Cache midpoints to avoid recomputation
midpoint_cache = {}

# Initialize GLFW
if not glfw.init():
    raise Exception("GLFW cannot be initialized!")

# Set OpenGL version to 2.1 (for GLSL version 120)
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

window = glfw.create_window(800, 600, "Dynamic Fractal Geometry", None, None)
if not window:
    glfw.terminate()
    raise Exception("GLFW window cannot be created!")

glfw.make_context_current(window)

# Set viewport size
width, height = glfw.get_framebuffer_size(window)
glViewport(0, 0, width, height)
glEnable(GL_DEPTH_TEST)

# Set the clear color
glClearColor(0.1, 0.1, 0.1, 1.0)

# Vertex Shader Code (GLSL version 120)
vertex_src = """
#version 120
attribute vec3 a_position;
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
void main()
{
    gl_Position = projection * view * model * vec4(a_position, 1.0);
}
"""

# Fragment Shader Code (GLSL version 120)
fragment_src = """
#version 120
void main()
{
    gl_FragColor = vec4(0.6, 0.4, 1.0, 1.0);  // Purple-like color
}
"""

# Compile shaders and create shader program
shader = compileProgram(
    compileShader(vertex_src, GL_VERTEX_SHADER),
    compileShader(fragment_src, GL_FRAGMENT_SHADER)
)

# Base vertices of the tetrahedron in 3D
base_tetrahedron = [
    [1, 1, 1],    # Vertex 0
    [-1, -1, 1],  # Vertex 1
    [-1, 1, -1],  # Vertex 2
    [1, -1, -1]   # Vertex 3
]

vertices = base_tetrahedron.copy()

# Initial faces of the tetrahedron (each face is a triplet of vertex indices)
faces = [
    [0, 1, 2],  # Face 0
    [0, 1, 3],  # Face 1
    [0, 2, 3],  # Face 2
    [1, 2, 3]   # Face 3
]

# Function to compute the midpoint and add it to the vertices list if not already present
@lru_cache(maxsize=None) 
def get_midpoint(v1_idx, v2_idx):
    # Order the vertex indices to ensure consistency
    smaller_idx = min(v1_idx, v2_idx)
    larger_idx = max(v1_idx, v2_idx)
    key = (smaller_idx, larger_idx)
    
    if key in midpoint_cache:
        return midpoint_cache[key]
    
    # Compute the midpoint coordinates
    v1 = np.array(vertices[v1_idx], dtype=np.float32)
    v2 = np.array(vertices[v2_idx], dtype=np.float32)
    midpoint = (v1 + v2)
    midpoint = midpoint / np.linalg.norm(midpoint)  # Normalize to lie on the unit sphere
    
    # Add the midpoint to the vertices list and cache its index
    vertices.append(midpoint.tolist())
    midpoint_idx = len(vertices) - 1
    midpoint_cache[key] = midpoint_idx
    return midpoint_idx

# Function to recursively subdivide the faces
def subdivide_faces(current_faces, depth, total_shapes):
    if depth == 0:
        return current_faces
    
    new_faces = []
    for face in current_faces:
        v0, v1, v2 = face
        # Get midpoints for each edge
        a = get_midpoint(v0, v1)
        b = get_midpoint(v1, v2)
        c = get_midpoint(v2, v0)
        
        # Create four new faces from the original face
        val = (depth + total_shapes) % 4
        if val % 4 <= 1:
            new_faces.append([v0, a, c])
            new_faces.append([a, v1, b])
            new_faces.append([c, b, v2])
        if val % 4 <= 4:
            new_faces.append([a, b, c])
    
    # Recur for the next level of depth
    return subdivide_faces(new_faces, depth - 1, total_shapes)

# Function to update the fractal based on current recursion depth
def update_fractal(recursion_depth, total_shapes):
    global faces, vertices, midpoint_cache

    # Subdivide the faces
    new_faces = subdivide_faces(faces, recursion_depth, total_shapes)
    faces.extend(new_faces)  # Append new faces to the existing ones

    # Convert faces to a flat list of indices for GL_LINES
    indices = []
    for face in faces:
        indices += [face[0], face[1],
                    face[1], face[2],
                    face[2], face[0]]

    indices = np.array(indices, dtype=np.uint32)
    vertices_np = np.array(vertices, dtype=np.float32).reshape(-1, 3)

    # Update the buffers with accumulated vertices and indices
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices_np.nbytes, vertices_np, GL_STATIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    
    return len(indices)

# Create VBO and EBO for rendering
VBO = glGenBuffers(1)
EBO = glGenBuffers(1)

# Bind the VBO before setting up vertex attributes
glBindBuffer(GL_ARRAY_BUFFER, VBO)
# Initialize buffer data (empty for now; will be updated later)
glBufferData(GL_ARRAY_BUFFER, 0, None, GL_STATIC_DRAW)

# Enable vertex attribute
position = glGetAttribLocation(shader, "a_position")
glEnableVertexAttribArray(position)

# Define the layout of the vertex data
glVertexAttribPointer(position, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

# Use the shader program
glUseProgram(shader)

# Set up the view and projection matrices
view = glm.lookAt(glm.vec3(0, 0, 6), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))
projection = glm.perspective(glm.radians(45), width / height, 0.1, 100.0)

model_loc = glGetUniformLocation(shader, "model")
view_loc = glGetUniformLocation(shader, "view")
proj_loc = glGetUniformLocation(shader, "projection")

# Send static matrices to the shader
glUniformMatrix4fv(view_loc, 1, GL_FALSE, glm.value_ptr(view))
glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))

# Variables for controlling recursion and time
current_depth = 0
total_shapes = 1

last_update_time = glfw.get_time()

# Generate initial fractal vertices and indices
num_indices = update_fractal(current_depth, total_shapes)

# Create and bind the EBO
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
# Note: buffer data was already set in update_fractal

# Enable wireframe mode for better visualization
glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

# Main rendering loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Check if the delay has passed and update recursion depth
    current_time = glfw.get_time()
    if current_time - last_update_time > RECURSION_DELAY:
        if current_depth < MAX_RECURSION_DEPTH:
            current_depth += 1
            print(current_depth % (10 * total_shapes))
            num_indices = update_fractal(current_depth % (10 * total_shapes), total_shapes)
            last_update_time = current_time
        else:
            total_shapes += 1
        

    # Update the model matrix (rotation)
    
    x_rotate = math.sin(current_time)
    y_rotate = 1/math.sin(current_time)
    z_rotate = math.sin(current_time)**2
    model = glm.rotate(glm.mat4(), current_time, glm.vec3(x_rotate, y_rotate, z_rotate))
    
    scale = math.log(current_time/SCALE_FACTOR)
    model = glm.scale(model, glm.vec3(current_time/SCALE_FACTOR, current_time/SCALE_FACTOR, current_time/SCALE_FACTOR))

    glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))

    # Bind the buffers before drawing
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)

    # Draw the fractal as lines (wireframe)
    glDrawElements(GL_LINES, num_indices, GL_UNSIGNED_INT, ctypes.c_void_p(0))

    glfw.swap_buffers(window)

# Clean up
glDisableVertexAttribArray(position)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
glUseProgram(0)
glDeleteBuffers(1, [VBO])
glDeleteBuffers(1, [EBO])
glDeleteProgram(shader)
glfw.terminate()
