package iotfrisbee.web.actors

import akka.actor.{Actor, ActorRef, Props}
import akka.cluster.pubsub.DistributedPubSubMediator._
import iotfrisbee.web.actors.CentralizedPubSubActor._

// This is is not a performant Akka PubSub implementation,
// it should be used only for debugging and testing,
// it has been created to allow for local actorsystem (non-cluster) tests,
// it also isn't a 1-to-1 interface replication,
// it only implements what's needed for IotFrisbee purposes,
// use akka.cluster.pubsub.DistributedPubSub for production
class CentralizedPubSubActor() extends Actor {
  var subscriptions: Map[String, List[ActorRef]] = Map.empty

  def receive: Receive = {
    case s: Subscribe =>
      withSubscription(subscriptions, s.topic, s.ref)
        .map(subscriptions = _)
        .map(_ => acknowledgeSub(s))

    case u: Unsubscribe =>
      withoutSubscription(subscriptions, u.topic, u.ref)
        .map(subscriptions = _)
        .map(_ => acknowledgeUnsub(u))

    case Publish(topic, message, _) =>
      subscriptions
        .get(topic)
        .map(_.foreach(_ ! message))
  }
}

object CentralizedPubSubActor {
  def withSubscription[A](
    subscriptions: Map[String, List[A]],
    topic: String,
    subscription: A,
  ): Option[Map[String, List[A]]] = {
    val subscribers = subscriptions.getOrElse(topic, List.empty)
    val newSubscriber = Option.when(!subscribers.contains(subscription))(subscription)
    val newSubscribers = newSubscriber.map(subscribers :+ _)
    val newSubscriptions = newSubscribers.map(subscriptions.updated(topic, _))

    newSubscriptions
  }

  def acknowledgeSub(subscription: Subscribe): Unit =
    subscription.ref ! SubscribeAck(subscription)

  def withoutSubscription[A](
    subscriptions: Map[String, List[A]],
    topic: String,
    subscription: A,
  ): Option[Map[String, List[A]]] = {
    val newSubscribers = subscriptions
      .get(topic)
      .flatMap(subscribers =>
        Option
          .when(subscribers.contains(subscription))(subscribers.filterNot(_ == subscription)),
      )
    val newSubscriptions = newSubscribers.map(subscriptions.updated(topic, _))

    newSubscriptions
  }

  def acknowledgeUnsub(unsubscription: Unsubscribe): Unit =
    unsubscription.ref ! UnsubscribeAck(unsubscription)

  def props: Props = Props(new CentralizedPubSubActor())
}
