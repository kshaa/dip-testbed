package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import play.api.mvc._
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.DiskGolfTrackService
import iotfrisbee.domain.DiskGolfTrackId
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
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
      ).leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(creation =>
          EitherT.fromEither(
            creation
              .toRight("Hardware with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                diskGolfTrack => Success(diskGolfTrack).withHttpStatus(OK),
              ),
          ),
        )
    }
  }

  def getDiskGolfTracks: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfTrackService.getDiskGolfTracks)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          diskGolfTracks => Success(diskGolfTracks).withHttpStatus(OK),
        )
    }

  def getDiskGolfTrack(diskGolfTrackId: DiskGolfTrackId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfTrackService.getDiskGolfTrack(diskGolfTrackId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Disk golf track with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                diskGolfTrack => Success(diskGolfTrack).withHttpStatus(OK),
              ),
          ),
        )
    }
}
