#ifdef USE_CUDNN

#include "dragon/operators/activation/sigmoid_op.h"

namespace dragon {

template <class Context>
template <typename T>
void CuDNNSigmoidOp<Context>::DoRunWithType() {
  auto &X = Input(0), *Y = Output(0, {0});
  CuDNNSetTensorDesc<T>(&input_desc_, X.dims());
  CUDNN_CHECK(cudnnActivationForward(
      ctx()->cudnn_handle(),
      act_desc_,
      CuDNNType<T>::one,
      input_desc_,
      X.template data<T, Context>(),
      CuDNNType<T>::zero,
      input_desc_,
      Y->ReshapeLike(X)->template mutable_data<T, Context>()));
}

template <class Context>
template <typename T>
void CuDNNSigmoidGradientOp<Context>::DoRunWithType() {
  auto &Y = Input(0), &dY = Input(1), *dX = Output(0);
  CuDNNSetTensorDesc<T>(&input_desc_, Y.dims());
  CUDNN_CHECK(cudnnActivationBackward(
      ctx()->cudnn_handle(),
      act_desc_,
      CuDNNType<T>::one,
      input_desc_,
      Y.template data<T, Context>(),
      input_desc_,
      dY.template data<T, Context>(),
      input_desc_,
      Y.template data<T, Context>(),
      CuDNNType<T>::zero,
      input_desc_,
      dX->ReshapeLike(Y)->template mutable_data<T, Context>()));
}

DEPLOY_CUDNN_OPERATOR(Sigmoid);
DEPLOY_CUDNN_OPERATOR(SigmoidGradient);

} // namespace dragon

#endif // USE_CUDNN
