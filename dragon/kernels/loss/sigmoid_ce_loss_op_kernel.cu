#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernel {

namespace {

template <typename T>
__global__ void _SigmoidCrossEntropy(
    const int nthreads,
    const T* logit,
    const T* target,
    T* loss,
    int* mask) {
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
    if (target[i] < 0) {
      loss[i] = mask[i] = 0;
    } else {
      loss[i] = log(T(1) + exp(logit[i] - T(2) * logit[i] * (logit[i] >= 0))) +
          logit[i] * ((logit[i] >= 0) - target[i]);
      mask[i] = 1;
    }
  }
}

template <typename T>
__global__ void _SigmoidCrossEntropyGrad(
    const int nthreads,
    const T* logit,
    const T* target,
    T* dx,
    int* mask) {
  CUDA_1D_KERNEL_LOOP(i, nthreads) {
    if (target[i] < 0) {
      dx[i] = mask[i] = 0;
    } else {
      dx[i] = T(1) / (T(1) + exp(-logit[i])) - target[i];
      mask[i] = 1;
    }
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

#define DEFINE_KERNEL_LAUNCHER(name, T)                                   \
  template <>                                                             \
  void name<T, CUDAContext>(                                              \
      const int count,                                                    \
      const T* logit,                                                     \
      const T* target,                                                    \
      T* loss,                                                            \
      int* mask,                                                          \
      CUDAContext* ctx) {                                                 \
    _##name<<<CUDA_BLOCKS(count), CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
        count, logit, target, loss, mask);                                \
  }

DEFINE_KERNEL_LAUNCHER(SigmoidCrossEntropy, float);
DEFINE_KERNEL_LAUNCHER(SigmoidCrossEntropy, double);

DEFINE_KERNEL_LAUNCHER(SigmoidCrossEntropyGrad, float);
DEFINE_KERNEL_LAUNCHER(SigmoidCrossEntropyGrad, double);

#undef DEFINE_KERNEL_LAUNCHER

} // namespace kernel

} // namespace dragon

#endif // USE_CUDA