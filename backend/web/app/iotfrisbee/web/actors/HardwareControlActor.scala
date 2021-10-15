package iotfrisbee.web.actors

import akka.actor.{Actor, ActorRef, Props}
import iotfrisbee.domain.{HardwareControlState, HardwareId, HardwareControlMessage => Control}
import play.api.http.websocket.{CloseCodes, CloseMessage, WebSocketCloseException}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.parser.decode
import io.circe.syntax.EncoderOps
import iotfrisbee.domain.HardwareControlState.Initial
import iotfrisbee.protocol.Codecs.{hardwareControlMessageDecoder, hardwareControlMessageEncoder}
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import iotfrisbee.web.actors.HardwareControlActor.hardwareEventTopic
import cats.effect.unsafe.IORuntime
import scala.annotation.unused

class HardwareControlActor(
  pubSubMediator: ActorRef,
  out: ActorRef,
  hardwareId: HardwareId)(implicit
  @unused iort: IORuntime) extends Actor {
  val eventTopic: String = hardwareEventTopic(hardwareId)
  var state: HardwareControlState = Initial

  def receive: Receive = {
    case controlMessage: Control =>
      pubSubMediator ! Publish(eventTopic, controlMessage)
      out ! controlMessage.asJson.noSpaces
  }
}

object HardwareControlActor {
  val subscribed = "subscribed"
  def hardwareActor(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-actor"
  def hardwareEventTopic(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-event"
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId)(implicit @unused iort: IORuntime): Props =
    Props(new HardwareControlActor(pubSubMediator, out, hardwareId))

  implicit val transformer: MessageFlowTransformer[Control, String] =
    MessageFlowTransformer.stringMessageFlowTransformer.map(x => {
      decode[Control](x).toTry.getOrElse {
        throw WebSocketCloseException(
          CloseMessage(Some(CloseCodes.Unacceptable), "Failed to parse message"))
      }
    })
}
