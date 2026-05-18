"""
Initializes and exports the active OpenGL graphics renderer instance.

Path: amoginarium/graphics/render_bindings/__init__.py
Project: amoginarium
Created: 17.03.2024
Authors: Nilusink, LukasKrah
"""

# from ._opengl import OpenGLRenderer as Renderer
from ._base_renderer import BaseRenderer, tColor
from ._opengl_shader import OpenGLShaderRenderer as Renderer

renderer: Renderer = Renderer()
