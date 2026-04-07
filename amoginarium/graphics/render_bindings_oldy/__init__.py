from ._opengl import OpenGLRenderer as Renderer
# from ._pygame import PyGameRenderer as Renderer
from ._base_renderer import BaseRenderer, tColor


renderer: BaseRenderer = Renderer()
