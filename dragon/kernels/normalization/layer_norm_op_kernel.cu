#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/device/common_cub.h"
#include "dragon/utils/math_functions.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernels {

namespace {

template <typename T, typename AccT>
__global__ void _LayerNorm(
    const int N,
    const int C,
    const AccT epsilon,
    const T* x,
    const AccT* gamma,
    const AccT* beta,
    AccT* mu,
    AccT* rsig,
    T* y) {
  __shared__ AccT block_mu, block_rsig;
  __shared__ typename BlockReduce<AccT>::TempStorage m_storage;
  __shared__ typename BlockReduce<AccT>::TempStorage v_storage;
  const AccT scale = AccT(1) / AccT(C);
  CUDA_2D_KERNEL_LOOP1(i, N) {
    AccT m_val = AccT(0), v_val = AccT(0);
    CUDA_2D_KERNEL_LOOP2(j, C) {
      const AccT val = convert::To<AccT>(__ldg(x + i * C + j));
      m_val += val;
      v_val += val * val;
    }
    m_val = BlockReduce<AccT>(m_storage).Sum(m_val);
    v_val = BlockReduce<AccT>(v_storage).Sum(v_val);
    if (threadIdx.x == 0) {
      mu[i] = block_mu = m_val = m_val * scale;
      rsig[i] = block_rsig = rsqrt(v_val * scale - m_val * m_val + epsilon);
    }
    __syncthreads();
    CUDA_2D_KERNEL_LOOP2(j, C) {
      const int index = i * C + j;
      m_val = convert::To<AccT>(__ldg(x + index));
      m_val = (m_val - block_mu) * block_rsig;
      y[index] = convert::To<T>(fma(m_val, __ldg(gamma + j), __ldg(beta + j)));
    }
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

#define DEFINE_KERNEL_LAUNCHER(T, AccT)                        \
  template <>                                                  \
  void LayerNorm<T, AccT, CUDAContext>(                        \
      const int N,                                             \
      const int C,                                             \
      const float epsilon,                                     \
      const T* x,                                              \
      const AccT* gamma,                                       \
      const AccT* beta,                                        \
      AccT* mu,                                                \
      AccT* rsig,                                              \
      T* y,                                                    \
      CUDAContext* ctx) {                                      \
    _LayerNorm<<<N, CUDA_THREADS, 0, ctx->cuda_stream()>>>(    \
        N,                                                     \
        C,                                                     \
        AccT(epsilon),                                         \
        reinterpret_cast<const math::ScalarType<T>::type*>(x), \
        gamma,                                                 \
        beta,                                                  \
        mu,                                                    \
        rsig,                                                  \
        reinterpret_cast<math::ScalarType<T>::type*>(y));      \
  }

DEFINE_KERNEL_LAUNCHER(float16, float);
DEFINE_KERNEL_LAUNCHER(float, float);
DEFINE_KERNEL_LAUNCHER(double, double);
#undef DEFINE_KERNEL_LAUNCHER

} // namespace kernels

} // namespace dragon

#endif // USE_CUDA
