#include "dragon/operators/array/transpose_op.h"
#include "dragon/core/workspace.h"
#include "dragon/utils/math_functions.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

template <class Context>
template <typename T>
void TransposeOp<Context>::DoRunWithType() {
  auto &X = Input(0), *Y = Output(0, {0});

  int num_axes, num_dims = X.ndim();
  perm(0, &num_axes);

  CHECK(num_axes == 0 || num_axes == num_dims)
      << "\nProviding " << num_axes << " dimensions to permute, "
      << "while Tensor(" << X.name() << ")'s dims are " << X.DimString();

  vec64_t new_axes(num_dims), new_dims(num_dims);
  for (int i = 0; i < num_dims; ++i) {
    new_axes[i] = num_axes > 0 ? perm(i) : num_dims - i - 1;
  }

  if (def().type() == "TransposeGradient") {
    auto old_axes(new_axes);
    for (int i = 0; i < num_dims; ++i) {
      new_axes[old_axes[i]] = i;
    }
  }

  for (int i = 0; i < num_dims; ++i) {
    new_dims[i] = X.dim(new_axes[i]);
  }

  vec64_t transpose_dims, transpose_axes;
  math::utils::CollapseTransposeAxes(
      num_dims,
      X.dims().data(),
      new_axes.data(),
      transpose_dims,
      transpose_axes);
  Tensor X_collapse(transpose_dims);
  num_dims = X_collapse.ndim();
  vec64_t X_strides(num_dims), Y_dims(num_dims);
  for (int i = 0; i < num_dims; ++i) {
    X_strides[i] = X_collapse.stride(transpose_axes[i]);
    Y_dims[i] = X_collapse.dim(transpose_axes[i]);
  }

  auto* scratch = ((void*)&X == (void*)Y)
      ? ctx()->workspace()->template data<T, Context>({X.count()})[0]
      : Y->Reshape(new_dims)->template mutable_data<T, Context>();

  kernels::Transpose(
      num_dims,
      X_strides.data(),
      Y_dims.data(),
      X.template data<T, Context>(),
      scratch,
      ctx());

  if ((void*)&X == (void*)Y) {
    math::Copy(
        X.count(),
        scratch,
        Y->Reshape(new_dims)->template mutable_data<T, Context>(),
        ctx());
  }
}

DEPLOY_CPU_OPERATOR(Transpose);
REGISTER_CPU_OPERATOR(TransposeGradient, TransposeOp<CPUContext>);
#ifdef USE_CUDA
DEPLOY_CUDA_OPERATOR(Transpose);
REGISTER_CUDA_OPERATOR(TransposeGradient, TransposeOp<CUDAContext>);
#endif

OPERATOR_SCHEMA(Transpose)
    /* X */
    .NumInputs(1)
    /* Y */
    .NumOutputs(1)
    /* X => Y */
    .AllowInplace({{0, 0}});

OPERATOR_SCHEMA(TransposeGradient)
    /* dY */
    .NumInputs(1)
    /* dX */
    .NumOutputs(1)
    /* dY => dX */
    .AllowInplace({{0, 0}});

REGISTER_GRADIENT(Transpose, SimpleGradientMaker);

} // namespace dragon
