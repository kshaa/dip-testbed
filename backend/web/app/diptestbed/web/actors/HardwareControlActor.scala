package diptestbed.web.actors

import akka.actor.{Actor, ActorRef, ActorSystem, Props}
import diptestbed.domain.{HardwareId, SerialConfig, SoftwareId, HardwareControlMessage => Control}
import play.api.http.websocket.{BinaryMessage, CloseCodes, CloseMessage, Message, TextMessage}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.parser.decode
import io.circe.syntax.EncoderOps
import diptestbed.protocol.Codecs.{hardwareControlMessageDecoder, hardwareControlMessageEncoder}
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import akka.stream.scaladsl.Flow
import cats.effect.IO
import diptestbed.web.actors.HardwareControlActor.hardwareSerialMonitorTopic
import cats.effect.unsafe.IORuntime
import diptestbed.domain.HardwareControlMessage._
import akka.util.{ByteString, Timeout}
import cats.data.EitherT
import cats.implicits.toTraverseOps
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.Charsets._
import diptestbed.domain.HardwareSerialMonitorMessage.{SerialMessageToAgent, SerialMessageToClient}
import diptestbed.web.actors.HardwareControlState.{ConfiguringMonitor, Initial, Uploading}
import diptestbed.web.actors.QueryActor.Promise
import play.api.libs.streams.AkkaStreams

import scala.concurrent.duration.{DurationInt, FiniteDuration}

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
) extends Actor
    with LazyLogging
    with HardwareControlStateActions {
  logger.info(s"Actor for hardware #${hardwareId} spawned")

  val serialMonitorTopic: String = hardwareSerialMonitorTopic(hardwareId)
  var state: HardwareControlState = Initial

  var listenerHeartbeatsReceived: Int = 0
  val listenerHeartbeatInterval: FiniteDuration = 5.seconds
  val listenerHeartbeatWaitTime: FiniteDuration = 2.seconds // Should be less than the interval

  def scheduleHeartbeatTest(): IO[Unit] = {
    val laterTest = IO.sleep(listenerHeartbeatInterval) >>
      IO(self ! SerialMonitorListenersHeartbeatStart())

    laterTest.start.void
  }

  scheduleHeartbeatTest().unsafeRunAsync(_ => ())

  def sendToAgent(message: Control): IO[Unit] =
    IO(out ! (message match {
      case m: Control.SerialMonitorMessageToAgent =>
        val dehydrated = m.message.base64Bytes.asBase64Bytes
        BinaryMessage(ByteString.fromArray(dehydrated))
      case m: Control => TextMessage(m.asJson.noSpaces)
    }))
  def sendToRequester(requester: ActorRef, message: Control): IO[Unit] =
    IO(requester ! message)

  def receive: Receive = {
    case controlMessage: Control =>
      isNonPingMessage(controlMessage).foreach(message =>
        logger.debug(s"Receiving non-ping control message: ${message}"),
      )
      controlHandler(None, controlMessage).unsafeRunSync()

    case Promise(inquirer, controlMessage: Control) =>
      logger.debug(s"Inquirer '${inquirer}' sent control message: ${controlMessage}")
      controlHandler(Some(inquirer), controlMessage).unsafeRunSync()

    case message =>
      logger.debug(s"Receiving and ignoring unknown message: ${message.toString}")
  }

  def controlHandler(inquirer: Option[ActorRef], message: Control): IO[Unit] =
    message match {
      case m: UploadSoftwareRequest                 => handleUploadSoftwareRequest(inquirer, m)
      case m: UploadSoftwareResult                  => handleUploadSoftwareResult(m)
      case m: SerialMonitorRequest                  => handleSerialMonitorRequest(inquirer, m)
      case m: SerialMonitorRequestStop              => handleSerialMonitorRequestStop(m)
      case m: SerialMonitorResult                   => handleSerialMonitorResult(m)
      case m: SerialMonitorMessageToClient          => handleSerialMonitorMessageToClient(m)
      case m: SerialMonitorMessageToAgent           => handleSerialMonitorMessageToAgent(m)
      case _: SerialMonitorListenersHeartbeatStart  => handleSerialMonitorListenersHeartbeatStart()
      case _: SerialMonitorListenersHeartbeatPing   => IO(())
      case _: SerialMonitorListenersHeartbeatPong   => handleSerialMonitorListenersHeartbeatPong()
      case _: SerialMonitorListenersHeartbeatFinish => handleSerialMonitorListenersHeartbeatFinish()
      case _: Ping                                  => IO(())
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

  def handleSerialMonitorRequestStop(message: SerialMonitorRequestStop): IO[Unit] =
    sendToAgent(message)

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
      // Reset state if upload happened
      _ <- IO.whenA(isMonitoring)(IO(setInitialState()))
    } yield ()

  def handleSerialMonitorMessageToClient(message: SerialMonitorMessageToClient): IO[Unit] =
    IO(pubSubMediator ! Publish(serialMonitorTopic, message))

  def handleSerialMonitorMessageToAgent(message: SerialMonitorMessageToAgent): IO[Unit] =
    sendToAgent(message)

  def handleSerialMonitorListenersHeartbeatStart(): IO[Unit] = {
    val startAndLaterFinish = IO { listenerHeartbeatsReceived = 0 } >>
      IO(pubSubMediator ! Publish(serialMonitorTopic, SerialMonitorListenersHeartbeatPing())) >>
      IO.sleep(listenerHeartbeatWaitTime) >>
      IO(self ! SerialMonitorListenersHeartbeatFinish())

    startAndLaterFinish.start.void
  }

  def handleSerialMonitorListenersHeartbeatPong(): IO[Unit] =
    IO { listenerHeartbeatsReceived += 1 }

  def handleSerialMonitorListenersHeartbeatFinish(): IO[Unit] =
    (if (listenerHeartbeatsReceived == 0) sendToAgent(SerialMonitorRequestStop())
     else sendToAgent(SerialMonitorRequest(None))) >>
      scheduleHeartbeatTest()
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
  ): Props = Props(new HardwareControlActor(pubSubMediator, out, hardwareId))

  def transformer(byteHandler: ByteString => Either[Control, Message]): MessageFlowTransformer[Control, Message] =
    (flow: Flow[Control, Message, _]) => {
      AkkaStreams.bypassWith[Message, Control, Message](Flow[Message].collect {
        case TextMessage(text) => decode[Control](text).swap.map(e =>
          CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
        case BinaryMessage(bytes: ByteString) => byteHandler(bytes)
      })(flow)
    }

  val controlTransformer = transformer((bytes: ByteString) =>
    Left(SerialMonitorMessageToClient(SerialMessageToClient(
      bytes.toArray.asCharsetString(defaultCharset).toBase64()))))

  val listenerTransformer = transformer((bytes: ByteString) =>
    Left(SerialMonitorMessageToAgent(SerialMessageToAgent(
      bytes.toArray.asCharsetString(defaultCharset).toBase64()))))

  def requestSerialMonitor(
    hardwareId: HardwareId,
    serialConfig: Option[SerialConfig],
  )(implicit actorSystem: ActorSystem, t: Timeout, iort: IORuntime): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(userActorPath(hardwareActor(hardwareId)))(actorSystem, implicitly)
      result <- QueryActor.queryActorT(
        hardwareRef,
        actorRef => Promise(actorRef, SerialMonitorRequest(serialConfig)),
        immediate = false,
      )
      monitorResult <- EitherT.fromEither[IO](result match {
        case SerialMonitorResult(result) => result.toLeft(())
        case _                           => Left("Hardware responded with an invalid response")
      })
    } yield monitorResult

  def sendToHardwareActor(
    hardwareId: HardwareId,
    serialMessage: Control,
  )(implicit actorSystem: ActorSystem, t: Timeout): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(userActorPath(hardwareActor(hardwareId)))(actorSystem, implicitly)
      _ <- EitherT.liftF(IO(hardwareRef ! serialMessage))
    } yield ()

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
