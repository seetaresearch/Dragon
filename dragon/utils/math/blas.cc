#include "dragon/utils/math/blas.h"
#include "dragon/utils/device/common_eigen.h"

namespace dragon {

namespace math {

template <>
DRAGON_API void Scale<float16, CPUContext>(
    const int N,
    const float alpha,
    const float16* x,
    float16* y,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_SCALE_FUNC(T)                                               \
  template <>                                                              \
  DRAGON_API void Scale<T, CPUContext>(                                    \
      const int N, const float alpha, const T* x, T* y, CPUContext* ctx) { \
    EigenVectorArrayMap<T>(y, N) =                                         \
        ConstEigenVectorArrayMap<T>(x, N) * T(alpha);                      \
  }

DEFINE_SCALE_FUNC(int8_t);
DEFINE_SCALE_FUNC(uint8_t);
DEFINE_SCALE_FUNC(int);
DEFINE_SCALE_FUNC(int64_t);
DEFINE_SCALE_FUNC(float);
DEFINE_SCALE_FUNC(double);
#undef DEFINE_SCALE_FUNC

#define DEFINE_COPY_FUNC(T)                             \
  template <>                                           \
  DRAGON_API void Copy<T, CPUContext>(                  \
      const int N, const T* x, T* y, CPUContext* ctx) { \
    if (x != y && N > 0) {                              \
      memcpy(y, x, sizeof(T) * N);                      \
    }                                                   \
  }

DEFINE_COPY_FUNC(bool);
DEFINE_COPY_FUNC(int8_t);
DEFINE_COPY_FUNC(uint8_t);
DEFINE_COPY_FUNC(int);
DEFINE_COPY_FUNC(int64_t);
DEFINE_COPY_FUNC(float16);
DEFINE_COPY_FUNC(float);
DEFINE_COPY_FUNC(double);
#undef DEFINE_COPY_FUNC

#define DEFINE_COPY_FUNC(T)                                               \
  template <>                                                             \
  DRAGON_API void Copy<T, CPUContext>(                                    \
      const int N,                                                        \
      const int incx,                                                     \
      const int incy,                                                     \
      const T* x,                                                         \
      T* y,                                                               \
      CPUContext* ctx) {                                                  \
    if (x != y && N > 0) {                                                \
      EigenStridedVectorMap<T>(y, 1, N, EigenInnerStride(incy)) =         \
          ConstEigenStridedVectorMap<T>(x, 1, N, EigenInnerStride(incx)); \
    }                                                                     \
  }

DEFINE_COPY_FUNC(bool);
DEFINE_COPY_FUNC(int8_t);
DEFINE_COPY_FUNC(uint8_t);
DEFINE_COPY_FUNC(int);
DEFINE_COPY_FUNC(int64_t);
DEFINE_COPY_FUNC(float16);
DEFINE_COPY_FUNC(float);
DEFINE_COPY_FUNC(double);
#undef DEFINE_COPY_FUNC

#define DEFINE_COPY_FUNC(T)                            \
  template <>                                          \
  DRAGON_API void CopyMatrix<T, CPUContext>(           \
      const int M,                                     \
      const int N,                                     \
      const int ldx,                                   \
      const int ldy,                                   \
      const T* x,                                      \
      T* y,                                            \
      CPUContext* ctx) {                               \
    if (M <= 0 || N <= 0) return;                      \
    if (ldx == N && ldy == N) {                        \
      if (x != y) memcpy(y, x, sizeof(T) * M * N);     \
      return;                                          \
    }                                                  \
    for (int i = 0; i < M; ++i) {                      \
      memcpy(y + ldy * i, x + ldx * i, sizeof(T) * N); \
    }                                                  \
  }

DEFINE_COPY_FUNC(bool);
DEFINE_COPY_FUNC(int8_t);
DEFINE_COPY_FUNC(uint8_t);
DEFINE_COPY_FUNC(int);
DEFINE_COPY_FUNC(int64_t);
DEFINE_COPY_FUNC(float16);
DEFINE_COPY_FUNC(float);
DEFINE_COPY_FUNC(double);
#undef DEFINE_COPY_FUNC

template <>
DRAGON_API void Axpy<float16, CPUContext>(
    const int N,
    const float alpha,
    const float16* x,
    float16* y,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_AXPY_FUNC(T)                                                \
  template <>                                                              \
  DRAGON_API void Axpy<T, CPUContext>(                                     \
      const int N, const float alpha, const T* x, T* y, CPUContext* ctx) { \
    EigenVectorArrayMap<T>(y, N) +=                                        \
        ConstEigenVectorArrayMap<T>(x, N) * T(alpha);                      \
  }

DEFINE_AXPY_FUNC(int8_t);
DEFINE_AXPY_FUNC(uint8_t);
DEFINE_AXPY_FUNC(int);
DEFINE_AXPY_FUNC(int64_t);
DEFINE_AXPY_FUNC(float);
DEFINE_AXPY_FUNC(double);
#undef DEFINE_AXPY_FUNC

#define DEFINE_AXPBY_FUNC(T)            \
  template <>                           \
  DRAGON_API void Axpby<T, CPUContext>( \
      const int N,                      \
      const float alpha,                \
      const T* x,                       \
      const float beta,                 \
      T* y,                             \
      CPUContext* ctx) {                \
    Scale(N, beta, y, y, ctx);          \
    Axpy(N, alpha, x, y, ctx);          \
  }

DEFINE_AXPBY_FUNC(int8_t);
DEFINE_AXPBY_FUNC(uint8_t);
DEFINE_AXPBY_FUNC(int);
DEFINE_AXPBY_FUNC(int64_t);
DEFINE_AXPBY_FUNC(float16);
DEFINE_AXPBY_FUNC(float);
DEFINE_AXPBY_FUNC(double);
#undef DEFINE_AXPBY_FUNC

template <>
DRAGON_API void Dot<float16, CPUContext>(
    int N,
    const float16* a,
    const float16* b,
    float16* y,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_DOT_FUNC(T)                                                 \
  template <>                                                              \
  DRAGON_API void Dot<T, CPUContext>(                                      \
      int N, const T* a, const T* b, T* y, CPUContext* ctx) {              \
    *y = ConstEigenVectorMap<T>(a, N).dot(ConstEigenVectorMap<T>(b, N));   \
  }                                                                        \
  template <>                                                              \
  DRAGON_API T Dot<T, CPUContext>(                                         \
      int N, const T* a, const T* b, CPUContext* ctx) {                    \
    return ConstEigenVectorMap<T>(a, N).dot(ConstEigenVectorMap<T>(b, N)); \
  }

DEFINE_DOT_FUNC(float);
DEFINE_DOT_FUNC(double);
#undef DEFINE_DOT_FUNC

#define DEFINE_ASUM_FUNC(T)                                                    \
  template <>                                                                  \
  DRAGON_API void ASum<T, CPUContext>(                                         \
      const int N, const T* x, T* y, CPUContext* ctx) {                        \
    *y = ConstEigenVectorArrayMap<T>(x, N).abs().sum();                        \
  }                                                                            \
  template <>                                                                  \
  DRAGON_API T ASum<T, CPUContext>(const int N, const T* x, CPUContext* ctx) { \
    return ConstEigenVectorArrayMap<T>(x, N).abs().sum();                      \
  }

DEFINE_ASUM_FUNC(float);
DEFINE_ASUM_FUNC(double);

template <>
DRAGON_API void Gemv<float16, CPUContext>(
    const CBLAS_TRANSPOSE TransA,
    const int M,
    const int N,
    const float alpha,
    const float16* A,
    const float16* x,
    const float beta,
    float16* y,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_GEMV_FUNC(T)                                                    \
  template <>                                                                  \
  DRAGON_API void Gemv<T, CPUContext>(                                         \
      const CBLAS_TRANSPOSE TransA,                                            \
      const int M,                                                             \
      const int N,                                                             \
      const float alpha,                                                       \
      const T* A,                                                              \
      const T* x,                                                              \
      const float beta,                                                        \
      T* y,                                                                    \
      CPUContext* ctx) {                                                       \
    T _alpha_ = alpha, _beta_ = beta;                                          \
    EigenVectorMap<T> y_vec(y, TransA == CblasNoTrans ? M : N);                \
    if (beta == 0.f)                                                           \
      y_vec.setZero();                                                         \
    else                                                                       \
      y_vec *= _beta_;                                                         \
    switch (TransA) {                                                          \
      case CblasNoTrans: {                                                     \
        y_vec.noalias() += alpha *                                             \
            (ConstEigenMatrixMap<T>(A, N, M).transpose() *                     \
             ConstEigenVectorMap<T>(x, N));                                    \
        return;                                                                \
      }                                                                        \
      case CblasTrans: {                                                       \
        y_vec.noalias() += alpha *                                             \
            (ConstEigenMatrixMap<T>(A, N, M) * ConstEigenVectorMap<T>(x, M));  \
        return;                                                                \
      }                                                                        \
      default:                                                                 \
        LOG(FATAL) << "Gemv float found an unexpected CBLAS_TRANSPOSE input."; \
    }                                                                          \
  }

DEFINE_GEMV_FUNC(float);
DEFINE_GEMV_FUNC(double);
#undef DEFINE_GEMV_FUNC

template <>
DRAGON_API void Gemm<float16, CPUContext>(
    const CBLAS_TRANSPOSE TransA,
    const CBLAS_TRANSPOSE TransB,
    const int M,
    const int N,
    const int K,
    const float alpha,
    const float16* A,
    const float16* B,
    const float beta,
    float16* C,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_GEMM_FUNC(T)                                        \
  template <>                                                      \
  DRAGON_API void Gemm<T, CPUContext>(                             \
      const CBLAS_TRANSPOSE TransA,                                \
      const CBLAS_TRANSPOSE TransB,                                \
      const int M,                                                 \
      const int N,                                                 \
      const int K,                                                 \
      const float alpha,                                           \
      const T* A,                                                  \
      const T* B,                                                  \
      const float beta,                                            \
      T* C,                                                        \
      CPUContext* ctx) {                                           \
    T _alpha_ = alpha, _beta_ = beta;                              \
    auto C_mat = EigenMatrixMap<T>(C, N, M);                       \
    if (beta == 0.f)                                               \
      C_mat.setZero();                                             \
    else                                                           \
      C_mat *= _beta_;                                             \
    switch (TransA) {                                              \
      case CblasNoTrans: {                                         \
        switch (TransB) {                                          \
          case CblasNoTrans:                                       \
            C_mat.noalias() += _alpha_ *                           \
                (ConstEigenMatrixMap<T>(B, N, K) *                 \
                 ConstEigenMatrixMap<T>(A, K, M));                 \
            return;                                                \
          case CblasTrans:                                         \
            C_mat.noalias() += _alpha_ *                           \
                (ConstEigenMatrixMap<T>(B, K, N).transpose() *     \
                 ConstEigenMatrixMap<T>(A, K, M));                 \
            return;                                                \
          default:                                                 \
            LOG(FATAL) << "Unexpected CBLAS_TRANSPOSE for TransB"; \
        }                                                          \
      }                                                            \
      case CblasTrans: {                                           \
        switch (TransB) {                                          \
          case CblasNoTrans:                                       \
            C_mat.noalias() += _alpha_ *                           \
                (ConstEigenMatrixMap<T>(B, N, K) *                 \
                 ConstEigenMatrixMap<T>(A, M, K).transpose());     \
            return;                                                \
          case CblasTrans:                                         \
            C_mat.noalias() += _alpha_ *                           \
                (ConstEigenMatrixMap<T>(B, K, N).transpose() *     \
                 ConstEigenMatrixMap<T>(A, M, K).transpose());     \
            return;                                                \
          default:                                                 \
            LOG(FATAL) << "Unexpected CBLAS_TRANSPOSE for TransB"; \
        }                                                          \
      }                                                            \
      default:                                                     \
        LOG(FATAL) << "Unexpected CBLAS_TRANSPOSE for TransA";     \
    }                                                              \
  }

DEFINE_GEMM_FUNC(float);
DEFINE_GEMM_FUNC(double);
#undef DEFINE_GEMM_FUNC

template <>
DRAGON_API void GemmBatched<float16, CPUContext>(
    const CBLAS_TRANSPOSE TransA,
    const CBLAS_TRANSPOSE TransB,
    const int batch_size,
    const int M,
    const int N,
    const int K,
    const float alpha,
    const float16** A,
    const float16** B,
    const float beta,
    float16** C,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_BATCHED_GEMM_FUNC(T)                                      \
  template <>                                                            \
  DRAGON_API void GemmBatched<T, CPUContext>(                            \
      const CBLAS_TRANSPOSE TransA,                                      \
      const CBLAS_TRANSPOSE TransB,                                      \
      const int batch_size,                                              \
      const int M,                                                       \
      const int N,                                                       \
      const int K,                                                       \
      const float alpha,                                                 \
      const T** A,                                                       \
      const T** B,                                                       \
      const float beta,                                                  \
      T** C,                                                             \
      CPUContext* ctx) {                                                 \
    for (int i = 0; i < batch_size; ++i) {                               \
      Gemm(TransA, TransB, M, N, K, alpha, A[i], B[i], beta, C[i], ctx); \
    }                                                                    \
  }

DEFINE_BATCHED_GEMM_FUNC(float);
DEFINE_BATCHED_GEMM_FUNC(double);
#undef DEFINE_BATCHED_GEMM_FUNC

template <>
DRAGON_API void GemmStridedBatched<float16, CPUContext>(
    const CBLAS_TRANSPOSE TransA,
    const CBLAS_TRANSPOSE TransB,
    const int batch_size,
    const int M,
    const int N,
    const int K,
    const int A_stride,
    const int B_stride,
    const int C_stride,
    const float alpha,
    const float16* A,
    const float16* B,
    const float beta,
    float16* C,
    CPUContext* ctx) {
  CPU_FP16_NOT_SUPPORTED;
}

#define DEFINE_STRIDED_BATCHED_GEMM_FUNC(T)          \
  template <>                                        \
  DRAGON_API void GemmStridedBatched<T, CPUContext>( \
      const CBLAS_TRANSPOSE TransA,                  \
      const CBLAS_TRANSPOSE TransB,                  \
      const int batch_size,                          \
      const int M,                                   \
      const int N,                                   \
      const int K,                                   \
      const int A_stride,                            \
      const int B_stride,                            \
      const int C_stride,                            \
      const float alpha,                             \
      const T* A,                                    \
      const T* B,                                    \
      const float beta,                              \
      T* C,                                          \
      CPUContext* ctx) {                             \
    for (int i = 0; i < batch_size; ++i) {           \
      Gemm(                                          \
          TransA,                                    \
          TransB,                                    \
          M,                                         \
          N,                                         \
          K,                                         \
          alpha,                                     \
          A + i * A_stride,                          \
          B + i * B_stride,                          \
          beta,                                      \
          C + i * C_stride,                          \
          ctx);                                      \
    }                                                \
  }

DEFINE_STRIDED_BATCHED_GEMM_FUNC(float);
DEFINE_STRIDED_BATCHED_GEMM_FUNC(double);
#undef DEFINE_STRIDED_BATCHED_GEMM_FUNC

} // namespace math

} // namespace dragon
