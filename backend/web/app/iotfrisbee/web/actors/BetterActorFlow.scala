package iotfrisbee.web.actors

// Shamelessly stolen from https://stackoverflow.com/a/40297555

import akka.NotUsed
import akka.actor._
import akka.stream.scaladsl.{Flow, Keep, Sink, Source}
import akka.stream.{Materializer, OverflowStrategy}

import scala.annotation.nowarn

object BetterActorFlow {

  @nowarn
  def actorSource[Out](bufferSize: Int, overflowStrategy: OverflowStrategy)(implicit mat: Materializer) =
    Source.actorRef[Out](bufferSize, overflowStrategy)
    .toMat(Sink.asPublisher(false))(Keep.both).run()

  @nowarn
  def actorSink(actorRefForSink: ActorRef): Sink[Any, NotUsed] =
    Sink.actorRef(actorRefForSink, Status.Success(()))

  def actorRef[In, Out](
    props: ActorRef => Props,
    bufferSize: Int = 16, overflowStrategy: OverflowStrategy = OverflowStrategy.dropNew,
    maybeName: Option[String] = None)(
    implicit factory: ActorRefFactory, mat: Materializer): Flow[In, Out, _] = {
    val (outActor, publisher) = actorSource(bufferSize, overflowStrategy)

    def flowActorProps: Props = {
      Props(new Actor {
        val flowActor = context.watch(context.actorOf(props(outActor), "flowActor"))

        def receive = {
          case Status.Success(_) | Status.Failure(_) => flowActor ! PoisonPill
          case Terminated(_) => context.stop(self)
          case other => flowActor ! other
        }

        override def supervisorStrategy = OneForOneStrategy() { case _ => SupervisorStrategy.Stop }
      })
    }

    def actorRefForSink =
      maybeName.fold(factory.actorOf(flowActorProps)) { name => factory.actorOf(flowActorProps, name) }

    Flow.fromSinkAndSource(actorSink(actorRefForSink), Source.fromPublisher(publisher))

  }
}
