package iotfrisbee.web.controllers

import cats.data.EitherT
import cats.effect.unsafe.IORuntime
import cats.effect.IO
import iotfrisbee.web.iocontroller.IOController
import iotfrisbee.database.services.{DiskGolfTrackService, UserService}
import play.api.mvc._
import scala.annotation.unused
import scala.concurrent.ExecutionContext

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
    Action {
      Ok("Hello from iotfrisbee!")
    }

  def status: Action[AnyContent] =
    IOAction { _ =>
      (for {
        userCountText <- EitherT(userService.countUsers())
        diskGolfTrackText <- EitherT(diskGolfTrackService.countDiskGolfTracks())
      } yield Ok(
        List(
          "Status page for iotfrisbee!",
          "",
          f"Registered users: ${userCountText}",
          f"Registered disk golf tracks: ${diskGolfTrackText}",
        ).mkString("\n"),
      )).leftMap(error => InternalServerError(f"Failed to process request. Reason: ${error.message}"))
    }

  def addUser(name: String): Action[AnyContent] =
    IOAction { _ =>
      EitherT(userService.createUser(name))
        .bimap(e => InternalServerError(e.message), u => Ok(u.id.toString))
    }
}
