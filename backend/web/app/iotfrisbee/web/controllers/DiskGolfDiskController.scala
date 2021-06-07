package iotfrisbee.web.controllers

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.DiskGolfDiskService
import iotfrisbee.domain.DiskGolfDiskId
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.protocol._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._

import scala.annotation.unused
import scala.concurrent.ExecutionContext

class DiskGolfDiskController(
  val cc: ControllerComponents,
  val diskGolfDiskService: DiskGolfDiskService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createDiskGolfDisk: Action[CreateDiskGolfDisk] = {
    IOActionJSON[CreateDiskGolfDisk] { request =>
      EitherT(
        diskGolfDiskService.createDiskGolfDisk(request.body.name, request.body.trackId, request.body.hardwareId),
      ).leftMap(databaseError => Failure(databaseError.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(creation =>
          EitherT.fromEither(
            creation
              .leftMap(_.map {
                case DiskGolfDiskService.NonExistentTrack    => "Track with that id doesn't exist"
                case DiskGolfDiskService.NonExistentHardware => "Hardware with that id doesn't exist"
              })
              .bimap(
                errorMessages => Failure(errorMessages).withHttpStatus(BAD_REQUEST),
                diskGolfDisk => Success(diskGolfDisk).withHttpStatus(OK),
              ),
          ),
        )
    }
  }

  def getDiskGolfDisks: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfDiskService.getDiskGolfTracks)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          diskGolfDisks => Success(diskGolfDisks).withHttpStatus(OK),
        )
    }

  def getDiskGolfDisk(diskGolfDiskId: DiskGolfDiskId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfDiskService.getDiskGolfDisk(diskGolfDiskId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Disk golf disk with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                diskGolfDisk => Success(diskGolfDisk).withHttpStatus(OK),
              ),
          ),
        )
    }
}
