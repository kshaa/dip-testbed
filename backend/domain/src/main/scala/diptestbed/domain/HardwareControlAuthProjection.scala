package diptestbed.domain

import cats.Monad
import cats.implicits._
import diptestbed.domain.HardwareControlEvent._
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._

object HardwareControlAuthProjection {
  def project[F[_]: Monad, A](
    auth: (String, String) => F[Either[String, User]],
    send: (A, HardwareControlMessage) => F[Unit]
  )(state: HardwareControlState[A], event: HardwareControlEvent[A]): Option[F[Unit]] = {
    event match {
      case CheckingAuth(username, password) =>
        Some(auth(username, password).flatMap(_.bimap(
          error => send(state.self, AuthFailure(error)),
          user => send(state.self, AuthSuccess(user))
        ).merge))
      case _ => None
    }
  }
}
