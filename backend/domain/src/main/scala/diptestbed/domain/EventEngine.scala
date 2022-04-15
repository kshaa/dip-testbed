package diptestbed.domain

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.{Applicative, Monad, Parallel}
import cats.data.NonEmptyList
import cats.implicits._
import com.typesafe.scalalogging.Logger

object EventEngine {
  val logger = Logger(getClass.getName)

  type MessageResult[F[_], E, S] =
    Either[F[Unit], NonEmptyList[(E, S, Option[F[Unit]])]]

  def defaultOnError[E, F[_]: Applicative, A](inquirer: Option[A], send: (A, E) => F[Unit])(error: E): F[Unit] =
    inquirer.traverse(send(_, error)).void

  def onMessage[M, X, E, S, F[_]](
    initialState: => S,
    handleMessage: (S, M) => Either[X, NonEmptyList[E]],
    toSideeffect: (S, E) => Option[F[Unit]],
    toState: (S, E) => S,
    onError: X => F[Unit]
  )(m: M): MessageResult[F, E, S] = {
    logger.debug(f"Message: ${m}")
    handleMessage(initialState, m).bimap(
      onError,
      _.foldLeft(List.empty[(E, S, Option[F[Unit]])]) {
        case (result, event) =>
          val previousState = result.headOption.map(_._2).getOrElse(initialState)
          val state = toState(previousState, event)
          val sideeffect = toSideeffect(previousState, event)

          result :+ (event, state, sideeffect)
      }.toNel.get, // This shouldn't throw, because we're folding over a non-empty list
    )
  }

  def unsafeMaterializeMessageResultIO[E, S](
    result: MessageResult[IO, E, S],
    setState: S => Unit,
  )(implicit ioruntime: IORuntime): Unit =
    result.bimap(
      errorImpact => errorImpact.unsafeRunAndForget(),
      eventImpact => {
        setState(eventImpact.last._2)
        eventImpact.toList.foreach(_._3.foreach(_.unsafeRunAndForget()))
      },
    )

  def multiSideeffectProjection[S, E, F[_]: Parallel: Monad](
    toSideeffects: List[(S, E) => Option[F[Unit]]],
  )(state: S, event: E): Option[F[Unit]] = {
    logger.debug(f"Event: ${event}")
    val effects = toSideeffects.flatMap(_(state, event))
    if (effects.isEmpty) None
    else Some(effects.parSequence.void)
  }
}
