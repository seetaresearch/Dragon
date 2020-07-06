#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernel {

namespace {

template <typename T>
__global__ void _IndexSelect(
    const int nthreads,
    const int inner_dim,
    const int axis_dim,
    const int num_indices,
    const int64_t* indices,
    const T* x,
    T* y) {
  CUDA_1D_KERNEL_LOOP(yi, nthreads) {
    const int j = yi % inner_dim;
    const int i = yi / inner_dim / num_indices;
#if __CUDA_ARCH__ >= 350
    int index = __ldg(indices + ((yi / inner_dim) % num_indices));
#else
    int index = indices[(yi / inner_dim) % num_indices];
#endif
    index = index >= 0 ? index : index + axis_dim;
    y[yi] = x[(i * axis_dim + index) * inner_dim + j];
  }
}

template <typename T>
__global__ void _IndexSelectGrad(
    const int nthreads,
    const int inner_dim,
    const int axis_dim,
    const int num_indices,
    const int64_t* indices,
    const T* dy,
    T* dx) {
  CUDA_1D_KERNEL_LOOP(ti, nthreads) {
    const int i = ti / inner_dim;
    const int j = ti % inner_dim;
    const int c = i * axis_dim * inner_dim + j;
    const T* offset_dy = dy + i * num_indices * inner_dim + j;
    for (int k = 0; k < num_indices; ++k) {
#if __CUDA_ARCH__ >= 350
      int index = __ldg(indices + k);
#else
      int index = indices[k];
#endif
      index = index >= 0 ? index : index + axis_dim;
      dx[c + index * inner_dim] += (*offset_dy);
      offset_dy += inner_dim;
    }
  }
}

template <>
__global__ void _IndexSelectGrad<half>(
    const int nthreads,
    const int inner_dim,
    const int axis_dim,
    const int num_indices,
    const int64_t* indices,
    const half* dy,
    half* dx) {
  CUDA_1D_KERNEL_LOOP(ti, nthreads) {
#if __CUDA_ARCH__ >= 530
    const int i = ti / inner_dim;
    const int j = ti % inner_dim;
    const int c = i * axis_dim * inner_dim + j;
    const half* offset_dy = dy + i * num_indices * inner_dim + j;
    for (int k = 0; k < num_indices; ++k) {
      int index = __ldg(indices + j);
      index = index >= 0 ? index : index + axis_dim;
      index = c + index * inner_dim;
      dx[index] = __hadd(dx[index], *(offset_dy));
      offset_dy += inner_dim;
    }
#endif
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

template <>
void IndexSelectGrad<float16, CUDAContext>(
    const int outer_dim,
    const int inner_dim,
    const int axis_dim,
    const int num_indices,
    const int64_t* indices,
    const float16* dy,
    float16* dx,
    CUDAContext* ctx) {
  const int nthreads = outer_dim * inner_dim;
  _IndexSelectGrad<<<
      CUDA_BLOCKS(nthreads),
      CUDA_THREADS,
      0,
      ctx->cuda_stream()>>>(
      nthreads,
      inner_dim,
      axis_dim,
      num_indices,
      indices,
      reinterpret_cast<const half*>(dy),
      reinterpret_cast<half*>(dx));
} // IndexSelectGrad

#define DEFINE_KERNEL_LAUNCHER(T)                                   \
  template <>                                                       \
  void IndexSelect<T, CUDAContext>(                                 \
      const int outer_dim,                                          \
      const int inner_dim,                                          \
      const int axis_dim,                                           \
      const int num_indices,                                        \
      const int64_t* indices,                                       \
      const T* x,                                                   \
      T* y,                                                         \
      CUDAContext* ctx) {                                           \
    const int nthreads = outer_dim * num_indices * inner_dim;       \
    _IndexSelect<<<                                                 \
        CUDA_BLOCKS(nthreads),                                      \
        CUDA_THREADS,                                               \
        0,                                                          \
        ctx->cuda_stream()>>>(                                      \
        nthreads, inner_dim, axis_dim, num_indices, indices, x, y); \
  }

#define DEFINE_GRAD_KERNEL_LAUNCHER(T)                                \
  template <>                                                         \
  void IndexSelectGrad<T, CUDAContext>(                               \
      const int outer_dim,                                            \
      const int inner_dim,                                            \
      const int axis_dim,                                             \
      const int num_indices,                                          \
      const int64_t* indices,                                         \
      const T* dy,                                                    \
      T* dx,                                                          \
      CUDAContext* ctx) {                                             \
    const int nthreads = outer_dim * inner_dim;                       \
    _IndexSelectGrad<<<                                               \
        CUDA_BLOCKS(nthreads),                                        \
        CUDA_THREADS,                                                 \
        0,                                                            \
        ctx->cuda_stream()>>>(                                        \
        nthreads, inner_dim, axis_dim, num_indices, indices, dy, dx); \
  }

DEFINE_KERNEL_LAUNCHER(bool);
DEFINE_KERNEL_LAUNCHER(int8_t);
DEFINE_KERNEL_LAUNCHER(uint8_t);
DEFINE_KERNEL_LAUNCHER(int);
DEFINE_KERNEL_LAUNCHER(int64_t);
DEFINE_KERNEL_LAUNCHER(float16);
DEFINE_KERNEL_LAUNCHER(float);
DEFINE_KERNEL_LAUNCHER(double);

DEFINE_GRAD_KERNEL_LAUNCHER(float);
DEFINE_GRAD_KERNEL_LAUNCHER(double);

#undef DEFINE_KERNEL_LAUNCHER
#undef DEFINE_GRAD_KERNEL_LAUNCHER

} // namespace kernel

} // namespace dragon

#endif // USE_CUDA