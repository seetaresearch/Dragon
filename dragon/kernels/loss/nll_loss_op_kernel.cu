#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernel {

namespace {

template <typename LogitType, typename TargetType>
__global__ void _NLLLoss(
    const int nthreads,
    const int axis_dim,
    const int inner_dim,
    const int ignore_index,
    const LogitType* log_prob,
    const TargetType* target,
    LogitType* loss,
    int* mask) {
  CUDA_1D_KERNEL_LOOP(yi, nthreads) {
    const int i = yi / inner_dim;
    const int j = yi % inner_dim;
    const int label = target[i * inner_dim + j];
    if (label == ignore_index) {
      loss[yi] = mask[yi] = 0;
    } else {
      loss[yi] = -log_prob[(i * axis_dim + label) * inner_dim + j];
      mask[yi] = 1;
    }
  }
}

template <typename LogitType, typename TargetType>
__global__ void _NLLLossGrad(
    const int nthreads,
    const int axis_dim,
    const int inner_dim,
    const int ignore_index,
    const LogitType* log_prob,
    const TargetType* target,
    LogitType* dx,
    int* mask) {
  CUDA_1D_KERNEL_LOOP(yi, nthreads) {
    const int i = yi / inner_dim;
    const int j = yi % inner_dim;
    const int label = target[i * inner_dim + j];
    if (label == ignore_index) {
      mask[yi] = 0;
    } else {
      dx[(i * axis_dim + label) * inner_dim + j] = LogitType(-1);
      mask[yi] = 1;
    }
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

#define DEFINE_KERNEL_LAUNCHER(name, LogitType, TargetType)                  \
  template <>                                                                \
  void name<LogitType, TargetType, CUDAContext>(                             \
      const int outer_dim,                                                   \
      const int axis_dim,                                                    \
      const int inner_dim,                                                   \
      const int ignore_index,                                                \
      const LogitType* log_prob,                                             \
      const TargetType* target,                                              \
      LogitType* loss,                                                       \
      int* mask,                                                             \
      CUDAContext* ctx) {                                                    \
    auto nthreads = outer_dim * inner_dim;                                   \
    _##name<<<CUDA_BLOCKS(nthreads), CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
        nthreads,                                                            \
        axis_dim,                                                            \
        inner_dim,                                                           \
        ignore_index,                                                        \
        log_prob,                                                            \
        target,                                                              \
        loss,                                                                \
        mask);                                                               \
  }

DEFINE_KERNEL_LAUNCHER(NLLLoss, float, float);
DEFINE_KERNEL_LAUNCHER(NLLLoss, float, int64_t);
DEFINE_KERNEL_LAUNCHER(NLLLoss, double, double);
DEFINE_KERNEL_LAUNCHER(NLLLoss, double, int64_t);

DEFINE_KERNEL_LAUNCHER(NLLLossGrad, float, float);
DEFINE_KERNEL_LAUNCHER(NLLLossGrad, float, int64_t);
DEFINE_KERNEL_LAUNCHER(NLLLossGrad, double, double);
DEFINE_KERNEL_LAUNCHER(NLLLossGrad, double, int64_t);

#undef DEFINE_KERNEL_LAUNCHER

} // namespace kernel

} // namespace dragon

#endif // USE_CUDA