import warnings
import chainer
import numpy as np
import collections
import numbers

"""
From http://wiki.scipy.org/Cookbook/SegmentAxis
"""

def segment_axis(a, length, overlap=0, axis=None, end='cut', endvalue=0):
    """ Generate a new array that chops the given array along the given axis into overlapping frames.

    :param a: The array to segment
    :param length: The length of each frame
    :param overlap: The number of array elements by which the frames should overlap
    :param axis: The axis to operate on; if None, act on the flattened array
    :param end: What to do with the last frame, if the array is not evenly
        divisible into pieces. Options are:
        * 'cut'   Simply discard the extra values
        * 'wrap'  Copy values from the beginning of the array
        * 'pad'   Pad with a constant value
    :param endvalue: The value to use for end='pad'
    :return:

    The array is not copied unless necessary (either because it is
    unevenly strided and being flattened or because end is set to
    'pad' or 'wrap').

    Example
    -------
    >>> segment_axis(np.arange(10), 4, 2)
    array([[0, 1, 2, 3],
           [2, 3, 4, 5],
           [4, 5, 6, 7],
           [6, 7, 8, 9]])
    """

    if axis is None:
        a = np.ravel(a)  # may copy
        axis = 0

    l = a.shape[axis]

    if overlap >= length: raise ValueError(
        "frames cannot overlap by more than 100%")
    if overlap < 0 or length <= 0: raise ValueError(
        "overlap must be nonnegative and length must be positive")

    if l < length or (l - length) % (length - overlap):
        if l > length:
            roundup = length + (1 + (l - length) // (length - overlap)) * (
            length - overlap)
            rounddown = length + ((l - length) // (length - overlap)) * (
            length - overlap)
        else:
            roundup = length
            rounddown = 0
        assert rounddown < l < roundup
        assert roundup == rounddown + (length - overlap) or (
        roundup == length and rounddown == 0)
        a = a.swapaxes(-1, axis)

        if end == 'cut':
            a = a[..., :rounddown]
        elif end in ['pad', 'wrap']:  # copying will be necessary
            s = list(a.shape)
            s[-1] = roundup
            b = np.empty(s, dtype=a.dtype)
            b[..., :l] = a
            if end == 'pad':
                b[..., l:] = endvalue
            elif end == 'wrap':
                b[..., l:] = a[..., :roundup - l]
            a = b

        a = a.swapaxes(-1, axis)

    l = a.shape[axis]
    if l == 0: raise ValueError(
        "Not enough data points to segment array in 'cut' mode; "
        "try 'pad' or 'wrap'")
    assert l >= length
    assert (l - length) % (length - overlap) == 0
    n = 1 + (l - length) // (length - overlap)
    s = a.strides[axis]
    newshape = a.shape[:axis] + (n, length) + a.shape[axis + 1:]
    newstrides = a.strides[:axis] + ((length - overlap) * s, s) + a.strides[
                                                                  axis + 1:]

    if not a.flags.contiguous:
        a = a.copy()
        newstrides = a.strides[:axis] + ((length - overlap) * s, s) + a.strides[
                                                                      axis + 1:]
        return np.ndarray.__new__(np.ndarray, strides=newstrides,
                                  shape=newshape, buffer=a, dtype=a.dtype)

    try:
        return np.ndarray.__new__(np.ndarray, strides=newstrides,
                                  shape=newshape, buffer=a, dtype=a.dtype)
    except TypeError or ValueError:
        warnings.warn("Problem with ndarray creation forces copy.")
        a = a.copy()
        # Shape doesn't change but strides does
        newstrides = a.strides[:axis] + ((length - overlap) * s, s) + a.strides[
                                                                      axis + 1:]
        return np.ndarray.__new__(np.ndarray, strides=newstrides,
                                  shape=newshape, buffer=a, dtype=a.dtype)

def to_ndarray(data, copy=True):
        if copy:
            cp = lambda x: np.copy(x)
        else:
            cp = lambda x: x
        if isinstance(data, chainer.Variable):
            return cp(data.num)
        elif isinstance(data, np.ndarray):
            return cp(data)
        elif isinstance(data, numbers.Number):
            return data
        elif isinstance(data, collections.Iterable):
            return np.asarray(data)
        else:
            raise ValueError('Unknown type of data {}. Cannot add to list'
                             .format(type(data)))