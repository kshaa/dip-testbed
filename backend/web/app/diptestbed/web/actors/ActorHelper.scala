package diptestbed.web.actors

import akka.actor.{ActorRef, ActorSystem}
import akka.stream.scaladsl.Flow
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.IO
import diptestbed.domain.ActorPath
import play.api.http.websocket.Message
import play.api.libs.streams.AkkaStreams
import play.api.mvc.WebSocket.MessageFlowTransformer

object ActorHelper {
  case class UserPrefixedActorPath[A <: ActorPath](subpath: A) extends ActorPath {
    def text() = s"/user/${subpath.text()}"
  }

  def resolveActorRef(
    actorPath: String,
  )(implicit actorSystem: ActorSystem, t: Timeout): EitherT[IO, String, ActorRef] = {
    val resolutionFuture = IO(actorSystem.actorSelection(actorPath).resolveOne())
    val resolution = IO.fromFuture(resolutionFuture)
    val resolutionError = Left("Entity not online")
    val resolutionOrError = resolution.redeem(_ => resolutionError, Right.apply)

    EitherT(resolutionOrError)
  }

  def websocketFlowTransformer[I, O](
    inputTransform: PartialFunction[Message, Either[Message, I]],
    outputTransform: O => Message,
  ): MessageFlowTransformer[I, O] = {
    val input = Flow[Message].collect(inputTransform.andThen(_.swap))
    def output(output: Flow[I, O, _]) = output.map(outputTransform)

    (flow: Flow[I, O, _]) => AkkaStreams.bypassWith[Message, I, Message](input)(output(flow))
  }
}
