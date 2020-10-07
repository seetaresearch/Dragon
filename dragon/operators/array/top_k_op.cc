#include "dragon/operators/array/top_k_op.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

template <class Context>
template <typename T>
void TopKOp<Context>::DoRunWithType() {
  auto &X = Input(0), *Y_value = Output(0), *Y_index = Output(1);
  CANONICALIZE_AXIS_WITH_TENSOR(X);
  axis = (axis == INT_MAX ? X.ndim() - 1 : axis);

  // Determine the output dimensions
  CHECK_LE(k_, X.dim(axis))
      << "\nThe top-K argument is out of the reduced dimension.";
  auto Y_dims = X.dims();
  Y_dims[axis] = k_;

  kernel::TopSelect(
      X.count(0, axis),
      X.count(axis + 1),
      X.dim(axis),
      k_,
      largest_,
      X.template data<T, Context>(),
      Y_value->Reshape(Y_dims)->template mutable_data<T, Context>(),
      Y_index->Reshape(Y_dims)->template mutable_data<int64_t, Context>(),
      ctx());
}

template <class Context>
void TopKOp<Context>::RunOnDevice() {
  DispatchHelper<NumericalTensorTypes>::Call(this, Input(0));
}

DEPLOY_CPU_OPERATOR(TopK);
#ifdef USE_CUDA
DEPLOY_CUDA_OPERATOR(TopK);
#endif

OPERATOR_SCHEMA(TopK)
    /* X */
    .NumInputs(1)
    /* Value, Index */
    .NumOutputs(2);

NO_GRADIENT(TopK);

} // namespace dragon
