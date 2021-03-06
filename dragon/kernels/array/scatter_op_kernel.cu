#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/math_functions.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernels {

namespace {

template <typename T, int D>
__global__ void _ScatterElements(
    const int N,
    const int axis,
    const int num_dims,
    const T value,
    const SimpleArray<int, D> X_dims,
    const SimpleArray<int, D> Y_strides,
    const int64_t* index,
    T* y) {
  CUDA_1D_KERNEL_LOOP(i, N) {
    int yi = 0, tmp = i;
    for (int d = num_dims - 1; d >= 0; --d) {
      int r;
      FIXED_DIVISOR_DIV_MOD(X_dims.data[d], tmp, &tmp, &r);
      yi += (d == axis ? index[i] : r) * Y_strides.data[d];
    }
    y[yi] = value;
  }
}

template <typename T, int D>
__global__ void _ScatterElements(
    const int N,
    const int axis,
    const int num_dims,
    const SimpleArray<int, D> X_dims,
    const SimpleArray<int, D> X_strides,
    const SimpleArray<int, D> Y_strides,
    const int64_t* index,
    const T* x,
    T* y) {
  CUDA_1D_KERNEL_LOOP(i, N) {
    int xi = 0, yi = 0, tmp = i;
    for (int d = num_dims - 1; d >= 0; --d) {
      int r;
      FIXED_DIVISOR_DIV_MOD(X_dims.data[d], tmp, &tmp, &r);
      xi += r * X_strides.data[d];
      yi += (d == axis ? index[i] : r) * Y_strides.data[d];
    }
    y[yi] = x[xi];
  }
}

template <typename T, typename AccT, int D>
__global__ void _ScatterAdd(
    const int N,
    const int axis,
    const int num_dims,
    const SimpleArray<int, D> X_dims,
    const SimpleArray<int, D> X_strides,
    const SimpleArray<int, D> Y_strides,
    const int64_t* index,
    const T* x,
    AccT* y) {
  CUDA_1D_KERNEL_LOOP(i, N) {
    int xi = 0, yi = 0, tmp = i;
    for (int d = num_dims - 1; d >= 0; --d) {
      int r;
      FIXED_DIVISOR_DIV_MOD(X_dims.data[d], tmp, &tmp, &r);
      xi += r * X_strides.data[d];
      yi += (d == axis ? index[i] : r) * Y_strides.data[d];
    }
    math::utils::AtomicAdd(y + yi, convert::To<AccT>(x[xi]));
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

#define DEFINE_KERNEL_LAUNCHER(name, T)                                        \
  template <>                                                                  \
  void name<T, CUDAContext>(                                                   \
      const int axis,                                                          \
      const int num_dims,                                                      \
      const T value,                                                           \
      const int64_t* dims,                                                     \
      const int64_t* y_strides,                                                \
      const int64_t* index,                                                    \
      T* y,                                                                    \
      CUDAContext* ctx) {                                                      \
    CUDA_TENSOR_DIMS_CHECK(num_dims);                                          \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> X_dims;                             \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> Y_strides;                          \
    const auto N =                                                             \
        std::accumulate(dims, dims + num_dims, 1, std::multiplies<int64_t>()); \
    for (int i = 0; i < num_dims; ++i) {                                       \
      X_dims.data[i] = dims[i];                                                \
      Y_strides.data[i] = y_strides[i];                                        \
    }                                                                          \
    _##name<<<CUDA_BLOCKS(N), CUDA_THREADS, 0, ctx->cuda_stream()>>>(          \
        N, axis, num_dims, value, X_dims, Y_strides, index, y);                \
  }

DEFINE_KERNEL_LAUNCHER(ScatterElements, bool);
DEFINE_KERNEL_LAUNCHER(ScatterElements, uint8_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int8_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int64_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, float16);
DEFINE_KERNEL_LAUNCHER(ScatterElements, float);
DEFINE_KERNEL_LAUNCHER(ScatterElements, double);
#undef DEFINE_KERNEL_LAUNCHER

#define DEFINE_KERNEL_LAUNCHER(name, T)                                        \
  template <>                                                                  \
  void name<T, CUDAContext>(                                                   \
      const int axis,                                                          \
      const int num_dims,                                                      \
      const int64_t* dims,                                                     \
      const int64_t* x_strides,                                                \
      const int64_t* y_strides,                                                \
      const int64_t* index,                                                    \
      const T* x,                                                              \
      T* y,                                                                    \
      CUDAContext* ctx) {                                                      \
    CUDA_TENSOR_DIMS_CHECK(num_dims);                                          \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> X_dims;                             \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> X_strides;                          \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> Y_strides;                          \
    const auto N =                                                             \
        std::accumulate(dims, dims + num_dims, 1, std::multiplies<int64_t>()); \
    for (int i = 0; i < num_dims; ++i) {                                       \
      X_dims.data[i] = dims[i];                                                \
      X_strides.data[i] = x_strides[i];                                        \
      Y_strides.data[i] = y_strides[i];                                        \
    }                                                                          \
    _##name<<<CUDA_BLOCKS(N), CUDA_THREADS, 0, ctx->cuda_stream()>>>(          \
        N, axis, num_dims, X_dims, X_strides, Y_strides, index, x, y);         \
  }

DEFINE_KERNEL_LAUNCHER(ScatterElements, bool);
DEFINE_KERNEL_LAUNCHER(ScatterElements, uint8_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int8_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int);
DEFINE_KERNEL_LAUNCHER(ScatterElements, int64_t);
DEFINE_KERNEL_LAUNCHER(ScatterElements, float16);
DEFINE_KERNEL_LAUNCHER(ScatterElements, float);
DEFINE_KERNEL_LAUNCHER(ScatterElements, double);
#undef DEFINE_KERNEL_LAUNCHER

#define DEFINE_KERNEL_LAUNCHER(name, T, AccT)                                  \
  template <>                                                                  \
  void name<T, AccT, CUDAContext>(                                             \
      const int axis,                                                          \
      const int num_dims,                                                      \
      const int64_t* dims,                                                     \
      const int64_t* x_strides,                                                \
      const int64_t* y_strides,                                                \
      const int64_t* index,                                                    \
      const T* x,                                                              \
      AccT* y,                                                                 \
      CUDAContext* ctx) {                                                      \
    CUDA_TENSOR_DIMS_CHECK(num_dims);                                          \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> X_dims;                             \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> X_strides;                          \
    SimpleArray<int, CUDA_TENSOR_MAX_DIMS> Y_strides;                          \
    const auto N =                                                             \
        std::accumulate(dims, dims + num_dims, 1, std::multiplies<int64_t>()); \
    for (int i = 0; i < num_dims; ++i) {                                       \
      X_dims.data[i] = dims[i];                                                \
      X_strides.data[i] = x_strides[i];                                        \
      Y_strides.data[i] = y_strides[i];                                        \
    }                                                                          \
    _##name<<<CUDA_BLOCKS(N), CUDA_THREADS, 0, ctx->cuda_stream()>>>(          \
        N,                                                                     \
        axis,                                                                  \
        num_dims,                                                              \
        X_dims,                                                                \
        X_strides,                                                             \
        Y_strides,                                                             \
        index,                                                                 \
        reinterpret_cast<const math::ScalarType<T>::type*>(x),                 \
        y);                                                                    \
  }

DEFINE_KERNEL_LAUNCHER(ScatterAdd, uint8_t, uint8_t);
DEFINE_KERNEL_LAUNCHER(ScatterAdd, int8_t, int8_t);
DEFINE_KERNEL_LAUNCHER(ScatterAdd, int, int)
DEFINE_KERNEL_LAUNCHER(ScatterAdd, int64_t, int64_t)
DEFINE_KERNEL_LAUNCHER(ScatterAdd, float16, float);
DEFINE_KERNEL_LAUNCHER(ScatterAdd, float, float)
DEFINE_KERNEL_LAUNCHER(ScatterAdd, double, float);
#undef DEFINE_KERNEL_LAUNCHER

} // namespace kernels

} // namespace dragon

#endif // USE_CUDA
