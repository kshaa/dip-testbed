package iotfrisbee.web.actors

import akka.actor.{ActorRef, ActorSystem}
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.IO

trait ActorHelper {
  def resolveActorRef(
    actorPath: String,
  )(implicit actorSystem: ActorSystem, t: Timeout): EitherT[IO, String, ActorRef] = {
    val resolutionFuture = IO(actorSystem.actorSelection(actorPath).resolveOne())
    val resolution = IO.fromFuture(resolutionFuture)
    val resolutionError = Left("Entity not online")
    val resolutionOrError = resolution.redeem(_ => resolutionError, Right.apply)

    EitherT(resolutionOrError)
  }

  def userActorPath(actorPath: String): String = s"/user/${actorPath}"
}
