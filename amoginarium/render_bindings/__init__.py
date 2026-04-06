from ._opengl import OpenGLRenderer as Renderer
# from ._opengl_cython import OpenGLRenderer as Renderer
from ._base_renderer import BaseRenderer, tColor

renderer: BaseRenderer = Renderer()
