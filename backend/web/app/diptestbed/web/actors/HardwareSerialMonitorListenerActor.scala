package diptestbed.web.actors

import akka.actor._
import diptestbed.domain._
import io.circe.syntax.EncoderOps
import diptestbed.protocol.Codecs._
import akka.cluster.pubsub.DistributedPubSubMediator.Subscribe
import cats.effect.IO
import diptestbed.web.actors.HardwareControlActor._
import cats.effect.unsafe.IORuntime
import akka.util.{ByteString, Timeout}
import io.circe.parser.decode
import cats.implicits._
import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._
import diptestbed.domain.HardwareSerialMonitorMessageNonBinary._
import diptestbed.domain.HardwareControlMessageInternal.SerialMonitorListenersHeartbeatPing
import diptestbed.web.actors.ActorHelper.websocketFlowTransformer
import play.api.http.websocket._
import play.api.mvc.WebSocket.MessageFlowTransformer
import scala.concurrent.duration.DurationInt

class HardwareSerialMonitorListenerActor(
  pubSubMediator: ActorRef,
  out: ActorRef,
  hardwareId: HardwareId,
  serialConfig: Option[SerialConfig],
)(implicit
  actorSystem: ActorSystem,
  iort: IORuntime,
  @unused timeout: Timeout,
) extends Actor
    with LazyLogging {
  logger.info(s"Serial monitor listener for hardware #${hardwareId} spawned")

  // Send monitor actor request for listening w/ a given baudrate and react accordingly
  requestSerialMonitor(hardwareId, serialConfig).value
    .flatMap {
      case Right(_) =>
        // Start listening to serial monitor topic
        IO(pubSubMediator ! Subscribe(hardwareId.serialTopic().text(), self))
      case Left(error) =>
        // Send error to listener
        val message: HardwareSerialMonitorMessageNonBinary = MonitorUnavailable(error)
        sendToListener(message) >>
          // Stop this listener
          killListener("Monitor unavailable")
    }
    .void
    .unsafeRunAsync(_ => ())

  def sendToListener(message: HardwareSerialMonitorMessage): IO[Unit] =
    IO(out ! message)

  def killListener(reason: String): IO[Unit] = {
    // Stop websocket listener
    IO.sleep(5.seconds) >>
      IO(out ! ConnectionClosed(reason)) >>
      // Stop this actor
      IO(self ! PoisonPill)
  }

  def receive: Receive = {
    // Initial hardware monitoring request to hardware control failed
    case badMessage: HardwareSerialMonitorMessageNonBinary.MonitorUnavailable =>
      val message: HardwareSerialMonitorMessage = badMessage
      (sendToListener(message) >> killListener("Monitor not valid anymore")).unsafeRunAsync(_ => ())
    // Hardware monitoring failed later in lifecycle
    case badMessage: HardwareControlMessageExternalNonBinary.SerialMonitorUnavailable =>
      val message: HardwareSerialMonitorMessage =
        HardwareSerialMonitorMessageNonBinary.MonitorUnavailable(badMessage.reason)
      (sendToListener(message) >> killListener("Monitor not valid anymore")).unsafeRunAsync(_ => ())
    // Hardware control published message to listeners
    case serialToClientMessage: SerialMonitorMessageToClient =>
      val message: HardwareSerialMonitorMessage = SerialMessageToClient(serialToClientMessage.message.bytes)
      sendToListener(message).unsafeRunAsync(_ => ())
    // Hardware control published heartbeat request to listeners
    case _: SerialMonitorListenersHeartbeatPing =>
      println("Received ping, responding pong")
      sendToHardwareActor(hardwareId, SerialMonitorListenersHeartbeatPong()).value.unsafeRunAsync(_ => ())
    // Listener is sending a message to hardware control
    case serialToAgentMessage: SerialMonitorMessageToAgent =>
      sendToHardwareActor(hardwareId, serialToAgentMessage).value.unsafeRunAsync(_ => ())
  }
}

object HardwareSerialMonitorListenerActor {
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId,
    serialConfig: Option[SerialConfig],
  )(implicit
    iort: IORuntime,
    timeout: Timeout,
    actorSystem: ActorSystem,
  ): Props = Props(new HardwareSerialMonitorListenerActor(pubSubMediator, out, hardwareId, serialConfig))

  val listenerTransformer: MessageFlowTransformer[HardwareControlMessage, HardwareSerialMonitorMessage] =
    websocketFlowTransformer(
      {
        case TextMessage(text) =>
          decode[HardwareControlMessageNonBinary](text)
            .leftMap(e => CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
        case BinaryMessage(bytes: ByteString) =>
          Right(SerialMonitorMessageToAgent(SerialMessageToAgent(bytes.toArray)))
      },
      {
        case m: SerialMessageToAgent                  => BinaryMessage(ByteString.fromArray(m.bytes))
        case m: SerialMessageToClient                 => BinaryMessage(ByteString.fromArray(m.bytes))
        case ConnectionClosed(reason)                 => CloseMessage(0, reason)
        case m: HardwareSerialMonitorMessageNonBinary => TextMessage(m.asJson.noSpaces)
      },
    )

}
