package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.stream.Materializer
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.{HardwareService, UserService}
import iotfrisbee.domain.HardwareId
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._

class HardwareController(
  val cc: ControllerComponents,
  val hardwareService: HardwareService[IO],
  val userService: UserService[IO]
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with AuthController[IO]
    with ResultsController[IO] {

  def createHardware: Action[CreateHardware] =
    IOActionJSON[CreateHardware](withRequestAuthnOrFail(_)((request, user) =>
      for {
        creation <- EitherT(hardwareService.createHardware(request.body.name, user.id)).leftMap(databaseErrorResult)
        result <- creation.toRight("Authenticated user was removed while executing request")
          .bimap(
            errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
            hardware => Success(hardware).withHttpStatus(OK),
          ).toEitherT[IO]
      } yield result
    ))

  def getHardwares: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardwares).leftMap(databaseErrorResult)
        .map(hardwares => Success(hardwares).withHttpStatus(OK))
    }

  def getHardware(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardware(hardwareId)).leftMap(databaseErrorResult)
        .subflatMap(_.toRight("Hardware with that id doesn't exist")
          .bimap(
            errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
            hardware => Success(hardware).withHttpStatus(OK),
          ))
    }
}
