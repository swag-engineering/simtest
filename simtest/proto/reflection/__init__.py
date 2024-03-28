import os
import sys

pkg_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(pkg_dir)

from .simtest_pb2 import *
