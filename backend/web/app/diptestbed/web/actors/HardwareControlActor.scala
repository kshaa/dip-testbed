package diptestbed.web.actors

import akka.actor.{Actor, ActorRef, ActorSystem, Props}
import diptestbed.domain.{HardwareId, SoftwareId, HardwareControlMessage => Control}
import play.api.http.websocket.{CloseCodes, CloseMessage, WebSocketCloseException}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.parser.decode
import io.circe.syntax.EncoderOps
import diptestbed.protocol.Codecs.{hardwareControlMessageDecoder, hardwareControlMessageEncoder}
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import cats.effect.IO
import diptestbed.web.actors.HardwareControlActor.hardwareSerialMonitorTopic
import cats.effect.unsafe.IORuntime
import diptestbed.domain.HardwareControlMessage._
import akka.util.Timeout
import cats.data.EitherT
import cats.implicits.toTraverseOps
import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.HardwareSerialMonitorMessage.BaudrateChanged
import diptestbed.web.actors.HardwareControlState.{ConfiguringMonitor, Initial, Uploading}
import diptestbed.web.actors.QueryActor.Promise

sealed trait HardwareControlState {}
object HardwareControlState {
  case object Initial extends HardwareControlState
  case class Uploading(requester: Option[ActorRef]) extends HardwareControlState
  case class ConfiguringMonitor(requester: Option[ActorRef]) extends HardwareControlState
}

trait HardwareControlStateActions {
  var state: HardwareControlState

  def isInitial: Boolean =
    state match {
      case Initial => true
      case _       => false
    }

  def isUploading: Boolean =
    state match {
      case _: Uploading => true
      case _            => false
    }

  def isMonitoring: Boolean =
    state match {
      case _: ConfiguringMonitor => true
      case _                     => false
    }

  def isUploadObserved: Option[ActorRef] =
    state match {
      case Uploading(Some(requester)) => Some(requester)
      case _                          => None
    }

  def isMonitorObserved: Option[ActorRef] =
    state match {
      case ConfiguringMonitor(Some(requester)) => Some(requester)
      case _                                   => None
    }

  def setInitialState(): Unit =
    state = Initial

  def setUploadingState(inquirer: Option[ActorRef]): Unit =
    state = Uploading(inquirer)

  def setConfiguringMonitorState(inquirer: Option[ActorRef]): Unit =
    state = ConfiguringMonitor(inquirer)

}

class HardwareControlActor(
  pubSubMediator: ActorRef,
  out: ActorRef,
  hardwareId: HardwareId,
)(implicit
  iort: IORuntime,
  @unused timeout: Timeout,
) extends Actor
    with LazyLogging
    with HardwareControlStateActions {
  logger.info(s"Actor for hardware #${hardwareId} spawned")

  val serialMonitorTopic: String = hardwareSerialMonitorTopic(hardwareId)
  var state: HardwareControlState = Initial

  def sendToAgent(message: Control): IO[Unit] =
    IO(out ! message.asJson.noSpaces)
  def sendToRequester(requester: ActorRef, message: Control): IO[Unit] =
    IO(requester ! message)

  def receive: Receive = {
    case controlMessage: Control =>
      isNonPingMessage(controlMessage).foreach(message =>
        logger.info(s"Receiving non-ping control message: ${message}"),
      )
      controlHandler(None, controlMessage).unsafeRunSync()

    case Promise(inquirer, controlMessage: Control) =>
      logger.info(s"Inquirer '${inquirer}' sent control message: ${controlMessage}")
      controlHandler(Some(inquirer), controlMessage).unsafeRunSync()

    case message =>
      logger.info(s"Receiving and ignoring unknown message: ${message.toString}")
  }

  def controlHandler(inquirer: Option[ActorRef], message: Control): IO[Unit] =
    message match {
      case m: UploadSoftwareRequest => handleUploadSoftwareRequest(inquirer, m)
      case m: UploadSoftwareResult  => handleUploadSoftwareResult(m)
      case m: SerialMonitorRequest  => handleSerialMonitorRequest(inquirer, m)
      case m: SerialMonitorResult   => handleSerialMonitorResult(m)
      case m: SerialMonitorMessage  => handleSerialMonitorMessage(m)
      case _: Ping                  => IO(())
    }

  def handleUploadSoftwareRequest(inquirer: Option[ActorRef], message: UploadSoftwareRequest): IO[Unit] =
    for {
      // If available, start upload, maybe respond eventually
      _ <- IO.whenA(isInitial)(sendToAgent(message))
      // If not available & response is expected, respond w/ unavailability
      _ <- inquirer.filter(_ => !isInitial).traverse(sendToRequester(_, uploadUnavailableMessage))
      // If available, also set new state
      _ <- IO.whenA(isInitial)(IO(setUploadingState(inquirer)))
    } yield ()

  def handleUploadSoftwareResult(message: UploadSoftwareResult): IO[Unit] =
    for {
      // Forward response if upload is observed
      _ <- isUploadObserved.traverse(sendToRequester(_, message))
      // Reset state if upload happened
      _ <- IO.whenA(isUploading)(IO(setInitialState()))
    } yield ()

  def handleSerialMonitorRequest(inquirer: Option[ActorRef], message: SerialMonitorRequest): IO[Unit] =
    for {
      // If available, start monitor, maybe respond eventually
      _ <- IO.whenA(isInitial)(sendToAgent(message))
      // If not available & response is expected, respond w/ unavailability
      _ <- inquirer.filter(_ => !isInitial).traverse(sendToRequester(_, monitorUnavailableMessage))
      // If available, also set new state
      _ <- IO.whenA(isInitial)(IO(setConfiguringMonitorState(inquirer)))
    } yield ()

  def handleSerialMonitorResult(message: SerialMonitorResult): IO[Unit] =
    for {
      // Forward response if monitor is observed
      _ <- isMonitorObserved.traverse(sendToRequester(_, message))
      // Broadcast conditional baudrate change
      _ <- isBaudrateChangeMessage(message).traverse(baudrate =>
        IO(pubSubMediator ! Publish(serialMonitorTopic, BaudrateChanged(baudrate))),
      )
      // Reset state if upload happened
      _ <- IO.whenA(isMonitoring)(IO(setInitialState()))
    } yield ()

  def handleSerialMonitorMessage(message: SerialMonitorMessage): IO[Unit] =
    for {
      // Broadcast monitor message
      _ <- IO(pubSubMediator ! Publish(serialMonitorTopic, message.message))
    } yield ()

}

object HardwareControlActor extends ActorHelper {
  val subscribed = "subscribed"
  def hardwareActor(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-actor"
  def hardwareSerialMonitorTopic(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-serial-monitor"
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId,
  )(implicit
    iort: IORuntime,
    timeout: Timeout,
  ): Props = Props(new HardwareControlActor(pubSubMediator, out, hardwareId))

  implicit val transformer: MessageFlowTransformer[Control, String] =
    MessageFlowTransformer.stringMessageFlowTransformer.map(x => {
      decode[Control](x).toTry.getOrElse {
        throw WebSocketCloseException(CloseMessage(Some(CloseCodes.Unacceptable), "Failed to parse message"))
      }
    })

  def requestSerialMonitor(
    hardwareId: HardwareId,
    baudrate: Option[Baudrate],
  )(implicit actorSystem: ActorSystem, t: Timeout, iort: IORuntime): EitherT[IO, String, BaudrateState] =
    for {
      hardwareRef <- resolveActorRef(userActorPath(hardwareActor(hardwareId)))(actorSystem, implicitly)
      result <- QueryActor.queryActorT(
        hardwareRef,
        actorRef => Promise(actorRef, SerialMonitorRequest(baudrate)),
        immediate = false,
      )
      monitorResult <- EitherT.fromEither[IO](result match {
        case SerialMonitorResult(result) => result
        case _                           => Left("Hardware responded with an invalid response")
      })
    } yield monitorResult

  def requestSoftwareUpload(
    hardwareId: HardwareId,
    softwareId: SoftwareId,
  )(implicit actorSystem: ActorSystem, t: Timeout, iort: IORuntime): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(userActorPath(hardwareActor(hardwareId)))
      result <- QueryActor.queryActorT(
        hardwareRef,
        actorRef => Promise(actorRef, UploadSoftwareRequest(softwareId)),
        immediate = false,
      )
      uploadResult <- EitherT.fromEither[IO](result match {
        case UploadSoftwareResult(result) => result.toLeft(())
        case _                            => Left("Hardware responded with an invalid response")
      })
    } yield uploadResult
}
