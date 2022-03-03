package diptestbed.web.controllers

import akka.actor.{ActorRef, ActorSystem}
import scala.annotation.unused
import akka.stream.Materializer
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.{HardwareCameraMessage, HardwareControlMessage, HardwareId, HardwareSerialMonitorMessage, SerialConfig, SoftwareId}
import diptestbed.protocol._
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.actors.HardwareCameraActor.cameraControlTransformer
import diptestbed.web.actors.HardwareControlActor.controlTransformer
import diptestbed.web.actors.HardwareSerialMonitorListenerActor.{listenerTransformer => controlListenerTransformer}
import diptestbed.web.actors.{BetterActorFlow, HardwareCameraActor, HardwareCameraListenerActor, HardwareControlActor, HardwareSerialMonitorListenerActor}
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import play.api.mvc.WebSocket.MessageFlowTransformer
import play.api.mvc._
import scala.concurrent.duration.DurationInt

class HardwareController(
  val cc: ControllerComponents,
  val pubSubMediator: ActorRef,
  val hardwareService: HardwareService[IO],
  val userService: UserService[IO],
)(implicit
  @unused iort: IORuntime,
  @unused actorSystem: ActorSystem,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController
    with AuthController[IO]
    with ResultsController[IO] {

  def createHardware: Action[CreateHardware] =
    IOActionJSON[CreateHardware](
      withRequestAuthnOrFail(_)((request, user) =>
        for {
          creation <- EitherT(hardwareService.createHardware(request.body.name, user.id)).leftMap(databaseErrorResult)
          result <-
            creation
              .toRight("Authenticated user was removed while executing request")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                hardware => Success(hardware).withHttpStatus(OK),
              )
              .toEitherT[IO]
        } yield result,
      ),
    )

  def getHardwares: Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardwares)
        .leftMap(databaseErrorResult)
        .map(hardwares => Success(hardwares).withHttpStatus(OK))
    }

  def getHardware(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareService.getHardware(hardwareId))
        .leftMap(databaseErrorResult)
        .subflatMap(
          _.toRight("Hardware with that id doesn't exist")
            .bimap(
              errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
              hardware => Success(hardware).withHttpStatus(OK),
            ),
        )
    }

  def controlHardware(hardwareId: HardwareId): WebSocket = {
    implicit val transformer: MessageFlowTransformer[HardwareControlMessage, HardwareControlMessage] =
      controlTransformer
    WebSocket.accept[HardwareControlMessage, HardwareControlMessage](_ => {
      BetterActorFlow.actorRef(
        subscriber => HardwareControlActor.props(pubSubMediator, subscriber, hardwareId),
        maybeName = hardwareId.actorId().text().some,
      )
    })
  }

  def uploadHardwareSoftware(hardwareId: HardwareId, softwareId: SoftwareId): Action[AnyContent] =
    IOActionAny { _ =>
      {
        implicit val timeout: Timeout = 60.seconds
        val uploadResult = HardwareControlActor.requestSoftwareUpload(hardwareId, softwareId)

        uploadResult.bimap(
          errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
          result => Success(result.toString).withHttpStatus(OK),
        )
      }
    }

  def listenHardwareSerialMonitor(hardwareId: HardwareId, serialConfig: Option[SerialConfig]): WebSocket = {
    implicit val transformer: MessageFlowTransformer[HardwareControlMessage, HardwareSerialMonitorMessage] =
      controlListenerTransformer
    WebSocket.accept[HardwareControlMessage, HardwareSerialMonitorMessage](_ => {
      implicit val timeout: Timeout = 60.seconds
      BetterActorFlow.actorRef(subscriber =>
        HardwareSerialMonitorListenerActor.props(pubSubMediator, subscriber, hardwareId, serialConfig),
      )
    })
  }

  def cameraSource(hardwareIds: List[HardwareId]): WebSocket = {
    implicit val transformer: MessageFlowTransformer[HardwareCameraMessage, HardwareCameraMessage] =
      cameraControlTransformer
    WebSocket.accept[HardwareCameraMessage, HardwareCameraMessage](_ => {
      BetterActorFlow.actorRef(subscriber =>
        HardwareCameraActor.props(pubSubMediator, subscriber, hardwareIds),
      )
    })
  }

  def cameraSink(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny { request: Request[AnyContent] =>
      {
        val sourceResult = HardwareCameraListenerActor.spawnCameraSource(pubSubMediator, hardwareId)
        def withStreamHeaders(x: Result): Result =
          x.as("application/ogg").withHeaders(
            // We don't accept range requests, WYSIWYG
            "Accept-Ranges" -> "none",
            // This content shouldn't be cached by the client
            "Cache-Control" -> "no-cache"
          )

        request.headers.get("Range") match {
          case None => EitherT.fromEither(Right(withStreamHeaders(Ok(""))))
          case Some(_) => sourceResult.bimap(
            errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
            source =>
              withStreamHeaders(Ok.chunked(source)),
          )
        }
      }
    }

}
