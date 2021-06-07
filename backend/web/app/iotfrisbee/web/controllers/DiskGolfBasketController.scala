package iotfrisbee.web.controllers

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.DiskGolfBasketService
import iotfrisbee.domain.DiskGolfBasketId
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.protocol._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._

import scala.annotation.unused
import scala.concurrent.ExecutionContext

class DiskGolfBasketController(
  val cc: ControllerComponents,
  val diskGolfBasketService: DiskGolfBasketService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createDiskGolfBasket: Action[CreateDiskGolfBasket] = {
    IOActionJSON[CreateDiskGolfBasket] { request =>
      EitherT(
        diskGolfBasketService.createDiskGolfBasket(request.body.name, request.body.trackId, request.body.hardwareId),
      ).leftMap(databaseError => Failure(databaseError.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(creation =>
          EitherT.fromEither(
            creation
              .leftMap(_.map {
                case DiskGolfBasketService.NonExistentTrack    => "Track with that id doesn't exist"
                case DiskGolfBasketService.NonExistentHardware => "Hardware with that id doesn't exist"
              })
              .bimap(
                errorMessages => Failure(errorMessages).withHttpStatus(BAD_REQUEST),
                diskGolfBasket => Success(diskGolfBasket).withHttpStatus(OK),
              ),
          ),
        )
    }
  }

  def getDiskGolfBaskets: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfBasketService.getDiskGolfBaskets)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          diskGolfBaskets => Success(diskGolfBaskets).withHttpStatus(OK),
        )
    }

  def getDiskGolfBasket(diskGolfBasketId: DiskGolfBasketId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(diskGolfBasketService.getDiskGolfBasket(diskGolfBasketId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Disk golf basket with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                diskGolfBasket => Success(diskGolfBasket).withHttpStatus(OK),
              ),
          ),
        )
    }
}
