package diptestbed.domain

import cats.data.NonEmptyList
import diptestbed.domain.HardwareCameraError._
import diptestbed.domain.HardwareCameraEvent._
import diptestbed.domain.HardwareCameraMessage._
import scala.annotation.unused

object HardwareCameraMessageHandler {
  type HardwareCameraResult[A] = Either[
    HardwareCameraError,
    NonEmptyList[HardwareCameraEvent[A]],
  ]

  def handle[A](
    inquirer: => Option[A],
  )(@unused state: HardwareCameraState[A], message: HardwareCameraMessage): HardwareCameraResult[A] =
    message match {
      case _: Ping                          => Right(NonEmptyList.of(CameraPinged()))
      case _: StartLifecycle                => Right(NonEmptyList.of(Started()))
      case _: EndLifecycle                  => Right(NonEmptyList.of(Ended()))
      case CameraSubscription()             =>
        NonEmptyList.fromList(inquirer.map(Subscription(_)).toList).toRight(RequestInquirerObligatory())
      case StopBroadcasting()               => Right(NonEmptyList.of(BroadcastStopped()))
      case CameraUnavailable(reason)        => Right(NonEmptyList.of(CameraDropped(reason)))
      case CameraChunk(chunk)               => Right(NonEmptyList.of(ChunkReceived(chunk)))
      case CameraListenersHeartbeatStart()  => Right(NonEmptyList.of(CameraListenerHeartbeatStarted()))
      case CameraListenersHeartbeatPong()   => Right(NonEmptyList.of(CameraListenerHeartbeatReceived()))
      case CameraListenersHeartbeatFinish() => Right(NonEmptyList.of(CameraListenerHeartbeatFinished()))
    }

}
