package iotfrisbee.web.controllers

import cats.data.EitherT
import cats.effect.unsafe.IORuntime
import cats.effect.IO
import play.api.mvc._
import scala.annotation.unused
import scala.concurrent.ExecutionContext
import iotfrisbee.database.services.{DiskGolfTrackService, UserService}
import iotfrisbee.web.iocontroller.PipelineOps._
import iotfrisbee.web.iocontroller._
import iotfrisbee.protocol.messages._
import iotfrisbee.protocol.Codecs.Home._
import iotfrisbee.protocol.messages.WebResult.{Failure, Success}

class HomeController(
  val cc: ControllerComponents,
  val userService: UserService[IO],
  val diskGolfTrackService: DiskGolfTrackService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
) extends AbstractController(cc)
    with IOController {
  def index: Action[AnyContent] =
    Action(Success(Hello("iotfrisbee")).withHttpStatus(OK))

  def status: Action[AnyContent] =
    IOAction { _ =>
      (for {
        userCountText <- EitherT(userService.countUsers())
        diskGolfTrackText <- EitherT(diskGolfTrackService.countDiskGolfTracks())
        status = ServiceStatus(userCountText, diskGolfTrackText)
      } yield status)
        .bimap(
          error => Failure[String](error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          status => Success(status).withHttpStatus(OK),
        )
    }

  def addUser(name: String): Action[AnyContent] =
    IOAction { _ =>
      EitherT(userService.createUser(name))
        .bimap(
          e => Failure(e.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          u => Success(u.id.toString).withHttpStatus(OK),
        )
    }
}
