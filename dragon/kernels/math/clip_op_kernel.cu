#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/cast.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernel {

namespace {

template <typename T>
__global__ void
_Clip(const int nthreads, const T low, const T high, const T* x, T* y) {
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
    y[i] = max(low, min(x[i], high));
  }
}

template <>
__global__ void _Clip<half>(
    const int nthreads,
    const half low,
    const half high,
    const half* x,
    half* y) {
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
#if __CUDA_ARCH__ >= 530
    const half val = __hlt(__ldg(x + i), high) ? __ldg(x + i) : high;
    y[i] = __hgt(val, low) ? val : low;
#endif
  }
}

template <typename T>
__global__ void _ClipGrad(
    const int nthreads,
    const T low,
    const T high,
    const T* dy,
    const T* x,
    T* dx) {
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
#if __CUDA_ARCH__ >= 350
    dx[i] = __ldg(x + i) < low || __ldg(x + i) > high ? T(0) : dy[i];
#else
    dx[i] = x[i] < low || x[i] > high ? T(0) : dy[i];
#endif
  }
}

template <>
__global__ void _ClipGrad<half>(
    const int nthreads,
    const half low,
    const half high,
    const half* dy,
    const half* x,
    half* dx) {
  const half kZero = __float2half(0.f);
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
#if __CUDA_ARCH__ >= 530
    dx[i] =
        __hlt(__ldg(x + i), low) || __hgt(__ldg(x + i), high) ? kZero : dy[i];
#endif
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

template <>
void Clip<float16, CUDAContext>(
    const int count,
    const float low,
    const float high,
    const float16* x,
    float16* y,
    CUDAContext* ctx) {
  _Clip<<<CUDA_BLOCKS(count), CUDA_THREADS, 0, ctx->cuda_stream()>>>(
      count,
      cast::to<half>(low),
      cast::to<half>(high),
      reinterpret_cast<const half*>(x),
      reinterpret_cast<half*>(y));
}

template <>
void ClipGrad<float16, CUDAContext>(
    const int count,
    const float low,
    const float high,
    const float16* dy,
    const float16* x,
    float16* dx,
    CUDAContext* ctx) {
  _ClipGrad<<<CUDA_BLOCKS(count), CUDA_THREADS, 0, ctx->cuda_stream()>>>(
      count,
      cast::to<half>(low),
      cast::to<half>(high),
      reinterpret_cast<const half*>(dy),
      reinterpret_cast<const half*>(x),
      reinterpret_cast<half*>(dx));
} // ClipGrad

#define DEFINE_KERNEL_LAUNCHER(T)                                       \
  template <>                                                           \
  void Clip<T, CUDAContext>(                                            \
      const int count,                                                  \
      const float low,                                                  \
      const float high,                                                 \
      const T* x,                                                       \
      T* y,                                                             \
      CUDAContext* ctx) {                                               \
    _Clip<<<CUDA_BLOCKS(count), CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
        count, cast::to<T>(low), cast::to<T>(high), x, y);              \
  }

#define DEFINE_GRAD_KERNEL_LAUNCHER(T)                                      \
  template <>                                                               \
  void ClipGrad<T, CUDAContext>(                                            \
      const int count,                                                      \
      const float low,                                                      \
      const float high,                                                     \
      const T* dy,                                                          \
      const T* x,                                                           \
      T* dx,                                                                \
      CUDAContext* ctx) {                                                   \
    _ClipGrad<<<CUDA_BLOCKS(count), CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
        count, cast::to<T>(low), cast::to<T>(high), dy, x, dx);             \
  }

DEFINE_KERNEL_LAUNCHER(int8_t);
DEFINE_KERNEL_LAUNCHER(uint8_t);
DEFINE_KERNEL_LAUNCHER(int);
DEFINE_KERNEL_LAUNCHER(int64_t);
DEFINE_KERNEL_LAUNCHER(float);
DEFINE_KERNEL_LAUNCHER(double);

DEFINE_GRAD_KERNEL_LAUNCHER(float);
DEFINE_GRAD_KERNEL_LAUNCHER(double);

#undef DEFINE_KERNEL_LAUNCHER
#undef DEFINE_GRAD_KERNEL_LAUNCHER

} // namespace kernel

} // namespace dragon

#endif // USE_CUDA