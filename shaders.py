from OpenGL.GL import *
import pygame, pygame.image, pygame.key
from pygame.locals import *
import numpy
import math
from random import Random
from ogl_helpers import (
    make_buffer,
    short_element_buffer,
    float_array,
    short_array,
    translation_matrix,
    make_texture,
    make_shader,
    show_info_log,
    make_program)



bullet_vertex_shader = '''\
#version 110

uniform vec2 focal_point;
uniform vec2 zoom;

attribute vec2 position;
attribute vec2 texcoord;
attribute vec4 color;

varying vec2 var_texcoord;
varying vec4 var_color;

void main()
{
    gl_Position.xy = (position - focal_point) * zoom;
    gl_Position.z = 0.0;
    gl_Position.w = 1.0;
    var_texcoord = texcoord;
    var_color = color;       

}
'''

bullet_fragment_shader = '''\
#version 110

varying vec2 var_texcoord;
varying vec4 var_color;

uniform sampler2D texture;

void main()
{
    gl_FragColor = texture2D(texture, var_texcoord) * var_color;
}
'''

class ShaderProgram(object):
    def __init__(self, program):
        self.program = program 
        self.uniforms = Uniforms()
        self.attributes = Attributes()

def make_shader_program(
    vertex_shader_source,
    fragment_shader_source,
    uniforms,
    attributes):
    vertex_shader = make_shader(
        GL_VERTEX_SHADER,
        vertex_shader_source)
    fragment_shader = make_shader(
        GL_FRAGMENT_SHADER,
        fragment_shader_source)
    program = make_program(
        vertex_shader,
        fragment_shader)
    shader_program = ShaderProgram(program)
    for u in uniforms:
        setattr(
            shader_program.uniforms, u,
            glGetUniformLocation(program, u))
    for a in attributes:
        setattr(
            shader_program.attributes, a,
            glGetAttribLocation(program, a))
    return shader_program

def make_bullet_program():
    resources.bullet_program = make_shader_program(
        bullet_vertex_shader,
        bullet_fragment_shader,
        uniforms = ["focal_point", "zoom", "texture"],
        attributes = ["position", "texcoord", "color"])
    
