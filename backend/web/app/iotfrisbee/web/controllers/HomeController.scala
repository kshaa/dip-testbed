package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.unsafe.IORuntime
import cats.effect.IO
import play.api.mvc._
import iotfrisbee.database.services._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import iotfrisbee.protocol.{Hello, ServiceStatus}
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._

class HomeController(
  val cc: ControllerComponents,
  val userService: UserService[IO],
  val hardwareService: HardwareService[IO],
  val hardwareMessageService: HardwareMessageService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {
  def index: Action[AnyContent] =
    Action(Success(Hello("iotfrisbee")).withHttpStatus(OK))

  def status: Action[AnyContent] =
    IOActionAny { _ =>
      (for {
        userCount <- EitherT(userService.countUsers())
        hardwareCount <- EitherT(hardwareService.countHardware())
        hardwareMessageCount <- EitherT(hardwareMessageService.countHardwareMessage())
        status = ServiceStatus(
          userCount,
          hardwareCount,
          hardwareMessageCount,
        )
      } yield status)
        .bimap(
          error => Failure[String](error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          status => Success(status).withHttpStatus(OK),
        )
    }
}
