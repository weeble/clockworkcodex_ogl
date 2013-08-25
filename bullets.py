#!/usr/bin/env python

# Andrew Wilson
# Translated from Joe Groff's "An intro to modern OpenGL"
# http://duriansoftware.com/joe/An-intro-to-modern-OpenGL.-Chapter-1:-The-Graphics-Pipeline.html

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

def render_bullets(resources, state):
    bullet_collection = state.bullet_collection
    bullet_buffers = state.bullet_buffers
    prog = resources.bullet_program.program
    unis = resources.bullet_program.uniforms
    atts = resources.bullet_program.attributes
    glUseProgram(prog)
    glUniform2f(unis.focal_point, 0,0)
    glUniform2f(unis.zoom, 0.1 / resources.aspect_ratio, 0.1)
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, resources.textures[2])
    glUniform1i(unis.tex, 0)

    glBindBuffer(GL_ARRAY_BUFFER, bullet_buffers.position_buffer)
    glVertexAttribPointer(
        atts.position,
        2,
        GL_FLOAT,
        GL_FALSE,
        ctypes.sizeof(GLfloat)*2,
        None)
    glEnableVertexAttribArray(atts.position)

    glBindBuffer(GL_ARRAY_BUFFER, bullet_buffers.texcoord_buffer)
    glVertexAttribPointer(
        atts.texcoord,
        2,
        GL_FLOAT,
        GL_FALSE,
        ctypes.sizeof(GLfloat)*2,
        None)
    glEnableVertexAttribArray(atts.texcoord)

    if not hasattr(state, "first"):
        state.first = True
        print bullet_collection.vertex_colors

    glBindBuffer(GL_ARRAY_BUFFER, bullet_buffers.color_buffer)
    glVertexAttribPointer(
        atts.color,
        4,
        GL_UNSIGNED_BYTE,
        GL_TRUE,
        ctypes.sizeof(GLubyte)*4,
        None)
    glEnableVertexAttribArray(atts.color)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, bullet_buffers.element_buffer)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glDrawElements(
        GL_TRIANGLES,
        bullet_collection.count*6,
        GL_UNSIGNED_SHORT,
        None)

    glDisable(GL_BLEND)
    
    glDisableVertexAttribArray(bullet_buffers.position_buffer)
    glDisableVertexAttribArray(bullet_buffers.texcoord_buffer)
    glDisableVertexAttribArray(bullet_buffers.color_buffer)

def render(resources, state):
    #glClearColor(0.1, 0.1, 0.1, 1.0)
    glClearColor(0,0,0,1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    render_bullets(resources, state)
    pygame.display.flip()

vertex_buffer_data = float_array(
    -1.0, -1.0, 0.0, 1.0,
     1.0, -1.0, 0.0, 1.0,
    -1.0,  1.0, 0.0, 1.0,
     1.0,  1.0, 0.0, 1.0)

vertex_color_data = float_array(
    1,1,1,0,
    0,1,1,1,
    1,0,0,1,
    0,0.5,0,1)

element_buffer_data = short_array(
    0,1,2,3)

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
#version 130

varying vec2 var_texcoord;
varying vec4 var_color;

uniform sampler2D tex;

void main()
{
    gl_FragColor = texture(tex, var_texcoord, -1.0) * var_color;
}
'''

def tex_coords(left, bottom, width, height):
    px = 0.5 / 512.0
    return (
        left+px, bottom+px,
        left+width-px, bottom+px,
        left+width-px, bottom+height-px,
        left+px, bottom+height-px)

bullet_texture_coords = {
    'triangle':  tex_coords(0.00, 0.75, 0.25, 0.25),
    'dart':      tex_coords(0.25, 0.75, 0.25, 0.25),
    'circle':    tex_coords(0.50, 0.75, 0.25, 0.25),
    'lozenge':   tex_coords(0.75, 0.75, 0.125, 0.25),
    'rectangle': tex_coords(0.875, 0.75, 0.125, 0.25),
    'dot':       tex_coords(0.00, 0.50, 0.25, 0.25),
    'hexagon':   tex_coords(0.25, 0.50, 0.25, 0.25),
    'oval':      tex_coords(0.875, 0.50, 0.125, 0.25),
    'test':      tex_coords(0.50, 0.25, 0.25, 0.25),
    }

bullet_sizes = {
    'triangle':  (1,1),
    'dart':      (1,1),
    'circle':    (1,1),
    'lozenge':   (0.5,1),
    'rectangle': (0.5,1),
    'dot':       (0.5,0.5),
    'hexagon':   (1,1),
    'oval':      (0.5,1),
    'test':      (1,1),
    }

class BulletCollection(object):
    def __init__(self, num):
        self.count = num
        self.positions = numpy.empty(shape=(num,2), dtype=GLfloat)
        self.positions[:,:] = 0
        self.angles = numpy.zeros(shape=(num), dtype=GLfloat)
        self.dimensions = numpy.zeros(shape=(num,2), dtype=GLfloat)
        self.vertex_positions = numpy.zeros(shape=(num,8), dtype=GLfloat)
        self.texture_coordinates = numpy.zeros(shape=(num,8), dtype=GLfloat)
        self.vertex_colors = numpy.zeros(shape=(num,16), dtype=GLubyte)
        self.ups = numpy.zeros(shape=(num,2), dtype=GLfloat)
        self.rights = numpy.zeros(shape=(num,2), dtype=GLfloat)
        self.velocities = numpy.zeros(shape=(num,2), dtype=GLfloat)
    def set_bullet(self, index, x, y, w, h, angle, vx, vy, texture_id, color):
        self.positions[index,:] = x, y
        self.angles[index] = angle
        bw, bh = bullet_sizes[texture_id]
        self.dimensions[index,:] = w*bw, h*bh
        self.velocities[index,:] = vx, vy
        self.texture_coordinates[index,:] = bullet_texture_coords[texture_id]
        self.vertex_colors[index,0:4] = color
        self.vertex_colors[index,4:8] = color
        self.vertex_colors[index,8:12] = color
        self.vertex_colors[index,12:16] = color
    def eliminate_bullets(self, indices):
        self.positions[indices,:] = 0
        self.velocities[indices,:] = 0
        self.dimensions[indices,:] = 0
    def update_positions(self):
        # Reset positions to centers:
        self.vertex_positions[:,::2] = self.positions[:,0:1]
        self.vertex_positions[:,1::2] = self.positions[:,1:2]
        # Calculate sine and cosine of angles:
        numpy.sin(self.angles.T, self.ups[:,0])
        numpy.cos(self.angles.T, self.ups[:,1])
        self.rights[:,:] = self.ups[:,::-1]
        # At this point, ups are (sine, cosine)
        #                downs are (cosine, sine)
        # We want:
        #    ups:    (-sine, cosine) * height
        #    rights: (cosine, sine) * width
        self.ups[:,0:1] = -1 * self.dimensions[:,1:2] * self.ups[:,0:1]
        self.ups[:,1:2] = self.dimensions[:,1:2] * self.ups[:,1:2]
        self.rights[:,:] = self.rights[:,:] * self.dimensions[:,0:1]
        # Finally displace the positions to the corners:
        # Bottom-left:
        self.vertex_positions[:,0:2] -= self.ups
        self.vertex_positions[:,0:2] -= self.rights
        # Bottom-right:
        self.vertex_positions[:,2:4] -= self.ups
        self.vertex_positions[:,2:4] += self.rights
        # Top-left:
        self.vertex_positions[:,6:8] += self.ups
        self.vertex_positions[:,6:8] -= self.rights
        # Top-right:
        self.vertex_positions[:,4:6] += self.ups
        self.vertex_positions[:,4:6] += self.rights
    def move_bullets(self, multiplier):
        self.positions[:,:] += self.velocities * multiplier
    
class BulletBuffers(object):
    def __init__(self, bullet_collection):
        self.bullets = bullet_collection
        self.position_buffer, self.texcoord_buffer, self.color_buffer = \
            glGenBuffers(3)
        self.element_buffer = short_element_buffer(
            *sum([[i+0,i+1,i+2,i+2,i+3,i+0]
                for i in xrange(0, 4*self.bullets.count, 4)], []))
        self.update_buffers()
    def update_buffers(self):
        target = GL_ARRAY_BUFFER
        for buf, data in (
            (self.position_buffer, self.bullets.vertex_positions),
            (self.texcoord_buffer, self.bullets.texture_coordinates),
            (self.color_buffer, self.bullets.vertex_colors)):
            glBindBuffer(target, buf)
            glBufferData(target, data.nbytes, data, GL_STREAM_DRAW)

class Resources(object):
    pass

class Uniforms(object):
    pass

class Attributes(object):
    pass

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


def make_resources(viewport_size): 
    resources = Resources()
    resources.textures=[
        make_texture("hello1.tga"),
        make_texture("hello2.tga"),
        make_texture("spaceship_simple_parts_flat.tga", True),
        ]
    resources.bullet_program = make_shader_program(
        bullet_vertex_shader,
        bullet_fragment_shader,
        uniforms = ["focal_point", "zoom", "tex"],
        attributes = ["position", "texcoord", "color"])
    w,h = viewport_size
    resources.aspect_ratio = (1.0 * w) / h
    return resources


class State(object):
    timer = 0
    camera_pos = float_array(0,0,-3)

def make_state():
    state = State()
    state.rng = Random()
    state.bullet_collection = BulletCollection(1000)
    state.paused = False
    random = state.rng.random
    bullet_textures = bullet_sizes.keys()
    for i in xrange(1000):
        angle = random()*math.pi*2.0
        size = random()*0.5+0.25
        speed = 3*random()+1
        color = [255, state.rng.randint(0,255), 0]
        state.rng.shuffle(color)
        color.append(state.rng.randint(63,255))
        state.bullet_collection.set_bullet(
            i,
            random()*16.0-8.0, random()*16.0-8.0,
            size, size,
            angle,
            math.cos(angle)*speed, math.sin(angle)*speed,
            state.rng.choice(bullet_textures),
            color)
    state.bullet_collection.update_positions()
    state.bullet_buffers = BulletBuffers(state.bullet_collection)
    return state

def zap_bullet(state, index):
    rng = state.rng
    random = rng.random
    x = random()*0.3
    y = random()*0.3 - 1.0
    angle = math.pi * 0.5 #(random()-0.5)*math.pi/16 + math.pi * 0.5
    state.bullet_collection.set_bullet(
        index,
        x, y,
        1, 1,
        angle+math.pi*0.5+random()*2.0*math.pi,
        math.cos(angle)*7.0,
        math.sin(angle)*7.0,
        "oval",
        (255, 255, 255, 200))

def update_timer(resources, state):
    milliseconds = pygame.time.get_ticks()
    lasttimer = state.timer
    state.timer = milliseconds * 0.001
    if not state.paused:
        elapsed = state.timer - lasttimer
        state.bullet_collection.move_bullets(elapsed)
        state.bullet_collection.angles += elapsed * 15.0
        dead_bullets = numpy.nonzero(
            numpy.sum(
                numpy.square(
                    state.bullet_collection.positions
                ),
                1
            )>100
        )
        for idx in dead_bullets:
            zap_bullet(state, idx)
        state.bullet_collection.update_positions()
        #state.bullet_collection.eliminate_bullets(dead_bullets)
        state.bullet_buffers.update_buffers()

def main():
    video_flags = OPENGL|DOUBLEBUF|RESIZABLE
    pygame.init()
    surface = pygame.display.set_mode((800,600), video_flags)
    surface = pygame.display.set_mode((800,600), video_flags)
    resources = make_resources((800,600))
    state = make_state()
    frames = 0
    done = 0
    ticks = pygame.time.get_ticks()
    while not done:
        while 1:
            event = pygame.event.poll()
            if event.type == NOEVENT:
                break
            if event.type == VIDEORESIZE:
                surface = pygame.display.set_mode(event.size, video_flags)
                glViewport(0,0,event.w,event.h)
                resources.aspect_ratio = (1.0 * event.w) / event.h
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = 1
                elif event.key == K_SPACE:
                    state.paused = not state.paused
            if event.type == QUIT:
                done = 1
        update_timer(resources, state)
        render(resources, state)
        #if state.timer > 15.0:
        #    done = 1
        frames += 1
    print "fps:  %d" % ((frames*1000)/(pygame.time.get_ticks()-ticks))

if __name__ == '__main__':
    main()
