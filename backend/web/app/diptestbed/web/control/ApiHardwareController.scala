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
import diptestbed.domain.{HardwareControlMessage, HardwareId, HardwareSerialMonitorMessage, SerialConfig, SoftwareId}
import diptestbed.protocol._
import diptestbed.protocol.Codecs._
import diptestbed.protocol.WebResult._
import diptestbed.web.actors.HardwareControlActor.controlTransformer
import diptestbed.web.actors.HardwareSerialMonitorListenerActor.listenerTransformer
import diptestbed.web.actors.{BetterActorFlow, HardwareControlActor, HardwareSerialMonitorListenerActor}
import diptestbed.web.ioControls.PipelineOps._
import diptestbed.web.ioControls._
import play.api.mvc.WebSocket.MessageFlowTransformer
import play.api.mvc._
import scala.concurrent.duration.DurationInt

class ApiHardwareController(
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
      listenerTransformer
    WebSocket.accept[HardwareControlMessage, HardwareSerialMonitorMessage](_ => {
      implicit val timeout: Timeout = 60.seconds
      BetterActorFlow.actorRef(subscriber =>
        HardwareSerialMonitorListenerActor.props(pubSubMediator, subscriber, hardwareId, serialConfig),
      )
    })
  }

}
