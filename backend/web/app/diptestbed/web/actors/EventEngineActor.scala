package diptestbed.web.actors

import akka.actor._
import akka.cluster.pubsub.DistributedPubSubMediator.{Publish, Subscribe}
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain._

abstract class EventEngineActor[S, M, E] extends Actor {
  implicit val iort: IORuntime

  var state: S

  val startMessage: Option[M]
  val endMessage: Option[M]

  def setState(newState: S): Unit = {
    state = newState
  }

  def send(actorRef: ActorRef, message: Any): IO[Unit] =
    IO(actorRef ! message)

  def unsafeMaterializeResult(
    result: MessageResult[IO, E, S],
  ): Unit = EventEngine.unsafeMaterializeMessageResultIO(result, setState)

  override def preStart(): Unit = {
    super.preStart()
    startMessage.foreach(message =>
      unsafeMaterializeResult(onMessage(None)(message)))
  }

  def receiveMessage: PartialFunction[Any, (Option[ActorRef], M)]

  override def receive: Receive = {
    case Terminated =>
      endMessage.foreach(message =>
        unsafeMaterializeResult(onMessage(None)(message)))
    case value if receiveMessage.isDefinedAt(value) =>
      val (inquirer, message) = receiveMessage(value)
      unsafeMaterializeResult(onMessage(inquirer)(message))
  }

  def onMessage(
    inquirer: => Option[ActorRef],
  ): M => MessageResult[IO, E, S]
}

abstract class PubSubEngineActor[S, M, E] extends EventEngineActor[S, M, E] {
    val pubSubMediator: ActorRef

    def subscriptionMessage(topic: PubSubTopic, actorRef: ActorRef): Subscribe = Subscribe(topic.text(), actorRef)

    def publish(topic: PubSubTopic, message: Any): IO[Unit] =
      send(pubSubMediator, Publish(topic.text(), message))
}

