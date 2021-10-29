package iotfrisbee.web.actors

import akka.actor.{Actor, ActorRef, ActorSystem, PoisonPill, Props}
import akka.pattern.{AskTimeoutException, ask}
import akka.util.Timeout
import cats.data.EitherT
import cats.effect.{Deferred, IO}
import cats.effect.unsafe.IORuntime
import iotfrisbee.web.actors.QueryActor.failableFutureIO

import scala.concurrent.Future

/**
  * This class couldn't be any dumber.
  * Essentially the ask pattern doesn't work properly in one of my controllers.
  * For some reason the inquired actor receives its own actor path instead,
  * so the controller ask doesn't get a response and times out.
  * So I've created this actor just to be a proxy for an ask query.
  *
  * immediate = true :: Ask by use of pattern `?`
  * immediate = false :: Ask by expecting a received message
  */
class QueryActor[O](
  destination: ActorRef,
  message: ActorRef => O,
  signal: Deferred[IO, Either[Throwable, Any]],
  immediate: Boolean,
)(implicit
  iort: IORuntime,
  timeout: Timeout,
) extends Actor {
  val builtMessage: O = message(self)
  def resolveQuery(result: Either[Throwable, Any]): IO[Unit] =
    for {
      _ <- signal.complete(result)
      _ <- IO(self ! PoisonPill)
    } yield ()

  val query =
    if (immediate)
      for {
        // [immediate] Send and expect answer
        safeResult <- failableFutureIO(destination ? builtMessage)
        // [immediate] Resolve after ask pattern finishes
        _ <- resolveQuery(safeResult)
      } yield ()
    else
      for {
        // [!immediate] Send out message
        _ <- IO(destination ! builtMessage)
        // [!immediate] Fail if we time out
        _ <- (IO.sleep(timeout.duration) *>
            resolveQuery(Left(new AskTimeoutException(s"Message timed out in ${timeout.duration}")))).start
      } yield ()

  query.unsafeRunSync()

  def receive: Receive =
    message => {
      // [!immediate] Resolve when receiving message
      resolveQuery(Right(message)).unsafeRunSync()
    }
}

object QueryActor {
  def props[O](
    destination: ActorRef,
    message: ActorRef => O,
    signal: Deferred[IO, Either[Throwable, Any]],
    immediate: Boolean,
  )(implicit
    iort: IORuntime,
    timeout: Timeout,
  ): Props = Props(new QueryActor(destination, message, signal, immediate))

  def query[O](
    destination: ActorRef,
    message: ActorRef => O,
    immediate: Boolean = true,
  )(implicit
    actorSystem: ActorSystem,
    iort: IORuntime,
    timeout: Timeout,
  ): IO[Either[Throwable, Any]] =
    for {
      signal <- Deferred[IO, Either[Throwable, Any]]
      actor = props(destination, message, signal, immediate)
      _ <- IO(actorSystem.actorOf(actor))
      result <- signal.get
    } yield result

  def queryActorT[O](
    actorRef: ActorRef,
    message: ActorRef => O,
    immediate: Boolean,
  )(implicit actorSystem: ActorSystem, iort: IORuntime, t: Timeout): EitherT[IO, String, Any] = {
    EitherT(
      QueryActor.query(
        actorRef,
        message,
        immediate,
      ),
    ).bimap(
      error => s"Failed to receive answer from hardware: ${error}",
      identity,
    )
  }

  def futureIO[T](value: Future[T]): IO[T] =
    IO.fromFuture(IO(value))

  def failableFutureIO[T](value: Future[T]): IO[Either[Throwable, T]] =
    futureIO(value).redeem(Left.apply, Right.apply)

  case class Promise[T](inquirer: ActorRef, message: T)
}
