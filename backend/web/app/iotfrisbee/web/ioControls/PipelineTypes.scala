package iotfrisbee.web.ioControls

import cats.data.EitherT
import play.api.mvc.Result

object PipelineTypes {
  type PipelineStage[F[_], A, B] = EitherT[F, A, B]
  type PipelineRes[F[_]] = PipelineStage[F, Result, Result]
}
