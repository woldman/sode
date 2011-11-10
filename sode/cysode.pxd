
import numpy as np
cimport numpy as np

ctypedef np.float64_t DTYPE_t
ctypedef double parameter
ctypedef unsigned int variable

cdef class CYSODE:
    cdef public unsigned int nvars
    cdef public _sys_opts
    cpdef drift(self, np.ndarray[DTYPE_t, ndim=1] a,
                      np.ndarray[DTYPE_t, ndim=1] x, double t)
    cpdef diffusion(self, np.ndarray[DTYPE_t, ndim=1] b,
                          np.ndarray[DTYPE_t, ndim=1] x, double t)
    cdef _drift(self, double* a, double* x, double t)
    cdef _diffusion(self, double* b, double* x, double t)
    cdef _solve_EM(self, double* x1, double t1, double* x2, double dt,
                         double sqrtdt, double *a, double *b)
    cpdef get_x0(self)
    cpdef solveto(self, np.ndarray[DTYPE_t, ndim=1] x1, double t1,
                        np.ndarray[DTYPE_t, ndim=1] x2, double t2, double dtmax)
