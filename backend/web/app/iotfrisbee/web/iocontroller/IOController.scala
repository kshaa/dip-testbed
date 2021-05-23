package iotfrisbee.web.iocontroller

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import play.api.mvc.{Action, AnyContent, Request}

trait IOController {
  import PipelineTypes._

  def cc: play.api.mvc.ControllerComponents

  def IOAction(
    handler: Request[AnyContent] => PipelineRes[IO],
  )(implicit iort: IORuntime): Action[AnyContent] =
    cc.actionBuilder.async(handler(_).merge.unsafeToFuture())
}
