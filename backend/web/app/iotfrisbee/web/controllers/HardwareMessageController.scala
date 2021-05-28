package iotfrisbee.web.controllers

import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.HardwareMessageService
import iotfrisbee.domain.HardwareMessageId
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._

import scala.annotation.unused
import scala.concurrent.ExecutionContext

class HardwareMessageController(
  val cc: ControllerComponents,
  val hardwareMessageService: HardwareMessageService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def createHardwareMessage: Action[CreateHardwareMessage] = {
    IOActionJSON[CreateHardwareMessage] { request =>
      EitherT(
        hardwareMessageService
          .createHardwareMessage(request.body.messageType, request.body.message, request.body.hardwareId),
      ).bimap(
        error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
        hardware => Success(hardware).withHttpStatus(OK),
      )
    }
  }

  def getHardwareMessages: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareMessageService.getHardwareMessages)
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          hardwareMessages => Success(hardwareMessages).withHttpStatus(OK),
        )
    }

  def getHardwareMessage(hardwareMessageId: HardwareMessageId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareMessageService.getHardwareMessage(hardwareMessageId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Hardware message with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                hardwareMessage => Success(hardwareMessage).withHttpStatus(OK),
              ),
          ),
        )
    }
}
