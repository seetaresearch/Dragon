#ifdef USE_CUDA

#include "dragon/core/context_cuda.h"
#include "dragon/utils/math_functions.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

namespace kernels {

namespace {

template <typename T>
__device__ float
_RoiAlignIntp(const int H, const int W, float h, float w, const T* x) {
  if (h < -1.f || h > H || w < -1.f || w > W) return T(0);

  if (h <= 0.f) h = 0.f;
  if (w <= 0.f) w = 0.f;

  int ti = (int)h, bi;
  int li = (int)w, ri;

  if (ti < H - 1) {
    bi = ti + 1;
  } else {
    ti = bi = H - 1;
    h = (float)ti;
  }

  if (li < W - 1) {
    ri = li + 1;
  } else {
    ri = li = W - 1;
    w = (float)li;
  }

  const float tl = convert::To<float>(__ldg(x + ti * W + li));
  const float tr = convert::To<float>(__ldg(x + ti * W + ri));
  const float bl = convert::To<float>(__ldg(x + bi * W + li));
  const float br = convert::To<float>(__ldg(x + bi * W + ri));

  const float v = h - ti;
  const float u = w - li;
  const float t = tl + (tr - tl) * u;
  const float b = bl + (br - bl) * u;

  return t + (b - t) * v;
}

template <typename T>
__device__ void _RoiAlignIntpParam(
    const int H,
    const int W,
    float h,
    float w,
    int& ti,
    int& bi,
    int& li,
    int& ri,
    T& v,
    T& u) {
  if (h < -1.f || h > H || w < -1.f || w > W) {
    li = ri = ti = bi = -1;
    return;
  }

  if (h <= 0.f) h = 0.f;
  if (w <= 0) w = 0.f;

  ti = (int)h;
  li = (int)w;

  if (ti < H - 1) {
    bi = ti + 1;
  } else {
    ti = bi = H - 1;
    h = (float)ti;
  }

  if (li < W - 1) {
    ri = li + 1;
  } else {
    ri = li = W - 1;
    w = (float)li;
  }

  v = h - ti;
  u = w - li;
}

template <typename T, typename AccT>
__global__ void _RoiAlign(
    const int nthreads,
    const int C,
    const int H,
    const int W,
    const int out_h,
    const int out_w,
    const float spatial_scale,
    const int sampling_ratio,
    const T* x,
    const float* rois,
    T* y) {
  CUDA_1D_KERNEL_LOOP(yi, nthreads) {
    const int w_out = yi % out_w;
    const int h_out = (yi / out_w) % out_h;
    const int c = (yi / out_w / out_h) % C;
    const int n = yi / out_w / out_h / C;

    const float* roi = rois + n * 5;
    const int batch_ind = roi[0];

    if (batch_ind < 0) {
      y[yi] = convert::To<T>(0.f);
      continue;
    }

    const float roi_wstart = roi[1] * spatial_scale;
    const float roi_hstart = roi[2] * spatial_scale;
    const float roi_wend = roi[3] * spatial_scale;
    const float roi_hend = roi[4] * spatial_scale;

    const float roi_w = max(roi_wend - roi_wstart, 1.f);
    const float roi_h = max(roi_hend - roi_hstart, 1.f);
    const float bin_h = roi_h / float(out_h);
    const float bin_w = roi_w / float(out_w);

    const float hstart = roi_hstart + h_out * bin_h;
    const float wstart = roi_wstart + w_out * bin_w;

    const int grid_h =
        sampling_ratio > 0 ? sampling_ratio : int(ceil(roi_h / float(out_h)));
    const int grid_w =
        sampling_ratio > 0 ? sampling_ratio : int(ceil(roi_w / float(out_w)));

    const T* offset_x = x + (batch_ind * C + c) * H * W;
    AccT val = AccT(0);
    for (int i = 0; i < grid_h; i++) {
      const float h = hstart + (i + .5f) * bin_h / grid_h;
      for (int j = 0; j < grid_w; j++) {
        const float w = wstart + (j + .5f) * bin_w / grid_w;
        val += _RoiAlignIntp(H, W, h, w, offset_x);
      }
    }
    y[yi] = convert::To<T>(val / AccT(grid_h * grid_w));
  }
}

template <typename T, typename AccT>
__global__ void _RoiAlignGrad(
    const int nthreads,
    const int C,
    const int H,
    const int W,
    const int out_h,
    const int out_w,
    const float spatial_scale,
    const int sampling_ratio,
    const T* dy,
    const float* rois,
    AccT* dx) {
  CUDA_1D_KERNEL_LOOP(yi, nthreads) {
    const int w_out = yi % out_w;
    const int h_out = (yi / out_w) % out_h;
    const int c = (yi / out_w / out_h) % C;
    const int n = yi / out_w / out_h / C;

    const float* roi = rois + n * 5;
    const int batch_ind = roi[0];

    if (batch_ind < 0) continue;

    const float roi_wstart = roi[1] * spatial_scale;
    const float roi_hstart = roi[2] * spatial_scale;
    const float roi_wend = roi[3] * spatial_scale;
    const float roi_hend = roi[4] * spatial_scale;

    const float roi_w = max(roi_wend - roi_wstart, 1.f);
    const float roi_h = max(roi_hend - roi_hstart, 1.f);
    const float bin_h = roi_h / float(out_h);
    const float bin_w = roi_w / float(out_w);

    const float hstart = roi_hstart + h_out * bin_h;
    const float wstart = roi_wstart + w_out * bin_w;

    const int grid_h =
        sampling_ratio > 0 ? sampling_ratio : int(ceil(roi_h / float(out_h)));
    const int grid_w =
        sampling_ratio > 0 ? sampling_ratio : int(ceil(roi_w / float(out_w)));
    const float dyi = convert::To<float>(dy[yi]) / float(grid_h * grid_w);
    float* offset_dx = dx + (batch_ind * C + c) * H * W;

    for (int i = 0; i < grid_h; i++) {
      const float h = hstart + (i + .5f) * bin_h / grid_h;
      for (int j = 0; j < grid_w; j++) {
        const float w = wstart + (j + .5f) * bin_w / grid_w;
        int ti, bi, li, ri;
        float v, u;
        _RoiAlignIntpParam(H, W, h, w, ti, bi, li, ri, v, u);
        if (li >= 0 && ri >= 0 && ti >= 0 && bi >= 0) {
          const float db = dyi * v;
          const float dt = dyi * (1.f - v);
          math::utils::AtomicAdd(offset_dx + ti * W + li, (1.f - u) * dt);
          math::utils::AtomicAdd(offset_dx + ti * W + ri, u * dt);
          math::utils::AtomicAdd(offset_dx + bi * W + li, (1.f - u) * db);
          math::utils::AtomicAdd(offset_dx + bi * W + ri, u * db);
        }
      } // End i
    } // End j
  }
}

} // namespace

/* ------------------- Launcher Separator ------------------- */

#define DEFINE_KERNEL_LAUNCHER(name, InputT, OutputT)                     \
  template <>                                                             \
  void name<InputT, CUDAContext>(                                         \
      const int C,                                                        \
      const int H,                                                        \
      const int W,                                                        \
      const int out_h,                                                    \
      const int out_w,                                                    \
      const int num_rois,                                                 \
      const float spatial_scale,                                          \
      const int sampling_ratio,                                           \
      const InputT* x,                                                    \
      const float* rois,                                                  \
      OutputT* y,                                                         \
      CUDAContext* ctx) {                                                 \
    auto nthreads = num_rois * C * out_h * out_w;                         \
    _##name<math::ScalarType<InputT>::type, float>                        \
        <<<CUDA_BLOCKS(nthreads), CUDA_THREADS, 0, ctx->cuda_stream()>>>( \
            nthreads,                                                     \
            C,                                                            \
            H,                                                            \
            W,                                                            \
            out_h,                                                        \
            out_w,                                                        \
            spatial_scale,                                                \
            sampling_ratio,                                               \
            reinterpret_cast<const math::ScalarType<InputT>::type*>(x),   \
            rois,                                                         \
            reinterpret_cast<math::ScalarType<OutputT>::type*>(y));       \
  }

DEFINE_KERNEL_LAUNCHER(RoiAlign, float16, float16);
DEFINE_KERNEL_LAUNCHER(RoiAlign, float, float);
DEFINE_KERNEL_LAUNCHER(RoiAlign, double, double);
DEFINE_KERNEL_LAUNCHER(RoiAlignGrad, float16, float); // RoiAlignGrad
DEFINE_KERNEL_LAUNCHER(RoiAlignGrad, float, float); // RoiAlignGrad
DEFINE_KERNEL_LAUNCHER(RoiAlignGrad, double, float); // RoiAlignGrad
#undef DEFINE_KERNEL_LAUNCHER

} // namespace kernels

} // namespace dragon

#endif // USE_CUDA
