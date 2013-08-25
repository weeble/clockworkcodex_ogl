# Andrew Wilson
# Translated from Joe Groff's "An intro to modern OpenGL"
# http://duriansoftware.com/joe/An-intro-to-modern-OpenGL.-Chapter-1:-The-Graphics-Pipeline.html

from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps
import pygame, pygame.image, pygame.key
from pygame.locals import *
import numpy
import math
import sys

def make_buffer(target, buffer_data, size):
    buffer = glGenBuffers(1)
    glBindBuffer(target, buffer)
    glBufferData(target, size, buffer_data, GL_STATIC_DRAW)
    return buffer

def float_array(*args):
    return numpy.array(args, dtype=GLfloat)

def short_array(*args):
    return numpy.array(args, dtype=GLshort)

def float_array_buffer(*args):
    array = float_array(*args)
    return make_buffer(
        GL_ARRAY_BUFFER,
        array,
        array.nbytes)

def short_element_buffer(*args):
    array = short_array(*args)
    return make_buffer(
        GL_ELEMENT_ARRAY_BUFFER,
        array,
        array.nbytes)

def translation_matrix(x,y,z):
    return numpy.matrix(
        [[1,0,0,0],
         [0,1,0,0],
         [0,0,1,0],
         [x,y,z,1]],
        dtype=GLfloat)

def make_texture(filename, mipmaps=False):
    image = pygame.image.load(filename)
    pixels = pygame.image.tostring(image, "RGBA", True)
    texture=glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
        GL_LINEAR_MIPMAP_LINEAR if mipmaps else GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,     GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,     GL_CLAMP_TO_EDGE)
    if mipmaps:
        gluBuild2DMipmaps(
            GL_TEXTURE_2D,
            GL_RGBA8,
            image.get_width(),
            image.get_height(),
            GL_RGBA, GL_UNSIGNED_BYTE,
            pixels)
    else:
        glTexImage2D(
            GL_TEXTURE_2D, 0,
            GL_RGBA8,
            image.get_width(), image.get_height(), 0,
            GL_RGBA, GL_UNSIGNED_BYTE,
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
        show_info_log(shader, glGetShaderiv, glGetShaderInfoLog)
        glDeleteShader(shader)
        raise Exception("Failed to compile shader.")
    return shader

def show_info_log(object, getiv, getinfolog):
    log_length = ctypes.c_int()
    getiv(object, GL_INFO_LOG_LENGTH, log_length)
    log = ctypes.create_string_buffer(log_length.value)
    #getinfolog(object, log_length, None, log)
    log = getinfolog(object)
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
        show_info_log(program, glGetProgramiv, glGetProgramInfoLog)
        glDeleteProgram(program)
        raise Exception("Failed to link shader program.")
    return program


