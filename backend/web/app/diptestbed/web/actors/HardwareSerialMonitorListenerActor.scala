package diptestbed.web.actors

import akka.actor.{Actor, ActorRef, ActorSystem, PoisonPill, Props}
import diptestbed.domain.{HardwareControlMessage, HardwareId, SerialConfig, HardwareSerialMonitorMessage => MonitorMessage}
import io.circe.syntax.EncoderOps
import diptestbed.protocol.Codecs._
import akka.cluster.pubsub.DistributedPubSubMediator.{Subscribe, SubscribeAck}
import cats.effect.IO
import diptestbed.web.actors.HardwareControlActor._
import cats.effect.unsafe.IORuntime
import diptestbed.domain.HardwareControlMessage._
import akka.util.{ByteString, Timeout}
import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.Charsets.{ByteOps, StringOps, defaultCharset}
import diptestbed.domain.HardwareSerialMonitorMessage.{MonitorUnavailable, SerialMessageToAgent}
import play.api.http.websocket._
import scala.concurrent.duration.DurationInt
import io.circe.parser.decode

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
        IO(pubSubMediator ! Subscribe(hardwareSerialMonitorTopic(hardwareId), self))
      case Left(error) =>
        // Send error to listener
        val message: MonitorMessage = MonitorMessage.MonitorUnavailable(error)
        sendToListener(message) >>
          // Stop this listener
          killListener("Monitor unavailable")
    }
    .void
    .unsafeRunAsync(_ => ())

  def sendToListener(message: MonitorMessage): IO[Unit] =
    IO(out ! (message match {
      case m: MonitorMessage.SerialMessageToClient =>
        BinaryMessage(ByteString.fromArray(m.base64Bytes.asBase64Bytes))
      case m => TextMessage(m.asJson.noSpaces)
    }))

  def killListener(reason: String): IO[Unit] = {
    // Stop websocket listener
    IO.sleep(5.seconds) >>
      IO(out ! CloseMessage(0, reason)) >>
      // Stop this actor
      IO(self ! PoisonPill)
  }

  def receive: Receive = {
    case badMessage: MonitorUnavailable =>
      val message: MonitorMessage = badMessage
      (sendToListener(message) >> killListener("Monitor not valid anymore"))
        .unsafeRunAsync(_ => ())
    case serialMessage: SerialMonitorMessageToClient =>
      val message: MonitorMessage = MonitorMessage.SerialMessageToClient(serialMessage.message.base64Bytes)
      sendToListener(message).unsafeRunAsync(_ => ())
    case _: SerialMonitorListenersHeartbeatPing =>
      sendToHardwareActor(hardwareId, SerialMonitorListenersHeartbeatPong()).value.unsafeRunAsync(_ => ())
    case text: TextMessage =>
      decode[HardwareControlMessage](text.data).toOption.foreach {
        case serialMessage: SerialMonitorMessageToAgent =>
          sendToHardwareActor(hardwareId, serialMessage).value.unsafeRunAsync(_ => ())
        case _ => ()
      }
    case binary: BinaryMessage =>
      val hydrated = binary.data.toArray.asCharsetString(defaultCharset).toBase64()
      val message = HardwareControlMessage.SerialMonitorMessageToAgent(
        SerialMessageToAgent(hydrated))
      sendToHardwareActor(hardwareId, message).value.unsafeRunAsync(_ => ())
    case _: SubscribeAck =>
      logger.info(s"Serial monitor listener for hardware #${hardwareId} subscribed")
    case _ => ()
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
}
