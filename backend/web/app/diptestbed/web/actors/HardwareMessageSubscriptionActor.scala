package diptestbed.web.actors

import akka.actor.{Actor, ActorRef, Props}
import akka.cluster.pubsub.DistributedPubSubMediator._
import diptestbed.domain.HardwareId
import diptestbed.web.actors.HardwareMessageSubscriptionActor._

class HardwareMessageSubscriptionActor(pubSubMediator: ActorRef, out: ActorRef, hardwareId: HardwareId) extends Actor {
  pubSubMediator ! Subscribe(hardwareMessageTopic(hardwareId), self)

  def receive: Receive = {
    // Hopefully if I don't make any mistakes, then this String will be Json[HardwareMessage].noSpaces
    case hardwareMessage: String => out ! hardwareMessage
    case _: SubscribeAck         => out ! subscribed
  }
}

object HardwareMessageSubscriptionActor {
  val subscribed = "subscribed"
  def hardwareMessageTopic(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-messages"
  def props(pubSubMediator: ActorRef, out: ActorRef, hardwareId: HardwareId): Props =
    Props(new HardwareMessageSubscriptionActor(pubSubMediator, out, hardwareId))
}
