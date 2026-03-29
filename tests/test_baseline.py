import cv2
import numpy as np

def test_environment_setup():
    """
    Sanity check to ensure the CI/CD pipeline installs 
    OpenCV and Numpy correctly before we run complex CV logic.
    """
    assert cv2.__version__ is not None
    assert np.__version__ is not None

def test_math_baseline():
    """
    Basic threshold math check to ensure the runner operates correctly.
    """
    assert 10 + 10 == 20