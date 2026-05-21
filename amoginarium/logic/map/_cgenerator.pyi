import numpy as np

def array_get[A, B](
    array: np.typing.NDArray[A], pos: tuple[int, int], default: B = None
) -> A | B:
    """
    Get from array with default.

    :param array: get a value from a numpy array, if non-existent return default
    :param pos:
    :param default:
    :return:
    """

def iterate_chunk(chunk: np.typing.NDArray[np.float64], i: int, n_steps: int) -> bool:
    """
    Iterate a chunk.

    :param chunk: chunk buffer to iterate
    :param i: current step
    :param n_steps: max steps before deterministic conversion
    :return: True if done
    """
