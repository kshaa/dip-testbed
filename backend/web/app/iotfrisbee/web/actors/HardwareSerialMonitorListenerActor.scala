package iotfrisbee.web.actors

import akka.actor.{Actor, ActorRef, ActorSystem, PoisonPill, Props}
import iotfrisbee.domain.HardwareId
import io.circe.syntax.EncoderOps
import iotfrisbee.protocol.Codecs._
import akka.cluster.pubsub.DistributedPubSubMediator.{Subscribe, SubscribeAck}
import cats.effect.IO
import iotfrisbee.web.actors.HardwareControlActor._
import cats.effect.unsafe.IORuntime
import iotfrisbee.domain.HardwareControlMessage._
import akka.util.Timeout

import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import iotfrisbee.domain.HardwareSerialMonitorMessage.{BaudrateChanged, MonitorUnavailable}
import iotfrisbee.domain.{HardwareSerialMonitorMessage => MonitorMessage}
import play.api.http.websocket._

class HardwareSerialMonitorListenerActor(
  pubSubMediator: ActorRef,
  out: ActorRef,
  hardwareId: HardwareId,
  baudrate: Option[Baudrate],
)(implicit
  actorSystem: ActorSystem,
  iort: IORuntime,
  @unused timeout: Timeout,
) extends Actor
    with LazyLogging {
  logger.info(s"Serial monitor listener for hardware #${hardwareId} spawned")

  // Send monitor actor request for listening w/ a given baudrate and react accordingly
  requestSerialMonitor(hardwareId, baudrate).value
    .flatMap {
      case Right(baudrateState) =>
        // Send baudrate to listener
        sendToListener(MonitorMessage.BaudrateSet(baudrateState.baudrate)) >>
          // Start listening to serial monitor topic
          IO(pubSubMediator ! Subscribe(hardwareSerialMonitorTopic(hardwareId), self))
      case Left(error) =>
        // Send error to listener
        sendToListener(MonitorMessage.MonitorUnavailable(error)) >>
          // Stop this listener
          killListener("Monitor unavailable")
    }
    .void
    .unsafeRunAsync(_ => ())

  def sendToListener(message: MonitorMessage): IO[Unit] =
    IO(out ! TextMessage(message.asJson.noSpaces))

  def killListener(reason: String): IO[Unit] = {
    // Stop websocket listener
    IO(out ! CloseMessage(0, reason)) >>
      // Stop this actor
      IO(self ! PoisonPill)
  }

  def receive: Receive = {
    case badMessage: BaudrateChanged =>
      (sendToListener(badMessage) >> killListener("Monitor not valid anymore"))
        .unsafeRunAsync(_ => ())
    case badMessage: MonitorUnavailable =>
      (sendToListener(badMessage) >> killListener("Monitor not valid anymore"))
        .unsafeRunAsync(_ => ())
    case monitorMessage: MonitorMessage =>
      sendToListener(monitorMessage).unsafeRunAsync(_ => ())
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
    baudrate: Option[Baudrate],
  )(implicit
    iort: IORuntime,
    timeout: Timeout,
    actorSystem: ActorSystem,
  ): Props = Props(new HardwareSerialMonitorListenerActor(pubSubMediator, out, hardwareId, baudrate))
}
