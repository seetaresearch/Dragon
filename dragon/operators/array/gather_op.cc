#include "dragon/core/workspace.h"
#include "dragon/operators/array/gather_ops.h"
#include "dragon/utils/math_functions.h"
#include "dragon/utils/op_kernels.h"

namespace dragon {

template <class Context>
template <typename T>
void GatherOp<Context>::DoRunWithType() {
  auto &X = Input(0), &X_index = Input(1), *Y = Output(0);
  GET_OP_AXIS_ARG(axis, X.ndim(), 0);
  GET_OP_AXIS_ARG(end_axis, X.ndim(), axis);
  SET_INPUT_SPEC(0);

  CHECK_GT(X_index.count(), 0) << "\nLength of index must > 0.";
  vec64_t X_dims(X.dims());
  vec64_t Y_dims(X_dims.begin(), X_dims.begin() + axis);
  Y_dims.insert(Y_dims.end(), X_index.dims().begin(), X_index.dims().end());
  Y_dims.insert(Y_dims.end(), X_dims.begin() + end_axis + 1, X_dims.end());

  kernels::Gather(
      X.count(0, axis),
      X.count(end_axis + 1),
      X.count(axis, end_axis + 1),
      X_index.count(),
      X_index.template data<int64_t, Context>(),
      X.template data<T, Context>(),
      Y->Reshape(Y_dims)->template mutable_data<T, Context>(),
      ctx());
}

template <class Context>
void GatherOp<Context>::RunOnDevice() {
  DispatchHelper<dtypes::Generic>::Call(this, Input(0));
}

template <class Context>
template <typename T>
void GatherGradientOp<Context>::DoRunWithType() {
  auto &X_index = Input(0), &dY = Input(1), *dX = Output(0);
  dX->ReshapeLike(INPUT_SPEC(0));
  GET_OP_AXIS_ARG(axis, dX->ndim(), 0);
  GET_OP_AXIS_ARG(end_axis, dX->ndim(), axis);

  auto* dx = dX->template mutable_data<T, Context>();
  auto* dx_acc = (TypeMeta::Id<T>() == TypeMeta::Id<float>())
      ? (float*)nullptr
      : ctx()->workspace()->template data<float, Context>({dX->count()})[0];

  // Empty gradient
  math::Set(
      dX->count(),
      0.f,
      dx_acc != nullptr ? dx_acc : reinterpret_cast<float*>(dx),
      ctx());

  // Accumulate to dX
  kernels::GatherGrad(
      dX->count(0, axis),
      dX->count(end_axis + 1),
      dX->count(axis, end_axis + 1),
      X_index.count(),
      X_index.template data<int64_t, Context>(),
      dY.template data<T, Context>(),
      dx_acc != nullptr ? dx_acc : reinterpret_cast<float*>(dx),
      ctx());

  // Convert to dX if necessary
  if (dx_acc != nullptr) {
    math::Cast(dX->count(), dx_acc, dx, ctx());
  }
}

template <class Context>
void GatherGradientOp<Context>::RunOnDevice() {
  DispatchHelper<dtypes::Floating>::Call(this, Input(1));
}

DEPLOY_CPU_OPERATOR(Gather);
#ifdef USE_CUDA
DEPLOY_CUDA_OPERATOR(Gather);
#endif

DEPLOY_CPU_OPERATOR(GatherGradient);
#ifdef USE_CUDA
DEPLOY_CUDA_OPERATOR(GatherGradient);
#endif

OPERATOR_SCHEMA(Gather)
    /* X, X_index */
    .NumInputs(2)
    /* Y */
    .NumOutputs(1);

OPERATOR_SCHEMA(GatherGradient)
    /* X_index, dY */
    .NumInputs(2)
    /* dX */
    .NumOutputs(1);

namespace {

class GradientMaker final : public GradientMakerBase {
 public:
  GRADIENT_MAKER_CTOR(GradientMaker);
  void CreateGradientDefs() override {
    AddGradientDef(
        def().type() + "Gradient",
        "",
        vector<string>({I(1), GO(0)}),
        vector<string>({GI(0)}));
  }
};

} // namespace

REGISTER_GRADIENT(Gather, GradientMaker);

} // namespace dragon
