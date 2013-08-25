#!/usr/bin/env python

# Andrew Wilson
# Translated from Joe Groff's "An intro to modern OpenGL"
# http://duriansoftware.com/joe/An-intro-to-modern-OpenGL.-Chapter-1:-The-Graphics-Pipeline.html

from OpenGL.GL import *
import pygame, pygame.image, pygame.key
from pygame.locals import *
import numpy
import math
import sys

def render(resources):
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(resources.program)
    glUniform1f(resources.uniforms.timer, resources.timer)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, resources.textures[0])
    glUniform1i(resources.uniforms.textures[0], 0)
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, resources.textures[1])
    glUniform1i(resources.uniforms.textures[1], 1)
    glBindBuffer(GL_ARRAY_BUFFER, resources.vertex_buffer)
    glVertexAttribPointer(
        resources.attributes.position,
        4, # size
        GL_FLOAT, # type
        GL_FALSE, # normalized?
        ctypes.sizeof(GLfloat)*4, # stride
        None # offset
        )
    glEnableVertexAttribArray(resources.attributes.position)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, resources.element_buffer)
    glDrawElements(
        GL_TRIANGLE_STRIP,
        4,
        GL_UNSIGNED_SHORT,
        None)
    glDisableVertexAttribArray(resources.attributes.position)
    pygame.display.flip()

def make_buffer(target, buffer_data, size):
    buffer = glGenBuffers(1)
    glBindBuffer(target, buffer)
    glBufferData(target, size, buffer_data, GL_STATIC_DRAW)
    return buffer

def float_array(*args):
    return numpy.array(args, dtype=GLfloat)

def short_array(*args):
    return numpy.array(args, dtype=GLshort)

vertex_buffer_data = float_array(
    -1.0, -1.0, 0.0, 1.0,
     1.0, -1.0, 0.0, 1.0,
    -1.0,  1.0, 0.0, 1.0,
     1.0,  1.0, 0.0, 1.0)

element_buffer_data = short_array(
    0,1,2,3)

vertex_shader_1 = '''\
#version 110

uniform float timer;

attribute vec4 position;

varying vec2 texcoord;
varying float fade_factor;

void main()
{
    gl_Position = position;
    //vec4(position, 0.0, 1.0);
    texcoord = position.xy * vec2(0.5) + vec2(0.5);
    fade_factor = sin(timer) * 0.5 + 0.5;
}
'''

vertex_shader_2 = '''\
#version 110

uniform float timer;

attribute vec4 position;

varying vec2 texcoord;
varying float fade_factor;

void main()
{
    mat3 window_scale = mat3(
        vec3(3.0/4.0, 0.0, 0.0),
        vec3(    0.0, 1.0, 0.0),
        vec3(    0.0, 0.0, 1.0)
    );
    mat3 rotation = mat3(
        vec3( cos(timer),  sin(timer),  0.0),
        vec3(-sin(timer),  cos(timer),  0.0),
        vec3(        0.0,         0.0,  1.0)
    );
    mat3 object_scale = mat3(
        vec3(4.0/3.0, 0.0, 0.0),
        vec3(    0.0, 1.0, 0.0),
        vec3(    0.0, 0.0, 1.0)
    );
    gl_Position = vec4(window_scale * rotation * object_scale * position.xyz, 1.0);
    texcoord = position.xy * vec2(0.5) + vec2(0.5);
    fade_factor = sin(timer) * 0.5 + 0.5;    
}
'''

vertex_shader_3='''\
#version 110

uniform float timer;

attribute vec4 position;

varying vec2 texcoord;
varying float fade_factor;

mat4 view_frustum(
    float angle_of_view,
    float aspect_ratio,
    float z_near,
    float z_far
) {
    return mat4(
        vec4(1.0/tan(angle_of_view),           0.0, 0.0, 0.0),
        vec4(0.0, aspect_ratio/tan(angle_of_view),  0.0, 0.0),
        vec4(0.0, 0.0,    (z_far+z_near)/(z_far-z_near), 1.0),
        vec4(0.0, 0.0, -2.0*z_far*z_near/(z_far-z_near), 0.0)
    );
}

mat4 scale(float x, float y, float z)
{
    return mat4(
        vec4(x,   0.0, 0.0, 0.0),
        vec4(0.0, y,   0.0, 0.0),
        vec4(0.0, 0.0, z,   0.0),
        vec4(0.0, 0.0, 0.0, 1.0)
    );
}

mat4 translate(float x, float y, float z)
{
    return mat4(
        vec4(1.0, 0.0, 0.0, 0.0),
        vec4(0.0, 1.0, 0.0, 0.0),
        vec4(0.0, 0.0, 1.0, 0.0),
        vec4(x,   y,   z,   1.0)
    );
}

mat4 rotate_x(float theta)
{
    return mat4(
        vec4(1.0,         0.0,         0.0, 0.0),
        vec4(0.0,  cos(timer),  sin(timer), 0.0),
        vec4(0.0, -sin(timer),  cos(timer), 0.0),
        vec4(0.0,         0.0,         0.0, 1.0)
    );
}

void main()
{
    gl_Position = view_frustum(radians(45.0), 4.0/3.0, 0.5, 5.0)
        * translate(cos(timer), 0.0, 3.0+sin(timer))
        * rotate_x(timer)
        * scale(4.0/3.0, 1.0, 1.0)
        * position;
    texcoord = position.xy * vec2(0.5) + vec2(0.5);
    fade_factor = sin(timer) * 0.5 + 0.5;
}
'''

vertex_shader = vertex_shader_3

fragment_shader = '''\
#version 110

varying float fade_factor;
uniform sampler2D textures[2];

varying vec2 texcoord;

void main()
{
    gl_FragColor = mix(
        texture2D(textures[0], texcoord),
        texture2D(textures[1], texcoord),
        fade_factor
    );
}
'''


class Resources(object):
    pass

class Uniforms(object):
    pass

class Attributes(object):
    pass

def make_resources():
    resources = Resources()
    resources.vertex_buffer = make_buffer(
        GL_ARRAY_BUFFER,
        vertex_buffer_data,
        vertex_buffer_data.nbytes)
    resources.element_buffer = make_buffer(
        GL_ELEMENT_ARRAY_BUFFER,
        element_buffer_data,
        element_buffer_data.nbytes)
    resources.textures=[
        make_texture("hello1.tga"),
        make_texture("hello2.tga")]
    resources.vertex_shader=make_shader(
        GL_VERTEX_SHADER,
        vertex_shader)
    resources.fragment_shader=make_shader(
        GL_FRAGMENT_SHADER,
        fragment_shader)
    resources.program=make_program(
        resources.vertex_shader,
        resources.fragment_shader)
    resources.uniforms=Uniforms()
    resources.uniforms.timer = glGetUniformLocation(
        resources.program,
        "timer")
    resources.uniforms.textures =[
        glGetUniformLocation(resources.program, "textures[0]"),
        glGetUniformLocation(resources.program, "textures[1]")]
    resources.attributes=Attributes()
    resources.attributes.position = glGetAttribLocation(
        resources.program, "position")
    return resources

class State(object):
    timer = 0
    camera_pos = float_array(0,0,-3)

def make_texture(filename):
    image = pygame.image.load(filename)
    pixels = pygame.image.tostring(image, "RGB", True)
    texture=glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,     GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,     GL_CLAMP_TO_EDGE)
    glTexImage2D(
        GL_TEXTURE_2D, 0,
        GL_RGB8,
        image.get_width(), image.get_height(), 0,
        GL_RGB, GL_UNSIGNED_BYTE,
        pixels)
    return texture

def make_shader(type, source):
    shader = glCreateShader(type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    retval = ctypes.c_uint()
    glGetShaderiv(shader, GL_COMPILE_STATUS, retval)
    if not retval:
        print >> sys.stderr, "Failed to compile shader."
        print >> sys.stderr, glGetShaderInfoLog(shader)
        glDeleteShader(shader)
        raise Exception("Failed to compile shader.")
    return shader

def show_info_log(object, getiv, getinfolog):
    log_length = ctypes.c_int()
    getiv(object, GL_INFO_LOG_LENGTH, log_length)
    log = ctypes.create_string_buffer(log_length)
    getinfolog(object, log_length, None, log)
    print >> sys.stderr, log

def make_program(vertex_shader, fragment_shader):
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    retval = ctypes.c_int()
    glGetProgramiv(program, GL_LINK_STATUS, retval)
    if not retval:
        print >> sys.stderr, "Failed to link shader program."
        print >> sys.stderr, glGetProgramInfoLog(program)
        glDeleteProgram(program)
        raise Exception("Failed to link shader program.")
    return program

def update_timer(resources):
    milliseconds = pygame.time.get_ticks()
    resources.timer = milliseconds * 0.001

def main():
    video_flags = OPENGL|DOUBLEBUF
    pygame.init()
    surface = pygame.display.set_mode((640,480), video_flags)
    resources = make_resources()
    frames = 0
    done = 0
    ticks = pygame.time.get_ticks()
    while not done:
        while 1:
            event = pygame.event.poll()
            if event.type == NOEVENT:
                break
            if event.type == KEYDOWN:
                pass
            if event.type == QUIT:
                done = 1
        update_timer(resources)
        render(resources)
        frames += 1
    print "fps:  %d" % ((frames*1000)/(pygame.time.get_ticks()-ticks))

if __name__ == '__main__':
    main()
