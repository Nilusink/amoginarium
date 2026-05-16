# from ._opengl import OpenGLRenderer as Renderer
from ._base_renderer import BaseRenderer, tColor
from ._opengl_shader import OpenGLShaderRenderer as Renderer

renderer: Renderer = Renderer()
