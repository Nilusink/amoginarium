# from ._opengl_shader import OpenGLShaderRenderer as Renderer
from ._opengl import OpenGLRenderer as Renderer
from ._base_renderer import BaseRenderer, tColor

renderer: Renderer = Renderer()
