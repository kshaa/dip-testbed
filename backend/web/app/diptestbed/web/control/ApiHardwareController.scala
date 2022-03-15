package diptestbed.web.control

import akka.actor.{ActorRef, ActorSystem}

import scala.annotation.unused
import akka.stream.Materializer
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, HardwareCameraMessage, HardwareControlMessage, HardwareId, HardwareSerialMonitorMessage, SerialConfig, SoftwareId}
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

class ApiHardwareController(
  val appConfig: DIPTestbedConfig,
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
          _ <- EitherT.fromEither[IO](Either.cond(
            user.isLabOwner, (), permissionErrorResult("Lab owner")))
          creation = hardwareService.createHardware(request.body.name, user.id, isPublic = false)
          creationOrError <- EitherT(creation).leftMap(databaseErrorResult)
          result <-
            creationOrError
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
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        hardwares <- EitherT(hardwareService.getHardwares(Some(user), write = false)).leftMap(databaseErrorResult)
        result = Success(hardwares).withHttpStatus(OK)
      } yield result
    ))

  def getHardware(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) =>
      for {
        hardware <- EitherT(hardwareService.getHardware(Some(user), hardwareId, write = false)).leftMap(databaseErrorResult)
        _ <- EitherT.fromEither[IO](hardware.toRight(unknownIdErrorResult))
        result = Success(hardware).withHttpStatus(OK)
      } yield result
    ))

  def controlHardware(hardwareId: HardwareId): WebSocket = {
    implicit val transformer: MessageFlowTransformer[HardwareControlMessage, HardwareControlMessage] =
      controlTransformer
    WebSocket.accept[HardwareControlMessage, HardwareControlMessage](_ => {
      BetterActorFlow.actorRef(
        subscriber => HardwareControlActor.props(appConfig, pubSubMediator, subscriber, hardwareId),
        maybeName = hardwareId.actorId().text().some,
      )
    })
  }

  def uploadHardwareSoftware(hardwareId: HardwareId, softwareId: SoftwareId): Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((_, user) => {
      implicit val timeout: Timeout = 60.seconds
      for {
        hardware <- EitherT(hardwareService.getHardware(Some(user), hardwareId, write = false)).leftMap(databaseErrorResult)
        _ <- EitherT.fromEither[IO](hardware.toRight(unknownIdErrorResult))
        _ <- EitherT.fromEither[IO](Either.cond(
          user.canInteractHardware, (), permissionErrorResult("Hardware access")))
        uploadResult <- HardwareControlActor.requestSoftwareUpload(hardwareId, softwareId).bimap(
          errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
          result => Success(result.toString).withHttpStatus(OK),
        )
      } yield uploadResult
    }))

  // TODO: Secure with auth
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

  // TODO: Secure with auth
  def cameraSource(hardwareIds: List[HardwareId]): WebSocket = {
    implicit val transformer: MessageFlowTransformer[HardwareCameraMessage, HardwareCameraMessage] =
      cameraControlTransformer
    WebSocket.accept[HardwareCameraMessage, HardwareCameraMessage](_ => {
      BetterActorFlow.actorRef(subscriber =>
        HardwareCameraActor.props(appConfig, pubSubMediator, subscriber, hardwareIds),
      )
    })
  }

  private def withStreamHeaders(x: Result): Result =
    x.as("application/ogg").withHeaders(
      // We don't accept range requests, WYSIWYG
      "Accept-Ranges" -> "none",
      // This content shouldn't be cached by the client
      "Cache-Control" -> "no-cache"
    )

  def cameraSink(hardwareId: HardwareId): Action[AnyContent] =
    IOActionAny(withRequestAuthnOrFail(_)((request, user) => {
      for {
        hardware <- EitherT(hardwareService.getHardware(Some(user), hardwareId, write = false)).leftMap(databaseErrorResult)
        _ <- EitherT.fromEither[IO](hardware.toRight(unknownIdErrorResult))
        _ <- EitherT.fromEither[IO](Either.cond(
          user.canInteractHardware, (), permissionErrorResult("Hardware access")))
        result <-
          request.headers.get("Range") match {
            case None => EitherT.fromEither[IO](Right[Result, Result](withStreamHeaders(Ok(""))))
            case Some(_) => HardwareCameraListenerActor.spawnCameraSource(appConfig, pubSubMediator, hardwareId).bimap[Result, Result](
              errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
              source =>
                withStreamHeaders(Ok.chunked(source)),
            )
          }
      } yield result
    }))

}
