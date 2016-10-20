from distutils.core import setup
import py2exe

#setup(console=['test.py'], options={"py2exe":{"includes":["scipy.sparse.csgraph._validation","scipy.linalg.cython_blas","scipy.linalg.cython_lapack"]}})
setup(windows=[{"script":'test.py',"dest_base" : "JoPro v0.1",}], options={"py2exe":{"includes":["scipy.sparse.csgraph._validation","scipy.linalg.cython_blas","scipy.linalg.cython_lapack"]}})