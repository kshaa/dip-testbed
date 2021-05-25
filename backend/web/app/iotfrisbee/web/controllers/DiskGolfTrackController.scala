package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import play.api.mvc._
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import iotfrisbee.database.services.DiskGolfTrackService
import iotfrisbee.domain.DiskGolfTrackId
import iotfrisbee.protocol.Codecs.Domain._
import iotfrisbee.protocol.Codecs.DiskGolfTrack._
import iotfrisbee.protocol.messages.diskGolfTrack.CreateDiskGolfTrack
import iotfrisbee.protocol.messages.http.WebResult.{Failure, Success}
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._

class DiskGolfTrackController(
  val cc: ControllerComponents,
  val diskGolfTrackService: DiskGolfTrackService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createDiskGolfTrack: Action[CreateDiskGolfTrack] = {
    IOActionJSON[CreateDiskGolfTrack] { request =>
      EitherT(
        diskGolfTrackService.createDiskGolfTrack(request.body.ownerId, request.body.name, request.body.timezoneId),
      ).bimap(
        error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
        diskGoldTrack => Success(diskGoldTrack).withHttpStatus(OK),
      )
    }
  }

  def getDiskGolfTracks: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfTrackService.getDiskGolfTracks)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          users => Success(users).withHttpStatus(OK),
        )
    }

  def getDiskGolfTrack(diskGolfTrackId: DiskGolfTrackId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfTrackService.getDiskGolfTrack(diskGolfTrackId))
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          user => Success(user).withHttpStatus(OK),
        )
    }
}
