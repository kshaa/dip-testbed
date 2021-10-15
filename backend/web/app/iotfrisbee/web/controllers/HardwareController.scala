package iotfrisbee.web.controllers

import akka.actor.{ActorRef, ActorSystem, Props}

import scala.annotation.unused
import akka.stream.Materializer
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import iotfrisbee.database.services.{HardwareService, UserService}
import iotfrisbee.domain.HardwareControlMessage.UploadSoftwareRequest
import iotfrisbee.domain.{HardwareControlMessage, HardwareId, SoftwareId}
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.actors.HardwareControlActor.{hardwareActor, transformer}
import iotfrisbee.web.actors.{BetterActorFlow, HardwareControlActor}
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._
import play.api.mvc._
import scala.concurrent.duration.DurationInt

class HardwareController(
  val cc: ControllerComponents,
  val pubSubMediator: ActorRef,
  val hardwareService: HardwareService[IO],
  val userService: UserService[IO]
)(implicit
  @unused iort: IORuntime,
  @unused actorSystem: ActorSystem,
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

  def controlHardwareActor(subscriber: ActorRef, hardwareId: HardwareId): Props =
    HardwareControlActor.props(pubSubMediator, subscriber, hardwareId)

  def controlHardware(hardwareId: HardwareId): WebSocket = {
    WebSocket.accept[HardwareControlMessage, String](_ => {
      BetterActorFlow.actorRef(
        subscriber => controlHardwareActor(subscriber, hardwareId),
        maybeName = hardwareActor(hardwareId).some)
    })
  }

  def uploadHardwareSoftware(hardwareId: HardwareId, softwareId: SoftwareId): Action[AnyContent] =
    IOActionAny { _ => {
      implicit val timeout: Timeout = 5.seconds
      val uploadSoftwareMessage: HardwareControlMessage = UploadSoftwareRequest(softwareId)
      val hardwareActorPath = EitherT[IO, String, ActorRef](IO.fromFuture(IO(
        actorSystem
          .actorSelection(s"/user/${hardwareActor(hardwareId)}")
          .resolveOne())).map(Right.apply))
      val uploadResult: EitherT[IO, String, Any] = hardwareActorPath.flatMap(hardware =>
        EitherT[IO, String, Any](IO(
          hardware ! uploadSoftwareMessage)
          .map(Right.apply[String, Any]))
      )

      uploadResult.bimap(
        errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
        _ => Success(()).withHttpStatus(OK),
      )
    }}

}
