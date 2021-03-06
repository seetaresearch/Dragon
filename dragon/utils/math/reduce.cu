#ifdef USE_CUDA

#include "dragon/core/workspace.h"
#include "dragon/utils/device/common_cub.h"
#include "dragon/utils/device/common_thrust.h"
#include "dragon/utils/math/blas.h"
#include "dragon/utils/math/functional.h"
#include "dragon/utils/math/reduce.h"
#include "dragon/utils/math/utils.h"

namespace dragon {

namespace math {

namespace {

template <typename T, typename AccT, class Reducer>
__global__ void _RowwiseReduce(
    const int rows,
    const int cols,
    const Reducer reducer,
    const AccT init,
    const AccT scale,
    const T* x,
    T* y) {
  __shared__ typename BlockReduce<AccT>::TempStorage storage;
  CUDA_2D_KERNEL_LOOP1(i, cols) {
    AccT val = init;
    CUDA_2D_KERNEL_LOOP2(j, rows) {
      val = reducer(val, convert::To<AccT>(x[j * cols + i]));
    }
    val = BlockReduce<AccT>(storage).Reduce(val, reducer);
    if (threadIdx.x == 0) {
      y[i] = convert::To<T>(val * scale);
    }
  }
}

template <typename T, typename AccT, class Reducer>
__global__ void _ColwiseReduce(
    const int rows,
    const int cols,
    const Reducer reducer,
    const AccT init,
    const AccT scale,
    const T* x,
    T* y) {
  __shared__ typename BlockReduce<AccT>::TempStorage storage;
  CUDA_2D_KERNEL_LOOP1(i, rows) {
    AccT val = init;
    CUDA_2D_KERNEL_LOOP2(j, cols) {
      val = reducer(val, convert::To<AccT>(x[i * cols + j]));
    }
    val = BlockReduce<AccT>(storage).Reduce(val, reducer);
    if (threadIdx.x == 0) {
      y[i] = convert::To<T>(val * scale);
    }
  }
}

template <typename T, typename AccT, class Reducer, int D>
__global__ void _GenericReduce(
    const int rows,
    const int cols,
    const SimpleArray<int, D> x_dims,
    const SimpleArray<int, D> x_strides,
    const Reducer reducer,
    const AccT init,
    const AccT scale,
    const T* x,
    T* y) {
  __shared__ typename BlockReduce<AccT>::TempStorage storage;
  CUDA_2D_KERNEL_LOOP1(i, rows) {
    AccT val = init;
    CUDA_2D_KERNEL_LOOP2(j, cols) {
      int xi = 0, c = i * cols + j;
#pragma unroll
      for (int d = D - 1; d >= 0; --d) {
        int r;
        FIXED_DIVISOR_DIV_MOD(x_dims.data[d], c, &c, &r);
        xi += r * x_strides.data[d];
      }
      val = reducer(val, convert::To<AccT>(x[xi]));
    }
    val = BlockReduce<AccT>(storage).Reduce(val, reducer);
    if (threadIdx.x == 0) {
      y[i] = convert::To<T>(val * scale);
    }
  }
}

template <typename T, typename AccT, class Reducer, int D>
void _GenericReduceImpl(
    const int* dims,
    const int num_axes,
    const int* axes,
    const Reducer reducer,
    const AccT init,
    const AccT scale,
    const T* x,
    T* y,
    CUDAContext* ctx) {
  SimpleArray<int, D> transpose_axes;
  SimpleArray<int, D> transpose_strides;
  SimpleArray<int, D> transpose_dims;
  math::utils::TransposeAxesForReduce(D, num_axes, axes, transpose_axes.data);
  math::utils::ComputeTransposeStrides(
      D, dims, transpose_axes.data, transpose_strides.data);
  int rows = 1, cols = 1;
  const int pivot = D - num_axes;
  for (int i = 0; i < pivot; ++i) {
    rows *= dims[transpose_axes.data[i]];
  }
  for (int i = pivot; i < D; ++i) {
    cols *= dims[transpose_axes.data[i]];
  }
  for (int i = 0; i < D; ++i) {
    transpose_dims.data[i] = dims[transpose_axes.data[i]];
  }
  _GenericReduce<<<rows, CUDA_THREADS, 0, ctx->cuda_stream()>>>(
      rows,
      cols,
      transpose_dims,
      transpose_strides,
      reducer,
      init,
      scale,
      x,
      y);
}

#define DEFINE_REDUCE_DISPATCHER(name)                               \
  template <typename T, typename AccT, typename Reducer>             \
  void _Reduce##name(                                                \
      const int num_dims,                                            \
      const int* dims,                                               \
      const int num_axes,                                            \
      const int* axes,                                               \
      const Reducer reducer,                                         \
      const AccT init,                                               \
      const AccT scale,                                              \
      const T* x,                                                    \
      T* y,                                                          \
      CUDAContext* ctx) {                                            \
    int rows, cols;                                                  \
    vec32_t out_dims(dims, dims + num_dims);                         \
    for (int i = 0; i < num_axes; ++i) {                             \
      out_dims[axes[i]] = 1;                                         \
    }                                                                \
    if (math::utils::IsRowwiseReduce(                                \
            num_dims, dims, out_dims.data(), &rows, &cols)) {        \
      _RowwiseReduce<<<cols, CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
          rows, cols, reducer, init, scale, x, y);                   \
      return;                                                        \
    }                                                                \
    if (math::utils::IsColwiseReduce(                                \
            num_dims, dims, out_dims.data(), &rows, &cols)) {        \
      _ColwiseReduce<<<rows, CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
          rows, cols, reducer, init, scale, x, y);                   \
      return;                                                        \
    }                                                                \
    CUDA_TENSOR_DIMS_CHECK(num_dims);                                \
    DISPATCH_FUNC_BY_VALUE_WITH_TYPE_3(                              \
        _GenericReduceImpl,                                          \
        T,                                                           \
        AccT,                                                        \
        Reducer,                                                     \
        num_dims,                                                    \
        dims,                                                        \
        num_axes,                                                    \
        axes,                                                        \
        reducer,                                                     \
        init,                                                        \
        scale,                                                       \
        x,                                                           \
        y,                                                           \
        ctx);                                                        \
  }

DEFINE_REDUCE_DISPATCHER(Max);
DEFINE_REDUCE_DISPATCHER(Min);
DEFINE_REDUCE_DISPATCHER(Sum);
#undef DEFINE_REDUCE_DISPATCHER

} // namespace

// Disable FP16 DeviceReduce.
// We found that FP16 accumulator drops too many small values in
// empirical experiments.
template <>
DRAGON_API void ReduceSum<float16, CUDAContext>(
    const int num_dims,
    const int* dims,
    const int num_axes,
    const int* axes,
    const float scale,
    const float16* x,
    float16* y,
    CUDAContext* ctx) {
  // NB: Performance may drop in some cases.
  _ReduceSum(
      num_dims,
      dims,
      num_axes,
      axes,
      math::PlusFunctor<float>(),
      0.f,
      scale,
      x,
      y,
      ctx);
}

#define DEFINE_REDUCE_FUNC(name, T, AccT, Reducer, kInit)                  \
  template <>                                                              \
  DRAGON_API void Reduce##name<T, CUDAContext>(                            \
      const int num_dims,                                                  \
      const int* dims,                                                     \
      const int num_axes,                                                  \
      const int* axes,                                                     \
      const float scale,                                                   \
      const T* x,                                                          \
      T* y,                                                                \
      CUDAContext* ctx) {                                                  \
    const int count =                                                      \
        std::accumulate(dims, dims + num_dims, 1, std::multiplies<int>()); \
    if (num_dims == num_axes && count > 10000) {                           \
      size_t ws_nbytes = 0;                                                \
      cub::DeviceReduce::Reduce(                                           \
          nullptr,                                                         \
          ws_nbytes,                                                       \
          x,                                                               \
          y,                                                               \
          count,                                                           \
          Reducer<T>(),                                                    \
          convert::To<T>(kInit),                                           \
          ctx->cuda_stream());                                             \
      cub::DeviceReduce::Reduce(                                           \
          ctx->workspace()->data<CUDAContext>({ws_nbytes}, "data:1")[0],   \
          ws_nbytes,                                                       \
          x,                                                               \
          y,                                                               \
          count,                                                           \
          Reducer<T>(),                                                    \
          convert::To<T>(kInit),                                           \
          ctx->cuda_stream());                                             \
      math::Scale(1, scale, y, y, ctx);                                    \
      return;                                                              \
    }                                                                      \
    _Reduce##name(                                                         \
        num_dims,                                                          \
        dims,                                                              \
        num_axes,                                                          \
        axes,                                                              \
        Reducer<AccT>(),                                                   \
        convert::To<AccT>(kInit),                                          \
        convert::To<AccT>(scale),                                          \
        x,                                                                 \
        y,                                                                 \
        ctx);                                                              \
  }

DEFINE_REDUCE_FUNC(
    Max,
    uint8_t,
    uint8_t,
    math::MaxFunctor,
    std::numeric_limits<uint8_t>::lowest());
DEFINE_REDUCE_FUNC(
    Max,
    int8_t,
    int8_t,
    math::MaxFunctor,
    std::numeric_limits<int8_t>::lowest());
DEFINE_REDUCE_FUNC(
    Max,
    int,
    int,
    math::MaxFunctor,
    std::numeric_limits<int>::lowest());
DEFINE_REDUCE_FUNC(
    Max,
    int64_t,
    int64_t,
    math::MaxFunctor,
    std::numeric_limits<int64_t>::lowest());
DEFINE_REDUCE_FUNC(
    Max,
    float16,
    float,
    math::MaxFunctor,
    cub::Traits<half>::Lowest());
DEFINE_REDUCE_FUNC(
    Max,
    float,
    float,
    math::MaxFunctor,
    std::numeric_limits<float>::lowest());
DEFINE_REDUCE_FUNC(
    Max,
    double,
    double,
    math::MaxFunctor,
    std::numeric_limits<double>::lowest());
DEFINE_REDUCE_FUNC(
    Min,
    uint8_t,
    uint8_t,
    math::MinFunctor,
    std::numeric_limits<uint8_t>::max());
DEFINE_REDUCE_FUNC(
    Min,
    int8_t,
    int8_t,
    math::MinFunctor,
    std::numeric_limits<int8_t>::max());
DEFINE_REDUCE_FUNC(
    Min,
    int,
    int,
    math::MinFunctor,
    std::numeric_limits<int>::max());
DEFINE_REDUCE_FUNC(
    Min,
    int64_t,
    int64_t,
    math::MinFunctor,
    std::numeric_limits<int64_t>::max());
DEFINE_REDUCE_FUNC(
    Min,
    float16,
    float,
    math::MinFunctor,
    cub::Traits<half>::Max());
DEFINE_REDUCE_FUNC(
    Min,
    float,
    float,
    math::MinFunctor,
    std::numeric_limits<float>::max());
DEFINE_REDUCE_FUNC(
    Min,
    double,
    double,
    math::MinFunctor,
    std::numeric_limits<double>::max());
DEFINE_REDUCE_FUNC(Sum, uint8_t, uint8_t, math::PlusFunctor, uint8_t(0));
DEFINE_REDUCE_FUNC(Sum, int8_t, int8_t, math::PlusFunctor, int8_t(0));
DEFINE_REDUCE_FUNC(Sum, int, int, math::PlusFunctor, int(0));
DEFINE_REDUCE_FUNC(Sum, int64_t, int64_t, math::PlusFunctor, int64_t(0));
DEFINE_REDUCE_FUNC(Sum, float, float, math::PlusFunctor, 0.f);
DEFINE_REDUCE_FUNC(Sum, double, double, math::PlusFunctor, 0.);
#undef DEFINE_REDUCE_FUNC

#define DEFINE_SUM_FUNC(T)                                                  \
  template <>                                                               \
  DRAGON_API void Sum<T, CUDAContext>(                                      \
      const int N, const float alpha, const T* x, T* y, CUDAContext* ctx) { \
    vec32_t dims = {N}, axes = {0};                                         \
    math::ReduceSum(1, dims.data(), 1, axes.data(), alpha, x, y, ctx);      \
  }

DEFINE_SUM_FUNC(uint8_t);
DEFINE_SUM_FUNC(int8_t);
DEFINE_SUM_FUNC(int);
DEFINE_SUM_FUNC(int64_t);
DEFINE_SUM_FUNC(float16);
DEFINE_SUM_FUNC(float);
DEFINE_SUM_FUNC(double);
#undef DEFINE_SUM_FUNC

#define DEFINE_SUM_FUNC(T)                                            \
  template <>                                                         \
  DRAGON_API T Sum<T, CUDAContext>(                                   \
      const int N, const float alpha, const T* x, CUDAContext* ctx) { \
    auto policy = thrust::cuda::par.on(ctx->cuda_stream());           \
    auto val = thrust::reduce(policy, x, x + N) * alpha;              \
    return static_cast<T>(val);                                       \
  }

DEFINE_SUM_FUNC(uint8_t);
DEFINE_SUM_FUNC(int8_t);
DEFINE_SUM_FUNC(int);
DEFINE_SUM_FUNC(int64_t);
DEFINE_SUM_FUNC(float);
DEFINE_SUM_FUNC(double);
#undef DEFINE_SUM_FUNC

} // namespace math

} // namespace dragon

#endif // USE_CUDA
