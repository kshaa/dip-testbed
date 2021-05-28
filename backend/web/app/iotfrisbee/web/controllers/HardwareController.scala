package iotfrisbee.web.controllers

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.HardwareService
import iotfrisbee.domain.HardwareId
import iotfrisbee.protocol.Codecs.Domain._
import iotfrisbee.protocol.Codecs.Hardware._
import iotfrisbee.protocol.messages.hardware.CreateHardware
import iotfrisbee.protocol.messages.http.WebResult.{Failure, Success}
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._

import scala.annotation.unused
import scala.concurrent.ExecutionContext

class HardwareController(
  val cc: ControllerComponents,
  val hardwareService: HardwareService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createHardware: Action[CreateHardware] = {
    IOActionJSON[CreateHardware] { request =>
      EitherT(
        hardwareService.createHardware(request.body.name, request.body.ownerId),
      ).bimap(
        error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
        hardware => Success(hardware).withHttpStatus(OK),
      )
    }
  }

  def getHardwares: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardwares)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          hardwares => Success(hardwares).withHttpStatus(OK),
        )
    }

  def getHardware(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardware(hardwareId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Hardware with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                hardware => Success(hardware).withHttpStatus(OK),
              ),
          ),
        )
    }
}
